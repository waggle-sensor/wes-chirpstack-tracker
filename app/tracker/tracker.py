import logging
import argparse
import os
from pathlib import Path
from argparse import Namespace
from .parse import *
from .convert_date import *
from chirpstack_api_wrapper import ChirpstackClient
try:  # production # pragma: no cover
    from django_client import DjangoClient
    from mqtt_client import MqttClient
    from manifest import Manifest
except ImportError:  # testing
    from app.django_client import DjangoClient
    from app.mqtt_client import MqttClient
    from app.manifest import Manifest

class Tracker(MqttClient):
    """
    A class that ties all clients together to track lorawan records
    """
    def __init__(self, args: Namespace):
        super().__init__(args)
        self.c_client = ChirpstackClient(args.chirpstack_account_email,args.chirpstack_account_password,args.chirpstack_api_interface)
        self.d_client = DjangoClient(args)

    #if execution of this method slows down mqtt client's network loop
    # consider offloading tasks to seperate thread using 'threading' module
    def on_message(self, client, userdata, message):
        #log message if debug flag was passed
        self.log_message(message) if self.args.debug else None

        #parse message for metadata and deviceInfo. 
        result = self.parse_message(message)
        if result is not None:
            try:
                metadata, deviceInfo = result
            except ValueError as e:
                logging.error(f"Tracker.on_message(): Message did not parse correctly, {e}")
        else:
            return

        #load the node manifest
        manifest = Manifest(self.args.manifest)

        #retrieve data from chirpstack
        device_resp = self.c_client.get_device(deviceInfo["devEui"])
        deviceprofile_resp = self.c_client.get_device_profile(deviceInfo["deviceProfileId"])
        act_resp = self.c_client.get_device_activation(deviceInfo["devEui"])

        #check for lorawan connection in server
        # lc/ld/sh search: True=found, False=404 missing, None=ambiguous/error (do not create)
        server_lc_exist = self.d_client.lc_search(deviceInfo["devEui"])
        if server_lc_exist is None:
            logging.error(
                f"Tracker.on_message(): ambiguous lorawan connection lookup for {deviceInfo['devEui']}; skipping"
            )
            return

        #if lorawan connection exist in django then...
        if server_lc_exist:
            #update lorawan device, connection, and key                
            self.update_ld(deviceInfo["devEui"], device_resp)
            self.update_lc(deviceInfo["devEui"], device_resp, deviceprofile_resp)
            self.update_lk(deviceInfo["devEui"], act_resp, deviceprofile_resp)
        else:
            #if lorawan device exist in django then...
            ld_exist = self.d_client.ld_search(deviceInfo["devEui"])
            if ld_exist is None:
                logging.error(
                    f"Tracker.on_message(): ambiguous lorawan device lookup for {deviceInfo['devEui']}; skipping"
                )
                return
            if ld_exist:
                # update lorawan device
                self.update_ld(deviceInfo["devEui"], device_resp) 
            #else lorawan device does not exist in django then...
            else:
                # Resolve existing SH (including duplicate hw_model fallback) before creating.
                # hw_model is not a stable unique key in Django; never create on ambiguous lookup.
                sh_id = self.resolve_sh_id(deviceprofile_resp)
                if sh_id is None:
                    logging.error(
                        f"Tracker.on_message(): could not resolve sensor hardware for {deviceInfo['devEui']}; skipping create"
                    )
                    return
                # create a new lorawan device
                self.create_ld(deviceInfo["devEui"], sh_id, device_resp)

            #create a new lorawan connection and key
            lc_str = self.create_lc(deviceInfo["devEui"], device_resp, deviceprofile_resp)
            self.create_lk(deviceInfo["devEui"], lc_str, act_resp, deviceprofile_resp)

        #update manifest
        self.update_manifest(deviceInfo["devEui"], manifest, device_resp, deviceprofile_resp)
        return
    
    def update_ld(self, deveui: str, device_resp: dict):
        """
        Update lorawan device using mqtt message, chirpstack client, and django client
        device_resp: the output of chirpstack client's get_device
        """        
        battery_level = device_resp.device_status.battery_level
        dev_name = replace_spaces(device_resp.device.name)
        ld_data = {
            "name": dev_name,
            "battery_level": battery_level
        }
        self.d_client.update_ld(deveui, ld_data)

        return

    def create_ld(self, deveui: str, sh_id: int, device_resp: dict):
        """
        Create lorawan device using mqtt message, chirpstack client, and django client
        sh_id: sensor hardware record id in django
        device_resp: the output of chirpstack client's get_device
        """
        battery_level = device_resp.device_status.battery_level
        dev_name = replace_spaces(device_resp.device.name)
        ld_data = {
            "name": dev_name,
            "battery_level": battery_level,
            "hardware": sh_id,
            "deveui": deveui
        }
        self.d_client.create_ld(ld_data)

        return

    def update_lc(self, deveui: str, device_resp: dict, deviceprofile_resp: dict):
        """
        Update lorawan connection using mqtt message, chirpstack client, and django client
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """   
        dev_name = replace_spaces(device_resp.device.name)
        datetime_obj_utc = epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        margin = device_resp.device_status.margin
        expected_uplink = deviceprofile_resp.device_profile.uplink_interval
        con_type = "OTAA" if deviceprofile_resp.device_profile.supports_otaa else "ABP"
        lc_data = {
            "connection_name": dev_name,
            'last_seen_at': last_seen_at, 
            "margin": margin,
            "expected_uplink_interval_sec": expected_uplink,
            "connection_type": con_type
        }
        self.d_client.update_lc(deveui, lc_data)

        return

    def create_lc(self, deveui: str, device_resp: dict, deviceprofile_resp: dict) -> str:
        """
        Create a lorawan connection using mqtt message, chirpstack client, and django client.
        Returns the lorawan connection uid in django.
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        dev_name = replace_spaces(device_resp.device.name)
        datetime_obj_utc = epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        margin = device_resp.device_status.margin
        expected_uplink = deviceprofile_resp.device_profile.uplink_interval
        con_type = "OTAA" if deviceprofile_resp.device_profile.supports_otaa else "ABP"
        lc_data = {
            "node": self.args.vsn,
            "lorawan_device": deveui,
            "connection_name": dev_name,
            'last_seen_at': last_seen_at, 
            "margin": margin,
            "expected_uplink_interval_sec": expected_uplink,
            "connection_type": con_type
        }
        response = self.d_client.create_lc(lc_data)
        if response['json_body']:
            lc_str = self.args.vsn + "-" + dev_name + "-" + deveui
            return lc_str
        else:
            logging.error("Tracker.create_lc(): d_client.create_lc() did not return a valid response")
            return None
        
    def update_lk(self, deveui: str, act_resp: dict, deviceprofile_resp: dict):
        """
        Update lorawan keys using mqtt message, chirpstack client, and django client
        act_resp: the output of chirpstack client's get_device_activation()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        con_type = "OTAA" if deviceprofile_resp.device_profile.supports_otaa else "ABP"
        nwk_key = act_resp.device_activation.nwk_s_enc_key
        app_s_key = act_resp.device_activation.app_s_key
        dev_adr = act_resp.device_activation.dev_addr
        lk_data = {
            "network_Key": nwk_key, 
            "app_session_key": app_s_key,
            "dev_address": dev_adr
        }
        if con_type == "OTAA":
            lw_v = deviceprofile_resp.device_profile.mac_version
            key_resp = self.c_client.get_device_app_key(deveui,lw_v)
            lk_data["app_key"] = key_resp
        self.d_client.update_lk(deveui, lk_data)

        return

    def create_lk(self, deveui: str, lc_str: str, act_resp: dict, deviceprofile_resp: dict):
        """
        Create lorawan keys using mqtt message, chirpstack client, and django client
        lc_str: the unique string of the lorawan connection. Used to reference the lorawan connection record
        act_resp: the output of chirpstack client's get_device_activation()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        con_type = "OTAA" if deviceprofile_resp.device_profile.supports_otaa else "ABP"
        nwk_key = act_resp.device_activation.nwk_s_enc_key
        app_s_key = act_resp.device_activation.app_s_key
        dev_adr = act_resp.device_activation.dev_addr
        lk_data = {
            "lorawan_connection": lc_str,
            "network_Key": nwk_key, 
            "app_session_key": app_s_key,
            "dev_address": dev_adr
        }
        if con_type == "OTAA":
            lw_v = deviceprofile_resp.device_profile.mac_version
            key_resp = self.c_client.get_device_app_key(deveui,lw_v)
            lk_data["app_key"] = key_resp
        self.d_client.create_lk(lk_data)

        return

    def resolve_sh_id(self, deviceprofile_resp: dict):
        """
        Resolve sensor hardware id for a device profile.
        - Use existing record when GET by hw_model succeeds
        - Create only on confirmed 404
        - On ambiguous GET (e.g. duplicate hw_model → 500), list and reuse lowest id
        - Never create when lookup is ambiguous, to avoid orphan duplicates
        """
        hw_model = clean_hw_model(deviceprofile_resp.device_profile.name)
        response = self.d_client.get_sh(hw_model)
        body = response.get("json_body")
        if isinstance(body, dict) and body.get("id") is not None:
            return body["id"]

        status_code = response.get("status_code")
        if status_code == 404:
            sh_id = self.create_sh(deviceprofile_resp)
            if sh_id is not None:
                return sh_id
            # create raced/failed; reuse any existing row instead of creating another
            logging.warning(
                f"Tracker.resolve_sh_id(): create failed for hw_model={hw_model}; falling back to list"
            )
            return self.d_client.find_sh_id(hw_model)

        # Ambiguous/error (common when hw_model is not unique): reuse oldest match, do not create
        logging.error(
            f"Tracker.resolve_sh_id(): ambiguous sensor hardware lookup for hw_model={hw_model} "
            f"(status={status_code}); reusing existing record if found"
        )
        return self.d_client.find_sh_id(hw_model)

    #TODO: consider using Tanuki to fill out fields like description, manufacturer, etc. in sensor hardware
    def create_sh(self, deviceprofile_resp: dict) -> int:
        """
        Create sensor hardware using django client. Returns the sensor hardware record id
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        hardware = deviceprofile_resp.device_profile.name
        hw_model = clean_hw_model(deviceprofile_resp.device_profile.name)
        description = deviceprofile_resp.device_profile.description
        capabilities = [35] #lorawan = 35
        sh_data = {
            "hardware": hardware,
            "hw_model": hw_model,
            "description": description,
            "capabilities": capabilities
        }
        response = self.d_client.create_sh(sh_data)
        if response['json_body']:
            return response['json_body'].get('id')
        else:
            logging.error("Tracker.create_sh(): d_client.create_sh() did not return a valid response")
            return None

    def update_manifest(self, deveui: str, manifest: Manifest, device_resp: dict, deviceprofile_resp: dict):
        """
        Update manifest using mqtt message, chirpstack client, django client, and manifest
        dev_exist: boolean that tells if device exist in manifest
        manifest: Manifest object
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        datetime_obj_utc = epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        margin = device_resp.device_status.margin
        expected_uplink = deviceprofile_resp.device_profile.uplink_interval
        con_type = "OTAA" if deviceprofile_resp.device_profile.supports_otaa else "ABP"
        battery_level = device_resp.device_status.battery_level
        dev_name = replace_spaces(device_resp.device.name)
        manifest_data = {
            "connection_name": dev_name,
            "last_seen_at": last_seen_at,
            "margin": margin,
            "expected_uplink_interval_sec": expected_uplink,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": deveui,
                "name": dev_name,
                "battery_level": battery_level,
            }
        }
        #include hardware in manifest_data when the device is not in manifest
        #TODO: consider using Tanuki to fill out fields like description, manufacturer, etc. in sensor hardware
        if not manifest.ld_search(deveui):
            #Sensor hardware data is always coming from chirpstack client, so if django has updated
            #   sensor hardware data the manifest will not show it until update-stack.sh runs
            hardware = deviceprofile_resp.device_profile.name
            hw_model = clean_hw_model(deviceprofile_resp.device_profile.name)
            description = deviceprofile_resp.device_profile.description
            capabilities = ["lorawan"] 
            manifest_data["lorawandevice"]["hardware"] = {
                "hardware": hardware,
                "hw_model": hw_model,
                "capabilities": capabilities,
                "description": description
        }

        manifest.update_manifest(manifest_data)
        return

def main(): # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument(
        "--vsn",
        default=os.getenv("WAGGLE_NODE_VSN"),
        help="The Node's vsn.",
    )
    parser.add_argument(
        "--mqtt-server-ip",
        default=os.getenv("MQTT_SERVER_HOST"),
        help="MQTT server IP address",
    )
    parser.add_argument(
        "--mqtt-server-port",
        default=os.getenv("MQTT_SERVER_PORT"),
        help="MQTT server port",
        type=int,
    )
    parser.add_argument(
        "--mqtt-subscribe-topic",
        default=os.getenv("MQTT_SUBSCRIBE_TOPIC"),
        help="MQTT subscribe topic",
    )
    parser.add_argument(
        "--chirpstack-account-email",
        default=os.getenv("CHIRPSTACK_ACCOUNT_EMAIL"),
        help="The Chirpstack Account's email to use to access APIs",
    )
    parser.add_argument(
        "--chirpstack-account-password",
        default=os.getenv("CHIRPSTACK_ACCOUNT_PASSWORD"),
        help="The Chirpstack Account's password to use to access APIs",
    )
    parser.add_argument(
        "--chirpstack-api-interface",
        default=os.getenv("CHIRPSTACK_API_INTERFACE"),
        help="Chirpstack's server API interface. The port is usually 8080",
    )
    parser.add_argument(
        "--manifest",
        default=os.getenv("MANIFEST_FILE"),
        type=Path,
        help="path to node manifest file",
    )
    parser.add_argument(
        "--api-interface",
        default=os.getenv("API_INTERFACE"),
        help="API server interface.",
    )
    parser.add_argument(
        "--node-token",
        default=os.getenv("NODE_TOKEN"),
        help="The Node's token to access Django server API interface.",
    )
    parser.add_argument(
        "--lorawan-connection-router",
        default=os.getenv("LORAWANCONNECTION_ROUTER"),
        help="API server's Lorawan Connection Router.",
    )
    parser.add_argument(
        "--lorawan-key-router",
        default=os.getenv("LORAWANKEY_ROUTER"),
        help="API server's Lorawan Key Router.",
    )
    parser.add_argument(
        "--lorawan-device-router",
        default=os.getenv("LORAWANDEVICE_ROUTER"),
        help="API server's Lorawan Device Router.",
    )
    parser.add_argument(
        "--sensor-hardware-router",
        default=os.getenv("SENSORHARDWARE_ROUTER"),
        help="API server's Sensor Hardware Router.",
    )

    #get args
    args = parser.parse_args()

    #configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )

    tracker = Tracker(args)
    tracker.run()

if __name__ == "__main__":
    main() # pragma: no cover
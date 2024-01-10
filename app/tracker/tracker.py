import datetime
from argparse import Namespace
from chirpstack_client import ChirpstackClient
from django_client import DjangoClient
from mqtt_client import MqttClient
from manifest import Manifest
from .parse import *

class Tracker(MqttClient):
    """
    A class that ties all clients together to track lorawan records
    """
    def __init__(self, args: Namespace):
        super().__init__(args)
        self.c_client = ChirpstackClient(args)
        self.d_client = DjangoClient(args)

    def on_message(self, client, userdata, message):
        """
        Method to run when Mqtt message is received
        """
        #log message if debug flag was passed
        self.log_message(message) if self.args.debug else None

        #parse message for metadata and deviceInfo. 
        result = self.parse_message(message)
        if result is not None:
            try:
                metadata, deviceInfo = result
            except ValueError as e:
                logging.error(f"Message did not parse correctly, {e}")
        else:
            return

        #load the node manifest
        manifest = Manifest(self.args.manifest)

        #retrieve data from chirpstack
        device_resp = self.c_client.get_device(deviceInfo["devEui"])
        deviceprofile_resp = self.c_client.get_device_profile(deviceInfo["deviceProfileId"])
        act_resp = self.c_client.get_device_activation(deviceInfo["devEui"])

        # if ld exist in manifest then...
        if manifest.ld_search(deviceInfo["devEui"]):
            #update ld, lc, lk, and manifest                
            self.update_ld(deviceInfo["devEui"], device_resp)
            self.update_lc(deviceInfo["devEui"], device_resp, deviceprofile_resp)
            self.update_lk(deviceInfo["devEui"], act_resp, deviceprofile_resp)
            self.update_manifest(deviceInfo["devEui"], manifest, device_resp, deviceprofile_resp)

        #else ld does not exist in manifest then...
        else:
            #if ld exist in django then...
            if self.d_client.ld_check(deviceInfo["devEui"]): 
                # relate the device to this node by creating a new lc and lk and updating ld and manifest
                self.update_ld(deviceInfo["devEui"], device_resp)
                lc_str = self.create_lc(deviceInfo["devEui"], device_resp, deviceprofile_resp)
                self.create_lk(deviceInfo["devEui"], lc_str, act_resp, deviceprofile_resp)
                self.update_manifest(deviceInfo["devEui"], manifest, device_resp, deviceprofile_resp)

            #else ld does not exist in django then...
            else:
                # create a new sensor hardware, ld, lc, lk, and update manifest
                #1) create hardware
                #2) create ld
                #3) create lc
                lc_str = self.create_lc(deviceInfo["devEui"], device_resp, deviceprofile_resp)
                #4) create lk
                self.create_lk(deviceInfo["devEui"], lc_str, act_resp, deviceprofile_resp)
                #5) update manifest

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
        self.d_client.update_ld(deveui, data)

        return

    def update_lc(self, deveui: str, device_resp: dict, deviceprofile_resp: dict):
        """
        Update lorawan connection using mqtt message, chirpstack client, and django client
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """   
        dev_name = replace_spaces(device_resp.device.name)
        datetime_obj_utc = self.epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
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
        Create a lorawan connection using mqtt message, chirpstack client, and django client
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        dev_name = replace_spaces(device_resp.device.name)
        datetime_obj_utc = self.epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
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
        if response:
            lc_str = self.args.vsn + "-" + dev_name + "-" + deveui
            return lc_str
        else:
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
        self.d_client.update_lk(deveui, lk_data)

        return



    def update_manifest(self, deveui: str, manifest: Manifest, device_resp: dict, deviceprofile_resp: dict):
        """
        Update manifest using mqtt message, chirpstack client, django client, and manifest
        manifest: Manifest object
        device_resp: the output of chirpstack client's get_device()
        deviceprofile_resp: the output of chirpstack client's get_device_profile()
        """
        datetime_obj_utc = self.epoch_to_UTC(device_resp.last_seen_at.seconds, device_resp.last_seen_at.nanos)        
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
        #TODO: include hardware in manifest_data when the device is new (not in django)
        manifest.update_manifest(manifest_data)

        return

    @staticmethod
    def epoch_to_UTC(sec: int, nanos: int) -> datetime:
        """
        Convert seconds since epoch to a UTC datetime object
        """
        #TODO: check if this converts the date correctly
        total_seconds = sec + nanos / 1e9 # Calculate the total seconds with nanoseconds 
        datetime_obj_utc = datetime.datetime.utcfromtimestamp(total_seconds) # Convert seconds since epoch to a datetime object
        return datetime_obj_utc
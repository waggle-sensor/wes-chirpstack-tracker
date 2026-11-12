import requests
import logging
import argparse
import sys
import os
from urllib.parse import urljoin
from argparse import Namespace
from enum import Enum

class HttpMethod(Enum):
    GET = requests.get
    POST = requests.post
    PATCH = requests.patch

class DjangoClient:
    """
    Django client to call Api(s)
    """

    def __init__(self, args: Namespace):
        self.args = args
        self.server = self.args.api_interface
        self.vsn = self.args.vsn
        self.auth_token = self.args.node_token
        self.auth_header = {"Authorization": f"node_auth {self.auth_token}"}
        self.LC_ROUTER = self.args.lorawan_connection_router
        self.LK_ROUTER = self.args.lorawan_key_router
        self.LD_ROUTER = self.args.lorawan_device_router
        self.SH_ROUTER = self.args.sensor_hardware_router

    def get_lc(self, dev_eui: str) -> dict:
        """
        Get LoRaWAN connection using dev EUI
        """
        api_endpoint = f"{self.LC_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def create_lc(self, data: dict) -> dict:
        """
        Create LoRaWAN connection
        """
        api_endpoint = f"{self.LC_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_lc(self, dev_eui: str, data: dict) -> dict:
        """
        Update LoRaWAN connection
        """
        api_endpoint = f"{self.LC_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def lc_search(self, dev_eui: str):
        """
        Search the db for a lorawan connection.
        Returns True if found, False if 404, None on ambiguous/error (do not create).
        """
        api_endpoint = f"{self.LC_ROUTER}{self.vsn}/{dev_eui}/"
        return self._search_result(self.call_api(HttpMethod.GET, api_endpoint), api_endpoint, "lc_search")

    def get_ld(self, dev_eui: str) -> dict:
        """
        Get LoRaWAN device using dev EUI
        """
        api_endpoint = f"{self.LD_ROUTER}{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def create_ld(self, data: dict) -> dict:
        """
        Create LoRaWAN device
        """
        api_endpoint = f"{self.LD_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_ld(self, dev_eui: str, data: dict) -> dict:
        """
        Update LoRaWAN device
        """
        api_endpoint = f"{self.LD_ROUTER}{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def ld_search(self, dev_eui: str):
        """
        Search the db for a lorawan device.
        Returns True if found, False if 404, None on ambiguous/error (do not create).
        """
        api_endpoint = f"{self.LD_ROUTER}{dev_eui}/"
        return self._search_result(self.call_api(HttpMethod.GET, api_endpoint), api_endpoint, "ld_search")

    def get_lk(self, dev_eui: str) -> dict:
        """
        Get LoRaWAN key using dev EUI
        """
        api_endpoint = f"{self.LK_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def create_lk(self, data: dict) -> dict:
        """
        Create LoRaWAN key
        """
        api_endpoint = f"{self.LK_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_lk(self, dev_eui: str, data: dict) -> dict:
        """
        Update LoRaWAN key
        """
        api_endpoint = f"{self.LK_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def get_sh(self, hw_model: str) -> dict:
        """
        Get Sensor Hardware using hw_model
        """
        api_endpoint = f"{self.SH_ROUTER}{hw_model}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def list_sh(self) -> dict:
        """
        List Sensor Hardware records
        """
        api_endpoint = f"{self.SH_ROUTER}"
        return self.call_api(HttpMethod.GET, api_endpoint)

    def create_sh(self, data: dict) -> dict:
        """
        Create Sensor Hardware
        """
        api_endpoint = f"{self.SH_ROUTER}"
        return self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_sh(self, hw_model: str, data: dict) -> dict:
        """
        Update Sensor Hardware 
        """
        api_endpoint = f"{self.SH_ROUTER}{hw_model}/"
        return self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def sh_search(self, hw_model: str):
        """
        Search the db for a sensor hardware.
        Returns True if found, False if 404, None on ambiguous/error (do not create).
        """
        api_endpoint = f"{self.SH_ROUTER}{hw_model}/"
        return self._search_result(self.call_api(HttpMethod.GET, api_endpoint), api_endpoint, "sh_search")

    def find_sh_id(self, hw_model: str):
        """
        Find an existing sensor hardware id by hw_model via list endpoint.
        Prefer the lowest id (oldest / original) when duplicates exist.
        Returns None if none found or list fails.
        """
        response = self.list_sh()
        items = self._normalize_list_body(response.get("json_body"))
        if items is None:
            logging.error(f"DjangoClient.find_sh_id(): failed to list sensor hardware for hw_model={hw_model}")
            return None

        matches = [
            item for item in items
            if isinstance(item, dict)
            and item.get("hw_model") == hw_model
            and item.get("id") is not None
        ]
        if not matches:
            return None
        return min(matches, key=lambda item: item["id"])["id"]

    def _normalize_list_body(self, body):
        """Normalize DRF list/paginated responses into a list of records."""
        if body is None:
            return None
        if isinstance(body, list):
            return body
        if isinstance(body, dict):
            results = body.get("results")
            if isinstance(results, list):
                return results
        return None

    def _search_result(self, response: dict, api_endpoint: str, method_name: str):
        """
        Interpret a GET-by-lookup response.
        True = found, False = confirmed missing (404), None = ambiguous/error.
        """
        if response.get("json_body"):
            return True

        status_code = response.get("status_code")
        if status_code == 404:
            return False

        logging.error(
            f"Unexpected status code in DjangoClient.{method_name}() for {api_endpoint}: {status_code}"
        )
        return None

    def call_api(self, method: HttpMethod, endpoint: str, data: dict = None) -> dict:
        """
        Create request based on the method and call the api
        """
        api_url = urljoin(self.server, endpoint)
        try:
            if data is not None:
                response = method(api_url, headers=self.auth_header, json=data)
            else:
                response = method(api_url, headers=self.auth_header)
            response.raise_for_status() # Raise an exception for bad responses (4xx or 5xx)

            return {
                'headers': dict(response.headers),
                'status_code': response.status_code,
                'json_body': response.json()
            }
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred in DjangoClient.call_api() for {endpoint}: {e}")
            try:
                logging.error(f"    Details returned by server: {response.json()}")
            except requests.exceptions.JSONDecodeError as e:
                logging.error(f"requests.exceptions.JSONDecodeError: {e}")
            return {
                'headers': dict(response.headers),
                'status_code': getattr(response, "status_code", None),
                'json_body': None
            }

def main(): # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument(
        "--vsn",
        default=os.getenv("WAGGLE_NODE_VSN"),
        help="The Node's vsn.",
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
    args = parser.parse_args()
    #configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(message)s",
        datefmt="%Y/%m/%d %H:%M:%S",
    )
    django_client = DjangoClient(args)

if __name__ == "__main__":
    main() # pragma: no cover
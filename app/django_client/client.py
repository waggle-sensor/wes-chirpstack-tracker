import requests
import logging
import sys
import os
from urllib.parse import urljoin

class HttpMethod(Enum):
    GET = requests.get
    POST = requests.post
    PATCH = requests.patch

class DjangoClient:
    """
    Django client to call Api(s)
    """
    LC_ROUTER = "lorawanconnections/"
    LK_ROUTER = "lorawankeys/"
    LD_ROUTER = "lorawandevices/"
    SH_ROUTER = "sensorhardwares/"

    def __init__(self, args):
        self.args = args
        self.server = self.args.django_api_interface
        self.vsn = self.args.vsn
        self.auth_token = self.args.node_token
        self.auth_header = {'Content-Type': 'application/json', "Authorization": f"node_auth {self.auth_token}"}

    def get_lc(self, dev_eui):
        """
        Get LoRaWAN connection using dev EUI
        """
        api_endpoint = f"{self.LC_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint, data)

    def create_lc(self, data):
        """
        Create LoRaWAN connection
        """
        api_endpoint = f"{self.LC_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_lc(self, dev_eui, data):
        """
        Update LoRaWAN connection
        """
        api_endpoint = f"{self.LC_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def get_ld(self, dev_eui):
        """
        Get LoRaWAN device using dev EUI
        """
        api_endpoint = f"{self.LD_ROUTER}{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint, data)

    def create_ld(self, data):
        """
        Create LoRaWAN device
        """
        api_endpoint = f"{self.LD_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_ld(self, dev_eui, data):
        """
        Update LoRaWAN device
        """
        api_endpoint = f"{self.LD_ROUTER}{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def get_lk(self, dev_eui):
        """
        Get LoRaWAN key using dev EUI
        """
        api_endpoint = f"{self.LK_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def create_lk(self, data):
        """
        Create LoRaWAN key
        """
        api_endpoint = f"{self.LK_ROUTER}"
        return  self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_lk(self, dev_eui, data):
        """
        Update LoRaWAN key
        """
        api_endpoint = f"{self.LK_ROUTER}{self.vsn}/{dev_eui}/"
        return  self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def get_sh(self, hw_model):
        """
        Get Sensor Hardware using hw_model
        """
        api_endpoint = f"{self.SH_ROUTER}{hw_model}/"
        return  self.call_api(HttpMethod.GET, api_endpoint)

    def create_sh(self, data):
        """
        Create Sensor Hardware
        """
        api_endpoint = f"{self.SH_ROUTER}"
        return self.call_api(HttpMethod.POST, api_endpoint, data)

    def update_sh(self, hw_model, data):
        """
        Update Sensor Hardware 
        """
        api_endpoint = f"{self.SH_ROUTER}{hw_model}/"
        return self.call_api(HttpMethod.PATCH, api_endpoint, data)

    def call_api(self, method: HttpMethod, endpoint: str, data: dict) -> dict:
        """
        Create request based on the method and call the api
        """
        api_url = urljoin(self.server, endpoint)

        if method not in HttpMethod:
            raise ValueError(f"Unsupported method: {method}")

        response = method.value(api_url, headers=self.auth_header, json=data)
        response.raise_for_status() # Raise an exception for bad responses (4xx or 5xx)
        return response.json()
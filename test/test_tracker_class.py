import unittest
import requests
import copy
from pytest import mark
from unittest.mock import Mock, patch, MagicMock
from chirpstack_api_wrapper import *
from app.django_client import DjangoClient, HttpMethod
from app.tracker import Tracker
from app.tracker.parse import *
from app.tracker.convert_date import *
from app.manifest import Manifest
from tools.manifest import ManifestTemplate
from tools.chirpstack import MessageTemplate, Mock_ChirpstackClient_Methods

API_INTERFACE = "https://auth.sagecontinuum.org"
LC_ROUTER = "lorawanconnections/"
LK_ROUTER = "lorawankeys/"
LD_ROUTER = "lorawandevices/"
SH_ROUTER = "sensorhardwares/"
VSN = "W030"
NODE_TOKEN = "999294cef6fc3a95fe14c145612825ef5ae27567"
CHIRPSTACK_API_INTERFACE = "wes-chirpstack-server:8080"
CHIRPSTACK_ACT_EMAIL = "test"
CHIRPSTACK_ACT_PASSWORD = "test"
MANIFEST_FILEPATH = '/etc/waggle/node-manifest-v2.json'

class TestUpdateLd(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient.get_device() return value
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.PATCH")
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_ld_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_django_patch):
        """
        Successfully use chirpstack lorawan device data to call django's client update_ld()
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock the DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        #mock return val
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(mock_dev_eui)

        #data that should have been used
        data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level
        }

        # Call the action in testing
        self.tracker.update_ld(mock_dev_eui, device_resp)

        # Assertions
        mock_django_patch.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{mock_dev_eui}/", headers=self.tracker.d_client.auth_header, json=data)

class TestCreateLd(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient.get_device() return value
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_ld_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_django_post):
        """
        Successfully use chirpstack lorawan device data to call DjangoClient.create_ld()
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock DeviceServiceStub
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        #mock return val
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(mock_dev_eui)

        # Mock sensor hardware id in django
        mock_sh_id = "mock_sh_id"

        #data that should have been used
        data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
            "hardware": mock_sh_id,
            "deveui": mock_dev_eui
        }

        # Call the action in testing
        self.tracker.create_ld(mock_dev_eui, mock_sh_id, device_resp)

        # Assertions
        mock_django_post.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/", headers=self.tracker.d_client.auth_header, json=data)

class TestUpdateLc(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.PATCH")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_lc_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_patch):
        """
        Successfully use chirpstack lorawan device and device profile data 
        to call DjangoClient.update_lc()
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        #mock return vals
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }

        # Call the action in testing
        self.tracker.update_lc(mock_dev_eui, device_resp, deviceprofile_resp)

        # Assertions
        mock_django_patch.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{mock_dev_eui}/", headers=self.tracker.d_client.auth_header, json=data)

class TestCreateLc(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_lc_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_post):
        """
        Successfully use chirpstack lorawan device and device profile data 
        to call DjangoClient.create_lc()
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        #mock return vals
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        data = {
            "node": VSN,
            "lorawan_device": mock_dev_eui,
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }

        # Call the action in testing
        lc_uid = self.tracker.create_lc(mock_dev_eui, device_resp, deviceprofile_resp)

        # Assertions
        mock_django_post.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.tracker.d_client.auth_header, json=data)
        self.assertEqual(lc_uid, VSN + "-" + replace_spaces(device_resp.device.name) + "-" + mock_dev_eui)

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_lc_no_response(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_post):
        """
        Test when DjangoClient.create_lc() returns no response
        """
        #Mock POST response
        mock_response = Mock()
        mock_response.headers = {
                'Content-Type': 'application/json', 
                'status-code': 404,
                'Custom-Header': 'Mocked-Value',
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_django_post.return_value = mock_response

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        
        #mock return vals
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        data = {
            "node": VSN,
            "lorawan_device": mock_dev_eui,
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }

        # Assertions
        with self.assertLogs(level='ERROR') as log:            
            # Call the method under test
            lc_uid = self.tracker.create_lc(mock_dev_eui, device_resp, deviceprofile_resp)

            # Assert
            self.assertEqual(len(log.output), 3)
            self.assertEqual(len(log.records), 3)
            self.assertIn("Tracker.create_lc(): d_client.create_lc() did not return a valid response", log.output[2])
            mock_django_post.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.tracker.d_client.auth_header, json=data)
            self.assertIsNone(lc_uid)

class TestUpdateLk(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.PATCH")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_lk_otaa_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_patch):
        """
        Successfully use chirpstack lorawan device activation and device profile data 
        to call DjangoClient.update_lk() when the device is using OTAA
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_activation_ret_val
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get device activation
        act_resp = chirpstack_client.get_device_activation(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = chirpstack_client.get_device_app_key(mock_dev_eui,lw_v)
        data = {
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key, 
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }

        # Call the action in testing
        self.tracker.update_lk(mock_dev_eui, act_resp, deviceprofile_resp)

        # Assertions
        mock_django_patch.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/{VSN}/{mock_dev_eui}/", headers=self.tracker.d_client.auth_header, json=data)

    @patch("app.django_client.HttpMethod.PATCH")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_lk_abp_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_patch):
        """
        Successfully use chirpstack lorawan device activation and device profile data 
        to call DjangoClient.update_lk() when the device is using ABP
        """
        #change to ABP
        self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa = False

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_activation_ret_val
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get device activation
        act_resp = chirpstack_client.get_device_activation(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = chirpstack_client.get_device_app_key(mock_dev_eui,lw_v)
        data = {
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key, 
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr
        }

        # Call the action in testing
        self.tracker.update_lk(mock_dev_eui, act_resp, deviceprofile_resp)

        # Assertions
        mock_django_patch.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/{VSN}/{mock_dev_eui}/", headers=self.tracker.d_client.auth_header, json=data)

class TestCreateLk(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_lk_otaa_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_post):
        """
        Successfully use chirpstack lorawan device activation and device profile data 
        to call DjangoClient.create_lk() when the device is using OTAA
        """
        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_activation_ret_val
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get device activation
        act_resp = chirpstack_client.get_device_activation(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        mock_lc_str = "mock_lc_uid"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = chirpstack_client.get_device_app_key(mock_dev_eui,lw_v)
        data = {
            "lorawan_connection": mock_lc_str,
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key,  
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }

        # Call the action in testing
        self.tracker.create_lk(mock_dev_eui, mock_lc_str, act_resp, deviceprofile_resp)

        # Assertions
        mock_django_post.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.tracker.d_client.auth_header, json=data)

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_lk_abp_happy_path(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub, mock_django_post):
        """
        Successfully use chirpstack lorawan device activation and device profile data 
        to call DjangoClient.create_lk() when the device is using ABP
        """
        #change to ABP
        self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa = False

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_activation_ret_val
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the dev_eui
        mock_dev_eui = "mock_dev_eui"

        # Call chirpstack_client get device activation
        act_resp = chirpstack_client.get_device_activation(mock_dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        mock_lc_str = "mock_lc_uid"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = chirpstack_client.get_device_app_key(mock_dev_eui,lw_v)
        data = {
            "lorawan_connection": mock_lc_str,
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key,  
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr
        }

        # Call the action in testing
        self.tracker.create_lk(mock_dev_eui, mock_lc_str, act_resp, deviceprofile_resp)

        # Assertions
        mock_django_post.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.tracker.d_client.auth_header, json=data)

class TestCreateSh(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD
        )
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_sh_happy_path(self, mock_insecure_channel, mock_device_profile_service_stub, mock_django_post):
        """
        Successfully use chirpstack lorawan device profile data 
        to call DjangoClient.create_sh()
        """
        #mock response of requests.post method
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 201,
            'Custom-Header': 'Mocked-Value',
        }
        response_data = {
            "id": 1,
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
            "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
            "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description,
            "capabilities": [35]
            }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.status_code = 201
        mock_response.json.return_value = response_data
        mock_django_post.return_value = mock_response

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        # Mock return val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        data = {
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
            "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
            "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description,
            "capabilities": [35]
        }

        # Call the action in testing
        sh_uid = self.tracker.create_sh(deviceprofile_resp)

        # Assertions
        mock_django_post.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/", headers=self.tracker.d_client.auth_header, json=data)
        self.assertEqual(sh_uid, response_data["id"])

    @patch("app.django_client.HttpMethod.POST")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_create_sh_no_response(self, mock_insecure_channel, mock_device_profile_service_stub, mock_django_post):
        """
        Test when DjangoClient.create_sh() returns an error
        """
        #mock response of requests.post method
        mock_response = Mock()
        mock_response.headers = {
                'Content-Type': 'application/json', 
                'status-code': 400,
                'Custom-Header': 'Mocked-Value',
        }
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_django_post.return_value = mock_response

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        # Mock return val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #data that should have been used
        data = {
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
            "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
            "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description,
            "capabilities": [35]
        }

        # Assertions
        with self.assertLogs(level='ERROR') as log:            
            # Call the action in testing
            sh_uid = self.tracker.create_sh(deviceprofile_resp)

            # Assert
            self.assertEqual(len(log.output), 3)
            self.assertEqual(len(log.records), 3)
            self.assertIn("Tracker.create_sh(): d_client.create_sh() did not return a valid response", log.output[2])
            mock_django_post.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/", headers=self.tracker.d_client.auth_header, json=data)
            self.assertIsNone(sh_uid)

    @patch("app.django_client.DjangoClient.get_sh")
    def test_resolve_sh_id_found(self, mock_get_sh):
        mock_get_sh.return_value = {"status_code": 200, "json_body": {"id": 42}}
        sh_id = self.tracker.resolve_sh_id(self.mock_chirp_methods.get_device_profile_ret_val)
        self.assertEqual(sh_id, 42)

    @patch("app.tracker.tracker.Tracker.create_sh")
    @patch("app.django_client.DjangoClient.get_sh")
    def test_resolve_sh_id_creates_on_404(self, mock_get_sh, mock_create_sh):
        mock_get_sh.return_value = {"status_code": 404, "json_body": None}
        mock_create_sh.return_value = 99
        sh_id = self.tracker.resolve_sh_id(self.mock_chirp_methods.get_device_profile_ret_val)
        mock_create_sh.assert_called_once()
        self.assertEqual(sh_id, 99)

    @patch("app.django_client.DjangoClient.find_sh_id")
    @patch("app.tracker.tracker.Tracker.create_sh")
    @patch("app.django_client.DjangoClient.get_sh")
    def test_resolve_sh_id_ambiguous_reuses_existing(self, mock_get_sh, mock_create_sh, mock_find_sh_id):
        mock_get_sh.return_value = {"status_code": 500, "json_body": None}
        mock_find_sh_id.return_value = 3
        sh_id = self.tracker.resolve_sh_id(self.mock_chirp_methods.get_device_profile_ret_val)
        mock_create_sh.assert_not_called()
        mock_find_sh_id.assert_called_once()
        self.assertEqual(sh_id, 3)

    @patch("app.django_client.DjangoClient.find_sh_id")
    @patch("app.tracker.tracker.Tracker.create_sh")
    @patch("app.django_client.DjangoClient.get_sh")
    def test_resolve_sh_id_create_fail_falls_back_to_list(self, mock_get_sh, mock_create_sh, mock_find_sh_id):
        mock_get_sh.return_value = {"status_code": 404, "json_body": None}
        mock_create_sh.return_value = None
        mock_find_sh_id.return_value = 7
        sh_id = self.tracker.resolve_sh_id(self.mock_chirp_methods.get_device_profile_ret_val)
        self.assertEqual(sh_id, 7)

class TestUpdateManifest(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD,
            manifest=MANIFEST_FILEPATH
        )
        #set up manifest
        self.manifest = Manifest(self.args.manifest)
        self.manifest.dict = ManifestTemplate().sample
        #set up tracker
        self.tracker = Tracker(self.args)
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_manifest_dev_exist(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub):
        """
        Successfully use chirpstack lorawan device and device profile data to
        to call Manifest.update_manifest() when device exists in the manifest
        """
        #change deveui to one existing in manifest sample
        self.mock_chirp_methods.edit_deveui("7d1f5420e81235c1")

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(self.mock_chirp_methods.get_device_ret_val.device.dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #updated lorawan entry should look like this
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        new_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "created_at": "2023-12-13T19:47:45.355000Z",
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": "Sap Flow Meter",
                    "hw_model": "SFM1x",
                    "hw_version": "",
                    "sw_version": "",
                    "manufacturer": "ICT International",
                    "datasheet": "https://ictinternational.com/manuals-and-brochures/sfm1x-sap-flow-meter/",
                    "capabilities": ["lorawan"],
                    "description": "# SFM1x Sap Flow Meter\r\n\r\nThe SFM1x Sap Flow Meter enables individual tree water use and health to be monitored in real time. This is because the SFM has integrated data transmission direct to cloud using IoT/LTE-M Cat-M1. The SFM1x Sap Flow Meter is a discrete standalone instrument based upon the Heat Ratio Method. This measurement principle has proven to be a robust and flexible technique to measure plant water use; being able to measure high, low, zero and reverse flows in a large range of plant anatomies & species from herbaceous to woody, and stem sizes > 10 mm in diameter. The theoretical basis and ratio metric design of the Heat Ratio Method makes possible the measurement of high, low, zero and reverse flows. The SFM1x Sap Flow Meter consists of two temperature sensing needles arranged equidistance above and below a central heater. These needles are inserted into the water conducting tissue of the plant by drilling 3 small parallel holes. Heat is then pulsed every 10 minutes into the water conducting tissue of the plant. The heat is used as a tracer to directly measure the velocity of water movement in the plant stem."
                },
            }
        }

        #call the action in testing
        self.tracker.update_manifest(self.mock_chirp_methods.get_device_ret_val.device.dev_eui, self.manifest, device_resp, deviceprofile_resp)

        #Assert if manifest dict was updated
        self.assertTrue(self.manifest.dict["lorawanconnections"][0] == new_data) #self.manifest.dict["lorawanconnections"][0] is 7d1f5420e81235c1 device

    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def test_update_manifest_dev_not_exist(self, mock_insecure_channel, mock_device_service_stub, mock_device_profile_service_stub):
        """
        Successfully use chirpstack lorawan device and device profile data to
        to call Manifest.update_manifest() when device DOES NOT exists in the manifest
        """
        #change deveui to non existing in manifest sample
        self.mock_chirp_methods.edit_deveui("12345678912345a3")

        # Mock the gRPC channel
        mock_channel = Mock()
        mock_insecure_channel.return_value = mock_channel

        # Mock stubs
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value

        # Mock return values
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val

        # Create a ChirpstackClient instance
        chirpstack_client = ChirpstackClient(self.args.chirpstack_account_email,self.args.chirpstack_account_password,self.args.chirpstack_api_interface)

        # Call chirpstack_client get_device
        device_resp = chirpstack_client.get_device(self.mock_chirp_methods.get_device_ret_val.device.dev_eui)

        # Mock the device profile ID
        mock_device_profile_id = "mock_device_profile_id"

        # Call get_device_profile
        deviceprofile_resp = chirpstack_client.get_device_profile(mock_device_profile_id)

        #new lorawan entry should look like this
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        new_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
                    "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
                    "capabilities": ["lorawan"],
                    "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description
                },
            }
        }

        #call the action in testing
        self.tracker.update_manifest(self.mock_chirp_methods.get_device_ret_val.device.dev_eui, self.manifest, device_resp, deviceprofile_resp)

        #Assert if manifest dict was updated
        self.assertTrue(self.manifest.dict["lorawanconnections"][-1] == new_data)

class TestOnMessage(unittest.TestCase):

    @patch('chirpstack_api_wrapper.grpc.insecure_channel')
    def setUp(self, mock_insecure_channel):
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN,
            chirpstack_api_interface=CHIRPSTACK_API_INTERFACE,
            chirpstack_account_email=CHIRPSTACK_ACT_EMAIL,
            chirpstack_account_password=CHIRPSTACK_ACT_PASSWORD,
            manifest=MANIFEST_FILEPATH
        )
        #set up manifest
        self.manifest = Manifest(self.args.manifest)
        self.manifest.dict = ManifestTemplate().sample
        #set up tracker
        self.tracker = Tracker(self.args)
        #get Chripstack message sample
        self.MESSAGE = MessageTemplate().sample
        #mock ChirpstackClient method return values
        self.mock_chirp_methods = Mock_ChirpstackClient_Methods('mock_dev_eui')

    @patch('app.tracker.Tracker.parse_message')
    def test_on_message_Value_Error(self, mock_parse_message):
        """
        Test on_message() value error when parse_message returns less values to unpack
        """
        #Arrange
        client = Mock()
        userdata = Mock()
        ChirpMessage = Mock()
        ChirpMessage.payload = f'{self.MESSAGE}'.encode("utf-8")


        #Mock the return value for parse_message
        mock_parse_message.return_value = (None, {'deviceName': 'mock_device', 'devEui': 'mock_devEui'})


        # Assert Logs
        with self.assertLogs(level='ERROR') as log:
            # Call the log_message method
            with self.assertRaises(ValueError) as ve:
                self.tracker.on_message(client, userdata, ChirpMessage)
                self.assertEqual(len(log.output), 1)
                self.assertEqual(len(log.records), 1)
                self.assertIn(f"Tracker.on_message(): Message did not parse correctly, {ve}", log.output[0])

    @patch("app.django_client.HttpMethod.PATCH")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('app.manifest.Manifest.load_manifest')
    @patch('app.django_client.DjangoClient.lc_search')
    def test_on_message_dev_exist(self, mock_lc_search, mock_load_manifest, mock_device_service_stub, mock_device_profile_service_stub, mock_django_patch):
        """
        Test on_message() happy path when lorawan connection EXIST in Django and local manifest
        """
        #Arrange
        #   mock Manifest.load_manifest()
        mock_load_manifest.return_value = self.manifest.dict
        #   change deveui in mocks to one existing in manifest sample aka connection in local manifest
        deveui = "7d1f5420e81235c1" 
        self.MESSAGE = self.MESSAGE.replace('"devEui": "0101010101010101"', f'"devEui": "{deveui}"')
        self.mock_chirp_methods.edit_deveui(deveui)
        #   mock lc_search to return true aka connection found in django
        mock_lc_search.return_value = True
        #   mock chirpstack encoded message
        ChirpMessage = Mock()
        ChirpMessage.payload = f'{self.MESSAGE}'.encode("utf-8")
        #   mock ChirpstackClient.get_device()
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        #   mock ChirpstackClient.get_device_profile()
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackClient.get_device_activation()
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackCLinet.get_device_app_key()
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val

        #call the action in testing
        client = Mock()
        userdata = Mock()
        temp = self.tracker.on_message(client, userdata, ChirpMessage)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = self.tracker.c_client.get_device_app_key(deveui,lw_v)
        update_ld_data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level
        }
        udpate_lc_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }
        update_lk_data = {
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key, 
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }
        update_manifest_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "created_at": "2023-12-13T19:47:45.355000Z",
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": "Sap Flow Meter",
                    "hw_model": "SFM1x",
                    "hw_version": "",
                    "sw_version": "",
                    "manufacturer": "ICT International",
                    "datasheet": "https://ictinternational.com/manuals-and-brochures/sfm1x-sap-flow-meter/",
                    "capabilities": ["lorawan"],
                    "description": "# SFM1x Sap Flow Meter\r\n\r\nThe SFM1x Sap Flow Meter enables individual tree water use and health to be monitored in real time. This is because the SFM has integrated data transmission direct to cloud using IoT/LTE-M Cat-M1. The SFM1x Sap Flow Meter is a discrete standalone instrument based upon the Heat Ratio Method. This measurement principle has proven to be a robust and flexible technique to measure plant water use; being able to measure high, low, zero and reverse flows in a large range of plant anatomies & species from herbaceous to woody, and stem sizes > 10 mm in diameter. The theoretical basis and ratio metric design of the Heat Ratio Method makes possible the measurement of high, low, zero and reverse flows. The SFM1x Sap Flow Meter consists of two temperature sensing needles arranged equidistance above and below a central heater. These needles are inserted into the water conducting tissue of the plant by drilling 3 small parallel holes. Heat is then pulsed every 10 minutes into the water conducting tissue of the plant. The heat is used as a tracer to directly measure the velocity of water movement in the plant stem."
                },
            }
        }

        # Assertions
        patch_calls = mock_django_patch.call_args_list # Extract the call arguments from the call_args_list
        assert patch_calls, "Expected at least one PATCH call"
        patch_calls[0].assert_called_once_with( f"{API_INTERFACE}/lorawandevices/{deveui}/", headers=self.tracker.d_client.auth_header, json=update_ld_data)
        patch_calls[1].assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{deveui}/", headers=self.tracker.d_client.auth_header, json=udpate_lc_data)
        patch_calls[2].assert_called_once_with(f"{API_INTERFACE}/lorawankeys/{VSN}/{deveui}/", headers=self.tracker.d_client.auth_header, json=update_lk_data)
        self.assertTrue(self.manifest.dict["lorawanconnections"][0] == update_manifest_data) #self.manifest.dict["lorawanconnections"][0] is 7d1f5420e81235c1 device

    @patch("app.django_client.HttpMethod.POST")
    @patch("app.django_client.HttpMethod.PATCH")
    @patch("app.django_client.DjangoClient.ld_search")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('app.manifest.Manifest.load_manifest')
    @patch('app.django_client.DjangoClient.lc_search')
    def test_on_message_dev_not_exist_1(self, mock_lc_search, mock_load_manifest, mock_device_service_stub, mock_device_profile_service_stub, mock_ld_search, mock_django_patch, mock_django_post):
        """
        Test on_message() happy path when device DOES NOT exist in the manifest but EXIST in django
        """
        #Arrange
        #   mock Manifest.load_manifest()
        mock_load_manifest.return_value = self.manifest.dict
        #   change deveui in mocks to one NOT existing in manifest sample
        deveui = "12345678912345a3" 
        self.MESSAGE = self.MESSAGE.replace('"devEui": "0101010101010101"', f'"devEui": "{deveui}"')
        self.mock_chirp_methods.edit_deveui(deveui)
        #   mock lc_search to return false aka connection NOT found in django
        mock_lc_search.return_value = False
        #   mock chirpstack encoded message
        ChirpMessage = Mock()
        ChirpMessage.payload = f'{self.MESSAGE}'.encode("utf-8")
        #   mock ChirpstackClient.get_device()
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        #   mock ChirpstackClient.get_device_profile()
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackClient.get_device_activation()
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackCLinet.get_device_app_key()
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        # mock DjangoClient.ld_search() aka device found in django
        mock_ld_search.return_value = True

        #call the action in testing
        client = Mock()
        userdata = Mock()
        temp = self.tracker.on_message(client, userdata, ChirpMessage)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = self.tracker.c_client.get_device_app_key(deveui,lw_v)
        dev_name = replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name)
        lc_str = f"{VSN}-{dev_name}-{deveui}"
        update_ld_data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level
        }
        create_lc_data = {
            "node": VSN,
            "lorawan_device": deveui,
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }
        create_lk_data = {
            "lorawan_connection": lc_str,
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key,  
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }
        update_manifest_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
                    "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
                    "capabilities": ["lorawan"],
                    "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description
                },
            }
        }

        # Assertions
        post_calls = mock_django_post.call_args_list # Extract the call arguments from the call_args_list
        assert post_calls, "Expected at least one PATCH call"
        mock_django_patch.assert_called_once_with( f"{API_INTERFACE}/lorawandevices/{deveui}/", headers=self.tracker.d_client.auth_header, json=update_ld_data)
        post_calls[0].assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.tracker.d_client.auth_header, json=create_lc_data)
        post_calls[1].assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.tracker.d_client.auth_header, json=create_lk_data)
        self.assertTrue(self.manifest.dict["lorawanconnections"][-1] == update_manifest_data)

    @patch("app.django_client.HttpMethod.POST")
    @patch("app.django_client.DjangoClient.get_sh")
    @patch("app.django_client.DjangoClient.ld_search")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('app.manifest.Manifest.load_manifest')
    @patch('app.django_client.DjangoClient.lc_search')
    def test_on_message_dev_not_exist_2(self, mock_lc_search, mock_load_manifest, mock_device_service_stub, mock_device_profile_service_stub, mock_ld_search, mock_get_sh, mock_django_post):
        """
        Test on_message() happy path when device DOES NOT exist in the manifest and in django but sensor hardware exist in django
        """
        #Arrange
        #   mock Manifest.load_manifest()
        mock_load_manifest.return_value = self.manifest.dict
        #   change deveui in mocks to one NOT existing in manifest sample
        deveui = "12345678912345a3" 
        self.MESSAGE = self.MESSAGE.replace('"devEui": "0101010101010101"', f'"devEui": "{deveui}"')
        self.mock_chirp_methods.edit_deveui(deveui)
        #   mock lc_search to return false aka connection NOT found in django
        mock_lc_search.return_value = False
        #   mock chirpstack encoded message
        ChirpMessage = Mock()
        ChirpMessage.payload = f'{self.MESSAGE}'.encode("utf-8")
        #   mock ChirpstackClient.get_device()
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        #   mock ChirpstackClient.get_device_profile()
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackClient.get_device_activation()
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackCLinet.get_device_app_key()
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        #   mock search return values
        mock_ld_search.return_value = False
        #   mock django get sh return value (resolve_sh_id uses get_sh directly)
        mock_get_sh.return_value = {
            'status_code': 200,
            'json_body': {"id": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.id},
        }

        #call the action in testing
        client = Mock()
        userdata = Mock()
        temp = self.tracker.on_message(client, userdata, ChirpMessage)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = self.tracker.c_client.get_device_app_key(deveui,lw_v)
        dev_name = replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name)
        lc_str = f"{VSN}-{dev_name}-{deveui}"
        create_ld_data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.id,
            "deveui": deveui
        }
        create_lc_data = {
            "node": VSN,
            "lorawan_device": deveui,
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }
        create_lk_data = {
            "lorawan_connection": lc_str,
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key,  
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }
        update_manifest_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
                    "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
                    "capabilities": ["lorawan"],
                    "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description
                },
            }
        }

        # Assertions
        post_calls = mock_django_post.call_args_list # Extract the call arguments from the call_args_list
        assert post_calls, "Expected at least one PATCH call"
        post_calls[0].assert_called_once_with( f"{API_INTERFACE}/lorawandevices/", headers=self.tracker.d_client.auth_header, json=create_ld_data)
        post_calls[1].assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.tracker.d_client.auth_header, json=create_lc_data)
        post_calls[2].assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.tracker.d_client.auth_header, json=create_lk_data)
        self.assertTrue(self.manifest.dict["lorawanconnections"][-1] == update_manifest_data)


    @patch("app.django_client.HttpMethod.POST")
    @patch("app.django_client.DjangoClient.get_sh")
    @patch("app.django_client.DjangoClient.ld_search")
    @patch('chirpstack_api_wrapper.api.DeviceProfileServiceStub')
    @patch('chirpstack_api_wrapper.api.DeviceServiceStub')
    @patch('app.manifest.Manifest.load_manifest')
    @patch('app.django_client.DjangoClient.lc_search')
    def test_on_message_dev_not_exist_3(self, mock_lc_search, mock_load_manifest, mock_device_service_stub, mock_device_profile_service_stub, mock_ld_search, mock_get_sh, mock_django_post):
        """
        Test on_message() happy path when device DOES NOT exist in the manifest and in django and sensor hardware DOES NOT exist in django
        """
        #Arrange
        #   mock Manifest.load_manifest()
        mock_load_manifest.return_value = self.manifest.dict
        #   change deveui in mocks to one NOT existing in manifest sample
        deveui = "12345678912345a3" 
        self.MESSAGE = self.MESSAGE.replace('"devEui": "0101010101010101"', f'"devEui": "{deveui}"')
        self.mock_chirp_methods.edit_deveui(deveui)
        #   mock lc_search to return false aka connection NOT found in django
        mock_lc_search.return_value = False
        #   mock chirpstack encoded message
        ChirpMessage = Mock()
        ChirpMessage.payload = f'{self.MESSAGE}'.encode("utf-8")
        #   mock ChirpstackClient.get_device()
        mock_device_service_stub_instance = mock_device_service_stub.return_value
        mock_device_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_ret_val
        #   mock ChirpstackClient.get_device_profile()
        mock_device_profile_service_stub_instance = mock_device_profile_service_stub.return_value
        mock_device_profile_service_stub_instance.Get.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackClient.get_device_activation()
        mock_device_service_stub_instance.GetActivation.return_value = self.mock_chirp_methods.get_device_profile_ret_val
        #   mock ChirpstackCLinet.get_device_app_key()
        mock_device_service_stub_instance.GetKeys.return_value = self.mock_chirp_methods.get_device_app_key_ret_val
        #   mock search return values aka does not exist in django
        mock_ld_search.return_value = False
        mock_get_sh.return_value = {'status_code': 404, 'json_body': None}
        sh_id = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.id
        create_sh_response = Mock()
        create_sh_response.headers = {'Content-Type': 'application/json'}
        create_sh_response.status_code = 201
        create_sh_response.json.return_value = {"id": sh_id}
        create_other_response = Mock()
        create_other_response.headers = {'Content-Type': 'application/json'}
        create_other_response.status_code = 201
        create_other_response.json.return_value = {"id": "mock_lc_uid"}
        mock_django_post.side_effect = [
            create_sh_response,
            create_other_response,
            create_other_response,
            create_other_response,
        ]

        #call the action in testing
        client = Mock()
        userdata = Mock()
        temp = self.tracker.on_message(client, userdata, ChirpMessage)

        #data that should have been used
        datetime_obj_utc = epoch_to_UTC(
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.seconds, 
            self.mock_chirp_methods.get_device_ret_val.last_seen_at.nanos
        )        
        last_seen_at = datetime_obj_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
        con_type = "OTAA" if self.mock_chirp_methods.get_device_profile_ret_val.device_profile.supports_otaa else "ABP"
        lw_v = self.mock_chirp_methods.get_device_profile_ret_val.device_profile.mac_version
        key_resp = self.tracker.c_client.get_device_app_key(deveui,lw_v)
        dev_name = replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name)
        lc_str = f"{VSN}-{dev_name}-{deveui}"

        create_sh_data = {
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
            "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
            "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description,
            "capabilities": [35]
        }
        create_ld_data = {
            "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
            "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.id,
            "deveui": deveui
        }
        create_lc_data = {
            "node": VSN,
            "lorawan_device": deveui,
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            'last_seen_at': last_seen_at, 
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin,
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type
        }
        create_lk_data = {
            "lorawan_connection": lc_str,
            "network_Key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.nwk_s_enc_key,  
            "app_session_key": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.app_s_key,
            "dev_address": self.mock_chirp_methods.get_device_activation_ret_val.device_activation.dev_addr,
            "app_key": key_resp
        }
        update_manifest_data = {
            "connection_name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
            "last_seen_at": last_seen_at,
            "margin": self.mock_chirp_methods.get_device_ret_val.device_status.margin, 
            "expected_uplink_interval_sec": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.uplink_interval,
            "connection_type": con_type,
            "lorawandevice": {
                "deveui": self.mock_chirp_methods.get_device_ret_val.device.dev_eui,
                "name": replace_spaces(self.mock_chirp_methods.get_device_ret_val.device.name),
                "battery_level": self.mock_chirp_methods.get_device_ret_val.device_status.battery_level,
                "hardware": {
                    "hardware": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name,
                    "hw_model": clean_hw_model(self.mock_chirp_methods.get_device_profile_ret_val.device_profile.name),
                    "capabilities": ["lorawan"],
                    "description": self.mock_chirp_methods.get_device_profile_ret_val.device_profile.description
                },
            }
        }

        # Assertions
        post_calls = mock_django_post.call_args_list # Extract the call arguments from the call_args_list
        assert post_calls, "Expected at least one PATCH call"
        post_calls[0].assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/", headers=self.tracker.d_client.auth_header, json=create_sh_data)
        post_calls[1].assert_called_once_with( f"{API_INTERFACE}/lorawandevices/", headers=self.tracker.d_client.auth_header, json=create_ld_data)
        post_calls[2].assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.tracker.d_client.auth_header, json=create_lc_data)
        post_calls[3].assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.tracker.d_client.auth_header, json=create_lk_data)
        self.assertTrue(self.manifest.dict["lorawanconnections"][-1] == update_manifest_data)
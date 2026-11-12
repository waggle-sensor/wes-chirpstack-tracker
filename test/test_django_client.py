import unittest
import requests
from pytest import mark
from unittest.mock import Mock, patch, MagicMock
from app.django_client import DjangoClient, HttpMethod

DEV_EUI = "123456789"
API_INTERFACE = "https://auth.sagecontinuum.org"
LC_ROUTER = "lorawanconnections/"
LK_ROUTER = "lorawankeys/"
LD_ROUTER = "lorawandevices/"
SH_ROUTER = "sensorhardwares/"
HW_MODEL = "sfmx100"
VSN = "W030"
NODE_TOKEN = "999294cef6fc3a95fe14c145612825ef5ae27567"

class TestDjangoClient(unittest.TestCase):
    def setUp(self):
        # Set up the DjangoClient with a mock args object
        self.args = Mock(
            api_interface=API_INTERFACE,
            lorawan_connection_router=LC_ROUTER,
            lorawan_key_router=LK_ROUTER,
            lorawan_device_router=LD_ROUTER,
            sensor_hardware_router=SH_ROUTER,
            vsn=VSN,
            node_token=NODE_TOKEN
        )
        self.django_client = DjangoClient(self.args)

    @patch("app.django_client.HttpMethod.GET")
    def test_get_lc(self, mock_get):
        """
        Mocks the requests.get method in django client's get_lc method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = {
            'id': 1, 
            'node': 'W030', 
            'lorawan_device': '123456789', 
            'connection_name': 'test', 
            'created_at': '2023-11-03T20:49:56.290798Z', 
            'last_seen_at': '2023-11-03T20:49:42Z', 
            'margin': '25.00', 
            'expected_uplink_interval_sec': 1, 
            'connection_type': 'OTAA'
        }
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.get_lc(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertEqual(result['json_body'], {'id': 1, 'node': 'W030', 'lorawan_device': '123456789', 
        'connection_name': 'test', 'created_at': '2023-11-03T20:49:56.290798Z', 
        'last_seen_at': '2023-11-03T20:49:42Z', 'margin': '25.00', 
        'expected_uplink_interval_sec': 1, 'connection_type': 'OTAA'})

    @patch("app.django_client.HttpMethod.POST")
    def test_create_lc(self, mock_post):
        """
        Mocks the requests.post method in django client's create_lc method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 201,
            'Custom-Header': 'Mocked-Value',
        }
        create_data = {
            "node": "W030",
            "lorawan_device": "5556677",
            "connection_name": "MyConnection",
            "margin": 3.14,
            "expected_uplink_interval_sec": 60,
            "connection_type": "OTAA"
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = create_data
        mock_post.return_value = mock_response

        # Call the method under test
        result = self.django_client.create_lc(data=create_data)

        # Assertions
        mock_post.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/", headers=self.django_client.auth_header, json=create_data)
        self.assertEqual(result['json_body'], create_data)

    @patch("app.django_client.HttpMethod.PATCH")
    def test_update_lc(self, mock_patch):
        """
        Mocks the requests.patch method in django client's update_lc method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        data = {
            "node": "W030",
            "lorawan_device": "5556677",
            "connection_name": "MyConnection",
            "margin": 3.14,
            "expected_uplink_interval_sec": 60,
            "connection_type": "OTAA"
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = data
        mock_patch.return_value = mock_response

        # Call the method under test
        result = self.django_client.update_lc(dev_eui=DEV_EUI, data=data)

        # Assertions
        mock_patch.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header, json=data)
        self.assertEqual(result['json_body'], data)

    @patch("app.django_client.HttpMethod.GET")
    def test_get_ld(self, mock_get):
        """
        Mocks the requests.get method in django client's get_ld method to test it
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.json.return_value = {"deveui":"123456789","device_name":"test","battery_level":"0.01"}
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.get_ld(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertEqual(result['json_body'], {"deveui":"123456789","device_name":"test","battery_level":"0.01"})

    @patch("app.django_client.HttpMethod.POST")
    def test_create_ld(self, mock_post):
        """
        Mocks the requests.post method in django client's create_ld method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 201,
            'Custom-Header': 'Mocked-Value',
        }
        create_data = {
            "deveui": "5556677",
            "device_name": "MyDevice",
            "battery_level": 5.1
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = create_data
        mock_post.return_value = mock_response

        # Call the method under test
        result = self.django_client.create_ld(data=create_data)

        # Assertions
        mock_post.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/", headers=self.django_client.auth_header, json=create_data)
        self.assertEqual(result['json_body'], create_data)

    @patch("app.django_client.HttpMethod.PATCH")
    def test_update_ld(self, mock_patch):
        """
        Mocks the requests.patch method in django client's update_ld method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        data = {
            "deveui": "5556677",
            "device_name": "MyDevice",
            "battery_level": 5.1
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = data
        mock_patch.return_value = mock_response

        # Call the method under test
        result = self.django_client.update_ld(dev_eui=DEV_EUI, data=data)

        # Assertions
        mock_patch.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{DEV_EUI}/", headers=self.django_client.auth_header, json=data)
        self.assertEqual(result['json_body'], data)

    @patch("app.django_client.HttpMethod.GET")
    def test_get_lk(self, mock_get):
        """
        Mocks the requests.get method in django client's get_lk method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = {
            "id":9,
            "lorawan_connection":"W030-test-123456789",
            "app_key":"12345", 
            "network_Key":"12345",
            "app_session_key":"12345",
            "dev_address":"12345"
        }
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.get_lk(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertEqual(result['json_body'], {"id":9,"lorawan_connection":"W030-test-123456789","app_key":"12345", 
        "network_Key":"12345","app_session_key":"12345","dev_address":"12345"})

    @patch("app.django_client.HttpMethod.POST")
    def test_create_lk(self, mock_post):
        """
        Mocks the requests.post method in django client's create_lk method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 201,
            'Custom-Header': 'Mocked-Value',
        }
        create_data = {        
            "lorawan_connection": "W030-test-123456789", 
            "app_key": "12345",         
            "network_Key": "12345",           
            "app_session_key": "12345",
            "dev_address": "12345"             
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = create_data
        mock_post.return_value = mock_response

        # Call the method under test
        result = self.django_client.create_lk(data=create_data)

        # Assertions
        mock_post.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/", headers=self.django_client.auth_header, json=create_data)
        self.assertEqual(result['json_body'], create_data)

    @patch("app.django_client.HttpMethod.PATCH")
    def test_update_lk(self, mock_patch):
        """
        Mocks the requests.patch method in django client's update_lk method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        data = {        
            "lorawan_connection": "W030-test-123456789", 
            "app_key": "12345",         
            "network_Key": "12345",           
            "app_session_key": "12345",
            "dev_address": "12345"             
        }
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = data
        mock_patch.return_value = mock_response

        # Call the method under test
        result = self.django_client.update_lk(dev_eui=DEV_EUI, data=data)

        # Assertions
        mock_patch.assert_called_once_with(f"{API_INTERFACE}/lorawankeys/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header, json=data)
        self.assertEqual(result['json_body'], data)

    @patch("app.django_client.HttpMethod.GET")
    def test_get_sh(self, mock_get):
        """
        Mocks the requests.get method in django client's get_sh method to test it
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.json.return_value = {"hardware": "test","hw_model": HW_MODEL, "description": "test"}
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.get_sh(hw_model=HW_MODEL)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/{HW_MODEL}/", headers=self.django_client.auth_header)
        self.assertEqual(result['json_body'], {"hardware": "test","hw_model": HW_MODEL, "description": "test"})

    @patch("app.django_client.HttpMethod.POST")
    def test_create_sh(self, mock_post):
        """
        Mocks the requests.post method in django client's create_sh method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 201,
            'Custom-Header': 'Mocked-Value',
        }
        create_data = {"hardware": "test","hw_model": HW_MODEL, "description": "test"}
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = create_data
        mock_post.return_value = mock_response

        # Call the method under test
        result = self.django_client.create_sh(data=create_data)

        # Assertions
        mock_post.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/", headers=self.django_client.auth_header, json=create_data)
        self.assertEqual(result['json_body'], create_data)

    @patch("app.django_client.HttpMethod.PATCH")
    def test_update_sh(self, mock_patch):
        """
        Mocks the requests.patch method in django client's update_sh method to test it
        """
        headers = {
            'Content-Type': 'application/json', 
            'status-code': 200,
            'Custom-Header': 'Mocked-Value',
        }
        data = {"hardware": "test","hw_model": HW_MODEL, "description": "test"}
        mock_response = Mock()
        mock_response.headers = headers
        mock_response.json.return_value = data
        mock_patch.return_value = mock_response

        # Call the method under test
        result = self.django_client.update_sh(hw_model=HW_MODEL, data=data)

        # Assertions
        mock_patch.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/{HW_MODEL}/", headers=self.django_client.auth_header, json=data)
        self.assertEqual(result['json_body'], {"hardware": "test","hw_model": HW_MODEL, "description": "test"})

    @patch("app.django_client.HttpMethod.GET")
    def test_ld_search_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's ld_search method to test when ld is found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 200
        mock_response.json.return_value = {"deveui":"123456789","device_name":"test","battery_level":"0.01"}
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.ld_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertTrue(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_ld_search_Not_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's ld_search method to test when ld is not found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("not found")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.ld_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertFalse(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_ld_search_Unexpected_status(self, mock_get):
        """
        Mocks the requests.get method in django client's ld_search method to test when Unexpected status code is returned
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 500
        mock_response.json.return_value = {}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP error")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.ld_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawandevices/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertIsNone(result)

    @patch("app.django_client.DjangoClient.call_api")
    def test_ld_search_No_response(self, mock_call_api):
        """
        Mocks DjangoClient.call_api() method in ld_search method to test when response is None
        """
        mock_call_api.return_value = {
                'headers': {
                    'Content-Type': 'application/json', 
                    'Custom-Header': 'Mocked-Value',
                },
                'status_code': 500,
                'json_body': None
            }

        # Call the method under test
        result = self.django_client.ld_search(dev_eui=DEV_EUI)

        # Assertions
        self.assertIsNone(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_sh_search_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's sh_search method to test when sh is found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 200
        mock_response.json.return_value = {"hardware": "test","hw_model": HW_MODEL, "description": "test"}
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.sh_search(hw_model=HW_MODEL)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/{HW_MODEL}/", headers=self.django_client.auth_header)
        self.assertTrue(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_sh_search_Not_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's sh_search method to test when sh is not found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail":"not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("not found")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.sh_search(hw_model=HW_MODEL)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/{HW_MODEL}/", headers=self.django_client.auth_header)
        self.assertFalse(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_sh_search_Unexpected_status(self, mock_get):
        """
        Mocks the requests.get method in django client's sh_search method to test when Unexpected status code is returned
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP error")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.sh_search(hw_model=HW_MODEL)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/sensorhardwares/{HW_MODEL}/", headers=self.django_client.auth_header)
        self.assertIsNone(result)

    @patch("app.django_client.DjangoClient.call_api")
    def test_sh_search_No_response(self, mock_call_api):
        """
        Mocks DjangoClient.call_api() method in sh_search method to test when json response is None
        """
        mock_call_api.return_value = {
            'headers': {
                'Content-Type': 'application/json', 
                'Custom-Header': 'Mocked-Value',
        },
            'status_code': 500,
            'json_body': None
        }

        # Call the method under test
        result = self.django_client.sh_search(hw_model=HW_MODEL)

        # Assertions
        self.assertIsNone(result)

    @patch("app.django_client.DjangoClient.call_api")
    def test_find_sh_id_prefers_lowest_id(self, mock_call_api):
        """
        find_sh_id should reuse the oldest matching sensor hardware when duplicates exist
        """
        mock_call_api.return_value = {
            "headers": {},
            "status_code": 200,
            "json_body": [
                {"id": 12, "hw_model": HW_MODEL},
                {"id": 3, "hw_model": HW_MODEL},
                {"id": 7, "hw_model": "other"},
            ],
        }

        result = self.django_client.find_sh_id(HW_MODEL)

        mock_call_api.assert_called_once_with(HttpMethod.GET, SH_ROUTER)
        self.assertEqual(result, 3)

    @patch("app.django_client.DjangoClient.call_api")
    def test_find_sh_id_paginated_results(self, mock_call_api):
        """
        find_sh_id should support DRF paginated list responses
        """
        mock_call_api.return_value = {
            "headers": {},
            "status_code": 200,
            "json_body": {
                "count": 2,
                "results": [
                    {"id": 9, "hw_model": HW_MODEL},
                    {"id": 2, "hw_model": HW_MODEL},
                ],
            },
        }

        result = self.django_client.find_sh_id(HW_MODEL)
        self.assertEqual(result, 2)

    @patch("app.django_client.DjangoClient.call_api")
    def test_find_sh_id_not_found(self, mock_call_api):
        mock_call_api.return_value = {
            "headers": {},
            "status_code": 200,
            "json_body": [{"id": 1, "hw_model": "other"}],
        }

        result = self.django_client.find_sh_id(HW_MODEL)
        self.assertIsNone(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_lc_search_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's lc_search method to test when lc is found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 200
        mock_response.json.return_value = {"connection_name": "test","margin": 2, "connection_type": "OTAA"}
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.lc_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertTrue(result)


    @patch("app.django_client.HttpMethod.GET")
    def test_lc_search_Not_found_happy_path(self, mock_get):
        """
        Mocks the requests.get method in django client's lc_search method to test when lc is not found
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail":"not found"}
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("not found")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.lc_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertFalse(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_lc_search_Unexpected_status(self, mock_get):
        """
        Mocks the requests.get method in django client's lc_search method to test when Unexpected status code is returned
        """
        mock_response = Mock()
        headers = {
            'Content-Type': 'application/json', 
            'Custom-Header': 'Mocked-Value',
        }
        mock_response.headers = headers
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP error")
        mock_get.return_value = mock_response

        # Call the method under test
        result = self.django_client.lc_search(dev_eui=DEV_EUI)

        # Assertions
        mock_get.assert_called_once_with(f"{API_INTERFACE}/lorawanconnections/{VSN}/{DEV_EUI}/", headers=self.django_client.auth_header)
        self.assertIsNone(result)

    @patch("app.django_client.DjangoClient.call_api")
    def test_lc_search_No_response(self, mock_call_api):
        """
        Mocks DjangoClient.call_api() method in lc_search method to test when json response is None
        """
        mock_call_api.return_value = {
            'headers': {
                'Content-Type': 'application/json', 
                'Custom-Header': 'Mocked-Value',
        },
            'status_code': 500,
            'json_body': None
        }

        # Call the method under test
        result = self.django_client.lc_search(dev_eui=DEV_EUI)

        # Assertions
        self.assertIsNone(result)

    @patch("app.django_client.HttpMethod.GET")
    def test_call_api_sad_path(self, mock_get):
        """
        Test DjangoClient.call_api() with a bad response
        """
        mock_response = Mock()
        mock_response.headers = {
                'Content-Type': 'application/json', 
                'Custom-Header': 'Mocked-Value',
        }
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_get.return_value = mock_response

        #Mock endpoint
        api_endpoint = f"{SH_ROUTER}{HW_MODEL}/"

        #Call the method under test
        result = self.django_client.call_api(HttpMethod.GET, api_endpoint)

        # Assert
        self.assertIsNone(result['json_body'])
        self.assertEqual(result['status_code'], 500)


if __name__ == "__main__":
    unittest.main()
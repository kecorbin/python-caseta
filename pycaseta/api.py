import json
import time
import socket
import select
import requests
import sys
import telnetlib
from pycaseta.devices.standard.base import build_device
import logging
import re
#
# DEFAULT_USERNAME = b"lutron"
# DEFAULT_PASSWORD = b"integration"
# TEMP_HOST = '192.168.10.26'
# TEMP_PORT = 23

USERNAME = ""
PASSWORD = ""
HOST = ""
PORT = ""


_NEWLINE = b'\r\n'
# The amount of time we will wait for a response back from the telnet session
_WAIT_FOR_RESPONSE = 3

logging.getLogger('caseta.api')

# For well connected sites this should be in the 2-3 range, higher if connecting remotely
SOCKET_TIMEOUT = 2


def fix_telnet_response(device, resp):
    """
    Helper function to cleanup the response of a Lutron Telnet Integration.
    This function is basically making the telnet response received from the gateway appear to be RESTful

    :param resp: string response from a lutron command
    :return:
    """
    try:
        ret = resp.split(b"\r")[0].split(b"~")[1].split(b"\r\n")[0]
        logging.info("Device Response: {}".format(str(ret)))
        ret = ret.split(b",")
        ret = {'ID': ret[1],
               'state': {'output': ret[3]}}

    except IndexError:
        ret = ''
    return ret


class CasetaAPIInterface(object):
    """
    Represents a Caseta Hub
    """

    def __init__(self, host, port, user, password):
        self._conn = telnetlib.Telnet(host, port)
        self.connection = False
        self.username = user
        self.password = password

    def login(self):
        user = self.username + "\r\n"
        password = self.password + "\r\n"

        self._conn.read_until(b"login:")
        self._conn.write(bytes(user, encoding='ascii'))

        self._conn.read_until(b"password:")
        self._conn.write(bytes(password, encoding='ascii'))

        self.connection = True
        logging.info('Connected to Lutron Bridge')

    def _send_command(self, device, cmd):
        device_id = device.device_id()
        if not self.connection:
            self.login()
        self._conn.write(cmd.encode('ascii'))
        return fix_telnet_response(device, self._conn.read_until(_NEWLINE))


    def set_device_state(self, device, state, id_override=None):
        """
        :type device: WinkDevice
        :param state:   a boolean of true (on) or false ('off')
        :return: The JSON response from the API (new device state)
        """

        _id = device.device_id()
        if state == False:
            state = 0
        elif state == True:
            state = 100.00

        command = "#OUTPUT,{},1,{}\r\n".format(_id, state)
        logging.info(" caseta command: {}".format(command))
        resp = self._send_command(device, command)
        return resp

    def get_device_state(self, device, id_override=None):
        """
        :type device: CasetaDevice
        """
        _id = device.device_id()
        command = "?OUTPUT,{},1\r\n".format(_id)
        logging.info("Sending Lutron command: {}".format(command[:-2]))
        resp = self._send_command(device, command)
        return resp


def set_credentials(host, port, user, password):
    global HOST, PORT, USERNAME, PASSWORD
    HOST = host
    PORT = port
    USERNAME = user
    PASSWORD = password


def get_devices(integration_dict=None):
    # TODO Get JSON representation of all devices.
    # For now we'll fake it.
    # from pycaseta.devices.dummy.bridge import DEVICES
    #
    # response_dict = DEVICES
    return get_devices_from_response_dict(integration_dict)


def get_devices_from_response_dict(response_dict):
    """
    :rtype: list of CasetaDevices
    """
    items = response_dict.get('data')

    devices = []
    zones = response_dict['LIPIdList']['Zones']
    keys = ['ID','Name']

    # DYNAMICALLY POPULATE THIS
    api_interface = CasetaAPIInterface(HOST, PORT, USERNAME, PASSWORD)

    for item in zones:
        # We will extend each item with some useful tracking information
        logging.info('Extending model for {}'.format(item))
        starting_state = {'output': 0}
        item['desired_state'] = starting_state
        item['state'] = starting_state

        for key in keys:
            devices.append(build_device(item, api_interface))
    return devices



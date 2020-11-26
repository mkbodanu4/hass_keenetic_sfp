import voluptuous as vol

from homeassistant.helpers.entity import Entity
from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv

import paramiko
import json
import time
import re

CONF_NAME = "name"
CONF_HOSTNAME = "hostname"
CONF_PORT = "port"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_HOSTNAME): cv.string,
        vol.Required(CONF_PORT): cv.port,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)
    hostname = config.get(CONF_HOSTNAME)
    port = config.get(CONF_PORT)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    add_entities([KeeneticSFP(name, hostname, port, username, password)])


def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)


class KeeneticSFP(Entity):
    def __init__(self, name, hostname, port, username, password):
        self._name = name or DEVICE_DEFAULT_NAME
        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password

        self._result = {}

        self._state = "N/A"
        self._attributes = None

        self.update()

    def update(self):
        self._state = "N/A"
        self._attributes = None

        try:
            self._ssh = paramiko.SSHClient()
            self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._ssh.connect(self._hostname, self._port, self._username, self._password, timeout=1, banner_timeout=1, auth_timeout=1)

            stdin, stdout, stderr = self._ssh.exec_command("more proc:/driver/mt7621_eth/ddmi/info")
            time.sleep(.1)
            stderr.close()
            stdin.close()
            info = stdout.readlines()
            if len(info) > 0:
                for line in info:
                    pair = escape_ansi(line.strip()).split(':', 1)
                    if len(pair) == 2:
                        key, value = pair
                        self._result[key.strip()] = value.strip()

            stdin, stdout, stderr = self._ssh.exec_command("more proc:/driver/mt7621_eth/ddmi/diag")
            time.sleep(.1)
            stderr.close()
            stdin.close()
            diag = stdout.readlines()
            if len(diag) > 0:
                for line in diag:
                    pair = escape_ansi(line.strip()).split(':', 1)
                    if len(pair) == 2:
                        key, value = pair
                        self._result[key.strip()] = value.strip()

            time.sleep(.1)
            self._ssh.close()

            self._attributes = self._result
            self._state = "OK"
        except:
            self._state = "Error"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def should_poll(self):
        return True

    @property
    def state_attributes(self):
        return self._attributes

import netifaces
import os

from drcsim.server.data import constants
from drcsim.server.util.logging.logger import Logger
from drcsim.server.util.os_util import OsUtil
from drcsim.server.util.process_util import ProcessUtil


class InterfaceUtil:
    def __init__(self):
        pass

    @classmethod
    def get_wiiu_compatible_interfaces(cls):
        """
        Returns a list of interfaces that can operate on the 5GHz spectrum
        :return: array of interface names
        """
        all_interfaces = cls.get_all_interfaces()
        compatible_interfaces = []
        for interface in all_interfaces:
            if cls.is_interface_wiiu_compatible(interface):
                compatible_interfaces.append(interface)
        return compatible_interfaces

    @classmethod
    def get_all_interfaces(cls):
        """
        Gets a list of all system network interfaces
        :return: array of interface names
        """
        interfaces = []
        for interface in netifaces.interfaces():
            interfaces.append(interface)
        return interfaces

    @classmethod
    def is_interface_wiiu_compatible(cls, interface):
        if not OsUtil.is_linux():
            Logger.extra("Ignoring interface compatibility check for %s", interface)
            return False
        frequency_info = ProcessUtil.get_output(["iwlist", interface, "frequency"])
        return "5." in frequency_info
        # TODO check for 802.11n compliance

    @classmethod
    def get_ip(cls, interface):
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addresses:
            return addresses[netifaces.AF_INET][0]["addr"]
        return ""

    @classmethod
    def get_mac(cls, interface):
        addresses = netifaces.ifaddresses(interface)
        if netifaces.AF_LINK in addresses:
            return addresses[netifaces.AF_LINK][0]["addr"]
        return "0"

    @classmethod
    def set_metric(cls, interface, metric):
        ProcessUtil.call(["ifmetric", interface, str(metric)])

    @classmethod
    def dhclient(cls, interface):
        ProcessUtil.call(["killall", "dhclient"])
        ProcessUtil.call(["dhclient", interface])

    @classmethod
    def is_managed_by_network_manager(cls, interface):
        output = ProcessUtil.get_output(["nmcli", "-g", "GENERAL.STATE", "device", "show", interface]).strip()
        return "unmanaged" not in output

    @classmethod
    def get_device_unmanaged_entry(cls, interface):
        # Ubuntu 17.04+ randomizes the MAC address of the device each time network manager restarts.
        # Fortunately, the interface names make up for that by containing the hardware address
        if OsUtil.is_ubuntu() and int(OsUtil.get_dist_version()[0]) >= 17:
            return "interface-name:" + interface
        return "mac:" + cls.get_mac(interface)

    @classmethod
    def set_unmanaged_by_network_manager(cls, interface):
        Logger.debug("Adding interface \"%s-%s\" as an unmanaged interface to network manager", interface,
                     cls.get_mac(interface))
        with open(constants.PATH_CONF_NETWORK_MANAGER, "r") as conf_read:
            conf = conf_read.read().splitlines()
        added = False
        entry = cls.get_device_unmanaged_entry(interface)
        # Add Entry
        for line in range(0, len(conf)):
            # Add keyfile plugin if it's not enabled
            if conf[line].startswith("plugins=") and "keyfile" not in conf[line]:
                conf[line] += ",keyfile"
            # Add unmanaged device
            if conf[line].startswith("unmanaged-devices=") and entry not in conf[line]:
                conf[line] += ";" + entry
                added = True
        # Add the initial unmanaged entry if it was not present
        if not added:
            conf.append("[keyfile]")
            conf.append("unmanaged-devices=" + entry)
        # Write
        with open(constants.PATH_CONF_NETWORK_MANAGER, "w") as conf_write:
            for line in conf:
                conf_write.write(line + "\n")
        # Restart the service
        ProcessUtil.call(["service", "NetworkManager", "restart"])
        ProcessUtil.call(["service", "network-manager", "restart"])
        ProcessUtil.call(["service", "networking", "restart"])

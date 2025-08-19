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
        # I kinda hate this implementation, but I'm not sure how to get
        # this information programmatically any other way. This is
        # fragile.
        iwcommand = ["iw", "dev", interface, "info"]
        iwdev = ProcessUtil.get_output(iwcommand).strip()
        if not iwdev.startswith("Interface"):
            return False
        splitiwdev = iwdev.split("\n")
        for line in splitiwdev:
            if "wiphy" not in line:
                continue
            phynum = line.strip().split()[1]
            break
        else:
            raise ValueError(f"Failed to parse phyname from {iwcommand}")
        phyname = "phy" + phynum
        phyinfo = ProcessUtil.get_output(["iw", "phy", phyname, "info"])
        # 5180 MHz, channel 36, should be available in all regulatory
        # domains
        return "5180" in phyinfo

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
    def dhclient(cls, interface):
        ProcessUtil.call(["killall", "dhclient"])
        ProcessUtil.call(["dhclient", interface, "-e", "IF_METRIC=9999", "-e", "METRIC=9999"])

    @classmethod
    def is_managed_by_network_manager(cls, interface):
        output = ProcessUtil.get_output(["nmcli", "-g", "GENERAL.STATE", "device", "show", interface]).strip()
        if "Could not connect: No such file or directory" in output:
            # NetworkManager didn't respond appropriately, so we're gonna assume
            # the interface is unmanaged.
            Logger.warn("nmcli could not connect to NetworkManager. NM may not be running.")
            return False
        return output == "10 (unmanaged)"

    @classmethod
    def get_device_unmanaged_entry(cls, interface):
        # Ubuntu 17.04+ randomizes the MAC address of the device each time network manager restarts.
        # Fortunately, the interface names make up for that by containing the hardware address
        if OsUtil.is_ubuntu() and int(OsUtil.get_dist_version()[0]) >= 17:
            return "interface-name:" + interface
        return "mac:" + cls.get_mac(interface)

    @classmethod
    def set_managed_by_network_manager(cls, interface, managed: False):
        managed_str = "yes" if managed else "no"
        Logger.debug("Setting interface \"%s-%s\" managed \"%s\"", interface,
                     cls.get_mac(interface), managed_str)
        ProcessUtil.call(("nmcli", "device", "set", interface, "managed", managed_str))
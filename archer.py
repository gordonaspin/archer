""" connect to TP-Link router and enumerate topology """
import sys
import logging
import ipaddress
import click
import keyring
from tplinkrouterc6u import TplinkRouterProvider
from tplinkrouterc6u import TPLinkXDRClient
from tplinkrouterc6u.common.exception import ClientException
from tplinkrouterc6u.client.c6u import TplinkRouter
from tplinkrouterc6u.client.deco import TPLinkDecoClient
from tplinkrouterc6u.client_abstract import AbstractRouter
from tplinkrouterc6u.client.mr import TPLinkMRClient, TPLinkMRClientGCM
from tplinkrouterc6u.client.mr200 import TPLinkMR200Client
from tplinkrouterc6u.client.ex import TPLinkEXClient, TPLinkEXClientGCM
from tplinkrouterc6u.client.c5400x import TplinkC5400XRouter
from tplinkrouterc6u.client.c1200 import TplinkC1200Router
from tplinkrouterc6u.client.c80 import TplinkC80Router
from tplinkrouterc6u.client.vr import TPLinkVRClient
from tplinkrouterc6u.client.wdr import TplinkWDRRouter
from tplinkrouterc6u.client.re330 import TplinkRE330Router
from dataclasses import dataclass, field

#from tplinkrouterc6u.enum import Connection
from tplinkrouterc6u.common.package_enum import Connection
from tplinkrouterc6u.common.dataclass import Device
from mac_vendor_lookup import MacLookup
import macaddress
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()
maclookup = MacLookup()

logger = logging.getLogger("main")

def lookup(mac):
    """ return vendor for mac address """
    try:
        vendor = maclookup.lookup(str(mac))
    except: #pylint: disable=bare-except
        logger.debug(f"Unable to lookup mac {mac} {str(mac)}")
        vendor = "Unknown"

    return vendor

def setup_logger(log_level) -> None:
    """ sets up logger """
    level = logging.CRITICAL
    log_format='%(asctime)s %(levelname)-8s %(funcName)-32s %(message)s'
    if log_level == "debug":
        level = logging.DEBUG
    elif log_level == "info":
        level = logging.INFO
    elif log_level == "error":
        level = logging.ERROR
    elif log_level == "none":
        logging.disable()
        level = logging.CRITICAL

    logger.setLevel(level) 
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(log_format)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return level

def print_topology(dev, sortkey, indent, count, color):
    i = indent
    c = count
    if len(dev.hostname) < 5: #mint is shortest name
        color = Fore.RED
    elif isinstance(dev, AbsentDevice):
        color = Fore.CYAN
    elif isinstance(dev, RouterDevice):
        color = Fore.LIGHTGREEN_EX
    elif isinstance(dev, MeshDevice):
        color = Fore.LIGHTYELLOW_EX

    print(f"{color}{c:03} " + 1*i*" " + f"{dev.type.name[-2:]:{4-1*i}} "\
          f"{dev.macaddress} {dev.ipaddress:16s} {dev.hostname:34} {dev.model:12.12} "\
          f"{dev.vendor:36.36} {dev.lease_time:9.9s} {dev.device_type:16.16} "\
          f"{str(dev.signal_strength):>3.3s}"\
          f"{Style.RESET_ALL}")
    if len(dev.associates) > 0:
        match dev:
            case RouterDevice():
                color = Fore.GREEN
            case MeshDevice():
                color = Fore.YELLOW
        i = i + 1
        match sortkey:
            case 'm':
                dev.associates.sort(key=lambda a:a.macaddress)
            case 'i':
                dev.associates.sort(key=lambda a:a.ipaddress)
            case 'h':
                dev.associates.sort(key=lambda a:a.hostname)
            case 'o':
                dev.associates.sort(key=lambda a:a.model)
            case 'v':
                dev.associates.sort(key=lambda a:a.vendor)
            case 'l':
                dev.associates.sort(key=lambda a:a.lease_time)
            case 't':
                dev.associates.sort(key=lambda a:a.device_type)
            case 's':
                dev.associates.sort(key=lambda a:a.signal_strength)
            case _ :
                dev.associates.sort(key=lambda a:a.ipaddress)
        for dev in dev.associates:
            c = print_topology(dev, sortkey, i, c + 1, color)

    return c

@dataclass
class ExtendedDevice(Device):
    """ ExtendedDevice class implements topology with associated devices """
    def __init__(self, type: Connection, #pylint: disable=redefined-builtin, too-many-arguments
                 macaddr: macaddress,
                 ipaddr: ipaddress,
                 hostname: str) -> None:
        super().__init__(type, macaddr, ipaddr, hostname)
        self.model = "" 
        self.vendor = lookup(self.macaddress)
        self.lease_time = ""
        self.signal_strength = 0
        self.upload_speed = 0
        self.download_speed = 0
        self.device_type = ""
        self.associates = []
    def associate(self, dev):
        """ associate dev to this device """
        if dev not in self.associates:
            self.associates.append(dev)
    def set_device_type(self, devtype):
        if devtype == "other" or devtype == "iot_device":
            return
        else:
            self.device_type = devtype

@dataclass
class RouterDevice(ExtendedDevice):
    """ Class RouterDevice """
    def __init__(self, type: Connection, macaddr: macaddress, ipaddr: ipaddress, hostname: str) -> None:
        super().__init__(type, macaddr, ipaddr, hostname)

@dataclass
class MeshDevice(ExtendedDevice):
    """ Class MeshDevice """
    def __init__(self, type: Connection, macaddr: macaddress, ipaddr: ipaddress, hostname: str) -> None:
        super().__init__(type, macaddr, ipaddr, hostname)
        self.client_num = 0

@dataclass
class AbsentDevice(ExtendedDevice):
    """ Class AbsentDevice """
    def __init__(self, type: Connection, macaddr: macaddress, ipaddr: ipaddress, hostname: str) -> None:
        super().__init__(type, macaddr, ipaddr, hostname)

def map_connection_type(type):
    connection_type_map = { "2.4G": Connection.HOST_2G,
                  "5G": Connection.HOST_5G,
                  "6G": Connection.HOST_6G }
    
    if type is None:
        return Connection.HOST_2G
    
    connection_type = connection_type_map.get(type)
    return connection_type

@click.command()
@click.option("--router-host",       help="URL of router", default="http://192.168.0.1")
@click.option("--username",     help="username", default="admin")
@click.option("--password",     help="password")
@click.option("--sortkey",     help="m=MAC, i=IP, h=Hostname, o=Model, v=Vendor, l=Lease, t=Type, s=dB", default="i")
@click.option("--log-level",
              help="Log level (default: none)",
              type=click.Choice(["none", "debug", "info", "error"]),
              default="none")


def main(router_host, username, password, sortkey, log_level):
    """ main entry point"""
    level = setup_logger(log_level)
    #maclookup.update_vendors()

    logger.debug(f"router-host: {router_host}")
    logger.debug(f"username: {username}")
    logger.debug(f"password: {password is not None}")
    logger.debug(f"log-level: {log_level}")

    if password is None:
        logger.info("getting password from keyring")
        password = keyring.get_password("password://tp-link", "admin")

    logger.debug(f"connecting to router {router_host}")
    for client in [TplinkC5400XRouter, TPLinkVRClient, TPLinkEXClientGCM, TPLinkEXClient, TPLinkMRClientGCM,
                            TPLinkMRClient, TPLinkMR200Client, TPLinkDecoClient, TPLinkXDRClient, TplinkRouter,
                            TplinkC80Router, TplinkWDRRouter, TplinkRE330Router]:
        router = client(router_host, password, username, logger, True, 30)
        if router.supports():
            logger.info(f"Router is {client}")

    router = TplinkRouterProvider.get_client(router_host, password, logger=logger)
    try:
        router.authorize()
    except Exception as ex:
        print(ex)
        print(f"Login failed. Are you logged in in the browser ?")
        quit()

    # Get firmware info - returns Firmware
    logger.info("getting firmware info")
    firmware = router.get_firmware()
    print(f"firmware version: {firmware.firmware_version}")
    print(f"hardware version: {firmware.hardware_version}")
    print(f"model: {firmware.model}")

    devices = {}
    logger.info("getting router status")
    status = router.get_status()
    logger.debug(f"status: {status}")
    router_dev = devices[status._lan_macaddr] = RouterDevice(Connection.HOST_6G, status._lan_macaddr, status._lan_ipv4_addr, "router")
    router_dev.model = firmware.model
    router_dev.lease_time = "Permanent"
    router_dev.device_type = "Router"
    logger.info(f"From status, added RouterDevice {router_dev}")
    

    logger.debug(devices)

    for dev in status.devices:
        devices[dev.macaddress] = ExtendedDevice(dev.type, dev._macaddr, dev._ipaddr, dev.hostname)
        router_dev.associate(devices[dev.macaddress])
        logger.info(f"From status, added ExtendedDevice {devices[dev.macaddress]}")

    logger.debug(devices)

    logger.info("getting mesh devices")
    mesh_devices = router.request(
        'admin/easymesh_network?form=mesh_sclient_list_all&operation=read',
        'operation=read')
    logger.debug(mesh_devices)
    for item in mesh_devices:
        mac = item['mac']
        try:
            old_dev = devices[macaddress.EUI48(mac)]
            dev = devices[macaddress.EUI48(mac)] = MeshDevice(dev.type, dev._macaddr, dev._ipaddr, dev.hostname)
            logger.info(f"From mesh devices, changing {old_dev} to MeshDevice {devices[dev.macaddress]}")
        except KeyError as ex:
            dev = devices[dev.macaddress] = MeshDevice(Connection.HOST_5G, macaddress.EUI48(mac), ipaddress.ip_address(item['ip']), item['name'])
            dev.model = item['model']
            logger.info(f"From mesh devices, added {devices[dev.macaddress]}")
        dev.client_num = item['client_num']
        dev.device_type = item['device_type']
        dev.signal_strength = item['signal_strength']
        router_dev.associate(dev)
    
    logger.info("getting dhcp leases")
    ipv4_leases = router.get_ipv4_dhcp_leases()
    logger.debug(ipv4_leases)

    # Check for devices not currently in topology, but have retained dhcp lease
    for lease in ipv4_leases:
        try:
            dev = devices[lease.macaddress]
        except KeyError as ex:
            dev = devices[lease.macaddress] = AbsentDevice(Connection.HOST_2G, lease.macaddress, lease.ipaddress, lease.hostname)
            router_dev.associate(dev)
            logger.info(f"From ipv4 leases, added {devices[dev.macaddress]}")
        dev.lease_time = lease.lease_time
        dev._ipaddr = lease.ipaddress

    logger.debug(devices)

    logger.info("getting router ipv4 reservations")
    reservations = router.get_ipv4_reservations()
    logger.debug(reservations)

    for res in reservations:
        try:
            dev = devices[res.macaddress]
        except KeyError as ex:
            dev = devices[dev.macaddress] = ExtendedDevice(Connection.HOST_2G, res.macaddress, res.ipaddress, res.hostname)
            logger.debug(f"From reservations, added {devices[dev.macaddress]}")
        dev.lease_time = "Permanent"            
        router_dev.associate(devices[dev.macaddress])

    # Get signal strengths and other info
    logger.info("getting device signal strenghts and other info")
    game_accelerators = router.request(
        'admin/smart_network?form=game_accelerator&operation=loadDevice',
        'operation=loadDevice')
    logger.debug(game_accelerators)
    for item in game_accelerators:
        mac = item['mac']
        try:
            dev = devices[macaddress.EUI48(mac)]
            logger.info(f"From game accelerators, changing mac: {dev.macaddress} device_type from {dev.device_type} to {item.get('deviceType')}")
            dev.set_device_type(item.get('deviceType'))
        except KeyError as ex:
            match item['deviceTag']:
                case '2.4G':
                    device_type = Connection.HOST_2G
                case '5G':
                    device_type = Connection.HOST_5G
                case '6G':
                    device_type = Connection.HOST_6G
                case _ :
                    device_type = Connection.HOST_2G
                    logger.debug('Assuming Connection.HOST_2G')
            dev = devices[dev.macaddress] = ExtendedDevice(device_type, macaddress.EUI48(item['mac']), ipaddress.ip_address(item['ip']), item['deviceName'])
            logger.info(f"From game accelerators, added {devices[dev.macaddress]}")
        dev.signal_strength = item.get('signal', 0)
        dev.upload_speed = item.get('uploadSpeed', 0)
        dev.download_speed = item.get('downloadSpeed', 0)

    logger.debug(devices)

    print(f"{Fore.LIGHTBLUE_EX}Num Wifi MAC               IP               "\
            "Hostname                           Model        Vendor                               "\
            "Lease     Type              dB"\
            f"{Style.RESET_ALL}")

    print_topology(router_dev, sortkey, 0, 1, Fore.GREEN)
    router.logout()


if __name__ == '__main__':
    main() #pylint: disable=no-value-for-parameter


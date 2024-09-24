""" connect to TP-Link router and enumerate topology """
import logging
import ipaddress
import click
import keyring
from tplinkrouterc6u import TplinkRouterProvider
from tplinkrouterc6u.enum import Wifi
from tplinkrouterc6u.dataclass import Device
from mac_vendor_lookup import MacLookup
import macaddress
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()
maclookup = MacLookup()

def lookup(mac):
    """ return vendor for mac address """
    try:
        vendor = maclookup.lookup(str(mac))
    except: #pylint: disable=bare-except
        vendor = "Unknown"

    return vendor

class ExtendedDevice(Device):
    """ ExtendedDevice class implements topology with associated devices """
    def __init__(self, type: Wifi, #pylint: disable=redefined-builtin, too-many-arguments
                 macaddr: macaddress,
                 ipaddr: ipaddress,
                 hostname: str,
                 model: str,
                 lease_time: str) -> None:
        super().__init__(type, macaddr, ipaddr, hostname)
        self.model = model
        self.vendor = lookup(self.macaddress)
        self.lease_time = lease_time
        self.signal_strength = 0
        self.upload_speed = 0
        self.download_speed = 0
        self.device_type = ""
        self.associates = []
    def associate(self, dev):
        """ associate dev to this device """
        self.associates.append(dev)
    def set_device_type(self, devtype):
        if devtype == "other" or devtype == "iot_device":
            return
        else:
            self.device_type = devtype

class RouterDevice(ExtendedDevice):
    """ Class RouterDevice """

class MeshDevice(ExtendedDevice):
    """ Class MeshDevice """

class AbsentDevice(ExtendedDevice):
    """ Class AbsentDevice """

connection_type_map = { "2.4G": Wifi.WIFI_2G,
                  "5G": Wifi.WIFI_5G,
                  "6G": Wifi.WIFI_6G }

@click.command()
@click.option("--router",       help="URL of router", default="http://192.168.0.1")
@click.option("--username",     help="username", default="admin")
@click.option("--password",     help="password")
@click.option("--log-level",
              help="Log level (default: debug)",
              type=click.Choice(["none", "debug", "info", "error"]),
              default="none")


def main(router, username, password, log_level):
    """ main entry point"""
    if log_level == "none":
        logging.disable()
        log_level = logging.CRITICAL
    elif log_level == "info":
        log_level = logging.INFO
    elif log_level == "debug":
        log_level = logging.DEBUG
    elif log_level == "error":
        log_level = logging.ERROR

    #maclookup.update_vendors()

    logging.basicConfig(level=log_level, format="%(asctime)s %(levelname)-8s %(message)s")
    logging.debug("router: %s", router)
    logging.debug("username: %s", username)
    logging.debug("password: %s", password is not None)
    logging.debug("log-level: %s", log_level)

    if password is None:
        logging.info("getting password from keyring")
        password = keyring.get_password("password://tp-link", "admin")

    logging.debug("connecting to router %s", router)
    router = TplinkRouterProvider.get_client(router, password, logger=logging)
    router.authorize()

    # Get firmware info - returns Firmware
    logging.info("getting firmware info")
    firmware = router.get_firmware()
    print(f"firmware version: {firmware.firmware_version}")
    print(f"hardware version: {firmware.hardware_version}")
    print(f"model: {firmware.model}")

    logging.debug("getting router status")
    status = router.get_status()
    logging.debug("status: %s", router.request('admin/status?form=all&operation=read')
)

    devices = {}
    leases = {}
    for dev in status.devices:
        devices[dev.macaddress] = dev

    logging.debug("getting router ipv4 dhcp leases")
    for lease in router.get_ipv4_dhcp_leases():
        leases[lease.macaddress] = lease

    logging.debug("getting mesh topology")
    topology = router.request("/admin/onemesh_network?form=mesh_topology")
    logging.debug("topology: %s", topology)

    router_dev = RouterDevice(Wifi.WIFI_6G if status.wifi_6g_enable \
                              else Wifi.WIFI_5G if status.wifi_5g_enable \
                                else Wifi.WIFI_2G,
                        macaddress.EUI48(topology.get('mac')),
                        ipaddress.IPv4Address(topology.get('ip')),
                        topology.get('name'),
                        topology.get('model'),
                        "Permanent")
    router_dev.set_device_type(topology.get('device_type'))
    logging.debug("router device is %s", router_dev.hostname)
    if router_dev.macaddress in devices:
        pass
    else:
        devices[router_dev.macaddress] = router_dev

    # Devices hanging off the router
    for dev in topology.get('mesh_nclient_list'):
        mac = macaddress.EUI48(dev.get('mac'))
        if mac in devices and devices[mac].ipaddress != ipaddress.IPv4Address('0.0.0.0'):
            device = devices[mac] = ExtendedDevice(devices[mac].type,
                        devices[mac].macaddress,
                        devices[mac].ipaddress,
                        devices[mac].hostname,
                        '',
                        leases[mac].lease_time if mac in leases else "")
        else:
            connection_type = dev.get('connection_type')
            if connection_type is None:
                connection_type = '2.4G'
            connection_type = connection_type_map[connection_type]
            device = devices[mac] = ExtendedDevice(connection_type,
                        macaddress.EUI48(dev.get('mac')),
                        ipaddress.IPv4Address(dev.get('ip')),
                        dev.get('name'),
                        '',
                        leases[mac].lease_time if mac in leases else "")
        device.set_device_type(dev.get('device_type'))
        logging.debug("adding device %s to router", device.hostname)
        router_dev.associate(device)

    # Mesh devices
    for dev in topology.get('mesh_sclient_list'):
        mac = macaddress.EUI48(dev.get('mac'))
        if mac in devices:
            device = devices[mac] = MeshDevice(devices[mac].type,
                        devices[mac].macaddress,
                        devices[mac].ipaddress,
                        devices[mac].hostname,
                        dev.get('model'),
                        "Permanent")
        else:
            device = devices[mac] = MeshDevice(Wifi.WIFI_5G,
                        macaddress.EUI48(dev.get('mac')),
                        ipaddress.IPv4Address(dev.get('ip')),
                        dev.get('name'),
                        dev.get('model'),
                        "Permanent")
        device.set_device_type(dev.get('device_type'))
        logging.debug("adding mesh device %s to router", device.hostname)
        router_dev.associate(device)
        for dev in dev.get('mesh_nclient_list'):
            dev_mac = macaddress.EUI48(dev.get('mac'))
            if dev_mac in devices:
                device = devices[dev_mac] = ExtendedDevice(devices[dev_mac].type,
                            devices[dev_mac].macaddress,
                            devices[dev_mac].ipaddress,
                            devices[dev_mac].hostname,
                            '',
                            leases[dev_mac].lease_time if dev_mac in leases else "")
            else:
                connection_type = dev.get('connection_type')
                if connection_type is None:
                    connection_type = '2.4G'
                connection_type = connection_type_map[connection_type]
                device = devices[dev_mac] = ExtendedDevice(connection_type,
                            macaddress.EUI48(dev.get('mac')),
                            ipaddress.IPv4Address(dev.get('ip')),
                            dev.get('name'),
                            '',
                            leases[dev_mac].lease_time if dev_mac in leases else "")
            logging.debug("adding device %s to mesh device %s",
                          device.hostname, devices[mac].hostname)
            devices[mac].associate(device)

    # Check for devices not currently in topology, but have retained dhcp lease
    for mac, lease in leases.items():
        if mac not in devices:
            device = devices[mac] = AbsentDevice(Wifi.WIFI_2G,
                            mac,
                            lease.ipaddress,
                            lease.hostname,
                            'absent',
                            lease.lease_time)
            logging.debug("adding disconnected device %s with leased address to router device %s",
                          device.hostname, router_dev.hostname)
            router_dev.associate(device)

    logging.debug("getting router ipv4 reservations")
    for res in router.get_ipv4_reservations():
        if res.macaddress not in devices:
            print("%s %s not in devices", res.macaddress, res.hostname)

    # Get signal strengths and other info
    logging.debug("getting device signal strenghts and other info")
    game_accelerators = router.request(
        'admin/smart_network?form=game_accelerator',
        'operation=loadDevice')
    for item in game_accelerators:
        mac = item['mac']
        try:
            dev = devices[macaddress.EUI48(mac)]
            dev.signal_strength = item.get('signal', 0)
            dev.upload_speed = item.get('uploadSpeed', 0)
            dev.download_speed = item.get('downloadSpeed', 0)
            logging.debug("changing mac: %s device_type from %s to %s", dev.macaddress, dev.device_type, item.get('deviceType'))
            dev.set_device_type(item.get('deviceType'))
            logging.debug("mac: %s %s", dev.macaddr, item)
        except KeyError as ex:
            logging.error("KeyError %s %s", mac, ex)


    def print_topology(dev, indent, count, color):
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
            dev.associates.sort(key=lambda a:a.ipaddress)
            for dev in dev.associates:
                c = print_topology(dev, i, c + 1, color)

        return c

    print(f"{Fore.LIGHTBLUE_EX}Num Wifi MAC               IP               "\
          "Hostname                           Model        Vendor                               "\
          "Lease     Type              dB"\
          f"{Style.RESET_ALL}")
    print_topology(router_dev, 0, 1, Fore.GREEN)

if __name__ == '__main__':
    main() #pylint: disable=no-value-for-parameter

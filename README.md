# archer
command line tool to show network status from TP-Link router. Uses [TP-Link-Archer-C6U](https://github.com/AlexandrErohin/TP-Link-Archer-C6U.git)

```
git clone https://github.com/AlexandrErohin/TP-Link-Archer-C6U.git
git clone https://github.com/gordonaspin/archer.git
```
Usage:
```
Usage: archer.py [OPTIONS]

  main entry point

Options:
  --router TEXT                   URL of router
  --username TEXT                 username
  --password TEXT                 password
  --log-level [none|debug|info|error]
                                  Log level (default: debug)
  --help                          Show this message and exit.
```

```
Num Wifi   MAC               IP               Hostname                           Model        Vendor                               Lease     Type              dB
001 6G     AB-CD-EF-01-02-03 192.168.0.1      Archer AXE75                       AXE5400 Tri- TP-Link Corporation Limited          Permanent router             0
002   5G   AB-CD-EF-01-02-03 192.168.0.2      mint                                            Intel Corporate                      Permanent pc               -74
003   5G   AB-CD-EF-01-02-03 192.168.0.3      abcLoft-RE603X                     RE603X       TP-LINK TECHNOLOGIES CO.,LTD.        Permanent mesh               0
004     2G AB-CD-EF-01-02-03 192.168.0.28     defPatioLights-HS103                            TP-LINK TECHNOLOGIES CO.,LTD.        1:43:56   iot_device         0
005     2G AB-CD-EF-01-02-03 192.168.0.85     defMasterBedroomaaaaaa-wiz_45bf8a               WiZ IoT Company Limited              1:15:45   iot_device         0
006     2G AB-CD-EF-01-02-03 192.168.0.125    defMasterBedroomaaaaaa-wiz_4639f2               WiZ IoT Company Limited              1:28:59   iot_device         0
007     2G AB-CD-EF-01-02-03 192.168.0.126    abc-ecobee                                      ecobee inc                           1:16:54   other              0
008     2G AB-CD-EF-01-02-03 192.168.0.213    abcPatioLights-AmazonPlug2BWT                   Amazon Technologies Inc.             1:25:28   iot_device         0
009     2G AB-CD-EF-01-02-03 192.168.0.234    abcPatioFan-HS103                               TP-LINK TECHNOLOGIES CO.,LTD.        1:50:12   iot_device         0
010     5G AB-CD-EF-01-02-03 192.168.0.252    abcFamilyRoomEcho                               Amazon Technologies Inc.             1:47:31   tablet             0
011   5G   AB-CD-EF-01-02-03 192.168.0.4      defFamilyRoom-RE603X               RE603X       TP-LINK TECHNOLOGIES CO.,LTD.        Permanent mesh               0
012     2G AB-CD-EF-01-02-03 192.168.0.6      defPatioEcho                                    Amazon Technologies Inc.             1:21:55   other              0
013     2G AB-CD-EF-01-02-03 192.168.0.24     defFamilyRoomRoku                               Hui Zhou Gaoshengda Technology Co.,L 1:27:58   entertainment      0
014     2G AB-CD-EF-01-02-03 192.168.0.65     nixplay_W10B-05                                 Sichuan AI-Link Technology Co., Ltd. 1:27:57   other              0
015     2G AB-CD-EF-01-02-03 192.168.0.97     defMasterBedroomEchoDot                         Amazon Technologies Inc.             1:27:59   other              0
016     2G AB-CD-EF-01-02-03 192.168.0.155    defFamilyRoomEcho                               Amazon Technologies Inc.             1:27:58   other              0
017     2G AB-CD-EF-01-02-03 192.168.0.177    defChristmasTree-AmazonPlug5GLF                 Amazon.com, LLC                      1:36:46   iot_device         0
018     5G AB-CD-EF-01-02-03 192.168.0.215    defMasterBedroomRoku                            Hui Zhou Gaoshengda Technology Co.,L 1:31:2    entertainment      0
019     2G AB-CD-EF-01-02-03 192.168.0.231    Blink-Mini                                      Amazon Technologies Inc.             1:24:3    iot_device         0
020   2G   AB-CD-EF-01-02-03 192.168.0.5      printer                                         Hewlett Packard                      Permanent printer          -58
021   2G   AB-CD-EF-01-02-03 192.168.0.17     abcYaleBridge-connect                           Wistron Neweb Corporation            1:27:26   other            -54
022   5G   AB-CD-EF-01-02-03 192.168.0.19     US-Y423KPW4F6                                   Apple, Inc.                          1:21:14   pc               -65
023   5G   AB-CD-EF-01-02-03 192.168.0.42     aaaaaasiPhone14Pro                              Unknown                              1:12:42   phone            -77
024   2G   AB-CD-EF-01-02-03 192.168.0.121    Google-Home-Mini                                Google, Inc.                         1:24:41   other            -54
025   5G   AB-CD-EF-01-02-03 192.168.0.185    abcLoftBedroomEcho                              Amazon Technologies Inc.             1:29:8    other            -75
026   5G   AB-CD-EF-01-02-03 192.168.0.219    def-ecobee                                      ecobee inc                           1:55:51   other            -53
027   5G   AB-CD-EF-01-02-03 192.168.0.223    abcFamilyRoomRoku                               Hui Zhou Gaoshengda Technology Co.,L 1:30:41   entertainment    -77
```

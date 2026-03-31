#!/usr/bin/env python3
"""Bluetooth wardriving utility (modernized for Python 3).
"""

import argparse
import asyncio
import bleak
import copy
import getpass
import gps3.agps3 as agps3
import os
import queue
import re
import smtplib
import sqlite3
import sys
import threading
import time

try:
    import pygame
except ImportError:
    pygame = None

from bluedrivingWebServer import createWebServer
from getCoordinatesFromAddress import getCoordinates

__version__ = '0.1'

# Runtime flags
debug = False
verbose = False
threadbreak = False
global_location = ''
flag_sound = True
flag_internet = True
flag_gps = True
flag_lookup_services = True
flag_alarm = True
list_devices = {}
queue_devices = None
mail_username = ''
mail_password = ''

address_cache = {}

# terminal color constants
GRE = '\033[92m'
END = '\033[0m'
RED = '\033[91m'
CYA = '\033[96m'


def version():
    print(RED)
    print(f"   {sys.argv[0]} Version {__version__} @COPYLEFT")
    print('   Authors: Veronica Valeros (vero.valeros@gmail.com), Seba Garcia (eldraco@gmail.com)')
    print('   Contributors: nanojaus')
    print('   Bluedriving is a bluetooth wardriving utility.')
    print()
    print(END)


def usage():
    print(RED)
    print()
    print(f"   {sys.argv[0]} Version {__version__} @COPYLEFT")
    print('   Authors: Veronica Valeros (vero.valeros@gmail.com), Seba Garcia (eldraco@gmail.com)')
    print('   Contributors: nanojaus')
    print('   Bluedriving is a bluetooth wardriving utility.')
    print()
    print(f"\n   Usage: {sys.argv[0]} <options>")
    print('   Options:')
    print('  -h, --help                           Show this help message and exit.')
    print('  -D, --debug                          Debug mode ON. Prints debug information on the screen.')
    print('  -d, --database-name                  Name of the database to store the data.')
    print('  -w, --webserver                      It runs a local webserver to visualize and interact with the collected information. Defaults to port 8000.')
    print('  -p, --webserver-port                 Port where the webserver is going to listen. Defaults to 8000.')
    print('  -I, --webserver-ip                   IP address where the webserver binds. Defaults to 127.0.0.1.')
    print('  -s, --disable-sound                  Do not play discover sounds.')
    print('  -i, --not-internet                   Disable internet lookups.')
    print('  -l, --not-lookup-services            Disable service lookups for each device.')
    print('  -g, --not-gps                        Disable GPS integration.')
    print('  -f, --fake-gps                       Provide fake gps position: LAT,LON')
    print('  -m, --mail-user                      Gmail username for alarms (password prompted).')
    print(END)


def getGPS():
    global global_location, threadbreak

    try:
        the_connection = agps3.GPSDSocket()
        the_connection.connect()
        the_connection.watch()
        while not threadbreak:
            try:
                for new_data in the_connection:
                    if new_data:
                        if 'lat' in new_data and 'lon' in new_data:
                            if not global_location and pygame:
                                try:
                                    pygame.mixer.music.load('gps.ogg')
                                    pygame.mixer.music.play()
                                except Exception:
                                    pass
                            global_location = new_data
                        time.sleep(0.5)
                        break
            except Exception:
                time.sleep(0.5)
                pass

    except KeyboardInterrupt:
        print('Exiting received in getGPS() function.')
        threadbreak = True
    except Exception as exc:
        print('Exception getGPS() function:', exc)
        threadbreak = True


def get_address_from_gps(location_gps):
    global debug, address_cache, flag_internet, threadbreak

    if not location_gps:
        return ''

    if debug:
        print('Coordinates:', location_gps)

    if location_gps in address_cache:
        return address_cache[location_gps]

    if not flag_internet:
        return 'Internet option deactivated'

    try:
        coordinates, address = getCoordinates(location_gps)
        if address:
            address_cache[location_gps] = address
        return address
    except Exception as exc:
        if debug:
            print('get_address_from_gps error:', exc)
        threadbreak = True
        return ''


def bluetooth_discovering():
    global debug, verbose, threadbreak, flag_sound, global_location

    try:
        while not threadbreak:
            try:
                if debug:
                    print('Discovering BLE devices...')
                async def get_ble_devices():
                    devices = await bleak.discover()
                    return devices
                devices = asyncio.run(get_ble_devices())
                data = [(d.address, d.name or 'Unknown') for d in devices]

                if data:
                    loc = global_location
                    if verbose:
                        print(f'Found: {len(data)} BLE devices')
                    t = threading.Thread(target=process_devices, args=(data, loc))
                    t.daemon = True
                    t.start()
                else:
                    print('  -')
                    if flag_sound and pygame:
                        try:
                            if global_location:
                                pygame.mixer.music.load('nodevice-withgps.ogg')
                            else:
                                pygame.mixer.music.load('nodevice-withoutgps.ogg')
                            pygame.mixer.music.play()
                        except Exception:
                            pass

            except KeyboardInterrupt:
                print('Exiting received in bluetooth_discovering()')
                threadbreak = True
            except Exception as exc:
                if debug:
                    print('Exception in bluetooth_discovering():', exc)
                time.sleep(1)

        threadbreak = True
        return True

    except KeyboardInterrupt:
        print('Exiting received in bluetooth_discovering()')
        threadbreak = True
    except Exception as exc:
        print('Exception in bluetooth_discovering():', exc)
        threadbreak = True


def process_devices(device_list, loc):
    global debug, verbose, threadbreak, flag_gps, flag_internet, flag_sound, flag_lookup_services, list_devices, queue_devices

    try:
        for bdaddr, name in device_list:
            new_device = bdaddr not in list_devices
            if new_device:
                list_devices[bdaddr] = name
                if debug:
                    print('New device found:', bdaddr, name)

            ftime = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            location_gps = ''
            location_address = ''

            if flag_gps and isinstance(loc, dict):
                location_gps = f"{loc.get('lat')},{loc.get('lon')}"
            elif loc and not flag_gps:
                location_gps = str(loc)

            if location_gps and flag_internet:
                location_address = get_address_from_gps(location_gps)

            device_services = ['BLE']

            info_line = (ftime, bdaddr, name, location_gps, location_address or 'unknown', device_services)
            if len(device_services) > 1:
                print('  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format(*info_line[:6]))
            else:
                print('  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format(ftime, bdaddr, name, location_gps, (location_address or '').split(',')[0], device_services))

            if flag_sound and pygame:
                try:
                    sound_file = 'new.ogg' if new_device else 'old.ogg'
                    pygame.mixer.music.load(sound_file)
                    pygame.mixer.music.play()
                except Exception:
                    pass

            if queue_devices is not None:
                queue_devices.put([ftime, bdaddr, name, location_gps, location_address, device_services])

            if debug:
                print('Data loaded to queue')

    except KeyboardInterrupt:
        print('Exiting process_devices()')
        threadbreak = True
    except Exception as exc:
        print('Exception in process_devices():', exc)
        threadbreak = True


def db_create_database(database_name):
    global debug

    if not os.path.exists(database_name):
        if debug:
            print('Creating database', database_name)
        conn = sqlite3.connect(database_name)
        conn.execute('CREATE TABLE Devices(Id INTEGER PRIMARY KEY AUTOINCREMENT, Mac TEXT UNIQUE, Info TEXT, Vendor TEXT)')
        conn.execute('CREATE TABLE Locations(Id INTEGER PRIMARY KEY AUTOINCREMENT, MacId INTEGER, GPS TEXT, FirstSeen TEXT, LastSeen TEXT, Address TEXT, Name TEXT, UNIQUE(MacId,GPS))')
        conn.execute('CREATE TABLE Notes(Id INTEGER, Note TEXT)')
        conn.execute('CREATE TABLE Alarms(Id INTEGER, Alarm TEXT)')
        conn.commit()
        conn.close()
        if debug:
            print('Database created')


def db_get_database_connection(database_name):
    if not os.path.exists(database_name):
        db_create_database(database_name)
    return sqlite3.connect(database_name)


def db_get_device_id(conn, bdaddr, device_information):
    cur = conn.execute('SELECT Id FROM Devices WHERE Mac = ?', (bdaddr,))
    row = cur.fetchone()
    if row:
        return row[0]
    conn.execute('INSERT OR IGNORE INTO Devices (Mac, Info) VALUES (?,?)', (bdaddr, repr(device_information)))
    conn.commit()
    cur = conn.execute('SELECT Id FROM Devices WHERE Mac = ?', (bdaddr,))
    row = cur.fetchone()
    if row:
        return row[0]
    return None


def db_update_device(conn, device_id, device_information):
    conn.execute('UPDATE Devices SET Info = ? WHERE Id = ?', (repr(device_information), device_id))
    conn.commit()
    return True


def db_add_location(conn, device_id, location_gps, first_seen, location_address, device_name):
    try:
        conn.execute('INSERT OR IGNORE INTO Locations(MacId, GPS, FirstSeen, LastSeen, Address, Name) VALUES (?, ?, ?, ?, ?, ?)',
                     (device_id, location_gps, first_seen, first_seen, location_address, device_name))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def db_update_location(conn, device_id, location_gps, first_seen):
    conn.execute('UPDATE Locations SET LastSeen = ? WHERE MacId = ? AND GPS = ?',
                 (first_seen, device_id, location_gps))
    conn.commit()
    return True


def device_alert(device_id, device_name, database_name, location_gps, location_address, last_seen):
    global flag_internet, mail_username, mail_password

    conn = db_get_database_connection(database_name)
    rows = conn.execute('SELECT Alarm FROM Alarms WHERE Id = ?', (device_id,)).fetchall()
    for (alarm,) in rows:
        if 'Sound' in alarm and pygame:
            try:
                pygame.mixer.music.load('alarm.ogg')
                pygame.mixer.music.play()
            except Exception:
                pass
            break
        if 'Festival' in alarm:
            os.system(f"echo {device_name} | festival --tts")
            break
        if 'Mail' in alarm and flag_internet and mail_username and mail_password:
            try:
                fromaddr = f'{mail_username}@gmail.com'
                toaddrs = [f'{mail_username}@gmail.com']
                msg = f'Device {device_name}\nLocation {location_gps}\nAddress {location_address}\nLast seen {last_seen}'
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(mail_username, mail_password)
                server.sendmail(fromaddr, toaddrs, msg)
                server.quit()
            except Exception as exc:
                if debug:
                    print('Email alert failed', exc)
            break
    conn.close()


def store_device_information(database_name):
    global queue_devices, threadbreak, flag_alarm

    conn = db_get_database_connection(database_name)
    while not threadbreak:
        while not queue_devices.empty():
            temp = queue_devices.get()
            first_seen = temp[0]
            device_bdaddr = temp[1]
            device_name = temp[2]
            location_gps = temp[3]
            location_address = temp[4]
            device_information = temp[5]

            device_id = db_get_device_id(conn, device_bdaddr, device_information)
            if flag_alarm and device_id:
                t = threading.Thread(target=device_alert, args=(device_id, device_name, database_name, location_gps, location_address, first_seen))
                t.daemon = True
                t.start()

            if device_id:
                db_update_device(conn, device_id, device_information)
                if not db_add_location(conn, device_id, location_gps, first_seen, location_address, device_name):
                    db_update_location(conn, device_id, location_gps, first_seen)
        time.sleep(2)


def main():
    global debug, threadbreak, flag_sound, flag_internet, flag_gps, flag_lookup_services, flag_alarm, queue_devices, global_location, mail_username, mail_password

    parser = argparse.ArgumentParser(description='Bluedriving modernized')
    parser.add_argument('-D', '--debug', action='store_true', help='Debug mode on')
    parser.add_argument('-d', '--database-name', default='bluedriving.db')
    parser.add_argument('-w', '--webserver', action='store_true')
    parser.add_argument('-p', '--webserver-port', type=int, default=8000)
    parser.add_argument('-I', '--webserver-ip', default='127.0.0.1')
    parser.add_argument('-s', '--disable-sound', action='store_true')
    parser.add_argument('-i', '--not-internet', action='store_true')
    parser.add_argument('-l', '--not-lookup-services', action='store_true')
    parser.add_argument('-g', '--not-gps', action='store_true')
    parser.add_argument('-f', '--fake-gps', default='')
    parser.add_argument('-m', '--mail-user', default='')
    args = parser.parse_args()

    debug = args.debug
    if args.disable_sound:
        flag_sound = False
    if args.not_internet:
        flag_internet = False
    if args.not_lookup_services:
        flag_lookup_services = False
    if args.not_gps:
        flag_gps = False
        flag_internet = False
    if args.fake_gps:
        global_location = args.fake_gps
        flag_gps = False

    if args.mail_user:
        mail_username = args.mail_user
        mail_password = getpass.getpass('Provide your gmail password: ')

    version()
    queue_devices = queue.Queue()

    if flag_lookup_services:
        print('  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format('Date', 'MAC address', 'Device name', 'Global Position', 'Aproximate address', 'Info'))
    else:
        print('  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}'.format('Date', 'MAC address', 'Device name', 'Global Position', 'Aproximate address'))

    if flag_gps and not args.fake_gps:
        t = threading.Thread(target=getGPS)
        t.daemon = True
        t.start()

    if args.webserver:
        t = threading.Thread(target=createWebServer, args=(args.webserver_port, args.webserver_ip, args.database_name))
        t.daemon = True
        t.start()

    t = threading.Thread(target=bluetooth_discovering)
    t.daemon = True
    t.start()

    t = threading.Thread(target=store_device_information, args=(args.database_name,))
    t.daemon = True
    t.start()

    if flag_sound and pygame:
        try:
            pygame.init()
        except Exception:
            print('pygame could not be initialized, muting sound')
            flag_sound = False

    try:
        while not threadbreak:
            cmd = input().strip().lower()
            if cmd == 'a':
                flag_alarm = not flag_alarm
                print(f"{GRE}Alarms {'activated' if flag_alarm else 'deactivated'}{END}")
            elif cmd == 'd':
                debug = not debug
                print(f"{GRE}Debug {'activated' if debug else 'deactivated'}{END}")
            elif cmd == 's':
                flag_sound = not flag_sound
                print(f"{GRE}Sound {'activated' if flag_sound else 'deactivated'}{END}")
            elif cmd == 'i':
                flag_internet = not flag_internet
                print(f"{GRE}Internet {'activated' if flag_internet else 'deactivated'}{END}")
            elif cmd == 'l':
                flag_lookup_services = not flag_lookup_services
                print(f"{GRE}Lookup services {'activated' if flag_lookup_services else 'deactivated'}{END}")
            elif cmd in ('q', 'quit', 'exit'):
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    threadbreak = True
    print('\n[+] Exiting')


if __name__ == '__main__':
    main()

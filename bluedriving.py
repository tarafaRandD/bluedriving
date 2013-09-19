#!/usr/bin/python
#  Copyright (C) 2009  Veronica Valeros, Juan Manuel Abrigo, Sebastian Garcia
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#
# Author:
# Veronica Valeros vero.valeros@gmail.com
#
# Changelog
#  - Cache the requested coordinates and addresses to save bandwith
#  - Cache the device information to avoid extra queries to the database
#  - Updated README on the github wiki
#
# TODO
# Check this: Fix crashing when multiple threads try to write in the database
# Redesign the whole program. 
#
# KNOWN BUGS
#
# Description
#

# standar imports
import sys
import re
import getopt
import copy
import os
import time
import sqlite3
import bluetooth
import time
#import gps
from gps import *;
import threading
#import getCoordinatesFromAddress
from getCoordinatesFromAddress import getCoordinates
from bluedrivingWebServer import createWebServer
import lightblue
import Queue
import pygame
import getpass
import smtplib

# Global variables
vernum = '0.1'
debug = False
threadbreak = False
global_location = ""
flag_sound = True
flag_internet = True
flag_gps = True
flag_lookup_services = True
flag_alarm = True
list_devices = {}
queue_devices = ""
mail_username = ""
mail_password = ""

address_cache = {}
deviceservices = {}

GRE='\033[92m'
END='\033[0m'
RED='\033[91m'
CYA='\033[96m'

# End global variables

def version():
    """
    This function prints information about this utility
    """
    global RED
    global END

    print RED
    print "   "+ sys.argv[0] + " Version "+ vernum +" @COPYLEFT"
    print "   Authors: Vero Valeros (vero.valeros@gmail.com), Seba Garcia (eldraco@gmail.com)"
    print "   Contributors: nanojaus"
    print "   Bluedriving is a bluetooth wardriving utility."
    print 
    print END
 
def usage():
    """
    This function prints the posible options of this program.
    """
    global RED
    global END
    
    print RED
    print
    print "   "+ sys.argv[0] + " Version "+ vernum +" @COPYLEFT"
    print "   Authors: Vero Valeros (vero.valeros@gmail.com), Seba Garcia (eldraco@gmail.com)"
    print "   Contributors: nanojaus"
    print "   Bluedriving is a bluetooth wardriving utility."
    print 
    print "\n   Usage: %s <options>" % sys.argv[0]
    print "   Options:"
    print "  \t-h, --help                           Show this help message and exit."
    print "  \t-D, --debug                          Debug mode ON. Prints debug information on the screen."
    print "  \t-d, --database-name                  Name of the database to store the data."
    print "  \t-w, --webserver                      It runs a local webserver to visualize and interact with "
    print "                                             the collected information. Defaults to port 8000."
    print "  \t-p, --webserver-port                 Port where the webserver is going to listen. Defaults to 8000."
    print "  \t-I, --webserver-ip                   IP address where the webserver binds. Defaults to 127.0.0.1."
    print "  \t-s, --not-sound                      Do not play the beautiful discovering sounds. Are you sure you wanna miss this?"
    print "  \t-i, --not-internet                   If you dont have internet use this option to save time while getting "
    print "                                             coordinates and addresses from the web."
    print "  \t-l, --not-lookup-services            Use this option to not lookup for services for each device. "
    print "                                             This option makes the discovering a little faster."
    print "  \t-g, --not-gps                        Use this option when you want to run the bluedriving withouth a gpsd connection."
    print "  \t-f, --fake-gps                       Use a fake gps position. Useful when you don't have a gps but know your location from google maps."
    print "                                             Example: -f '38.897388,-77.036543'"
    print "  \t-m, --mail-user                      Gmail user to send mails from and to when a mail alarm is found. The password is entered later."
    print "                                             Alarms can be set up only from the web interface at the moment."
    print 
    print END
 

def getGPS():
    """
    """
    global debug
    global global_location
    global threadbreak

    counter = 0
    gps_session = ""
    gps_flag = False
    try:
        gps_session = gps(mode=WATCH_ENABLE)
        
        while not threadbreak:
            if counter > 10:
                global_location = ""
            try:
                location = gps_session.next()
                location['lon']
                location['lat']
                if global_location == "":
                    pygame.mixer.music.load('gps.ogg')
                    pygame.mixer.music.play()
                global_location = location
                counter = 0
                time.sleep(0.5)
            except:
                counter = counter + 1
                pass

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception getGPS()'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

""""
#FUNCTION DEPRECATED
def get_coordinates_from_gps():
    global debug
    global global_location
    global threadbreak

    counter = 0
    gps_session = ""
    gps_flag = False
    try:
        while True:
            if gps_session:
                while True:
                    if counter < 10:
                        try:
                            gpsdata = gps_session.next()
                            global_location =  str(gpsdata['lat'])+','+str(gpsdata['lon'])
                            if global_location and not gps_flag:
                                pygame.mixer.music.load('gps.ogg')
                                pygame.mixer.music.play()
                                gps_flag = True
                        except Exception, e:
                            try:
                                gpsdata = gps_session.next()
                                global_location =  str(gpsdata['lat'])+','+str(gpsdata['lon'])
                            except Exception,e:
                                #print "misc. exception (runtime error from user callback?):", e
                                global_location = False
                                counter = counter + 1
                    else:
                        try:
                            try:
                                gps_session.close()
                            except: 
                                pass
                            gps_session = gps(mode=WATCH_ENABLE)
                            gps_session.sock.settimeout(1)
                            counter = 0
                            gps_flag = False
                        except:
                            pass
            else:
                try:
                    gps_session = gps(mode=WATCH_ENABLE)
                    gps_session.sock.settimeout(1)
                except:
                    time.sleep(10)
                    pass

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in get_coordinates_from_gps'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)
"""
def get_address_from_gps(location_gps):
    global debug
    global verbose
    global address_cache
    global flag_internet
    global threadbreak
    
    coordinates = ""
    address = ""
    try:
        if location_gps:
            if debug:
                print 'Coordinates: {}'.format(location_gps)
            try:
                # If the location is already stored, we get it.
                address = address_cache[location_gps]
            except:
                if flag_internet:
                    print location_gps
                    #[coordinates,address] = getCoordinatesFromAddress.getCoordinates(location_gps)
                    [coordinates,address] = getCoordinates(location_gps)
                    address = address.encode('utf-8')
                    if debug:
                        print 'Coordinates: {} Address: {}'.format(coordinates,address)
                    
                    address_cache[location_gps] = address
                else:
                    address = "Internet deactivated"
        return address

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in get_address_from_gps()'
        print 'Received coordinates: {}'.format(location_gps)
        print 'Retrieved coordinates: {}'.format(coordinates)
        print 'Retrieved Address: {}'.format(address)
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

# Discovering function
def bluetooth_discovering():
    """
    This function performs a continue discovering of the nearby bluetooth devices and then sends the list of devices to the lookupdevices function.
    """
    global debug
    global verbose
    global threadbreak
    global flag_sound
    global global_location

    try:
        if debug:
            print '[+] In bluetooth_discovering() function'
            
        while not threadbreak:
            data = ""

            try:
                try:
                    if debug:
                        print 'Discovering devices...'
                    # Discovering devices
                    data = bluetooth.bluez.discover_devices(duration=3,lookup_names=True)
                    #data = bluetooth.discover_devices(duration=3,lookup_names=True)
                    if debug:
                        print data
                    
                    if data:
                        # We start a new thread that process the information retrieved 
                        loc = global_location
                        process_device_information_thread = threading.Thread(None,target = process_devices,args=(data,loc))
                        process_device_information_thread.setDaemon(True)
                        process_device_information_thread.start()
                    else: 
                        # No devices
                        print '  -'
                        if flag_sound:
                            if global_location:
                                # If we have gps, play a sound
                                pygame.mixer.music.load('nodevice-withgps.ogg')
                                pygame.mixer.music.play()
                            else:
                                print 'No global location on discover_devices'
                                print global_location
                                # If we do not have gps, play a sound
                                pygame.mixer.music.load('nodevice-withoutgps.ogg')
                                pygame.mixer.music.play()
                except:
                    if debug:
                        print 'Exception in bluetooth.discover_devices(duration=3,lookup_names=True) function.'
                    continue
            except KeyboardInterrupt:
                print 'Exiting. It may take a few seconds.'
                threadbreak = True
            except Exception as inst:
                print 'Exception in while of bluetooth_discovering() function'
                threadbreak = True
                print 'Ending threads, exiting when finished'
                print type(inst) # the exception instance
                print inst.args # arguments stored in .args
                print inst # _str_ allows args to printed directly
                x, y = inst # _getitem_ allows args to be unpacked directly
                print 'x =', x
                print 'y =', y
                sys.exit(1)

        threadbreak = True
        return True

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in bluetooth_discovering() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def process_devices(device_list,loc):
    global debug
    global verbose
    global threadbreak
    global flag_gps
    global flag_internet
    global flag_sound
    #global global_location
    global list_devices
    global queue_devices

    location_gps = "NO GPS DATA"
    location_address = "NO ADDRESS RETRIEVED"
    ftime = ""
    flag_new_device = False
    try:
        if device_list:
            for d in device_list:
                flag_new_device = False
                try:
                    list_devices[d[0]]
                    flag_new_device = False
                except:
                    list_devices[d[0]]=d[1]
                    flag_new_device = True
                    if debug:
                        print 'New device found'
                #ftime = time.asctime()
                ftime = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime())

                # We get location's related information
                if flag_gps:
                    #location_gps = global_location
                    if location_gps:
                        try:
                            location_gps = str(loc.get('lat'))+","+str(loc.get('lon'))
                            if debug:
                                print "location_gps: {}".format(location_gps)
                            if flag_internet:
                                location_address = get_address_from_gps(location_gps)
                        except:
                            location_address=""

                # We try to lookup more information about the device
                device_services = []
                if flag_lookup_services:
                    services_data = lightblue.findservices(d[0])
                    if services_data:
                        for i in services_data:
                            device_services.append(i[2])

                if len(device_services) > 1:
                    print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format(ftime,d[0],d[1],location_gps,location_address.split(',')[0],device_services[0])
                    for service in device_services[1:]:
                        print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format('','','','','',service)
                        #print '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t{:<30}'.format(service)
                else:
                    print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format(ftime,d[0],d[1],location_gps,location_address.split(',')[0],device_services)
                    
                if flag_sound:
                    if flag_new_device:
                        pygame.mixer.music.load('new.ogg')
                        pygame.mixer.music.play()
                    else:
                        pygame.mixer.music.load('old.ogg')
                        pygame.mixer.music.play()

                queue_devices.put([ftime,d[0],d[1],location_gps,location_address,device_services])

                if debug:
                    print 'Data loaded to queue'
                #time.sleep(0.5)
        # no devices?
        
    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in process_devices() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_create_database(database_name):
    global debug
    global verbose
    global threadbreak

    try:
        # We check if the database exists
        if not os.path.exists(database_name):
            if debug:
                print 'Creating database'
            # Creating database
            connection = sqlite3.connect(database_name)
            # Creating tables
            connection.execute("CREATE TABLE Devices(Id INTEGER PRIMARY KEY AUTOINCREMENT, Mac TEXT , Info TEXT)")
            connection.execute("CREATE TABLE Locations(Id INTEGER PRIMARY KEY AUTOINCREMENT, MacId INTEGER, GPS TEXT, FirstSeen TEXT, LastSeen TEXT, Address TEXT, Name TEXT, UNIQUE(MacId,GPS))")
            connection.execute("CREATE TABLE Notes(Id INTEGER, Note TEXT)")
            connection.execute("CREATE TABLE Alarms(Id INTEGER, Alarm TEXT)")
            if debug:
                print 'Database created'
        else:
            if debug:
                print 'Database already exist'

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_create_database(database_name) function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_get_database_connection(database_name):
    """
    """
    global debug
    global verbose
    global threadbreak

    try:
        if not os.path.exists(database_name):
            db_create_database(database_name)
        connection = sqlite3.connect(database_name)
        if debug:
            print 'Database connection retrieved'
        return connection

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in get_database_connection(database_name) function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_get_device_id(connection,bdaddr,device_information):
    """
    Receives a device address and returns a device id from the database. If device does not exists in database, it adds it.
    """
    global debug
    global verbose
    global threadbreak

    try:
        mac_id = ""
        try:
            mac_id = connection.execute("SELECT Id FROM Devices WHERE Mac = \""+bdaddr+"\" limit 1")
            mac_id = mac_id.fetchall()

            if not mac_id:
                db_add_device(connection,bdaddr,device_information)
                mac_id = connection.execute("SELECT Id FROM Devices WHERE Mac = \""+bdaddr+"\" limit 1")
                mac_id = mac_id.fetchall()

            if debug:
                print 'Macid in db_get_device_id() function: {}'.format(mac_id)
            return mac_id[0][0]
        except:
            print 'Device Id could not be retrieved. BDADDR: {}'.format(bdaddr)
            return False

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_get_device_id() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_add_device(connection,bdaddr,device_information):
    """
    """
    global debug
    global verbose
    global threadbreak

    try:
        try:
            connection.execute("INSERT OR IGNORE INTO Devices (Mac,Info) VALUES (?,?)",(bdaddr,repr(device_information)))
            connection.commit()
            if debug:
                print 'New device added'
            return True
        except:
            if debug:
                print 'Device already exists'
            return False
        
    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_add_device() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_update_device(connection,device_id,device_information):
    """
    """
    global debug
    global verbose
    global threadbreak

    try:
        try:
            connection.execute("UPDATE Devices SET Info=? WHERE Id=?", (repr(device_information), repr(device_id)))
            connection.commit()
            if debug:
                print 'Device information updated'
            return True
        except:
            if debug:
                print 'Device information not updated'
                print 'Device ID: {}'.format(device_id)
                print 'Device Information: {}'.format(device_information)
            return False

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_update_device() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_add_location(connection,device_id,location_gps,first_seen,location_address,device_name):
    """
    """
    global debug
    global verbose
    global threadbreak

    try:
        try:
            connection.execute("INSERT INTO Locations(MacId, GPS, FirstSeen, LastSeen, Address, Name) VALUES (?, ?, ?, ?, ?, ?)",(int(device_id), repr(location_gps),repr(first_seen),repr(first_seen),repr(location_address),repr(device_name.replace("'","''"))))
            connection.commit()
            if debug:
                print 'Location added'
        except:
            if debug:
                print 'Location not added'
                print 'Device ID: {}'.format(device_id)
                print 'Device Name: {}'.format(device_name)
                print 'GPS Location: {}'.format(location_gps)
                print 'First seen: {}'.format(first_seen)
                print 'Last seen: {}'.format(first_seen)
            return False

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_add_location() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def db_update_location(connection,device_id,location_gps,first_seen):
    """
    """
    global debug
    global verbose
    global threadbreak

    try:
        try:
            connection.execute("UPDATE Locations SET LastSeen=? WHERE MacId=? AND GPS=?",(repr(first_seen), int(device_id), repr(location_gps)))
            connection.commit()
            if debug:
                print 'Location updated'
                print 'Device ID: {}'.format(device_id)
                print 'GPS Location: {}'.format(location_gps)
                print 'Last seen: {}'.format(first_seen)
        except:
            if debug:
                print 'Location not updated'
                print 'Device ID: {}'.format(device_id)
                print 'GPS Location: {}'.format(location_gps)
                print 'Last seen: {}'.format(first_seen)
            return False

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in db_update_location() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def device_alert(device_id,device_name,database_name,location_gps,location_address,last_seen):
    global debug
    global verbose
    global mail_username
    global mail_password
    global flag_internet

    try:
        connection = db_get_database_connection(database_name)
        result = connection.execute('select * from alarms where id = ?',(device_id,))
        data = result.fetchall()
        
        for alarm in data:
            if 'Sound' in alarm:
                pygame.mixer.music.load('alarm.ogg')
                pygame.mixer.music.play()
                break
            if 'Festival' in alarm:
                os.system("echo "+device_name+"|festival --tts")
                break
            if 'Mail' in alarm:
                if flag_internet:
                    fromaddr = mail_username+'@gmail.com'
                    toaddrs = mail_username+'@gmail.com'
                    msg = 'Device '+device_name+'\nLocation '+location_gps+'\nAddress '+location_address+'\nLast seen '+last_seen
                    server = smtplib.SMTP('smtp.gmail.com:587')
                    server.starttls()
                    server.login(mail_username,mail_password)
                    server.sendmail(fromaddr, toaddrs, msg)
                    server.quit()
                break
        connection.commit()
        connection.close()

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in device_alert() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

def store_device_information(database_name):
    global debug
    global verbose
    global queue_devices
    global threadbreak
    global flag_alarm

    connection = ""
    try:
        # We create a database connection
        connection = db_get_database_connection(database_name)
        while not threadbreak:
            while not queue_devices.empty():
                # We clear the variables to use
                device_id = ""
                device_bdaddr = ""
                device_name = ""
                device_information = ""
                location_gps = ""
                location_address = ""
                first_seen = ""
                last_seen = ""

                if not queue_devices.empty():
                    # We extract the device from the queue
                    temp = queue_devices.get()

                    # We load the information

                    # From the text to time structure
                                        #temp2 = time.strptime(temp[0],"%a %b %d %H:%M:%S %Y")

                    # From time structure to supported text.
                    #temp_date = time.strftime("%Y-%m-%d %H:%M:%S",temp2)

                    last_seen = temp[0]
                    first_seen = temp[0]
                    device_bdaddr = temp[1]
                    device_name = temp[2]
                    location_gps = temp[3]
                    location_address = temp[4]
                    device_information = temp[5]
                    
                    device_id = db_get_device_id(connection,device_bdaddr,device_information)
                    
                    if flag_alarm: 
                        # Here we start the discovering devices threads
                        device_alert_thread = threading.Thread(None,target = device_alert, args=(device_id,device_name,database_name,location_gps,location_address,last_seen))
                        device_alert_thread.setDaemon(True)
                        device_alert_thread.start()

                    if device_id:
                        # If we have a device information, then we update the information for the device
                        result = db_update_device(connection,device_id,device_information)
                        if not result:
                            print 'Device information could not be updated'
                        # We try to store a new location
                        result = db_add_location(connection,device_id,location_gps,first_seen,location_address,device_name)

                        # If the location has not changed, result will be False. We update the last seen field into locations.
                        if not result:
                            result = db_update_location(connection,device_id,location_gps,last_seen)

                    #print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format(temp[0],temp[1],temp[2],temp[3],temp[4],temp[5])
            time.sleep(2)

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
    except Exception as inst:
        print 'Exception in store_device_information() function'
        threadbreak = True
        print 'Ending threads, exiting when finished'
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)

##########
# MAIN
##########
def main():
    global debug
    global threadbreak
    global flag_sound
    global flag_internet
    global flag_gps
    global flag_lookup_services
    global flag_alarm
    global queue_devices
    global GRE
    global CYA
    global END
    global global_location
    global mail_username
    global mail_password

    database_name = "bluedriving.db"
    flag_run_webserver = False
    fake_gps = ''
    mail_username = ""
    mail_password = ""
    webserver_port = 8000
    webserver_ip = "127.0.0.1"

    try:
        # By default we crawl a max of 5000 distinct URLs
        opts, args = getopt.getopt(sys.argv[1:], "hDd:wsilgf:m:I:p:", ["help","debug","database-name=","webserver","disable-sound","not-internet","not-lookup-services","not-gps","fake-gps=","mail-user=","webserver-port=","webserver-ip="])
    except: 
        usage()
        exit(-1)

    for opt, arg in opts:
        if opt in ("-h", "--help"): usage(); sys.exit()
        if opt in ("-D", "--debug"): debug = True
        if opt in ("-d", "--database-name"): database_name = arg
        if opt in ("-w", "--webserver"): flag_run_webserver = True
        if opt in ("-s", "--disable-sound"): flag_sound = False
        if opt in ("-i", "--not-internet"): flag_internet = False
        if opt in ("-l", "--not-lookup-services"): flag_lookup_services = False
        if opt in ("-g", "--not-gps"): flag_gps = False; flag_internet = False
        if opt in ("-f", "--fake-gps"): fake_gps = arg
        if opt in ("-m", "--mail-user"): mail_username = arg; print 'Provide your gmail password for given user: ',; mail_password = getpass.getpass()
        if opt in ("-p", "--webserver-port"): webserver_port = int(arg)
        if opt in ("-I", "--webserver-ip"): webserver_ip = str(arg)
    try:
        
        version()
        queue_devices = Queue.Queue()
        startTime = time.time()

        # We print the header for printing results on console
        print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format("Date","MAC address","Device name","Global Position","Aproximate address","Info")
        print '  {:<24}  {:<17}  {:<30}  {:<27}  {:<30}  {:<20}'.format("----","-----------","-----------","---------------","------------------","----")

        # Here we start the thread to get gps location        
        if flag_gps and not fake_gps:
            #gps_thread = threading.Thread(None,target=get_coordinates_from_gps)
            gps_thread = threading.Thread(None,target=getGPS)
            gps_thread.setDaemon(True)
            gps_thread.start()
        elif fake_gps:
            # Verify fake_gps
            if debug:
                print 'Using the fake gps address: {0}'.format(fake_gps)
            global_location = fake_gps
        
        # Here we start the web server
        if flag_run_webserver:
            webserver_thread = threading.Thread(None,createWebServer,"web_server",args=(webserver_port,webserver_ip))
            webserver_thread.setDaemon(True)
            webserver_thread.start()

        # Here we start the discovering devices threads
        bluetooth_discovering_thread = threading.Thread(None,target = bluetooth_discovering)
        bluetooth_discovering_thread.setDaemon(True)
        bluetooth_discovering_thread.start()

        # Here we start the thread that will continuosly store data to the database
        store_device_information_thread = threading.Thread(None,target = store_device_information,args=(database_name,))
        store_device_information_thread.setDaemon(True)
        store_device_information_thread.start()

        # Initializating sound
        if flag_sound:
            pygame.init()

        # This options are for live-options interaction
        k = ""
        while True:
            k = raw_input()
            if k == 'a' or k == 'A':
                if flag_alarm: 
                    flag_alarm = False
                    print GRE+'Alarms desactivated'+END
                else:
                    flag_alarm = True
                    print GRE+'Alarms activated'+END

            if k == 'd' or k == 'D':
                if debug:
                    debug = False
                    print GRE+'Debug mode desactivated'+END
                else:
                    debug = True
                    print GRE+'Debug mode activated'+END
    
            if k == 's':
                if flag_sound == True:
                    flag_sound = False
                    print GRE+'Sound desactivated'+END
                else:
                    pygame.init()
                    flag_sound = True
                    print GRE+'Sound activated'+END
            if k == 'i':
                if flag_internet == True:
                    flag_internet = False
                    print GRE+'Internet desactivated'+END
                else:
                    flag_internet = True
                    print GRE+'Internet activated'+END
            if k == 'l':
                if flag_lookup_services == True:
                    flag_lookup_services = False
                    print GRE+'Look up services desactivated'+END
                else:
                    flag_lookup_services = True
                    print GRE+'Look up services activated'+END
            if k == 'g':
                if flag_gps == True:
                    flag_gps = False
                    flag_internet = False
                    print GRE+'GPS desactivated'+END
                    print GRE+'Internet desactivated'+END
                else:
                    flag_gps = True
                    print GRE+'GPS activated'+END

            if k == 'Q' or k == 'q':
                break

        threadbreak = True
        print '\n[+] Exiting'

    except KeyboardInterrupt:
        print 'Exiting. It may take a few seconds.'
        threadbreak = True
        time.sleep(1)
        for thread in threading.enumerate():
            try:
                thread.stop_now()
            except:
                pass
    except Exception as inst:
        print 'Error in main() function'
        print 'Ending threads, exiting when finished'
        threadbreak = True
        print type(inst) # the exception instance
        print inst.args # arguments stored in .args
        print inst # _str_ allows args to printed directly
        x, y = inst # _getitem_ allows args to be unpacked directly
        print 'x =', x
        print 'y =', y
        sys.exit(1)


if __name__ == '__main__':
        main()


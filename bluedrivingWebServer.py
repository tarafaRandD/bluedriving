#!/usr/bin/env python3
"""Web server for bluedriving (Python 3 modernized)."""

import argparse
import json
import os
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

__version__ = '0.1.2'

database = 'bluedriving.db'
verbose = False
debug = False


def version():
    print('+----------------------------------------------------------------------+')
    print(f'| bluedrivingWebServer.py Version {__version__}')
    print('| This program is free software; you can redistribute it and/or modify |')
    print('| it under the terms of the GNU General Public License as published by |')
    print('| the Free Software Foundation; either version 2 of the License, or    |')
    print('| (at your option) any later version.                                  |')
    print('| Author: Sebastian Garcia, eldraco@gmail.com                          |')
    print('+----------------------------------------------------------------------+')
    print()


def usage():
    print('+----------------------------------------------------------------------+')
    print('| bluedrivingWebServer.py Version ' + __version__ + ' |')
    print('+----------------------------------------------------------------------+')
    print('\nusage: %s <options>' % sys.argv[0])
    print('options:')
    print('  -h, --help           Show this help message and exit')
    print('  -V, --version        Show the version')
    print('  -v, --verbose        Be verbose')
    print('  -D, --debug          Debug')
    print('  -p, --webserver-port Web server tcp port to use. Defaults to 8000')
    print('  -I, --webserver-ip   Web server ip to bind to. Defaults to 127.0.0.1')
    print('  -d, --database       If you wish to analyze another database, just give the file name here.')


def get_unread_registers():
    global database, debug
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    records = []
    for row in cursor.execute('SELECT * FROM Locations ORDER BY LastSeen DESC LIMIT 9000'):
        device = cursor.execute('SELECT Mac, Info FROM Devices WHERE Id = ?', (row['MacId'],)).fetchone()
        if not device:
            continue
        records.append({
            'gps': row['GPS'],
            'firstseen': row['FirstSeen'],
            'lastseen': row['LastSeen'],
            'address': row['Address'],
            'name': row['Name'],
            'mac': device['Mac'],
            'info': device['Info'],
        })

    conn.close()
    return json.dumps({'UnReadData': records})


def get_info_from_mac(temp_mac):
    global database, debug
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    row = cursor.execute('SELECT Info FROM Devices WHERE Mac = ?', (temp_mac,)).fetchone()
    conn.close()
    if row:
        return json.dumps({'Info': row[0]})
    return json.dumps({'Info': ''})


def get_all_devices_positions(amount):
    global database, debug
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    row = cursor.execute('SELECT DISTINCT MacId FROM Locations ORDER BY Id DESC LIMIT ?', (amount,)).fetchall()
    result = []
    for (macid,) in row:
        device = cursor.execute('SELECT Mac FROM Devices WHERE Id = ?', (macid,)).fetchone()
        if not device:
            continue
        mac = device[0]
        positions = []
        for loc in cursor.execute('SELECT GPS, Name, FirstSeen, LastSeen FROM Locations WHERE MacId = ? ORDER BY Id ASC', (macid,)):
            if loc[0] and 'not available' not in loc[0].lower():
                positions.append(loc[0])
            name = loc[1]
            firstseen = loc[2]
            lastseen = loc[3]

        result.append({'Mac': mac, 'Data': {'Name': name, 'FirstSeen': firstseen, 'LastSeen': lastseen, 'Pos': positions}})

    conn.close()
    return json.dumps(result)


def get_n_positions(mac):
    global database, debug
    conn = sqlite3.connect(database)
    cursor = conn.cursor()

    row = cursor.execute('SELECT Id FROM Devices WHERE Mac LIKE ? LIMIT 1', ('%' + mac + '%',)).fetchone()
    if not row:
        return json.dumps({})
    device_id = row[0]

    row = cursor.execute('SELECT Name FROM Locations WHERE MacId = ? LIMIT 1', (device_id,)).fetchone()
    name = row[0] if row else ''

    pos = [r[2] for r in cursor.execute('SELECT * FROM Locations WHERE MacId = ? AND GPS IS NOT NULL', (device_id,)).fetchall() if r[2] and r[2].strip()]

    conn.close()

    return json.dumps({'Name': name, 'Mac': mac, 'Pos': pos})


def note_to(operation, mac, note):
    global database, debug
    mac = mac.replace('+', ' ').strip()
    note = note.replace('+', ' ').strip()

    if len(mac.split(':')) != 6 or len(mac) != 17:
        return ''
    if len(note) > 253:
        return ''

    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    dev = cursor.execute('SELECT Id FROM Devices WHERE Mac LIKE ? LIMIT 1', ('%' + mac + '%',)).fetchone()
    if not dev:
        conn.close()
        return ''
    device_id = dev[0]

    if operation == 'add':
        cursor.execute('INSERT INTO Notes (Id, Note) VALUES (?,?)', (device_id, note))
        conn.commit()
        conn.close()
        return json.dumps({'Result': 'Added'})
    elif operation == 'del':
        cursor.execute('DELETE FROM Notes WHERE Id = ? AND Note = ?', (device_id, note))
        conn.commit()
        conn.close()
        return json.dumps({'Result': 'Deleted'})
    elif operation == 'get':
        notes = [r[0] for r in cursor.execute('SELECT Note FROM Notes WHERE Id = ?', (device_id,)).fetchall()]
        conn.close()
        return json.dumps({'Notes': notes})
    else:
        conn.close()
        return ''


def alarm_to(operation, mac, alarm_type):
    global database, debug
    conn = sqlite3.connect(database)
    cursor = conn.cursor()
    dev = cursor.execute('SELECT Id FROM Devices WHERE Mac LIKE ? LIMIT 1', ('%' + mac + '%',)).fetchone()
    if not dev:
        conn.close()
        return ''
    device_id = dev[0]

    if operation == 'add':
        cursor.execute('INSERT INTO Alarms (Id, Alarm) VALUES (?,?)', (device_id, alarm_type))
        conn.commit()
        conn.close()
        return json.dumps({'Result': 'Added'})
    elif operation == 'del':
        cursor.execute('DELETE FROM Alarms WHERE Id = ? AND Alarm = ?', (device_id, alarm_type))
        conn.commit()
        conn.close()
        return json.dumps({'Result': 'Deleted'})
    elif operation == 'get':
        alarms = [r[0] for r in cursor.execute('SELECT Alarm FROM Alarms WHERE Id = ?', (device_id,)).fetchall()]
        conn.close()
        return json.dumps({'Alarms': alarms})
    conn.close()
    return ''


class MyHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def _send_json(self, payload):
        data = payload.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        global debug
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        try:
            if path == '/data':
                self._send_json(get_unread_registers())
                return
            if path == '/addnote':
                mac = params.get('mac', [''])[0]
                note = params.get('note', [''])[0]
                self._send_json(note_to('add', mac, note))
                return
            if path == '/delnote':
                mac = params.get('mac', [''])[0]
                note = params.get('note', [''])[0]
                self._send_json(note_to('del', mac, note))
                return
            if path == '/getnote':
                mac = params.get('mac', [''])[0]
                self._send_json(note_to('get', mac, ''))
                return
            if path == '/getalarm':
                mac = params.get('mac', [''])[0]
                self._send_json(alarm_to('get', mac, ''))
                return
            if path == '/addalarm':
                mac = params.get('mac', [''])[0]
                alarm = params.get('type', [''])[0]
                self._send_json(alarm_to('add', mac, alarm))
                return
            if path == '/delalarm':
                mac = params.get('mac', [''])[0]
                alarm = params.get('type', [''])[0]
                self._send_json(alarm_to('del', mac, alarm))
                return
            if path == '/info':
                mac = params.get('mac', [''])[0]
                self._send_json(get_info_from_mac(mac))
                return
            if path == '/map':
                info = params.get('info', [''])[0]
                if len(info.split(':')) == 6:
                    self._send_json(get_n_positions(info))
                else:
                    try:
                        n = int(info)
                    except Exception:
                        n = 0
                    self._send_json(get_all_devices_positions(n))
                return
            if path == '/':
                content = open('index.html', 'rb').read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=UTF-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

            filepath = os.path.join(os.getcwd(), path.lstrip('/'))
            if os.path.isfile(filepath):
                _, ext = os.path.splitext(filepath)
                with open(filepath, 'rb') as f:
                    content = f.read()
                ctype = 'application/octet-stream'
                if ext == '.css':
                    ctype = 'text/css'
                elif ext == '.js':
                    ctype = 'application/javascript'
                elif ext in ('.html', '.htm'):
                    ctype = 'text/html; charset=UTF-8'
                elif ext == '.png':
                    ctype = 'image/png'
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

            self.send_error(404, f'File Not Found: {self.path}')

        except Exception as exc:
            if debug:
                print('Error processing request:', exc)
            self.send_error(500, 'Internal server error')


def createWebServer(port, ip_address, current_database):
    global database
    database = current_database
    server_address = (ip_address, port)
    httpd = HTTPServer(server_address, MyHandler)
    if debug:
        print('Serving HTTP on', ip_address, 'port', port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def main():
    global debug, verbose, database
    parser = argparse.ArgumentParser(description='Bluedriving web server')
    parser.add_argument('-V', '--version', action='store_true')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-D', '--debug', action='store_true')
    parser.add_argument('-p', '--webserver-port', type=int, default=8000)
    parser.add_argument('-I', '--webserver-ip', default='127.0.0.1')
    parser.add_argument('-d', '--database', default='bluedriving.db')
    args = parser.parse_args()
    if args.version:
        version()
        return
    debug = args.debug
    verbose = args.verbose
    database = args.database
    createWebServer(args.webserver_port, args.webserver_ip, database)


if __name__ == '__main__':
    main()

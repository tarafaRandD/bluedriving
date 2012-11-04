#! /usr/bin/env python
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
# Sebastian Garcia eldraco@gmail.com
#
# Changelog

#
# TODO

#
# KNOWN BUGS

#
# Description
# Web server for the bludriving.py
#
#


# Standard imports
import getopt
import sys
import BaseHTTPServer
from os import curdir, sep
import simplejson as json
import sqlite3
import copy

####################
# Global Variables

# Debug
debug=0
vernum="0.1"
#location_id = 0
####################



# Print version information and exit
def version():
  print "+----------------------------------------------------------------------+"
  print "| bludrivingWebServer.py Version "+ vernum +"                                      |"
  print "| This program is free software; you can redistribute it and/or modify |"
  print "| it under the terms of the GNU General Public License as published by |"
  print "| the Free Software Foundation; either version 2 of the License, or    |"
  print "| (at your option) any later version.                                  |"
  print "|                                                                      |"
  print "| Author: Sebastian Garcia, eldraco@gmail.com                          |"
  print "| Mateslab Hackspace, www.mateslab.com.ar                              |"
  print "+----------------------------------------------------------------------+"
  print


# Print help information and exit:
def usage():
  print "+----------------------------------------------------------------------+"
  print "| bludrivingWebServer.py Version "+ vernum +"                                      |"
  print "| This program is free software; you can redistribute it and/or modify |"
  print "| it under the terms of the GNU General Public License as published by |"
  print "| the Free Software Foundation; either version 2 of the License, or    |"
  print "| (at your option) any later version.                                  |"
  print "|                                                                      |"
  print "| Author: Sebastian Garcia, eldraco@gmail.com                          |"
  print "| Mateslab Hackspace, www.mateslab.com.ar                              |"
  print "+----------------------------------------------------------------------+"
  print "\nusage: %s <options>" % sys.argv[0]
  print "options:"
  print "  -h, --help         	Show this help message and exit"
  print "  -V, --version        Show the version"
  print "  -v, --verbose        Be verbose"
  print "  -D, --debug        Debug"
  print "  -p, --port        Web server tcp port to use"


def createWebServer(port):
	""" Crate a web server """

	global debug
	# By default bind to localhost
	server_address = ('127.0.0.1', port)

	# Create a webserver
	try:
		httpd = BaseHTTPServer.HTTPServer(server_address, MyHandler)
		# Get the socket
		sa = httpd.socket.getsockname()

		if debug:
			print "Serving HTTP on", sa[0], "port", sa[1], "..."

		# Run forever
		httpd.serve_forever()
	except KeyboardInterrupt:
		print ' Received, shutting down the server.'
		httpd.socket.close()


def get_unread_registers():
	""" Get unread registers from the database since the last read and return a json with all the data"""
	try:

		#global location_id
		global debug

		conn = sqlite3.connect('bluedriving.db')
		cursor = conn.cursor()

		# Encoder
		je = json.JSONEncoder()

		top = {}
		array = []

		top['UnReadData'] = array

		#location_id_tuple = (location_id,)

		# First select all the locations
		# This can be VERY HEAVY with a huge database...
		for row in cursor.execute('SELECT * FROM Locations order by lastseen DESC limit 100'):

			#if debug:
				#print ' >> Read locations {0}'.format(row)
			dev_id = (row[1],)

			# Update location id

			newcursor = conn.cursor()

			# add the limit!
			for newrow in newcursor.execute('SELECT * FROM Devices WHERE Id = ?',dev_id):
				if debug:
					print '  >> New row:{0}'.format(newrow)
				dict = {}
				# ID
				# GPS
				dict['gps'] = row[2]
				# first seen
				dict['firstseen'] = row[3]
				# last seen
				dict['lastseen'] = row[4]
				# address
				dict['address'] = row[5]
				# name
				dict['name'] = row[6]
				# MAC
				dict['mac'] = newrow[1]
				# Name
				dict['info'] = newrow[2]
			
				array.append(dict)

				""" This should go in the bluedriving.py 
				# Find if we have any alarm for this mac...
				if debug:
					print 'Finding alarms for mac: {0}'.format(dict['mac'])

					# First get the id of the mac
					askmac = ('%'+dict['mac']+'%',)
					cursor2 = conn.cursor()
					row2 = cursor2.execute("SELECT Id FROM devices WHERE Mac like ? limit 0,1",askmac)

					# Check the results, Does this mac exists?
					res = row2.fetchall()
					if len(res) != 0:
						(id,) = res[0]
					else:
						if debug:
							print ' >> This mac does not exist: {0}'.format(dict['mac'])
						return ''

					cursor3 = conn.cursor()
					for row3 in cursor3.execute('SELECT Alarm FROM Alarms where id like ?',(id,)):
						if debug:
							print ' > Found alarm: {0} for mac: {1}'.format(row3, dict['mac'])
				"""

		response = je.encode(top)
		return response

	except Exception as inst:
		if debug:
			print '\tError on get_unread_registers()'
		print type(inst)     # the exception instance
		print inst.args      # arguments stored in .args
		print inst           # __str__ allows args to printed directly
		exit(-1)



def get_info_from_mac(temp_mac):
	""" Get info from one mac """
	global debug

	try:
		conn = sqlite3.connect('bluedriving.db')
		cursor = conn.cursor()
		mac = (temp_mac,)

		# Encoder
		je = json.JSONEncoder()

		top = {}
		info = []

		for row in cursor.execute('SELECT Info FROM Devices WHERE Mac == ?',mac):
			(info,) = row
			if debug:
				print ' >> Info retrived: {0}'.format(info)

		top['Info'] = info
		return je.encode(top)



	except Exception as inst:
		if debug:
			print '\tError on get_info_from_mac()'
		print type(inst)     # the exception instance
		print inst.args      # arguments stored in .args
		print inst           # __str__ allows args to printed directly
		x, y = inst          # __getitem__ allows args to be unpacked directly
		print 'x =', x
		print 'y =', y
		exit(-1)


def get_n_positions(n):
	""" Get the n last positions of every MAC in the database """
	global debug

	try:
		conn = sqlite3.connect('bluedriving.db')
		cursor = conn.cursor()


		# Get all the macs into an array
		id_macs = {}
		for row in cursor.execute('SELECT Mac,Id FROM devices ORDER BY MAC'):
			id_macs[str(row[1])] = str(row[0])

		if debug:
			print ' >> Unique macs: {0}'.format(id_macs)


		# Encoder
		je = json.JSONEncoder()
		
		# Example
		# { "map": [ 
		#		{ "MAC":"00:11:22:33:44:55", 
		#			"pos": [ 					// Called pos_vect below
		#					"gps":"-21.0001 -32.0023", 	// Called gps_data below
		#					"gps":"-44.5423 -56.65544" 
		#				] }, 
		#		{}, // Each of this is called data below
		#		{}, 
		#		{} 
		#	   ] } 

		# Top stores everythin
		top = {}

		# Map is the vector of name 'Map'
		map = []

		# Link the map vector with the name 'Map'
		top['Map'] = map

		# For each mac, obtain the last n positions
		for id in id_macs:

			cursor2 = conn.cursor()

			mac = id_macs[id]
			if debug:
				print ' >> Asking for mac: {0}'.format(mac)

			# Data holds information for each mac with all its positions
			data = {}
			data['MAC'] = mac

			pos_vect=[]
			data['pos'] = pos_vect

			# gps_data holds all the gps info for a given mac
			gps_data = {}

			#askid = ('%'+id+'%',n)
			askid = (id,n)

			# Flag to know if this mac has at least one position and avoid returning an empty position vector.
			no_gps_at_all = True
			for row in cursor2.execute("SELECT * FROM Locations WHERE Id = ? ORDER BY LastSeen DESC limit 0,?",askid):
				gps = row[1]
				#if debug:
					#print '  >> Gps: {0}'.format(gps)

				# Add the other string for no gps
				if 'not available' not in gps and 'Not using' not in gps and gps != '':
					no_gps_at_all = False
					gps_data['gps'] = gps
					pos_vect.append(gps)
					if debug:
						print '\t >> MAC {0} has position: {1}'.format(mac,gps)

			if no_gps_at_all:
				if debug:
					print ' >> MAC {0} has no gps position at all.'.format(mac)
				# This avoids adding an empty data to the map results.
				continue

			# Store the info of all the positions of one mac
			map.append(data)

		return je.encode(top)

	except Exception as inst:
		if debug:
			print '\tget_n_positions()'
		print type(inst)     # the exception instance
		print inst.args      # arguments stored in .args
		print inst           # __str__ allows args to printed directly
		x, y = inst          # __getitem__ allows args to be unpacked directly
		print 'x =', x
		print 'y =', y
		exit(-1)


def note_to(typeof_call, mac,note):
	""" Get a MAC and a note and add the note to the database """
	import re
	global debug

	try:

		# Input sanitizing
		##################

		# Replace + with spaces.
		note = note.replace('+', ' ')
		# Replace %20 with spaces.
		note = note.replace('%20', ' ')
		if debug:
			print ' >> Sanitizing Mac: {0} and Note: {1}'.format(mac, note)

		# verify the data types
		try:
			# Are they strings?
			if type(mac) != str or type(note) != str:
				if debug:
					print ' >> Some strange attempt to hack the server:1'
				return ''
		        # Is the format ok?
			if len(mac.split(':')) != 6 or len(mac) != 17:
				if debug:
					print ' >> Some strange attempt to hack the server:2'
				return ''
		        # Is the len of the noteok?
			if len(note) > 253:
				if debug:
					print ' >> Some strange attempt to hack the server:4'
				return ''
			# Characters fot the mac
			if not re.match('^[a-fA-F0-9:]+$',mac):
				if debug:
					print ' >> Some strange attempt to hack the server:4'
				return ''
			# Characters fot the note
			if note and not re.match('^[a-zA-Z0-9 .,?]+$',note):
				if debug:
					print ' >> Some strange attempt to hack the server:5'
				return ''
		except Exception as inst:
			if debug:
				print ' >> Some strange attempt to hack the server.6'
			print type(inst)     # the exception instance
			print inst.args      # arguments stored in .args
			print inst           # __str__ allows args to printed directly
			x, y = inst          # __getitem__ allows args to be unpacked directly
			print 'x =', x
			print 'y =', y
			return ''

		# We are hopefully safe here...
		if debug:
			print ' >> We are safe'
		# END Input sanitizing
		##################


		if typeof_call == 'add':
			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

			row = cursor.execute("SELECT Id FROM Devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
				
			cursor = conn.cursor()

			# Try to insert
			try:
				cursor.execute("INSERT INTO Notes (Id,Note) values (?,?) ",(id,note))
				conn.commit()
				if debug:
					print ' >> Inserted values. Id: {0}, Note:{1}'.format(id,note)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem inserting in the database in the funcion note_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''

			return "{'Result':'Added'}"

		elif typeof_call == 'del':
			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

			row = cursor.execute("SELECT Id FROM devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
		
			asknote = ('%'+note+'%',)

			# The mac does exist. Let's delete it.
			cursor2 = conn.cursor()

			# Try to delete
			try:
				cursor2.execute("DELETE FROM Notes where Id like ? and Note like ?",(id,note))
				conn.commit()
				if debug:
					print ' >> Deleted values. Id: {0}, Note:{1}'.format(id,note)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem deleting in the database in the funcion note_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''

			return 'Deleted'

		elif typeof_call == 'get':
			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

		        je = json.JSONEncoder()

			row = cursor.execute("SELECT Id FROM devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
			# The mac does exist. Let's delete it.
			cursor2 = conn.cursor()

			notesdict = {}
                        notes = []
			notesdict['Notes'] = notes

			# Try to get the values
			try:
				row2 = cursor2.execute("SELECT Note from notes where Id like ? ",(id,))
				#row2 = cursor2.execute("SELECT Note from notes")
				for row in row2:
					notes.append(str(row[0]))

				conn.commit()
				if debug:
					print ' >> Getting values. Id: {0}, Note:{1}'.format(id,note)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem getting the notes in the funcion note_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''
		        response = je.encode(notesdict)
			return response
		else:
			return ''

	except Exception as inst:
		if debug:
			print '\tProblem in note_to()'
		print type(inst)     # the exception instance
		print inst.args      # arguments stored in .args
		print inst           # __str__ allows args to printed directly
		x, y = inst          # __getitem__ allows args to be unpacked directly
		print 'x =', x
		print 'y =', y
		exit(-1)

def alarm_to(type_ofcall, mac, alarm_type):
	""" Get a MAC and add, get or remove an alarm """
	global debug
	import re

	try:
		# verify the data types
		try:
			# Are they strings?
			if type(mac) != str or type(alarm_type) != str:
				if debug:
					print ' >> Some strange attempt to hack the server:1'
				return ''
		        # Is the format ok?
			if len(mac.split(':')) != 6 or len(mac) != 17:
				if debug:
					print ' >> Some strange attempt to hack the server:2'
				return ''
		        # Is the len of the noteok?
			if len(alarm_type) > 253:
				if debug:
					print ' >> Some strange attempt to hack the server:4'
				return ''
			# Characters fot the mac
			if not re.match('^[a-fA-F0-9:]+$',mac):
				if debug:
					print ' >> Some strange attempt to hack the server:4'
				return ''
			# Characters fot the note
			if alarm_type and not re.match('^[a-zA-Z0-9 .,?]+$',alarm_type):
				if debug:
					print ' >> Some strange attempt to hack the server:5'
				return ''
		except Exception as inst:
			if debug:
				print ' >> Some strange attempt to hack the server.6'
			print type(inst)     # the exception instance
			print inst.args      # arguments stored in .args
			print inst           # __str__ allows args to printed directly
			x, y = inst          # __getitem__ allows args to be unpacked directly
			print 'x =', x
			print 'y =', y
			return ''


		if type_ofcall == 'add':

			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

			row = cursor.execute("SELECT Id FROM Devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
				
			cursor = conn.cursor()


			# Try to insert
			try:
				cursor.execute("INSERT INTO Alarms (Id,Alarm) values (?,?) ",(id,alarm_type))
				conn.commit()
				if debug:
					print ' >> Inserted values. Id: {0}, Alarm:{1}, Mac:{2}'.format(id, alarm_type, mac)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem inserting in the database in the funcion alarm_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''

			return "{'Result':'Added'}"

		elif type_ofcall == 'del':

			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

			row = cursor.execute("SELECT Id FROM Devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
				
			cursor = conn.cursor()


			# Try to insert
			try:
				cursor.execute("DELETE From Alarms where Id like ? and Alarm like ?",(id,alarm_type))
				conn.commit()
				if debug:
					print ' >> Deleted values. Id: {0}, Alarm:{1}, Mac:{2}'.format(id, alarm_type, mac)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem deleting in the database in the funcion alarm_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''

			return "{'Result':'Deleted'}"

		elif type_ofcall == 'get':

			# Search fot that mac on the database first...
			conn = sqlite3.connect('bluedriving.db')
			cursor = conn.cursor()
			askmac = ('%'+mac+'%',)

		        je = json.JSONEncoder()

			row = cursor.execute("SELECT Id FROM Devices WHERE Mac like ? limit 0,1",askmac)

			# Check the results, Does this mac exists?
			res = row.fetchall()
			if len(res) != 0:
				(id,) = res[0]
			else:
				if debug:
					print ' >> This mac does not exist: {0}'.format(mac)
				return ''
				
			cursor = conn.cursor()

                        alarmsdict = {}
                        alarms = []
			alarmsdict['Alarms'] = alarms
			# Try to insert
			try:
				row2 = cursor.execute("SELECT Alarm from Alarms where Id like ?",(id,))
                                for row in row2:
					print row
                                        alarms.append(row)

				conn.commit()
				if debug:
					print ' >> Get values. Id: {0}, Alarm:{1}, Mac:{2}'.format(id, alarm_type, mac)
				conn.close()
			except Exception as inst:
				if debug:
					print ' >> Some problem getting from the database in the funcion alarm_to()'
				print type(inst)     # the exception instance
				print inst.args      # arguments stored in .args
				print inst           # __str__ allows args to printed directly
				x, y = inst          # __getitem__ allows args to be unpacked directly
				print 'x =', x
				print 'y =', y
				return ''

		        response = je.encode(alarmsdict)
			return response


	except Exception as inst:
		if debug:
			print '\tProblem in alarm_to()'
		print type(inst)     # the exception instance
		print inst.args      # arguments stored in .args
		print inst           # __str__ allows args to printed directly
		x, y = inst          # __getitem__ allows args to be unpacked directly
		print 'x =', x
		print 'y =', y
		exit(-1)



class MyHandler (BaseHTTPServer.BaseHTTPRequestHandler):
	""" Handle the requests """

	def log_message(self, format, *args):
		        return

	def do_GET(self):
		global debug
		note = ""
		alarm_type = ""
		try:
			if debug:
				print ' >> Path: {0}'.format(self.path)

			# Return the basic info about the MACs since last request
			if self.path == '/data':
				if debug:
					print ' >> Get /data'
				# Get the unread registers from the DB since last time
				json_to_send = get_unread_registers()

				#json_to_send = json.dumps("{'test': Yes}")

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)

			# Get a MAC and add a note in the database 
			elif self.path.rfind('/addnote?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /addnote'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				note = str(self.path.split('note=')[1])
				json_to_send = note_to('add', mac, note)

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)

			# Get a MAC and del a note from the database 
			elif self.path.rfind('/delnote?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /delnote'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				note = str(self.path.split('note=')[1])
				json_to_send = note_to('del', mac, note)

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)

			# Get a MAC and get all the notes from the database 
			elif self.path.rfind('/getnote?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /getnote'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				json_to_send = note_to('get', mac, "")

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)
			# Get alarms from a MAC  
			elif self.path.rfind('/getalarm?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /getalarm'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				#alarm_type = str(self.path.split('type=')[1].split('&')[0])
				json_to_send = alarm_to('get', mac, '')

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)
			# Add an alarm to a MAC  
			elif self.path.rfind('/addalarm?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /addalarm'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				alarm_type = str(self.path.split('type=')[1].split('&')[0])
				json_to_send = alarm_to('add', mac, alarm_type)

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)
			# Del an alarm from a MAC  
			elif self.path.rfind('/delalarm?mac=') == 0: # and self.path.find("note=") > 0:
				if debug:
					print ' >> Get /delalarm'
				mac = str(self.path.split('mac=')[1].split('&')[0])
				alarm_type = str(self.path.split('type=')[1].split('&')[0])
				json_to_send = alarm_to('del', mac, alarm_type)

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)
			# Get a MAC and return all the info about that MAC
			elif self.path.rfind('/info?mac=') == 0:
				if debug:
					print ' >> Get /info'
				
				mac = self.path.split('mac=')[1]
				json_to_send = get_info_from_mac(mac)

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)

			# Get an X amount and return for every MAC the last X positions.
			elif self.path.rfind('/map?amount=') == 0:
				if debug:
					print ' >> Get /map'

				n = self.path.split('amount=')[1]

				json_to_send = get_n_positions(int(n))

				self.send_response(200)
				self.send_header('Content-Type',        'text/html')
				self.end_headers()
				self.wfile.write(json_to_send)

			elif self.path == "/":
				if debug:
					print ' >> Get /'
				# Return the index.html
				file = open(curdir + sep + 'index.html')

				temp_read = file.read()
				file_len = len(temp_read)

				self.send_response(200)
				self.send_header('Content-Type','text/html; charset=UTF-8')
				self.send_header('Content-Length',file_len)
				self.end_headers()

				self.wfile.write(temp_read)
				file.close()


			elif self.path != "/":
				# Read files in the directory
				if debug:
					print ' >> Get generic file'

				try:
					extension = self.path.split('.')[-1]
				except:
					# Does not have . on it...
					self.send_response(200)
					return


				self.send_response(200)

				if extension == 'css':
					file = open(curdir + sep + self.path)
					temp_read = file.read()
					file_len = len(temp_read)
					self.send_header('Content-Type','text/css')
					self.send_header('Content-Length',file_len)
					self.end_headers()

				elif extension == 'png':
					file = open(curdir + sep + self.path)
					temp_read = file.read()
					file_len = len(temp_read)
					self.send_header('Content-Type','image/png')
					self.send_header('Content-Length',file_len)
					self.end_headers()

				elif extension == 'js':
					file = open(curdir + sep + self.path)
					temp_read = file.read()
					file_len = len(temp_read)
					self.send_header('Content-Type','text/javascript')
					self.send_header('Content-Length', file_len)
					self.end_headers()

				elif extension == 'html':
					file = open(curdir + sep + self.path)
					temp_read = file.read()
					file_len = len(temp_read)
					self.send_header('Content-Type','text/html; charset=UTF-8')
					self.send_header('Content-Length',file_len)
					self.end_headers()
				else:
					self.send_header('Content-Type','text/html; charset=UTF-8')
					self.send_header('Content-Length','9')
					self.end_headers()
					self.wfile.write('Hi there.')
					return

				self.wfile.write(temp_read)
				file.close()


			return


		except IOError:
			self.send_error(404,'File Not Found: {0}'.format(self.path))







def main():
	try:
		global debug
		# Default port to use
		port = 8000

		opts, args = getopt.getopt(sys.argv[1:], "VvDh", ["help","version","verbose","debug","port"])
	except getopt.GetoptError: usage()

	for opt, arg in opts:
	    if opt in ("-h", "--help"): usage();exit(-1)
	    if opt in ("-V", "--version"): version();exit(-1)
	    if opt in ("-v", "--verbose"): verbose=True
	    if opt in ("-D", "--debug"): debug=1
	    if opt in ("-p", "--port"): port=int(arg)
	try:

		try:
			if True:
				createWebServer(port)
				

			else:
				usage()
				sys.exit(1)

		except Exception, e:
			print "misc. exception (runtime error from user callback?):", e
		except KeyboardInterrupt:
			sys.exit(1)


	except KeyboardInterrupt:
		# CTRL-C pretty handling.
		print "Keyboard Interruption!. Exiting."
		sys.exit(1)


if __name__ == '__main__':
    main()

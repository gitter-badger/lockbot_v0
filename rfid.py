#!/usr/bin/python3

# SL030 RFID reader driver for skpang supplied SL030 Mifare reader
# (c) 2013 Thinking Binaries Ltd, David Whale


# set to True to detect card presence by using GPIO
# set to False to detect card presence by reading card status

CFGEN_GPIO        = True


# Set to the GPIO required to monitor the tag detect (OUT) line
CFG_TAG_DETECT        = 4



if CFGEN_GPIO:
	import RPi.GPIO as GPIO

from quick2wire.i2c import I2CMaster, writing_bytes, reading
import time
import sys
import os
from time import sleep

ADDRESS           = 0x50
CMD_SELECT_MIFARE = 0x01
CMD_GET_FIRMWARE  = 0xF0
WR_RD_DELAY       = 0.05

import socket

# timeout in seconds, don't wait a whole minute if the network is down
timeout = 10
socket.setdefaulttimeout(timeout)

# if 'SERVER_SOFTWARE' in os.environ

# allow accessing the acserver using a proxy for debugging locally
if 'SOCKS_HOST' in os.environ and 'SOCKS_PORT'  in os.environ and 'SOCKS_HOST'  in os.environ and 'SOCKS_PORT'  in os.environ:

	print( "socks host " + os.environ['SOCKS_HOST'] + ":" + os.environ['SOCKS_PORT'])
#
	import socks

	socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, 
		os.environ['SOCKS_HOST'], 
			int(os.environ['SOCKS_PORT']))
      
	socket.socket = socks.socksocket

try:
    import urllib.request as urllib2
except:
    import urllib2

from urllib.request import Request, urlopen, URLError, HTTPError

# set these in the environment of whatever script calls this
masterid = os.environ['MASTERID']
print("masterid:"+masterid)

masterid = "B337FAA4"
host = os.environ['HOSTURL']

def error(str):
	print("ERROR:" + str)

class SL030:
	def __init__(self):
		self.type = None
		self.uid  = None

		if CFGEN_GPIO:
			GPIO.setmode(GPIO.BCM)
			GPIO.setup(CFG_TAG_DETECT, GPIO.IN)

		# set the lock pin controller
		GPIO.setup(23, GPIO.OUT)
		GPIO.output(23, 1)
		
		# leds
		GPIO.setup(17, GPIO.OUT)
		GPIO.setup(18, GPIO.OUT)
		
		GPIO.output(17, 0)
		GPIO.output(18, 1)

	def tag_present(self):
		if CFGEN_GPIO:
			return GPIO.input(CFG_TAG_DETECT) == False
		else:
			return self.select_mifare()

	def wait_tag(self):
		while not self.tag_present():
			time.sleep(0.01)

	def wait_notag(self):
		while self.tag_present():
			time.sleep(0.5)

	def validate_ver(self, ver):
		first = ver[0]
		if first != ord('S'):
			if first == ord('S') + 0x80:
				error("I2C clock speed too high, bit7 corruption")
				print("try: sudo modprobe -r i2c_bcm2708")
				print("     sudo modprobe i2c_bcm2708 baudrate=50000")
			else:
				error("unrecognised device")

	def tostr(self, ver):
		verstr = ""
		for b in ver:
			verstr += chr(b)
		return verstr

	def get_firmware(self):
		with I2CMaster() as master:
			# request firmware id read
			# <len> <cmd>
			master.transaction(writing_bytes(ADDRESS, 1, CMD_GET_FIRMWARE))
			time.sleep(WR_RD_DELAY)

			# read the firmware id back
			responses = master.transaction(reading(ADDRESS, 15))
			response = responses[0]
			# <len> <cmd> <ver...>
			len = response[0]
			cmd = response[1]
			ver = response[3:len]
			self.validate_ver(ver)
			
			return self.tostr(ver)

	def get_typename(self, type):
		if (type == 0x01):
			return "mifare 1k, 4byte UID"
		elif (type == 0x02):
			return "mifare 1k, 7byte UID"
		elif (type == 0x03):
			return "mifare UltraLight, 7 byte UID"
		elif (type == 0x04):
			return "mifare 4k, 4 byte UID"
		elif (type == 0x05):
			return "mifare 4k, 7 byte UID"
		elif (type == 0x06):
			return "mifare DesFilre, 7 byte UID"
		elif (type == 0x0A):
			return "other"
		else:
			return "unknown:" + str(type)

	def select_mifare(self):
		with I2CMaster() as master:
			# select mifare card
			# <len> <cmd> 
			master.transaction(writing_bytes(ADDRESS, 1, CMD_SELECT_MIFARE))
			time.sleep(WR_RD_DELAY)

			# read the response
			responses = master.transaction(reading(ADDRESS, 15))
			response = responses[0]
			# <len> <cmd> <status> <UUID> <type>
			len    = response[0]
			cmd    = response[1]
			status = response[2]

			if (status != 0x00):
				self.uid  = None
				self.type = None
				return False 

			# uid length varies on type, and type is after uuid
			uid       = response[3:len]
			type      = response[len]
			self.type = type
			self.uid  = uid
			return True

	def get_uid(self):
		return self.uid

	def get_uidstr(self):
		uidstr = ""
		for b in self.uid:
			uidstr += "%02X" % b
		return uidstr

	def get_type(self):
		return self.type

##########################################################################
# Fix the baud rate of the I2C driver.
# The combination of the SL030 and the Raspberry Pi I2C driver
# causes some corruption of the data at the default baud rate of
# 100k. Until this problem is completely fixed, we just change the
# baud rate here to a known working rate. Interestingly, it fails at
# 90k but works at 200k and 400k.

def fixrate():
	newspeed = 200000
	os.system("sudo modprobe -r i2c_bcm2708")
	os.system("sudo modprobe i2c_bcm2708 baudrate=" + str(newspeed))
	time.sleep(1.0)



###########################################################################
# Simple test program
#
# Just run rfid.py to run this test program against the driver.
#
# For your own application, copy these lines into a new file
# and put this at the top of your new file:
#
# import rfid
#
# Then modify your application to suit


# fill in this map with your card id's

cards = {
	"2B53B49B"       : "whaleygeek", 
	"04982B29EE0280" : "1", 
	"EAC85517"       : "David",
	#"24B1E145"       : "Daniel",
	"C2091F58"       : "4"
	}

def checkuid(rfid):
	global masterid
	print("master id:"+masterid)
	
	if rfid==masterid:
		pass
		print("opening lock on master id")
		return True

	elif rfid in ["880455449D"]:

		pass
		print("opening lock on list override")
		return True	
	
	else:
		content = 0 
		hosturl = host+"/4/card/"+rfid
					
		req = Request(hosturl)
		
		try:
			response = urlopen(req)
		except HTTPError as e:
			print('The server couldn\'t fulfill the request.')
			print('Error code: ', e.code)
		except URLError as e:
			print('We failed to reach a server.'+hosturl)
			print('Reason: ', e.reason)
		else:
			# everything is fine
			pass
			content = response.read()
			if int(content)==1:
				return True	
			elif int(content)==2:
				# is maintainer
				return True	
			
		print( "content was "+str(content))
	
	return False


def example():
	rfid = SL030()
	fw = rfid.get_firmware()
	print("RFID reader firmware:" + fw)
	print()

	while True:
		rfid.wait_tag()
		print("card present")

		if rfid.select_mifare():
			type = rfid.get_type()
			print("type:" + rfid.get_typename(type))

			id = rfid.get_uidstr()
			try:
				#user = cards[id]
				#print(user)
				if checkuid(id):
					
					print("opening on presentation of ID "+id)
					
					# set the lock pin controller
					GPIO.output(23, 0)
					
					# leds
					GPIO.output(17, 1)
					GPIO.output(18, 0)
					
					sleep(3)
					
					print("closing")
					
					# set the lock pin controller
					GPIO.output(23, 1)
					
					# leds
					GPIO.output(17, 0)
					GPIO.output(18, 1)
						
				else:
					print("not opening "+id)
					for x in range(0, 2):
						print( "We're on time")
						
						GPIO.output(18, 0)
						sleep(0.5)
						
						GPIO.output(18, 1)
						sleep(0.5)
					
				#os.system("aplay " + user)
			except KeyError:
				print("Unknown card:" + id)

		rfid.wait_notag()
		print("card removed")
		print()

if __name__ == "__main__":
	
	fixrate()
	example()

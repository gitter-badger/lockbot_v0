# coding=utf-8

import RPi.GPIO as GPIO
import MFRC522
import signal

import sys
import os

import datetime
import time

import socket

# timeout in seconds, don't wait a whole minute if the network is down
timeout = 10
socket.setdefaulttimeout(timeout)

debug = False

# allow accessing the acserver using a proxy for debugging locally
if os.environ.has_key('SOCKS_HOST') and os.environ.has_key('SOCKS_PORT') and  os.environ['SOCKS_HOST'] and os.environ['SOCKS_PORT']:

  print "socks host " + os.environ['SOCKS_HOST'] + ":" + os.environ['SOCKS_PORT']
  
  import socks
  
  socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, 
    os.environ['SOCKS_HOST'], 
      int(os.environ['SOCKS_PORT']))
      
  socket.socket = socks.socksocket

import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError

continue_reading = True

# exit with a default error unless login 0 or not recognised 2 is set
exitcode = 1

# set these in the environment of whatever script calls this
masterid = os.environ['MASTERID']
host = os.environ['HOSTURL']

# Capture SIGINT for cleanup when the script is aborted
def end_read(signal,frame):
    global continue_reading
    global exitcode
    print "Ctrl+C captured, ending read.\n"
    continue_reading = False
    GPIO.cleanup()
    os._exit(exitcode)

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

print "waiting for card2" 

# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:
    
    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQALL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected: Type " +str(TagType)
    
        ## Get the UID of the card (also selects card)  
        (status,uid) = MIFAREReader.MFRC522_GetUID()
                       
        # If we have the UID, continue
        if status == MIFAREReader.MI_OK:
          
            # Print UID
            uidh = map(hex, uid)
            uidh = map(str, uidh)
            
            print "UID Length: "+str(len(uid))
            print "Card read UID: "+ ", ".join(map(str,uid))
            print "Card read HEX: "+ ", ".join(uidh)
        
            # Select key for authentication
            key = MIFAREReader.defaultKeyA

            # Authenticate
            status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 8, key, uid)

            # Check if authenticated
            if status == MIFAREReader.MI_OK:
                MIFAREReader.MFRC522_Read(8)
                MIFAREReader.MFRC522_StopCrypto1()
            else:
                print "Authentication error"

            
            rfid = ""
        
            # hex returns 0xAA strings, I just want the hex chars so [2:4] slices them
            for s in uid:
                print s
                #print hex(s)
                rfid=rfid+hex(s)[2:4].upper().rjust(2,'0')
          
            print "rfid: "+rfid
                 
            with open("auth.log", "a") as myfile:
              myfile.write(str(datetime)+": "+"rfid: "+rfid+"\n")
            
            
            if rfid==masterid:
              pass
              print "opening lock on master id"
              exitcode=0
            
            elif rfid in ["880455449D"]:
              
              pass
              print "opening lock on list override"
              exitcode=0
              
            else:
            
              content = "0"          
              hosturl = host+"/4/card/"+rfid
                        
              req = Request(hosturl)
              try:
                  response = urlopen(req)
              except HTTPError as e:
                  print 'The server couldn\'t fulfill the request.'
                  print 'Error code: ', e.code
              except URLError as e:
                  print 'We failed to reach a server.'
                  print 'Reason: ', e.reason
              else:
                  # everything is fine
                  pass
                  
              content = response.read()

              if int(content)>0:
                exitcode=0

              else:
                exitcode=2
        
            # Stop scanning for cards
            continue_reading = False
            
        
    #elif status == MIFAREReader.MI_OK:

GPIO.cleanup()
os._exit(exitcode)

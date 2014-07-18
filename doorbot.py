# coding=utf-8

import RPi.GPIO as GPIO
import MFRC522
import signal

import sys
import os

# allow accessing the acserver using a proxy for debugging locally
if os.environ.has_key('SOCKS_HOST') and os.environ.has_key('SOCKS_PORT') and  os.environ['SOCKS_HOST'] and os.environ['SOCKS_PORT']:

  print "using socks proxy " + os.environ['SOCKS_HOST'] + " port " + os.environ['SOCKS_PORT']
  
  import socks
  import socket
  
  socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, 
    os.environ['SOCKS_HOST'], 
      int(os.environ['SOCKS_PORT']))
      
  socket.socket = socks.socksocket

import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError

# timeout in seconds
timeout = 10
socket.setdefaulttimeout(timeout)

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
    print "Ctrl+C captured, ending read."
    continue_reading = False
    GPIO.cleanup()
    os._exit(exitcode)

# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522()

print "waiting for card"

while continue_reading:
    
    # Scan for cards    
    (status,TagType) = MIFAREReader.MFRC522_Request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print "Card detected"
    else:
        pass
        #print "status  "+str(status)
    
    # Get the UID of the card
    (status,uid) = MIFAREReader.MFRC522_Anticoll()

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        rfid = ""
        
        # hex returns 0xAA strings, I just want the hex chars so [2:4] slices them
        for s in uid:
          rfid=rfid+hex(s)[2:4].upper()
          
        print "rfid: "+rfid
             
        if rfid==masterid:
          pass
          print "opening lock on master id"
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

          print "content:" + content
            
          if int(content)>0:
            exitcode=0

          else:
            sys.exit(2)

        # Make sure to stop scanning for cards
        continue_reading = False


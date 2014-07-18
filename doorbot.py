# coding=utf-8

import RPi.GPIO as GPIO
import MFRC522
import signal

import urllib2

import sys
import os
  

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
        
        for s in uid:
          rfid=rfid+hex(s)[2:4].upper()
          
        print "rfid: "+rfid
             
        if rfid==masterid:
          pass
          exitcode=0
          
        else:
        
          content = "0"
          
          print host+"/4/card/"+rfid
          
          #content = urllib2.urlopen(host+"/4/card/"+rfid).read()
          
          print "content:" + content
            
          if int(content)>0:
            exitcode=0

          else:
            sys.exit(2)


        # Make sure to stop scanning for cards
        continue_reading = False

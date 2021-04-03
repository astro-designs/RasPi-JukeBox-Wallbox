import RPi.GPIO as GPIO
import time
from datetime import datetime
import os
import sys
import math
import urllib
import urllib2
import requests

# Set the GPIO modes
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set variables for the GPIO pins
PinWallbox = 12 # Signal from Wallbox
pinWallboxPower = 13 # Wallbox On
pinWallboxPowerLED = 23 # Wallbox On
pinWallboxSignalLED = 22 # Wallbox Signal
pinTrackRequestLED = 20 # Track request sent
pinPlayerFoundLED = 21 # Connection to player

GPIO.setup(PinWallbox, GPIO.IN)
GPIO.setup(pinWallboxPower, GPIO.IN)

GPIO.setup(pinWallboxPowerLED, GPIO.OUT)
GPIO.output(pinWallboxPowerLED, False)
GPIO.setup(pinWallboxSignalLED, GPIO.OUT)
GPIO.output(pinWallboxSignalLED, False)
GPIO.setup(pinPlayerFoundLED, GPIO.OUT)
GPIO.output(pinPlayerFoundLED, False)
GPIO.setup(pinTrackRequestLED, GPIO.OUT)
GPIO.output(pinTrackRequestLED, False)

# Initialise variables...
playerFound = False
PosEdgeTime = 0.0
NegEdgeTime = 0.0
Started = False
Finished = True
phase = 0
alpha = 0
numeric = 0

# Dictionary of supported configuration files
Wallbox_models = {
    1 : {'filename' : 'c0s01.cnf', 'rand_timeout' : 0, 'model' : 'Seeburg 3W1 / 3W100', 'num_letters' : 10, 'num_numbers' : 10, 'num_indexes' : 200},
    2 : {'filename' : 'c0s02.cnf', 'rand_timeout' : 0, 'model' : 'Seeburg 3W160', 'num_letters' : 16, 'num_numbers' : 10, 'num_indexes' : 160},
    3 : {'filename' : 'c0s03.cnf', 'rand_timeout' : 0, 'model' : 'Seeburg 3WA', 'num_letters' : 20, 'num_numbers' : 10, 'num_indexes' : 200},
    4 : {'filename' : 'c1s01.cnf', 'rand_timeout' : 30, 'model' : 'Seeburg 3W1 / 3W100', 'num_letters' : 10, 'num_numbers' : 10, 'num_indexes' : 200},
    5 : {'filename' : 'c1s02.cnf', 'rand_timeout' : 30, 'model' : 'Seeburg 3W160', 'num_letters' : 16, 'num_numbers' : 10, 'num_indexes' : 160},
    6 : {'filename' : 'c1s03.cnf', 'rand_timeout' : 30, 'model' : 'Seeburg 3WA', 'num_letters' : 20, 'num_numbers' : 10, 'num_indexes' : 200},
    7 : {'filename' : 'c2s01.cnf', 'rand_timeout' : 300, 'model' : 'Seeburg 3W1 / 3W100', 'num_letters' : 10, 'num_numbers' : 10, 'num_indexes' : 200},
    8 : {'filename' : 'c2s02.cnf', 'rand_timeout' : 300, 'model' : 'Seeburg 3W160', 'num_letters' : 16, 'num_numbers' : 10, 'num_indexes' : 160},
    9 : {'filename' : 'c2s03.cnf', 'rand_timeout' : 300, 'model' : 'Seeburg 3WA', 'num_letters' : 20, 'num_numbers' : 10, 'num_indexes' : 200},
    10 : {'filename' : 'c3s01.cnf', 'rand_timeout' : 900, 'model' : 'Seeburg 3W1 / 3W100', 'num_letters' : 10, 'num_numbers' : 10, 'num_indexes' : 200},
    11 : {'filename' : 'c3s02.cnf', 'rand_timeout' : 900, 'model' : 'Seeburg 3W160', 'num_letters' : 16, 'num_numbers' : 10, 'num_indexes' : 160},
    12 : {'filename' : 'c3s03.cnf', 'rand_timeout' : 900, 'model' : 'Seeburg 3WA', 'num_letters' : 20, 'num_numbers' : 10, 'num_indexes' : 200}
    }

pins = {
   23 : {'name' : 'GPIO 23', 'state' : GPIO.LOW},
   24 : {'name' : 'GPIO 24', 'state' : GPIO.LOW}
   }


# Define some constants
Finish_Timeout = 1.0
Alpha_Timeout = 0.1


import argparse

parser = argparse.ArgumentParser(description='Raspberry Pi JukeBox Wallbox client')

parser.add_argument('-ip', action='store', dest='player_IP_Address', default='raspi-jukebox',
                    help='IP Address of Domoticz server (e.g. 192.168.1.118 or raspi-jukebox)')

arguments = parser.parse_args()

# Read arguments...
player_IP_Address = arguments.player_IP_Address

def ping(player_IP_Address):
     
    print("Pinging Player...")
    url = 'http://' + player_IP_Address + '/' + 'system/ping'
    print("url: ",url)
    try:
        request = urllib2.Request(url)
        print("Request: ",request)
        response = urllib2.urlopen(request)
        print("Response: ",response)
        playerFound = True
    except urllib2.HTTPError, e:
        print("e.code: ",e.code);
        print("e.args: ",e.args);
        playerFound = False
    except urllib2.URLError, e:
        print("e.code: ",e.code);
        print("e.args: ",e.args);
        playerFound = False
    
    return(playerFound)

def addToPlaylist(track):
    selection = '000' + str(track)
    selection = 'sel' + selection[-3:]
     
    print("Requesting Track...")
    url = 'http://' + player_IP_Address + '/' + selection + '/add'
    print("url: ",url)
    try:
        request = urllib2.Request(url)
        print("Request: ",request)
        response = urllib2.urlopen(request)
        print("Response: ",response)
        playerFound = True
    except urllib2.HTTPError, e:
        print("e.code: ",e.code);
        print("e.args: ",e.args);
        playerFound = False
    except urllib2.URLError, e:
        print("e.code: ",e.code);
        print("e.args: ",e.args);
        playerFound = False
    
    return(playerFound)

try:

    print("Raspberry Pi JukeBox")
    print("Wallbox client")
    
    # Search for Wallbox config file...
    print("Searching for configuration file...")

    num_letters = 0
    num_numbers = 0
    num_indexes = num_letters * num_numbers
    rand_timeout = 0
    config_file = ''
    
    for model in Wallbox_models:
        PATH = '/boot/' + Wallbox_models[model]['filename']
        if os.path.isfile(PATH) and os.access(PATH, os.R_OK):
            config_file = Wallbox_models[model]['filename']
            wallbox_name = Wallbox_models[model]['model']
            rand_timeout = Wallbox_models[model]['rand_timeout']
            num_letters = Wallbox_models[model]['num_letters']
            num_numbers = Wallbox_models[model]['num_numbers']
            num_indexes = Wallbox_models[model]['num_indexes']            
            break
    
    if num_indexes == 0:
        print("Error reading configuration file!")    
    else:
        print("Configuration: " + Wallbox_models[model]['model'])
    
        # Setup constants for selected wallbox 
        letters = num_letters
        numbers = num_numbers
        
        # Start...
        while True:
        
            # Check Wallbox power...
            if GPIO.input(pinWallboxPower) == False:
                print("Wallbox Power OK")
                GPIO.output(pinWallboxPowerLED, True)
            else:
                print("Check Wallbox Power!")
                GPIO.output(pinWallboxPowerLED, False)

            # Search for JukeBox player...
            print("Looking for player at IP Address ", player_IP_Address)
            
            playerFound = ping(player_IP_Address)

            if playerFound:
                print("Player found")
                GPIO.output(pinPlayerFoundLED, True)
            else:
                print("Player unavailable")
                GPIO.output(pinPlayerFoundLED, False)
            
            while playerFound:
                
                print("Waiting for selection...")
                
                # Wait for negative edge...
                while GPIO.input(PinWallbox)== 1:
                    time.sleep(0.001)
                    if time.time() - PosEdgeTime > Finish_Timeout: # Look for a long time without a positive edge to identify the end
                        if Finished == False:
                            print("Selection: ", alpha-1, numeric)
                            addToPlaylist((alpha - 2) * numbers + numeric)
                            if playerFound == True:
                                # Flash green LED for 1s
                                GPIO.output(pinTrackRequestLED, True)
                                time.sleep(1)
                                GPIO.output(pinTrackRequestLED, False)
                            else:
                                print("Player unavailable")
                                GPIO.output(pinTrackRequestLED, True)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, False)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, True)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, False)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, True)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, False)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, True)
                                time.sleep(0.125)
                                GPIO.output(pinTrackRequestLED, False)
                                time.sleep(0.125)

                            Finished = True

                NegEdgeTime = time.time()
                HighTime = NegEdgeTime - PosEdgeTime
                GPIO.output(pinWallboxSignalLED, True)
                print("High time: ", HighTime)

                if Finished: #
                    #print("Starting Alpha...")
                    Started = True
                    Finished = False
                    phase = 0
                    alpha = 0
                    numeric = 0
                    
                elif HighTime > Alpha_Timeout: # Look for a short pause to identify the start of the numeric phase
                    #print("Starting Numeric...")
                    phase = 1
                
                #if Started and not Finished:
                    #print ("HighTime: ",HighTime)

                # Wait for positive edge...
                while GPIO.input(PinWallbox)== 0:
                    time.sleep(0.001)

                PosEdgeTime = time.time()
                LowTime = PosEdgeTime - NegEdgeTime
                GPIO.output(pinWallboxSignalLED, False)
                print("Low time: ", LowTime)

                if phase == 0:
                    alpha = alpha + 1
                else:
                    numeric = numeric + 1
                
                #if Started and not Finished:
                    #print ("LowTime: ",LowTime)

            # Pause for 5 seconds before looking for a player again...
            time.sleep(5)
        
except KeyboardInterrupt:
    print("Keyboard Interrupt (ctrl-c) - exiting program loop")

finally:
    print("Closing Wallbox client")
    GPIO.cleanup()

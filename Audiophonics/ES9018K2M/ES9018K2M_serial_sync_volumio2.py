#!/usr/bin/python2
# coding: utf-8
#
# Audiophonics ES9018K2M DAC hardware volume management script for Volumio 2
# 
# Based on script for Runeaudio by Audiophonics and Fujitus
# https://github.com/audiophonics/ES9018K2M_serial_sync
#
# Adapted to Volumio 2 by Jean-Charles BARBAUD
#
# Require to setup ES9018K2M DAC in serial hardware mode as defined on Audiophonics product page.
# Refer to http://www.audiophonics.fr/fr/dac-diy/audiophonics-i-sabre-dac-es9018k2m-raspberry-pi-3-pi-2-a-b-i2s-p-11500.html

import time , serial
import subprocess , os
from urllib2 import Request, urlopen, URLError
      
def VolumioGetStatus():
        process = subprocess.Popen("/volumio/app/plugins/system_controller/volumio_command_line_client/volumio.sh status", stdout=subprocess.PIPE, shell=True)
        os.waitpid(process.pid, 0)[1]
        Status = process.stdout.read().strip()
        ParamList = Status.split('\n')
        VolumioCurrentStatus = ParamList[0][11:15]        
        VolumioCurrentService = ParamList[-1][12:15]     # need to know which service is running as parameters list differ            
	VolumioCurrentBitDepth = "24"                    # set to 24 bit as default, compliant qith webradio service
	VolumeRank = 0
	if (VolumioCurrentStatus != "play"):             # no known services are playing, check if Volspotconnect plugin is active
	        try:
		   VolspotconnectResponse = urlopen('http://volumio.local:4000/api/info/status')
		except URLError:
		   VolumioCurrentVolume = "0"            # set volume to zero to avoid audio glitches at next bitdepth switching
		   return (VolumioCurrentStatus , VolumioCurrentBitDepth , VolumioCurrentVolume)
		else:
		   VolspotconnectStatus = VolspotconnectResponse.read().split()
		   if (VolspotconnectStatus[2][0:4] == 'true') and (VolspotconnectStatus[6][0:4] == 'true'):	# if Volspotconnect is active and is playing			 
                         VolumioCurrentBitDepth = "16"   # set DAC to 16 bit mode to please Volspotconnect plugin        
                         VolumeRank = 14
	else:                                            # known services are playing, check required bitdepth
	        VolumioCurrentBitDepth = ParamList[11][13:15]
        if (VolumioCurrentService == "mpd") or (VolumioCurrentService == "web"):
                VolumeRank = 16
        elif (VolumioCurrentService == "spo"):
                VolumeRank = 15                
        if VolumeRank == 0:
	        VolumioCurrentVolume = "100"             # if unknown service, set volume to 100 and exit without further processing
                return (VolumioCurrentStatus , VolumioCurrentBitDepth , VolumioCurrentVolume)	
        VolumioCurrentVolume = ParamList[VolumeRank].split(':')  # as volume char wide can be from 1 to 3 (volume 0 to 100), processing needed to extract the volume figure
        VolumioCurrentVolume = VolumioCurrentVolume[1].strip()   # remove space char at both ends
        VolumioCurrentVolume = VolumioCurrentVolume[:-1]         # remove the trailing coma
        return (VolumioCurrentStatus , VolumioCurrentBitDepth , VolumioCurrentVolume)

if __name__ == '__main__':
        ser = serial.Serial('/dev/ttyAMA0', 2400)
        ser.isOpen()
        DACFilter = "1"  # default value, no documentation describing this parameter
        DACVolume = "0"
        last_setup = "A,0,0,0"
        try:
                while True:
                        VolumioStatus = VolumioGetStatus()
                        if (VolumioStatus[1] == "16"):
                                DACBitDepth = "A,0"              # switch DAC to 16 bit bitdepth mode
                        else:
                                DACBitDepth = "A,1"              # switch DAC to 24/32 bit bitdepth mode
                        DACVolume = VolumioStatus[2]             # set DAC hardware volume according to Volumio UI volume setting                                           
                        DACsetup = DACBitDepth + "," + DACVolume + "," + DACFilter
                        if (DACsetup != last_setup):
                                last_setup = DACsetup
                                ser.write(DACsetup.encode('utf-8'))  # send new setup to DAC other serial link
                        time.sleep(0.1)        
        except KeyboardInterrupt:
                ser.close()
ser.close()

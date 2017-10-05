__author__ = "Alexey D. Filimoniov <filimonic>"
__credits__ = ["haribertlondon/dreamcat4 for LG TV Remote 2011","msloth for LG TV Remote 2015", "ubaransel for LG TV Remote 2012-2014"]
__license__ = "GPL"
__version__ = "1.1.6"
__maintainer__ = "Alexey D. Filimonov <filimonic>"
__email__ = "alexey@filimonic.net"
__status__ = "Developement"
__url__ = "https://github.com/filimonic/Kodi.Screensaver.TurnOffLGTV"

import sys
import xbmcgui
import xbmcaddon
import xbmc
import time
import json
import urllib2
import threading
import os
import xml.etree.ElementTree as etree

Addon = xbmcaddon.Addon()
Player = xbmc.Player()

#This is done because we can not import ws4py from resources/lib directly
__path__ = Addon.getAddonInfo('path')
sys.path.insert(1,os.path.join( __path__ ,'resources/lib'))

#This import available only after adding sys.path
from ws4py.client.threadedclient import WebSocketClient

Dialog = xbmcgui.Dialog()
__scriptname__ = Addon.getAddonInfo('name')


class xbmc_log:
    @staticmethod
    def log(message, debuglevel=xbmc.LOGDEBUG):
        xbmc.log("LG TV PowerOff Screensaver :: " + str(message), debuglevel)

class LGTVNetworkShutdownScreensaver():
    TV_TYPE_2015 = '0'
    TV_TYPE_2012 = '1'
    TV_TYPE_2011 = '2'

    ip_address = '0.0.0.0'
    tv_type = '0'
    timeout = 10
    timeout_timer = None
    cli = None
    def __init__(self):
        _tv_type = Addon.getSetting('tv_type')
        if _tv_type != '':
            self.tv_type = _tv_type
        ip_address = Addon.getSetting('ip_address')
        if ip_address != '':
            self.ip_address = ip_address

        self.timeout_timer = threading.Timer(self.timeout,self.timeout_timer_fired)
        xbmc_log.log("Tv type is: " + self.tv_type)
        if self.tv_type == self.TV_TYPE_2015:
            xbmc_log.log("Running timer")
            self.timeout_timer.start()
            xbmc_log.log("Creating shutdowneer")
            try:
                self.cli = LGTVNetworkShutdown2015(ip_address)
            except RuntimeWarning as detail:
                xbmc_log.log('{W}:' + detail.message)
        elif self.tv_type == self.TV_TYPE_2012:
            xbmc_log.log("Running timer")
            self.timeout_timer.start()
            xbmc_log.log("Creating shutdowneer")
            try:
                self.cli = LGTVNetworkShutdown2012(ip_address)
            except RuntimeWarning as detail:
                xbmc_log.log('{W}:' + detail.message)
        elif self.tv_type == self.TV_TYPE_2011:
            xbmc_log.log("Running timer")
            self.timeout_timer.start()
            xbmc_log.log("Creating shutdowner")
            try:
                self.cli = LGTVNetworkShutdown2011(ip_address)
            except RuntimeWarning as detail:
                xbmc_log.log('{W}:' + detail.message)
            except Exception as e:
                xbmc_log.log('Error: ' + str(e))
        else:
            xbmc_log.log("Ignoring TV type" + str(self.tv_type))
        xbmc_log.log("finished")
        self.exit()


    def timeout_timer_fired(self):
        xbmc_log.log("Timer fired!")
        self.timeout_timer.cancel()
        try:
            self.cli.close()
        except:
            pass

    def exit(self):
        xbmc_log.log("Exiting LGTVNetworkShutdownScreensaver")
        try:
            self.timeout_timer.cancel()
        except:
            pass
        try:
            self.cli.close()
        except:
            pass
        try:
            del self.cli
        except:
            pass


class Screensaver(xbmcgui.WindowXMLDialog):
    shutter = None
    class ExitMonitor(xbmc.Monitor):

        def __init__(self, exit_callback):
            self.exit_callback = exit_callback

        def onScreensaverDeactivated(self):
            xbmc_log.log('ExitMonitor: sending exit_callback')
            self.exit_callback()

    def onInit(self):
        xbmc_log.log('Screensaver: onInit')
        self.monitor = self.ExitMonitor(self.exit)
        self.shutter = LGTVNetworkShutdownScreensaver()

    def exit(self):
        xbmc_log.log('Screensaver: Exit requested')
        try:
            self.shutter.exit()
        except:
            pass
        try:
            del self.monitor
        except:
            pass
        self.close()


class LGTVNetworkShutdown2012:
    PAIRING_KEY_PARAMETER_NAME = 'pairing_key_2012'
    HTTP_HEADERS = {"Content-Type": "application/atom+xml"}
    COMMAND_KEY_POWER = str(1) #Refer to http://developer.lgappstv.com/TV_HELP/index.jsp?topic=%2Flge.tvsdk.references.book%2Fhtml%2FUDAP%2FUDAP%2FAnnex+A+Table+of+virtual+key+codes+on+remote+Controller.htm
    COMMAND_KEY_ESM  = str(409)
    COMMAND_KEY_DOWN = str(13)
    COMMAND_KEY_OK   = str(20)
    HTTP_TIMEOUT = 3

    @property
    def client_key(self):
        key = "000000"
        try:
            key_tmp = xbmcaddon.Addon().getSetting(self.PAIRING_KEY_PARAMETER_NAME)
            xbmc_log.log("Pairing key read: " + key_tmp, xbmc.LOGDEBUG)
            if key_tmp != '':
                key = key_tmp
        except:
            xbmc_log.log("Unable to read pairing key", xbmc.LOGERROR)
        return key

    def check_connection(self, ip_address):
        try:
            connection_url = 'http://' + ip_address + ':8080'
            xbmc_log.log("Checking connection to " + connection_url )
            response=urllib2.urlopen(connection_url,timeout=3)
            xbmc_log.log("Got response, code = " + str(response.getcode()))
            if (response.getcode() == 404):
                xbmc_log.log("Check passed, 404 expected {1}")
                return True
            else:
                xbmc_log.log("Check failed, response not as expected")
                Dialog.notification("LG TV 2012-2014","Seems this is is not TV")
                return False
        except urllib2.HTTPError as err:
            if err.code == 404:
                xbmc_log.log("Check passed, 404 expected {2}")
                return True
            else:
                xbmc_log.log("Check failed, response is not as expected" + str(err.code))
                Dialog.notification("LG TV 2012-2014","Seems this is is not TV")
                return False
        except urllib2.URLError as err:
            Dialog.notification("LG TV 2012-2014","Connection failed. Maybe IP or type is incorrect?")
            xbmc_log.log("Check failed, URLError")
        return False

    def check_registration(self,ip_address):
        data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type><value>" + self.client_key + "</value></auth>"
        try:
            request = urllib2.Request('http://'+ip_address+':8080/roap/api/auth',data=data,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            print(response.read())
            return True
        except urllib2.HTTPError as err:
            if err.code == 401:
                xbmc_log.log("Wrong key supplied: " + self.client_key)
                Dialog.notification("LG TV 2012-2014","Go to settings to set up key")
                return False
            else:
                xbmc_log.log("Unexpected response code " + str(err.code))
        except urllib2.URLError:
            xbmc_log.log("Error checking registration: unable to connect or make a request {URLError)")
            return False

    def send_turn_off_command(self,ip_address):
        bIsMusicModeEnabled = ( Addon.getSetting("music_mode_2012") == "true" )
        bIsInMusicMode = ( Player.isPlayingAudio() == 1 )
        xbmc_log.log("music_mode_2012:" + str(Addon.getSetting("music_mode_2012")) + "; bIsMusicModeEnabled:" + str(bIsMusicModeEnabled) + "; bIsInMusicMode:" + str(bIsInMusicMode) + "; Player.isPlayingAudio():" + str(Player.isPlayingAudio()) + "; (bIsMusicModeEnabled and bIsInMusicMode): " + str((bIsMusicModeEnabled and bIsInMusicMode)))
        if (not (bIsMusicModeEnabled and bIsInMusicMode) ):
            xbmc_log.log("Sending TURN OFF command")
            return self.send_command(ip_address,self.COMMAND_KEY_POWER)
        else:
            i = int(float(Addon.getSetting("music_mode_2012_value")))
            xbmc_log.log("Sending ESM MENU command")
            self.send_command(ip_address,self.COMMAND_KEY_ESM)
            while i > 0 :
                xbmc_log.log("Sending DOWN command. i=" + str(i))
                self.send_command(ip_address,self.COMMAND_KEY_DOWN)
                i = i - 1
            xbmc_log.log("Sending OK command")
            return self.send_command(ip_address,self.COMMAND_KEY_OK);

    def send_command(self,ip_address,command):
        data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command><name>HandleKeyInput</name><value>" + command + "</value></command>"
        try:
            request = urllib2.Request('http://'+ip_address+':8080/roap/api/command',data=data,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            Dialog.notification("LG TV 2012-2014","Command sent")
            xbmc_log.log("Command sent")
            time.sleep(1);
            return True
        except urllib2.HTTPError as err:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {HTTPErrror): " + str(err.code))
            return False
        except urllib2.URLError:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {URLError)")
            return False

    def __init__(self, ip_address):
        if self.check_connection(ip_address) == True:
            if self.check_registration(ip_address) == True:
                if self.send_turn_off_command(ip_address) == True:
                    xbmc_log.log("Successfully sent PWR_OFF")
                else:
                    raise RuntimeWarning('Unable to send PWR_OFF')
            else:
                raise RuntimeWarning('Unable to check registration - possibly wrong key')
        else:
            raise RuntimeWarning('Unable to check connection')

    def close(self):
        pass

class LGTVNetworkShutdown2015(WebSocketClient):
    _msg_id = 0
    _registered = 0
    _power_off_sent = 0
    PAIRING_KEY_PARAMETER_NAME = 'pairing_key_2015'

    def send(self, payload, binary=False):
        self._msg_id = self._msg_id+1
        xbmc_log.log("Sending data to TV" + payload, xbmc.LOGDEBUG)
        super(LGTVNetworkShutdown2015,self).send(payload,binary)
    def save_pairing_key(self, key):
        try:
           xbmcaddon.Addon().setSetting(self.PAIRING_KEY_PARAMETER_NAME,key)
           xbmc_log.log("Pairing key saved: " + key, xbmc.LOGDEBUG)
        except:
            xbmc_log.log("Unable to save pairng key", xbmc.LOGERROR)
    @property
    def client_key(self):
        key = "123"
        try:
            key = xbmcaddon.Addon().getSetting(self.PAIRING_KEY_PARAMETER_NAME)
            xbmc_log.log("Pairing key read: " + key, xbmc.LOGDEBUG)
        except:
            xbmc_log.log("Unable to read pairing key", xbmc.LOGERROR)
        return key
    @property
    def register_string(self):
        key = self.client_key
        if key == "":
            register_string = json.JSONEncoder().encode(
                {
                    "type" : "register",
                    "id" : "register_" + str(self._msg_id),
                    "payload" : {
                        "pairingType" : "PROMPT",
                        "manifest" : {
                            "permissions": [
                                "CONTROL_POWER"
                            ]
                        }
                    }
                }
            )
        else:
            register_string = json.JSONEncoder().encode(
                {
                    "type" : "register",
                    "id" : "register_" + str(self._msg_id),
                    "payload" : {
                        "pairingType" : "PROMPT",
                        "client-key" : key,
                        "manifest" : {
                            "permissions": [
                                "CONTROL_POWER"
                            ]
                        }
                    }
                }
            )
        xbmc_log.log("Register string is" + register_string, xbmc.LOGDEBUG)
        return  register_string
    def opened(self):
        xbmc_log.log("Connection to TV opened", xbmc.LOGDEBUG)
        self._msg_id = 0
        self.send(self.register_string)
    def closed(self, code, reason=None):
        xbmc_log.log("Connection to TV closed : " + str(code) + "(" + reason + ")", xbmc.LOGDEBUG)
    def received_message(self, message):
        xbmc_log.log("Message received : (" + str(message) + ")", xbmc.LOGDEBUG)
        if message.is_text:
            response = json.loads(message.data.decode("utf-8"),"utf-8" )
            if 'client-key' in response['payload']:
                self.save_pairing_key(response['payload']['client-key'])
            if response['type'] == 'registered':
                xbmc_log.log("State changed to REGISTERED", xbmc.LOGDEBUG)
                self._registered = 1
            if self._registered == 0 and response['type'] == 'error':
                xbmc_log.log("Pairing error " + str(response['error']), xbmc.LOGERROR)
            if self._power_off_sent == 0 and self._registered == 1:
                xbmc_log.log("Sending POWEROFF", xbmc.LOGDEBUG)
                self.send_power_off()
                self.close()
        else:
            xbmc_log.log("Unreadable message", xbmc.LOGDEBUG)

    def send_power_off(self):
        power_off_string = json.JSONEncoder().encode(
               {
                "type" : "request",
                "id" : "request_" + str(self._msg_id),
                "uri" : "ssap://system/turnOff",
                "payload" : {
                    "client-key" : self.client_key
                }
            }
        )
        self.send(power_off_string)
        self._power_off_sent = 1
        Dialog.notification("LG TV 2015+","Sent command to turn off TV")
        xbmc_log.log("Sent POWEROFF successfully", xbmc.LOGDEBUG)
    @property
    def handshake_headers(self):
        """
        Should overload this, because LG TVs do not operate with Origin correctly
        """
        return [(p, v)
                   for p,v in super(LGTVNetworkShutdown2015,self).handshake_headers
                   if p != "Origin"
               ]
    def __init__(self,ip_address):
        xbmc_log.log("Initing")
        if self.check_connection(ip_address):
            connection_string = 'ws://' + ip_address + ':3000'
            xbmc_log.log("Connection string is [" + connection_string+ "]", xbmc.LOGDEBUG)
            super(LGTVNetworkShutdown2015,self).__init__(connection_string,protocols=['http-only', 'chat'])
            try:
                self.connect()
            except:
                raise RuntimeWarning('Unable to estabilish connection')
                return
            self.run_forever()
        else:
            Dialog.notification("LG TV 2015","Connection failed. Maybe IP or type is incorrect?")
            raise RuntimeWarning('Unable to test connection')
    def check_connection(self, ip_address):
        try:
            connection_url = 'http://' + ip_address + ':3000'
            xbmc_log.log("Checking connection to " + connection_url )
            response=urllib2.urlopen(connection_url,timeout=3)
            xbmc_log.log("Check passed")
            return True
        except urllib2.URLError as err:
            xbmc_log.log("Check failed")
        return False

class LGTVNetworkShutdown2011(WebSocketClient):
    PAIRING_KEY_PARAMETER_NAME = 'pairing_key_2011'
    HTTP_HEADERS = {"Content-Type": "application/atom+xml"}
    COMMAND_KEY_POWER = str(8) 
    HTTP_TIMEOUT = 10

    @property
    def client_key(self):
        key = "000000"
        try:
            key_tmp = xbmcaddon.Addon().getSetting(self.PAIRING_KEY_PARAMETER_NAME)
            xbmc_log.log("Pairing key read: " + key_tmp, xbmc.LOGDEBUG)
            if key_tmp != '':
                key = key_tmp
        except:
            xbmc_log.log("Unable to read pairing key", xbmc.LOGERROR)
        return key

    def check_connection(self, ip_address):
        try:
            self.sessionID = ""
            connection_url = 'http://' + ip_address + ':8080'
            xbmc_log.log("Checking connection to " + connection_url )
            
            request = urllib2.Request(connection_url,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            xbmc_log.log("Got response, code = " + str(response.getcode()))
            if (response.getcode() == 404 or response.getcode() == 406):
                xbmc_log.log("Check passed, "+str(response.getcode())+" expected {1}")
                return True
            else:
                xbmc_log.log("Check failed, response not as expected")
                Dialog.notification("LG TV 2011","Seems this is is not a 2011 TV")
                return False
        except urllib2.HTTPError as err:
            if err.code == 404 or err.code == 406:
                xbmc_log.log("Check passed, "+str(err.code)+" expected {2}")
                return True
            else:
                xbmc_log.log("Check failed, response is not as expected" + str(err.code))
                Dialog.notification("LG TV 2011","Seems this is is not a 2011 TV")
                return False
        except urllib2.URLError as err:
            Dialog.notification("LG TV 2011","Connection failed. Maybe IP or type is incorrect?")
            xbmc_log.log("Check failed, URLError")
        return False

    def getSessionString(self, responseStr):
        try:
            tree = etree.XML(responseStr)
            self.sessionID = tree.find('session').text
            xbmc_log.log("Found SessionID:"+self.sessionID)
            return True
        except Exception as e:
            self.sessionID = ""
            xbmc_log.log("Did not find session ID " + str(e))
            return False

    def check_registration(self,ip_address):
        #ignore following
        if len(self.client_key)>1:
            data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type><value>" + self.client_key + "</value></auth>"
        else:
            data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><auth><type>AuthReq</type></auth>" #display key at the TV
            
        try:
            url = 'http://'+ip_address+':8080/hdcp/api/auth'
            request = urllib2.Request(url,data=data,headers=self.HTTP_HEADERS)
            xbmc_log.log(url)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            responseStr = response.read()
            xbmc_log.log("No errors during registration check"+responseStr)                    

            ok = self.getSessionString(responseStr)
                        
            return ok
        except urllib2.HTTPError as err:
            if err.code == 401:
                xbmc_log.log("Wrong key supplied: " + self.client_key)
                Dialog.notification("LG TV 2011","Go to settings to set up key")
                return False
            else:
                xbmc_log.log("Unexpected response code " + str(err.code))
        except urllib2.URLError:
            xbmc_log.log("Error checking registration: unable to connect or make a request {URLError)")
            return False

    def send_turn_off_command(self,ip_address):                
        xbmc_log.log("Sending TURN OFF command")
        
        ok = False
        isTvStillOn = True
        for i in range(3): #try 3 times to shutdown TV (sometimes the shutdown command is not accepted for the first time. Do not know why)
            time.sleep(1)
            xbmc_log.log("Send Command")
            ok=self.send_command(ip_address,self.COMMAND_KEY_POWER)
            xbmc_log.log("Command sent. Now wait...")
            time.sleep(4) #wait for TV to switch off

            xbmc_log.log("Check if TV is still on")
            isTvStillOn = self.check_registration(ip_address)            

            if not isTvStillOn:
                xbmc_log.log("TV is off. Successful.")
                break
            else:
                xbmc_log.log("TV is still on. Retry...")                

        return ok

    def send_command(self,ip_address,command):
        #data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command><name>HandleKeyInput</name><value>" + command + "</value></command>"
        data = "<?xml version=\"1.0\" encoding=\"utf-8\"?><command><session>" + self.sessionID  + "</session><type>HandleKeyInput</type><value>" + command + "</value></command>"
        xbmc_log.log(data)
        try:
            request = urllib2.Request('http://'+ip_address+':8080/hdcp/api/dtv_wifirc',data=data,headers=self.HTTP_HEADERS)
            response = urllib2.urlopen(request, timeout=self.HTTP_TIMEOUT)
            Dialog.notification("LG TV 2011","Command sent")
            xbmc_log.log("Command sent")
            time.sleep(1);
            return True
        except urllib2.HTTPError as err:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {HTTPErrror): " + str(err.code))
            return False
        except urllib2.URLError:
            xbmc_log.log("Error sending PWR_OFF: unable to connect or make a request {URLError)")
            return False

    def __init__(self, ip_address):
        if self.check_connection(ip_address) == True:
            if self.check_registration(ip_address) == True:
                if self.send_turn_off_command(ip_address) == True:
                    xbmc_log.log("Successfully sent PWR_OFF")
                else:
                    raise RuntimeWarning('Unable to send PWR_OFF')
            else:
                raise RuntimeWarning('Unable to check registration - possibly wrong key')
        else:
            raise RuntimeWarning('Unable to check connection')

    def close(self):
        pass



if __name__ == '__main__':
    if 'show_help' in sys.argv:
        raise NotImplementedError()
    else:
        screensaver_gui = Screensaver("screensaver-display.xml",__path__,"default")
        screensaver_gui.doModal()
        del screensaver_gui
        del Addon
        del Dialog
        xbmc_log.log('Screensaver deleted')
        sys.modules.clear()

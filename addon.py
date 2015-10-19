import sys
from ws4py.client.threadedclient import WebSocketClient
import time
import json
import xbmcgui
import xbmcaddon
import xbmc
import urllib2
import getopt

class LGTVNetworkShutdownScreensaver(WebSocketClient):
    _msg_id = 0
    _registered = 0
    _power_off_sent = 0
    PairingOnly = False
    def send(self, payload, binary=False):
        self._msg_id = self._msg_id+1
        xbmc.log("Sending data to TV" + payload, xbmc.LOGDEBUG)
        super(LGTVNetworkShutdownScreensaver,self).send(payload,binary)
    def save_pairing_key(self, key):
        try:
           xbmcaddon.Addon().setSetting('pairing_key',key)
           xbmc.log("Pairing key saved: " + key, xbmc.LOGDEBUG)
        except:
            xbmc.log("Unable to save pairng key", xbmc.LOGERROR)
    @property
    def client_key(self):
        key = "123"
        try:
            key = xbmcaddon.Addon().getSetting('pairing_key')
            xbmc.log("Pairing key read: " + key, xbmc.LOGDEBUG)
        except:
            xbmc.log("Unable to read pairing key", xbmc.LOGERROR)
        return key
    @property
    def register_string(self):
        key = self.client_key
        if key == "" or self.PairingOnly == True:
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
            ##register_string = register_string.replace("%CLIENTKEYPLACEHOLDER%","");
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
            ##register_string = register_string.replace("%CLIENTKEYPLACEHOLDER%","\"client-key\":\"" + key + "\",");
        xbmc.log("Register string is" + register_string, xbmc.LOGDEBUG)
        return  register_string
    def opened(self):
        xbmc.log("Connection to TV opened", xbmc.LOGDEBUG)
        self.msg_id = 0
        self.send(self.register_string)
    def closed(self, code, reason=None):
        xbmc.log("Connection to TV closed : " + str(code) + "(" + reason + ")", xbmc.LOGDEBUG)
    def received_message(self, message):
        xbmc.log("Message received : (" + str(message) + ")", xbmc.LOGDEBUG)
        if message.is_text:
            response = json.loads(message.data.decode("utf-8"),"utf-8" )
            if 'client-key' in response['payload']:
                    self.save_pairing_key(response['payload']['client-key'])
                    if self.PairingOnly:
                        xbmcgui.Dialog().ok("Pairing key received!","Press OK to continue");
            if response['type'] == 'registered':
                xbmc.log("State changed to REGISTERED", xbmc.LOGDEBUG)
                self._registered = 1
                if self.PairingOnly == True:
                    xbmcgui.Dialog().ok("Pairing successful!","Now you can use the screensaver");
                    self.close();
            if self._registered == 0 and response['type'] == 'error':
                xbmc.log("Pairing error " + str(response['error']), xbmc.LOGERROR)
                if self.PairingOnly == True:
                    xbmcgui.Dialog().ok("Pairing error",str(response['error']));
                    self.close();
            if self._power_off_sent == 0 and self._registered == 1 and self.PairingOnly == False:
                xbmc.log("Sending POWEROFF", xbmc.LOGDEBUG)
                self.send_power_off()
            if self._power_off_sent == 1:
                xbmc.log("TV reports POWEROFF received", xbmc.LOGDEBUG)
                self.close(1000,"PowerOff sent")

        else:
            xbmc.log("Unreadable message", xbmc.LOGDEBUG)



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
        try:
            xbmcgui.Dialog().notification("TV turned off","Sent command to turn off TV")
        except:
            pass
        xbmc.log("Sent POWEROFF successfully", xbmc.LOGDEBUG)
    @property
    def handshake_headers(self):
        """
        Should overload this, because LG TVs do not operate with Origin correctly
        """
        return [(p, v)
                   for p,v in super(LGTVNetworkShutdownScreensaver,self).handshake_headers
                   if p != "Origin"
               ]
    def onScreensaverDeactivated(self):
        xbmc.log("OnScreensaverDeactivated!", xbmc.LOGDEBUG)
        try:
            self.close()
        except:
            pass
    xbmc.log("New shutdowner started", xbmc.LOGDEBUG)


def check_connection(address):
    try:
        response=urllib2.urlopen('http://' + address + ':3000',timeout=3)
        return True
    except urllib2.URLError as err:
        pass
    return False


def Start(pairing_from_gui):
    tv_ip_address = ""
    try:
        tv_ip_address = xbmcaddon.Addon().getSetting('lgtvipaddress')
    except:
        if pairing_from_gui == True:
            xbmcgui.Dialog().ok("Unable to read IP address from settings","Please save settings before pairing")
        xbmc.log("Unable to read IP address of TV from settings", xbmc.LOGERROR)
    if len(tv_ip_address) <= 0:
        if pairing_from_gui == True:
            xbmcgui.Dialog().ok("Unable to read IP address from settings","Please save settings before pairing")
        xbmc.log("IP address of TV from settings is not suitable", xbmc.LOGERROR)
    elif (check_connection(tv_ip_address) == True):
        connection_string = 'ws://' + tv_ip_address + ':3000'
        xbmc.log("Connection string is [" + connection_string+ "]", xbmc.LOGDEBUG)
        ws = LGTVNetworkShutdownScreensaver(connection_string,protocols=['http-only', 'chat'])
        ws.PairingOnly = pairing_from_gui
        try:
            xbmc.log("Connecting...", xbmc.LOGDEBUG)
            ws.connect()
            xbmc.log("Connected!", xbmc.LOGDEBUG)
            ws.run_forever()
            ws.close()
        except:
            if pairing_from_gui == True:
                xbmcgui.Dialog().ok("Could not connect to TV","Could not connect to TV")
            xbmc.log("Error while connecting to TV", xbmc.LOGERROR)
        del ws
    else:
        xbmcgui.Dialog().notification("TV is not available over network", "Possibly unsupported model or wrong configuration of screensaver addon?",xbmcgui.NOTIFICATION_WARNING, 30000 ,False)
        xbmc.log("Seems that TV is not available over network", xbmc.LOGDEBUG)

try:
    if 'pairing_only' in sys.argv:
        xbmc.log("1", xbmc.LOGDEBUG)
        old_ip_address = ""
        try:
            old_ip_address = str(xbmcaddon.Addon().getSetting("lgtvipaddress"))
        except
            pass
        xbmc.log("1-1", xbmc.LOGDEBUG)
        new_ip_address = xbmcgui.Dialog().input("Enter IP address of your TV",old_ip_address,type=xbmcgui.INPUT_IPADDRESS)
        xbmc.log("2" , xbmc.LOGDEBUG)
        if new_ip_address != '':
            xbmc.log("22" , xbmc.LOGDEBUG)
            xbmcgui.Dialog().ok("Get ready!","Please press OK and be ready to confirm pairing on your TV remote")
            xbmc.log("23" , xbmc.LOGDEBUG)
            xbmcaddon.Addon().setSetting("pairing_key",'undefined')
            xbmc.log("24" , xbmc.LOGDEBUG)
            xbmcaddon.Addon().setSetting("lgtvipaddress",new_ip_address)
            xbmc.log("25" , xbmc.LOGDEBUG)

            Start(True)
            xbmc.log("26" , xbmc.LOGDEBUG)
        else:
            xbmc.log("31" , xbmc.LOGDEBUG)
            xbmcgui.Dialog().ok("Pairing was cancelled","Input was cancelled")
    else:
        xbmc.log("Running in screensaver mode", xbmc.LOGDEBUG)
        Start(False)
except:
    xbmc.log("Error in getopt" + str(sys.exc_info()[0]) , xbmc.LOGDEBUG)
    Start(False)





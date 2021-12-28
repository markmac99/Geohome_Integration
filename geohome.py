# -*- coding: utf-8 -*-
"""
Script to intergrate GeoTogether meter readings into the Openhab
Still needs some work to handle errors

"""
import requests
import json
import threading
import time
from datetime import datetime
#from openhab import OpenHAB
import os

BASE_URL = 'https://api.geotogether.com/'
LOGIN_URL = 'usersservice/v2/login'
DEVICEDETAILS_URL = 'api/userapi/v2/user/detail-systems?systemDetails=true'
LIVEDATA_URL = 'api/userapi/system/smets2-live-data/'
PERIODICDATA_URL = 'api/userapi/system/smets2-periodic-data/'
USERNAME = 'mark.jm.mcintyre@cesmail.net'
PASSWORD = 'Wombat33geo!'
LOG_DIRECTORY = './logs/'


#openhab_URL = 'xxxxxxxxxxxx'
#openhab = OpenHAB(openhab_URL)
#HouseElectricityPower = openhab.get_item('HouseElectricityPower')
#HouseGasMeterReading = openhab.get_item('HouseGasMeterReading')
#HouseGasPower = openhab.get_item('HouseGasPower')

class GeoHome(threading.Thread):

    # Thread class with a _stop() method.
    # The thread itself has to check
    # regularly for the stopped() condition.

    def __init__(self, varUserName, varPassword):

        log = "Start Intalising: " + str(datetime.now())
        threading.Thread.__init__(self)
        #super(Thread, self).__init__()
        self._stop = threading.Event()
        self.varUserName = varUserName
        self.varPassword = varPassword
        self.headers = ""
        self.deviceId = ""
        self.authorise()
        self.getDevice()
        log = log + os.linesep + "End Intalising: " + str(datetime.now())
        with open(LOG_DIRECTORY+"GeoHomeLog"+time.strftime("%Y%m%d")+".json", mode='a+', encoding='utf-8') as f:
            f.write(log + os.linesep)
        self.ttlcountdown = 0

    def authorise(self):
        data = {'identity': self.varUserName, 'password': self.varPassword}
        r = requests.post(BASE_URL+LOGIN_URL,
                          data=json.dumps(data), verify=False)
        authToken = json.loads(r.text)['accessToken']
        self.headers = {"Authorization": "Bearer " + authToken}
        return

    def getDevice(self):
        r = requests.get(BASE_URL+DEVICEDETAILS_URL, headers=self.headers)
        self.deviceId = json.loads(r.text)['systemRoles'][0]['systemId']
        print('Device Id:' + self.deviceId)
        return

    # function using _stop function
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while True:
            if self.stopped():
                return

            log = "Start Api Call: " + str(datetime.now())

            r = requests.get(BASE_URL+LIVEDATA_URL +
                             self.deviceId, headers=self.headers)
            if r.status_code != 200:
                # Not successful. Assume Authentication Error
                log = log + os.linesep + \
                    "Request Status Error:" + str(r.status_code)
                # Reauthenticate. Need to add more error trapping here in case api goes down.
                self.authorise()
                self.getDevice()
            else:
                #log = log + os.linesep + json.dumps(r.text)
                power_dict = json.loads(r.text)['power']
                outfnam = datetime.now().strftime('live-%Y%m.json')
                with open(outfnam, 'a') as outf:
                    outf.write('{}\n'.format(r.text))

                # Try to find the electrivity usage
                try:
                    Electrcity_usage = (
                        [x for x in power_dict if x['type'] == 'ELECTRICITY'][0]['watts'])
                except:
                    # Cant find Electricity in list. Add to log file but do nothing else
                    log = log + os.linesep + "No Electricity reading found"
                else:
                    # Code executed ok so update the usage
                    #HouseElectricityPower.state= Electrcity_usage
                    #log = log + os.linesep + "Electrcity_usage:"+str(Electrcity_usage)
                    pass
                try:
                    Gas_usage = (
                        [x for x in power_dict if x['type'] == 'GAS_ENERGY'][0]['watts'])
                except:
                    # Cant find Gas in list. Add to log file but do nothing else
                    log = log + os.linesep + "No Gas reading found"
                else:
                    # Update Gas reading 
                    # log = log + os.linesep + "Gas Usage:" + str(Gas_usage)
                    pass

            with open(LOG_DIRECTORY+"GeoHomeLog"+time.strftime("%Y%m%d")+".json", mode='a+', encoding='utf-8') as f:
                f.write(log + os.linesep)
            if self.ttlcountdown == 0:
                r = requests.get(BASE_URL+PERIODICDATA_URL +
                                self.deviceId, headers=self.headers)
                if r.status_code != 200:
                    # Not successful. Assume Authentication Error
                    log = log + os.linesep + \
                        "Request Status Error:" + str(r.status_code)
                    # Reauthenticate. Need to add more error trapping here in case api goes down.
                    self.authorise()
                    self.getDevice()
                else:
                    self.ttlcountdown = json.loads(r.text)['ttl']
                    outfnam = datetime.now().strftime('peri-%Y%m.json')
                    with open(outfnam, 'a') as outf:
                        outf.write('{}\n'.format(r.text))
                    print(r.text)

            time.sleep(10)
            self.ttlcountdown -= 10


t1 = GeoHome(USERNAME, PASSWORD)
t1.start()
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    t1.stop()

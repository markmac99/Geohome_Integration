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
from openhab import OpenHAB
import os

from loadconfig import username, getGeohomePass, getOpenhabURL

import backoff

BASE_URL = 'https://api.geotogether.com/'
LOGIN_URL = 'usersservice/v2/login'
DEVICEDETAILS_URL = 'api/userapi/v2/user/detail-systems?systemDetails=true'
LIVEDATA_URL = 'api/userapi/system/smets2-live-data/'
PERIODICDATA_URL = 'api/userapi/system/smets2-periodic-data/'
LOG_DIRECTORY = './logs/'
num_max_retries = 20


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=5,
    giveup=lambda e: e.response is not None and e.response.status_code < 500
)
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
        self.writeLogEntry(log)
        self.ttlcountdown = 0

    def authorise(self):
        data = {'identity': self.varUserName, 'password': self.varPassword}
        r = requests.post(BASE_URL+LOGIN_URL,
                          data=json.dumps(data), verify=False)
        # print(r.text)
        authToken = json.loads(r.text)['accessToken']
        self.headers = {"Authorization": "Bearer " + authToken}
        return

    def getDevice(self):
        r = requests.get(BASE_URL+DEVICEDETAILS_URL, headers=self.headers, timeout=10)
        self.deviceId = json.loads(r.text)['systemRoles'][0]['systemId']
        print('Device Id:' + self.deviceId)
        return
    
    def writeLogEntry(self, msg, live=True):
        if live is True:
            with open(LOG_DIRECTORY+"GHlive"+time.strftime("%Y%m%d")+".log", mode='a+', encoding='utf-8') as f:
                f.write(msg + '\n')
        else:
            with open(LOG_DIRECTORY+"GHperi"+time.strftime("%Y%m%d")+".log", mode='a+', encoding='utf-8') as f:
                f.write(msg + '\n')

    # function using _stop function
    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

    def run(self):
        while True:
            if self.stopped():
                return

            try: 
                openhab = OpenHAB(getOpenhabURL())
                HouseElectricityPower = openhab.get_item('HouseElectricityPower')
                HouseElectricityMeterReading = openhab.get_item('HouseElectricityMeterReading')
                HouseGasMeterReading = openhab.get_item('HouseGasMeterReading')
                HouseGasPower = openhab.get_item('HouseGasPower')
                HouseMeterTimestamp = openhab.get_item('HouseMeterTimestamp')
                HousePowerTimestamp = openhab.get_item('HousePowerTimestamp')

                r = requests.get(BASE_URL+LIVEDATA_URL + self.deviceId, headers=self.headers)
                if r.status_code != 200:
                    # Not successful. Assume Authentication Error
                    log = "Request Status Error:" + str(r.status_code)
                    self.writeLogEntry(log)

                    # Reauthenticate. Need to add more error trapping here in case api goes down.
                    self.authorise()
                    self.getDevice()
                else:
                    power_dict = json.loads(r.text)['power']
                    powertime = int(json.loads(r.text)['powerTimestamp'])
                    HousePowerTimestamp.state = datetime.fromtimestamp(powertime)
                    #self.writeLogEntry(r.text)
                    # Try to find the electricity usage
                    try:
                        Electrcity_usage = (
                            [x for x in power_dict if x['type'] == 'ELECTRICITY'][0]['watts'])
                    except:
                        # Cant find Electricity in list. Add to log file but do nothing else
                        self.writeLogEntry('No Electricity reading found')
                    else:
                        # Code executed ok so update the usage
                        HouseElectricityPower.state = Electrcity_usage
                    try:
                        Gas_usage = (
                            [x for x in power_dict if x['type'] == 'GAS_ENERGY'][0]['watts'])
                    except:
                        # Cant find Gas in list. Add to log file but do nothing else
                        self.writeLogEntry('No Gas reading found')
                    else:
                        HouseGasPower.state = Gas_usage
                    self.writeLogEntry(f'{HousePowerTimestamp.state},{Electrcity_usage},{Gas_usage}')
            except Exception: 
                self.writeLogEntry('unable to connect for realtime data')
            if self.ttlcountdown == 0:
                try:
                    r = requests.get(BASE_URL+PERIODICDATA_URL + self.deviceId, headers=self.headers)
                    if r.status_code != 200:
                        # Not successful. Assume Authentication Error
                        log = "Request Status Error:" + str(r.status_code)
                        self.writeLogEntry(log, False)

                        # Reauthenticate. Need to add more error trapping here in case api goes down.
                        self.authorise()
                        self.getDevice()
                    else:
                        self.ttlcountdown = json.loads(r.text)['ttl']
                        #self.writeLogEntry(r.text)
                        powertime = int(json.loads(r.text)['totalConsumptionTimestamp'])
                        HouseMeterTimestamp.state = datetime.fromtimestamp(powertime)
                        power_dict = json.loads(r.text)['totalConsumptionList']
                        # Try to find the electrivity usage
                        try:
                            Electrcity_usage = (
                                [x for x in power_dict if x['commodityType'] == 'ELECTRICITY'][0]['totalConsumption'])
                        except:
                            # Cant find Electricity in list. Add to log file but do nothing else
                            self.writeLogEntry('No Electricity reading found', False)
                        else:
                            # Code executed ok so update the usage
                            HouseElectricityMeterReading.state = Electrcity_usage
                        try:
                            Gas_usage = (
                                [x for x in power_dict if x['commodityType'] == 'GAS_ENERGY'][0]['totalConsumption'])
                        except:
                            # Cant find Gas in list. Add to log file but do nothing else
                            self.writeLogEntry('No Gas reading found', False)
                        else:
                            HouseGasMeterReading.state = float(Gas_usage)/1000
                    self.writeLogEntry(f'{HouseMeterTimestamp.state},{Electrcity_usage},{Gas_usage}', False)
                except Exception:
                    self.writeLogEntry('unable to connect for periodic data', False)

            time.sleep(10)
            self.ttlcountdown -= 10


# main function
os.makedirs(LOG_DIRECTORY, exist_ok=True)
t1 = GeoHome(username, getGeohomePass())
t1.start()
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    t1.stop()

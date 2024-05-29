# copyright Mark McIntyre, 2024-

# script to capture electricit and gas meter data from the Geohome network

import requests
import json
import time
import datetime
import os
from openhab import OpenHAB
import logging

from loadconfig import username, getGeohomePass, getOpenhabURL

log = logging.getLogger('geohome')

BASE_URL = 'https://api.geotogether.com/'
LOGIN_URL = 'usersservice/v2/login'
DEVICEDETAILS_URL = 'api/userapi/v2/user/detail-systems?systemDetails=true'
LIVEDATA_URL = 'api/userapi/system/smets2-live-data/'
PERIODICDATA_URL = 'api/userapi/system/smets2-periodic-data/'


def connectGeohome():
    data = {'identity': username, 'password': getGeohomePass()}
    try:
        r = requests.post(BASE_URL+LOGIN_URL, data=json.dumps(data))
        authToken = json.loads(r.text)['accessToken']
        return {"Authorization": "Bearer " + authToken}
    except Exception as e:
        log.error(e)
        return False


def getDevice(authn):
    try:
        r = requests.get(BASE_URL+DEVICEDETAILS_URL, headers=authn, timeout=10)
        deviceId = json.loads(r.text)['systemRoles'][0]['systemId']
        log.info(f'Device Id: {deviceId}')
        return deviceId
    except Exception as e:
        log.error(e)
        return False


def updateOpenhabLive(powertime, elecval, gasval):
    try:
        openhab = OpenHAB(getOpenhabURL())
        HouseElectricityPower = openhab.get_item('HouseElectricityPower')
        HouseGasPower = openhab.get_item('HouseGasPower')
        HousePowerTimestamp = openhab.get_item('HousePowerTimestamp')
        HousePowerTimestamp.state = powertime
        HouseElectricityPower.state = round(elecval, 1)
        HouseGasPower.state = round(gasval, 1)
    except Exception as e:
        log.error('problem updating openhab realtime data')
        log.error(e)
    return 


def updateOpenhabMeters(electime, elecval, gastime, gasval):
    try:
        openhab = OpenHAB(getOpenhabURL())
        HouseElectricityMeterReading = openhab.get_item('HouseElectricityMeterReading')
        HouseGasMeterReading = openhab.get_item('HouseGasMeterReading')
        HouseMeterTimestamp = openhab.get_item('HouseMeterTimestamp')
        GasMeterTimestamp = openhab.get_item('GasMeterTimestamp')
        HouseMeterTimestamp.state = electime
        HouseElectricityMeterReading.state = round(elecval, 1)
        GasMeterTimestamp.state = gastime
        HouseGasMeterReading.state = round(gasval, 1)
    except Exception as e:
        log.error('problem updating openhab meter data')
        log.error(e)
    return 


def getLiveData():
    authn = connectGeohome()
    if not authn:
        return False, False, False
    deviceId = getDevice(authn)
    if not deviceId:
        return False, False, False
    try:
        r = requests.get(BASE_URL+LIVEDATA_URL + deviceId, headers=authn)
        if r.status_code != 200:
            # Not successful. Assume Authentication Error
            print(f'Request Status Error: {r.status_code}')
        else:
            power_dict = json.loads(r.text)['power']
            powertime = int(json.loads(r.text)['powerTimestamp'])
            try:
                elecval = ([x for x in power_dict if x['type'] == 'ELECTRICITY'][0]['watts'])
                log.info(f'elecval {elecval}')
            except Exception:
                log.info('No Electricity reading found')
            try:
                gasval = ([x for x in power_dict if x['type'] == 'GAS_ENERGY'][0]['watts'])
                log.info(f'gasval {gasval}')
            except Exception:
                log.info('No Gas reading found')
            try:
                powertime = datetime.datetime.fromtimestamp(powertime)
                log.info(f'HousePowerTimeStamp {powertime.strftime("%Y-%m-%dT%H:%M:%SZ")}')
            except Exception:
                log.info('invalid datestamp')
    except Exception: 
        log.info('unable to connect for realtime data')
    return powertime, elecval, gasval


def getMeterData():
    authn = connectGeohome()
    if not authn:
        return False, False, False
    deviceId = getDevice(authn)
    if not deviceId:
        return False, False, False
    try:
        r = requests.get(BASE_URL+PERIODICDATA_URL + deviceId, headers=authn)
        if r.status_code != 200:
            # Not successful. Assume Authentication Error
            log.info(f'Request Status Error: {r.status_code}')
        else:
            ttl = json.loads(r.text)['ttl']
            power_dict = json.loads(r.text)['totalConsumptionList']
            try:
                elecval = ([x for x in power_dict if x['commodityType'] == 'ELECTRICITY'][0]['totalConsumption'])
                electime = ([x for x in power_dict if x['commodityType'] == 'ELECTRICITY'][0]['readingTime'])
                log.info(f'elecval {elecval}')
            except Exception:
                log.info('No Electricity reading found')
            try:
                gasval = ([x for x in power_dict if x['commodityType'] == 'GAS_ENERGY'][0]['totalConsumption'])
                gastime = ([x for x in power_dict if x['commodityType'] == 'GAS_ENERGY'][0]['readingTime'])
                log.info(f'gasval {gasval}')
            except Exception:
                log.info('No Gas reading found')
    except Exception: 
        log.info('unable to connect for realtime data')
    electime = datetime.datetime.fromtimestamp(electime)
    gastime = datetime.datetime.fromtimestamp(gastime)
    return electime, elecval, gastime, float(gasval)/1000, ttl


if __name__ == '__main__':
    logpath = os.path.expanduser('~/logs')
    logname=os.path.join(logpath, 'geohome.log')
    log.setLevel(logging.INFO)
    fh = logging.FileHandler(logname)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    log.addHandler(fh)

    stopfile = '.stopgh'
    rtwait = 10
    ttlcountdown = 0
    while True:
        pt, ev, gv = getLiveData()
        if pt:
            log.info(f'{pt}, {ev}, {gv}')
            #updateOpenhabLive(pt, ev, gv)
        if ttlcountdown == 0:
            et, em, gt, gm, ttl = getMeterData()
            ttlcountdown = ttl
            log.info(f'{et}, {em}, {gt}, {gm}')
            updateOpenhabMeters(et, em, gt, gm)
        time.sleep(rtwait)
        if os.path.isfile(stopfile):
            os.remove(stopfile)
            log.info('exiting...')
            break

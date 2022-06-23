#
# python to analyse energy meter data and create graphs
#

import datetime
import json
import matplotlib.pyplot as plt
import pandas as pd


def graphCumReadings(ym):
    dts = []
    ele = []
    gas = []
    if ym == 0:
        ym = datetime.datetime.now().strftime('%Y%m')
    fname = 'peri-{}.json'.format(ym)
    jpgename = 'peri-ele-{}.jpg'.format(ym)
    jpggname = 'peri-gas-{}.jpg'.format(ym)
    csvfname = 'peri-{}.csv'.format(ym)
    with open(fname,'r') as inf:
        lis = inf.readlines()
    for li in lis:
        dta = json.loads(li.strip())
        dtstamp = datetime.datetime.fromtimestamp(dta['latestUtc'])
        power_dict = dta['totalConsumptionList']
        try:
            eleval = ([x for x in power_dict if x['commodityType']=='ELECTRICITY'][0]['totalConsumption'])
        except:
            eleval = 0
        else:
            eleval = float(eleval)
        try:
            gasval = ([x for x in power_dict if x['commodityType']=='GAS_ENERGY'][0]['totalConsumption'])
        except:
            gasval = 0
        else:
            gasval = float(gasval)/1000
        if dtstamp > datetime.datetime.fromtimestamp(0): 
            dts.append(dtstamp)
            ele.append(eleval)
            gas.append(gasval)
    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)
    plt.plot(dts, ele, label='Electricity')
    plt.xlabel('Time')
    plt.ylabel('kW')
    plt.title('Meter Readings')
    plt.show()
    plt.savefig(jpgename)
    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)
    plt.plot(dts, gas, label='Gas')
    plt.xlabel('Time')
    plt.ylabel('kW')
    plt.title('Meter Readings')
    plt.show()
    plt.savefig(jpggname)
    df = pd.DataFrame(list(zip(ele, gas)), columns=['ele','gas'], index=dts)
    df.to_csv(csvfname)
    return 


def graphLiveData(ym):

    dts = []
    ele = []
    gas = []
    if ym == 0:
        ym = datetime.datetime.now().strftime('%Y%m')

    fname = 'live-{}.json'.format(ym)
    jpgfname = 'live-{}.jpg'.format(ym)
    csvfname = 'live-{}.csv'.format(ym)

    with open(fname,'r') as inf:
        lis = inf.readlines()
    for li in lis:
        dtstamp = datetime.datetime.fromtimestamp(json.loads(li)['latestUtc'])
        power_dict = json.loads(li)['power']
        try:
            Electrcity_usage = (
                [x for x in power_dict if x['type'] == 'ELECTRICITY'][0]['watts'])
        except:
            eleval = 0
        else:
            eleval = float(Electrcity_usage)
        try:
            gas_usage = (
                [x for x in power_dict if x['type'] == 'GAS_ENERGY'][0]['watts'])
        except:
            gasval = 0
        else:
            gasval = float(gas_usage)
#        print(dtstamp.strftime('%Y-%m-%dT%H:%M:%S'), eleval, gasval )
        if dtstamp > datetime.datetime.fromtimestamp(0): 
            dts.append(dtstamp)
            ele.append(eleval)
            gas.append(gasval)

    plt.clf()
    fig = plt.gcf()
    fig.set_size_inches(11.6, 8.26)

    plt.plot(dts, ele, label='Electricity')
    plt.plot(dts, gas, label='Gas')
    plt.xlabel('Time')
    plt.ylabel('kW')
    plt.title('Home Energy Consumption')
    plt.show()
    plt.savefig(jpgfname)
    df = pd.DataFrame(list(zip(ele, gas)), columns=['ele','gas'], index=dts)
    df.to_csv(csvfname)
    return 


def printPeriodicData(ym):
    if ym == 0:
        fname = datetime.datetime.now().strftime('peri-%Y%m.json')
    else:
        fname = 'live-{}.json'.format(ym)
    with open(fname,'r') as inf:
        lastline = inf.readlines()[-1]
    jsondata = json.loads(lastline)
    dtstamp = datetime.datetime.fromtimestamp(jsondata['latestUtc'])
    # get price per unit (kWh)
    tariff = jsondata['activeTariffList']
    eprice = ([x for x in tariff if x['commodityType'] == 'ELECTRICITY'][0]['activeTariffPrice'])
    gprice = ([x for x in tariff if x['commodityType'] == 'GAS_ENERGY'][0]['activeTariffPrice'])

    print(dtstamp)

    # get daily, weekly and monthly spends
    elec = jsondata['currentCostsElec']
    ecostday = ([x for x in elec if x['duration'] == 'DAY'][0]['costAmount'])
    eamtday = ([x for x in elec if x['duration'] == 'DAY'][0]['energyAmount'])
    ecostwek = ([x for x in elec if x['duration'] == 'WEEK'][0]['costAmount'])
    eamtwek = ([x for x in elec if x['duration'] == 'WEEK'][0]['energyAmount'])
    ecostmth = ([x for x in elec if x['duration'] == 'MONTH'][0]['costAmount'])
    eamtmth = ([x for x in elec if x['duration'] == 'MONTH'][0]['energyAmount'])
    print('electicity costs')
    print('cost/unit {}'.format(eprice))
    print('cost per day/week/month', ecostday, ecostwek, ecostmth)
    print('energy per day/week/month', eamtday, eamtwek, eamtmth)

    gas = jsondata['currentCostsGas']
    gcostday = ([x for x in gas if x['duration'] == 'DAY'][0]['costAmount'])
    gamtday = ([x for x in gas if x['duration'] == 'DAY'][0]['energyAmount'])
    gcostwek = ([x for x in gas if x['duration'] == 'WEEK'][0]['costAmount'])
    gamtwek = ([x for x in gas if x['duration'] == 'WEEK'][0]['energyAmount'])
    gcostmth = ([x for x in gas if x['duration'] == 'MONTH'][0]['costAmount'])
    gamtmth = ([x for x in gas if x['duration'] == 'MONTH'][0]['energyAmount'])
    print('gas costs')
    print('cost/unit {}'.format(gprice))
    print('cost per day/week/month', gcostday, gcostwek, gcostmth)
    print('energy per day/week/month', gamtday, gamtwek, gamtmth)
    return 


if __name__ == '__main__':
    graphLiveData(0)
    printPeriodicData(0)
    graphCumReadings(0)
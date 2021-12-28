#
#
#

import datetime
import json
import matplotlib.pyplot as plt


def graphLiveData(ym):

    dts = []
    ele = []
    gas = []
    if ym == 0:
        fname = datetime.datetime.now().strftime('live-%Y%m.json')
    else:
        fname = 'live-{}.json'.format(ym)
    with open (fname,'r') as inf:
        lis = inf.readlines()
    for li in lis:
        dtstamp = datetime.datetime.fromtimestamp(json.loads(li)['latestUtc'])
        try:
            Electrcity_usage = (
                [x for x in power_dict if x['type'] == 'ELECTRICITY'][0]['watts'])
        except:
            eleval = 0
        else:
            eleval = float(Electrcity_usage)
        
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
        print(dtstamp.strftime('%Y-%m-%dT%H:%M:%S'), eleval, gasval )
        if dtstamp > datetime.datetime.fromtimestamp(0): 
            dts.append(dtstamp)
            ele.append(eleval)
            gas.append(gasval)

    plt.plot(dts, ele, label='Electricity')
    plt.plot(dts, gas, label='Gas')
    plt.xlabel('Time')
    plt.ylabel('kW')
    plt.title('Home Energy Consumption')
    plt.show()
    fname2 = datetime.datetime.now().strftime('live-%Y%m.jpg')
    plt.savefig(fname2)

if __name__ == '__main__':
    graphLiveData(0)

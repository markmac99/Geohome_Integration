# config file
import os

username = 'mark.jm.mcintyre@cesmail.net'


def getGeohomePass():
    passwordfile = os.path.expanduser('~/.ssh/geopass')
    with open(passwordfile) as inf:
        passwd = inf.readline().strip()
    return passwd


def getOpenhabURL():
    passwordfile = os.path.expanduser('~/.ssh/myohpass')
    with open(passwordfile) as inf:
        username = inf.readline().strip()
        passwd = inf.readline().strip()
    
    ohurl = 'https://{}:{}@myopenhab.org/rest'.format(username, passwd)
    return ohurl

# config file
import os

username = 'mark.jm.mcintyre@cesmail.net'
savelogs = False
openhab_URL ='http://themcintyres.ddns.net:8080/rest/'
#openhab_URL = 'http://wxsatpi:8080/rest'

def getpass():
    passwordfile = os.path.expanduser('~/.ssh/geopass')
    with open(passwordfile) as inf:
        passwd = inf.readline().strip()
    return passwd

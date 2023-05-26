

# See https://docs.python.org/3/library/configparser.html

import configparser
import sys

config = configparser.ConfigParser()
config.read('pyPlc.ini')

def getConfigValue(s):
    try:
        return config['general'][s]
    except:
        print("Error: seems we have a problem with pyPlc.ini, with entry " + s)
        print("How to fix: Try to use the docs/pyPlc.ini.template,")
        print(" copy it into the pyPlc's main folder,")
        print(" rename it to pyPlc.ini, and edit it for your needs.")
        sys.exit()

def getConfigValueBool(s):
    try:
        return config.getboolean('general', s)
    except:
        print("Error: seems we have a problem with pyPlc.ini, with entry " + s)
        print("How to fix: Try to use the docs/pyPlc.ini.template,")
        print(" copy it into the pyPlc's main folder,")
        print(" rename it to pyPlc.ini, and edit it for your needs.")
        sys.exit()

if __name__ == "__main__":
    print("Testing configmodule...")
    print(str(config.sections()))
    print(config['general']['mode'])
    for key in config['general']:
        print(key + " has value " + config['general'][key])
    print(config.getboolean('general', 'display_via_serial'))
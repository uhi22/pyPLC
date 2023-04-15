

# See https://docs.python.org/3/library/configparser.html

import configparser

config = configparser.ConfigParser()
config.read('pyPlc.ini')

def getConfigValue(s):
    return config['general'][s]

def getConfigValueBool(s):
    return config.getboolean('general', s)

if __name__ == "__main__":
    print("Testing configmodule...")
    print(str(config.sections()))
    print(config['general']['mode'])
    for key in config['general']:
        print(key + " has value " + config['general'][key])
    print(config.getboolean('general', 'display_via_serial'))
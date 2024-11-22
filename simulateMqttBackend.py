import paho.mqtt.client as mqtt
from configmodule import getConfigValue, getConfigValueBool

def mqtt_on_connect(client, userdata, flags, rc):
    client.subscribe(getConfigValue("mqtt_topic") + "/#")

def mqtt_on_message(client, userdata, msg):
    global simulatedInletVoltage
    if msg.topic == getConfigValue("mqtt_topic") + "/fsm_state":
        if "CableCheck" in msg.payload.decode("utf-8"):
            simulatedInletVoltage = 0
        if "PreCharging" in msg.payload.decode("utf-8"):
            client.publish(getConfigValue("mqtt_topic") + "/inlet_voltage", simulatedInletVoltage)
            simulatedInletVoltage = simulatedInletVoltage + 15
    elif msg.topic == getConfigValue("mqtt_topic") + "/pev_voltage":
        client.publish(getConfigValue("mqtt_topic") + "/inlet_voltage", msg.payload)
    elif msg.topic == getConfigValue("mqtt_topic") + "/pev_current":
        client.publish(getConfigValue("mqtt_topic") + "/target_current", msg.payload)

simulatedInletVoltage = 0
mqttclient = mqtt.Client()
mqttclient.on_connect = mqtt_on_connect
mqttclient.on_message = mqtt_on_message
mqttclient.connect(getConfigValue("mqtt_broker"), 1883, 60)

mqttclient.loop_forever()

#!/usr/bin/env python

from sense_hat import SenseHat
from subprocess import call
import time, json, os, thread
import paho.mqtt.client as mqtt

senseHat = SenseHat()
client = mqtt.Client()
loop = False
previousTemperature = 0


def on_message(client, userdata, message):
    if (message.payload == "shutdown"):
        print("[" + time.strftime('%x %X') + "] SHUTDOWN")
        time.sleep(5)
        call(["/sbin/shutdown","-h","now"])


def getCPUTemp():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

def on_connect(client, userdata, flags, rc):
    global senseHat
    senseHat.show_message("connect")
    print("[" + time.strftime('%x %X') + "] CONNECT")
    thread.start_new_thread(measure_loop,())

def on_disconnect(client, userdata, flags):
    global senseHat, loop
    loop = False
    print("[" + time.strftime('%x %X') + "] DISCONNECT")
    senseHat.show_message("disconnect")

def measure_loop():
    global loop, client
    try:
        if (not loop):
            loop = True
            while (loop):
                send_data()
                time.sleep(10)
    except (KeyboardInterrupt, SystemExit):
        client.disconnect()
        pass

def send_data():
    global senseHat
    global client
    global previousTemperature
    #Because the sense hat temperature sensor is not shielded
    #need to try to figure some way of getting a reasonably
    #accurate temperature
    #Get the temperature from the temperature sensor
    temperature = senseHat.get_temperature()
    #Get the temperature from the pressure sensor
    temperatureFromPressure = senseHat.get_temperature_from_pressure()
    #Get the temperature from the humidity sensor
    temperatureFromHumidity = senseHat.get_temperature_from_humidity()
    #Get the temperature from the cpu
    cpuTemperature = float(getCPUTemp())
    temperatureCalc = int(((temperature+temperatureFromPressure+temperatureFromHumidity)/3)-(cpuTemperature/5))
    # Not rounded to an int
    temperatureCalc1 = ((temperature+temperatureFromPressure+temperatureFromHumidity)/3)-(cpuTemperature/5)
    temperatureCalc1 = round(temperatureCalc1,1)
    pressure = round(senseHat.get_pressure(),1)
    humidity = round(senseHat.get_humidity(),1)

    #keep this temperature in case we want to compare it next time
    previousTemperature = temperatureCalc
        
    #Publish the values over mqtt
    client.publish("Temp", temperatureCalc1,1,True)
    client.publish("Humidity", humidity,1,True)
    client.publish("Pressure", pressure,1,True)
    
    print("[" + time.strftime('%x %X') + "] Pressure: " + str(pressure) + ", Humidity: " + str(humidity) + ", Temp: " + str(temperatureCalc1))
    senseHat.show_message("T:"+str(temperatureCalc1))
    senseHat.show_message("H:"+str(humidity))
    senseHat.show_message("P:"+str(pressure))


client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect("mqtt.virit.in")
client.subscribe("sensehat/command")
client.loop_forever(10,1,True)
#client.loop_start()

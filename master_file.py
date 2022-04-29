from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient    #Import from AWS-IoT Library
from datetime import date, datetime                     #Import date and time feature
import RPi.GPIO as GPIO                                 #Import GPIO 
import time                                             #import time for creating delay 
import Adafruit_CharLCD as LCD                          #Import LCD library 
import Adafruit_DHT                                     #Import DHT Library for sensor
#from gpiozero import InputDevice


## MQTT Configurations in compliance with AWS IoT
myMQTTClient = AWSIoTMQTTClient("SmartGardenIoT") 
myMQTTClient.configureEndpoint("a3sjzxv94uqbse-ats.iot.us-east-1.amazonaws.com", 8883)

## Providing all credentials 
myMQTTClient.configureCredentials("/home/student/cert/AmazonRootCA1.pem", "/home/student/cert/pri.key", "/home/student/cert/dev.pem.crt")

myMQTTClient.configureOfflinePublishQueueing(-1) # Infinite offline Publish queueing
myMQTTClient.configureDrainingFrequency(2) # Draining: 2 Hz
myMQTTClient.configureConnectDisconnectTimeout(10) # 10 sec
myMQTTClient.configureMQTTOperationTimeout(5) # 5 sec
print ('Connecting to AWS IoT ....')
myMQTTClient.connect()


TRIG=21
ECHO=20
GPIO.setmode(GPIO.BCM)
sensor_name = Adafruit_DHT.DHT11  #we are using the DHT11 sensor
sensor_pin = 17                   #The sensor is connected to GPIO17 on Pi
#no_rain = InputDevice(13)
RAIN = 13
channel = 4
LDR = 5
led = 6
pump = 19
valve = 26

GPIO.setup(led, GPIO.OUT)         # Configuring LED as output 
GPIO.output(led, False)
GPIO.setup(pump, GPIO.OUT)        # Configuring Water Pump as output 
GPIO.output(pump, True)
GPIO.setup(valve, GPIO.OUT)       # Configuring LED as output 
GPIO.output(valve, False)
GPIO.setup(channel, GPIO.IN)
GPIO.setup(LDR, GPIO.IN)          # Configuring LDR as input
GPIO.setup(RAIN, GPIO.IN)          # Configuring LDR as input

lcd_rs        = 16               # RS of LCD is connected to GPIO 7 on PI
lcd_en        = 12               # EN of LCD is connected to GPIO 8 on PI 
lcd_d4        = 25               # D4 of LCD is connected to GPIO 25 on PI
lcd_d5        = 24               # D5 of LCD is connected to GPIO 24 on PI
lcd_d6        = 23               # D6 of LCD is connected to GPIO 23 on PI
lcd_d7        = 18               # D7 of LCD is connected to GPIO 18 on PI
lcd_backlight =  0               # LED is not connected so we assign to 0

lcd_columns = 16                 #  16*2 LCD
lcd_rows    = 2                  #  16*2 LCD

lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, 
                           lcd_columns, lcd_rows, lcd_backlight)   #Send all the pin details to library 

lcd.message('SMART IoT GARDEN\n      IITH      ')        #   Welcome message

time.sleep(5)                                            #   wait 

plant_water = 0                                          # Global Variable for indicating water requirement
rain_detected = 0                                        # Global Variable for indicating rain 


# Running infinite Loop

while 1: 
    lcd.clear() #Clear the LCD screen
    print("Variable Values at starting of LOOP :: ", plant_water, rain_detected)
           
    # Callback for rain trigger
    
    def callback(RAIN):
        print("Callback triggered for Rain")
        global rain_detected
        if GPIO.input(RAIN):
            rain_detected = 0
            print ("It's not raining ..", rain_detected)
            lcd.clear() #Clear the LCD screen
            lcd.message ('NOT RAINING\n****************')
            time.sleep(2)            
        else:
            rain_detected = 1
            print ("It's Raining")
            lcd.clear() #Clear the LCD screen
            lcd.message ('IT\'S RAINING.\n****************') 
            time.sleep(2)
 
    GPIO.add_event_detect(RAIN, GPIO.BOTH, bouncetime=300)  # Added event
    GPIO.add_event_callback(RAIN, callback)  # Added Callback
    time.sleep(2)


    # Callback for Moisture Sensor
    
    def callback(channel):
        print("Callback triggered for Moisture Sensor")
        global plant_water
        if GPIO.input(channel):
            plant_water = 1
            print ("Dry soil ")
            lcd.clear() 
            lcd.message ('SOIL IS DRY.\n****************')
            time.sleep(2)            
        else:
            plant_water = 0
            print ("Water Detected!")
            #GPIO.output(pump, True)
            lcd.clear() #Clear the LCD screen
            lcd.message ('SOIL IS WET.\n****************') 
            time.sleep(2)
 
    GPIO.add_event_detect(channel, GPIO.BOTH, bouncetime=300)  # Added event
    GPIO.add_event_callback(channel, callback)  # Added Callback
    time.sleep(2)
    
    # Callback for LDR Sensor
    
    def callback(LDR):
        if GPIO.input(LDR):
                GPIO.output(led, True)
                time.sleep(3)
                print ("LOW INTENSITY Detected!" + " ..... " + "Switching ON the LED")
                lcd.clear() #Clear the LCD screen
                lcd.message ('LOW INTENSITY \n   DETECTED     ')
                time.sleep(2)
                lcd.clear() #Clear the LCD screen
                lcd.message ('SWITCHING ON\n        LED     ') 
                time.sleep(2)
        else:
                print ("HIGH INTENSITY DETECTED" + " ... " + "Switching OFF the LED")
                lcd.message ('HIGH INTENSITY\n     DETECTED   ')
                time.sleep(2)
                lcd.clear() #Clear the LCD screen
                lcd.message ('SWITCHING OFF\n      LED       ') 
                time.sleep(2)
                GPIO.output(led, False)
                time.sleep(3)
                time.sleep(2)
 
    GPIO.add_event_detect(LDR, GPIO.BOTH, bouncetime=300)  # Added event
    GPIO.add_event_callback(LDR, callback)          # Added Callback
    time.sleep(2)
    
    while True:
        
        humidity, temperature = Adafruit_DHT.read_retry(sensor_name, sensor_pin) #read from sensor and save respective values in temperature and humidity varibale  
        lcd.clear() #Clear the LCD screen
        lcd.message ('TEMP = %.1f C' % temperature)          
        lcd.message ('\nHUM  = %.1f %%' % humidity)          
        print("Publishing message", temperature, humidity)
        myMQTTClient.publish(topic="smartgarden/temperature", QoS=1, payload = '{"Tempareture":"'+str(temperature)+'"}')
        myMQTTClient.publish(topic="smartgarden/humidity", QoS=1, payload = '{"Humidity":"'+str(humidity)+'"}')
        time.sleep(2) #Wait 
        
        print("Calculating Distance of water from sensor...")
        lcd.clear() #Clear the LCD screen
        lcd.message ('CALCULATING \n    DISTANCE    ') 
        GPIO.setup(TRIG,GPIO.OUT)
        GPIO.setup(ECHO,GPIO.IN)
        GPIO.output(TRIG,False)
        time.sleep(0.2)
        GPIO.output(TRIG,True)
        time.sleep(0.00001)
        GPIO.output(TRIG,False)
        while GPIO.input(ECHO)==0:
            pulse_start=time.time()
        while GPIO.input(ECHO)==1:
            pulse_end=time.time()
        pulse_duration=pulse_end-pulse_start
        distance=pulse_duration*17150
        distance=round(distance,2)
        print("Depth of water:",distance,"cm")
        lcd.clear() #Clear the LCD screen
        lcd.message ('WATER DEPTH: %.1f CM'% distance)
        myMQTTClient.publish(topic="smartgarden/tankstatus", QoS=1, payload = '{"Tank Depth from top ":"'+str(distance)+'"}')
        time.sleep(3)
        
        if ( distance <= 15 ):
            print("Tank is Full")
            lcd.clear() #Clear the LCD screen
            lcd.message ('TANK IS FULL\n****************')
            GPIO.output(valve, False)
            print("Variable Values are :: ", plant_water, rain_detected)
            
            if plant_water == 1 and rain_detected == 0:
                print("It's not raining and water is also not there, hence switching ON the Motor")
                lcd.clear() #Clear the LCD screen
                lcd.message ('MOTOR ON\n****************')
                GPIO.output(pump, False)           
            else:
                print("Soil is wet, hence water not required")
                lcd.clear() #Clear the LCD screen
                lcd.message ('WATER NOT REQD\n****************')
                GPIO.output(pump, True)
            time.sleep(3)
       
        if (distance > 15):
            print("Tank is Empty")
            lcd.clear() #Clear the LCD screen
            lcd.message ('TANK IS EMPTY\n****************')
            lcd.clear() #Clear the LCD screen
            lcd.message ('VALVE ON.\n****************')
            print("Tank is Empty, switching ON the Valve")
            GPIO.output(pump, True)
            GPIO.output(valve, True)
            time.sleep(3)
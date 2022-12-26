import subprocess
import io
import cv2
import time
import paho.mqtt.client as mqtt

#sudo modprobe bcm2835-v4l2
leds = io.open("/dev/fpga_led","wb",buffering=0)
fnds = io.open("/dev/fpga_fnd","wb",buffering=0) #0000~9999
dots = io.open("/dev/fpga_dot","wb",buffering=0) #0~9
textLcds = io.open("/dev/fpga_text_lcd","wb",buffering=0)
dipSwitchs = io.open("/dev/fpga_dip_switch","rb",buffering=0)
pushSwitchs = io.open("/dev/fpga_push_switch","rb",buffering=0)
buzzers = io.open("/dev/fpga_buzzer","wb",buffering=0)
stepMoters = io.open("/dev/fpga_step_motor","wb",buffering=0)
fail = 0
lockStatus = True #False then into pw mode

#=====use and modified "opencv example code", https://github.com/opencv/opencv/tree/master    =====
def face_extractor(img): #to detect face, not classifier
	gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
	faces = faceCascade.detectMultiScale(gray,1.3,5)
	if faces is(): #no face
		return None
	for(x,y,w,h) in faces: #yes face
		return 1
#=====finish to use "opencv example code"=====


#=====use and modified "paho.mqtt example code", https://pypi.org/project/paho-mqtt/#usage-and-api     =====
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("$SYS/#")
    client.subscribe("#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    global temp
    temp = msg.payload
    print(temp)
    
    if (str(temp) == "b'authorize'"):
        client.disconnect() 
#=====finish to use "paho.mqtt example code"=====


#=====to run other program=====
subprocess.call(['./DigitalClock'])
#====finish to run other program=====


#=====to receive and check mqtt message=====
print("need authorize! talk to admin")
s="                                "
b=bytearray()
b.extend(map(ord,s))
textLcds.write(b)
s="need authorize! talk to admin"
b=bytearray()
b.extend(map(ord,s))
textLcds.write(b)
        
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("your.Domain.local", 1883, 60) #change to your mqtt domain

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
#=====finish to receive and check mqtt message=====


#=====to write lcd =====
print("authorized... booting")
s="                                " #erase lcd
b=bytearray()
b.extend(map(ord,s))
textLcds.write(b)
s="authorized...   booting"
b=bytearray()
b.extend(map(ord,s))
textLcds.write(b)
        
s="1234" #print number
b=bytearray()
b.extend(map(ord,s))
fnds.write(b)
#=====finish to write lcd=====

#=====to use led dot matrix=====
for i in range(256):
    time.sleep(0.05)
    dots.write(bytearray([i,i,i,i,i,i,i,i,i,i]))
time.sleep(1)
dots.write(bytearray([0,0,0,0,0,0,0,0,0,0]))
#=====finish to use led dot matrix=====

while(True):
    #print(dipSwitchs.read(8)[0],'02x')

    #use camera && opencv
    #recognition face
    faceCascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')#to use opencv face library

    cap = cv2.VideoCapture(0)
    cap.set(3,320)
    cap.set(4,240)
    while(True):
        leds.write(bytearray([255])) #led on
        ret, img = cap.read()
        cv2.imshow('video',img)
        if face_extractor(img) == 1:
            break
        k = cv2.waitKey(30) & 0xff
        if k == 27:
            break
    cap.release()
    cv2.destroyAllWindows()
    leds.write(bytearray([0])) #led off    
    s="                                "
    b=bytearray()
    b.extend(map(ord,s))
    textLcds.write(b)    
    s="face detected!"
    b=bytearray()
    b.extend(map(ord,s))
    textLcds.write(b)
    time.sleep(1)  

    #use dipSwitch
    #to use Secure lock
    if(dipSwitchs.read(8)[0] == 255):
        #stepMoters.write(bytearray([1,1,255])) #data should give bytearray
        lockStatus = False
        print("able")
        s="                                "
        b=bytearray()
        b.extend(map(ord,s))
        textLcds.write(b)
        s="able"
        b=bytearray()
        b.extend(map(ord,s))
        textLcds.write(b)
        

        for i in range(3,0,-1):
                buzzers.write(bytearray([1]))
                time.sleep(3)
                if (pushSwitchs.read(9)==b'\x00\x00\x00\x00\x00\x00\x00\x00\x01'):
                        print("password correct")
                        s="                                "
                        b=bytearray()
                        b.extend(map(ord,s))
                        textLcds.write(b)
                        s="password correct"
                        b=bytearray()
                        b.extend(map(ord,s))
                        textLcds.write(b)
                        fail=0
                        break
                else:
                        print("password incorrect. %d attempts left." % (i-1))
                        s="                                "
                        b=bytearray()
                        b.extend(map(ord,s))
                        textLcds.write(b)
                        s="password incorrect. "+str(i-1)+" left."
                        b=bytearray()
                        b.extend(map(ord,s))
                        textLcds.write(b)
                        buzzers.write(bytearray([0]))
                        fail=1
        buzzers.write(bytearray([1]))
        if (fail==0):
                print("door unlocked!!")
                s="                                "
                b=bytearray()
                b.extend(map(ord,s))
                textLcds.write(b)
                s="door unlocked!!"
                b=bytearray()
                b.extend(map(ord,s))
                textLcds.write(b)
                stepMoters.write(bytearray([1,1,255]))
                time.sleep(2)
                stepMoters.write(bytearray([0,1,255]))
                time.sleep(0.7)
                print("door locked!!")
                s="                                "
                b=bytearray()
                b.extend(map(ord,s))
                textLcds.write(b)
                s="door locked!!"
                b=bytearray()
                b.extend(map(ord,s))
                textLcds.write(b)
                stepMoters.write(bytearray([1,0,255]))
                time.sleep(2)
                stepMoters.write(bytearray([0,0,255]))

        
    else:
        #stepMoters.write(bytearray([0,1,255])) #data should give bytearray
        lockStatus = True
        print("unable")
        s="                                "
        b=bytearray()
        b.extend(map(ord,s))
        textLcds.write(b)
        s="unable"
        b=bytearray()
        b.extend(map(ord,s))
        textLcds.write(b)





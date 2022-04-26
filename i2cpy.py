"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

import serial, time, os, struct

R_SHUNT=0.05

def i2cOpen(dev):

  #set up the serial connection
  ser = serial.Serial(
    port=dev,
    baudrate=19200,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_TWO,
    bytesize=serial.EIGHTBITS,
    timeout=1
    )
  return ser


def i2cWrite(dev, addr, cmd, payload):
  data=struct.pack('BBBB', 0x55, addr, cmd, len(payload))
  data+=payload
  dev.write(data)
  ret=dev.read(1)
  return ret

def i2cRead(dev, addr, cmd, len):
  data=struct.pack('BBBB', 0x55, addr+1, cmd, len)
  dev.write(data)
  ret=dev.read(len)
  return ret

def fgGetId(dev):
  print("ID")
  return i2cRead(dev, 0xE0, 0x18, 0x08)
  print("id")

def fgGetCharge(dev):
  rawData=i2cRead(dev, 0xE0, 0x02, 0x02)
  intVal=struct.unpack('<h', rawData)[0]
  realVal=intVal*1.0
  phyVal=realVal * 0.0000067
#  print("Charge {} {:x} {:d} {:f} {:f}Vh".format(rawData, intVal, intVal, realVal, phyVal))
  return phyVal

def fgGetCount(dev):
  rawData=i2cRead(dev, 0xE0, 0x04, 0x02)
  intVal=struct.unpack('<H', rawData)[0]
#  print("Cnt ",rawData, ' ', intVal)
  return intVal

def fgGetCurrent(dev):
  rawData=i2cRead(dev, 0xE0, 0x06, 0x02)
  intVal=struct.unpack('<h', rawData)[0]
  if (intVal & 0x2000):
    intVal = ( -1 & ~0x3FFF ) | intVal
  realVal=intVal*1.0
  phyVal=realVal * 0.00001177/R_SHUNT
#  print("Cur {} {:x} {:d} {:f} {:f}A".format(rawData, intVal, intVal, realVal, phyVal))
  return phyVal

def fgGetVoltage(dev):
  rawData=i2cRead(dev, 0xE0, 0x08, 0x02)
  intVal=struct.unpack('<H', rawData)[0]
  if (intVal & 0x2000):
    intVal = ( -1 & ~0x3FFF ) | intVal
  realVal=intVal*1.0
  phyVal=realVal * 0.00244
#  print("Volt {} {:x} {:d} {:f} {:f}V".format(rawData, intVal, intVal, realVal, phyVal))
  return phyVal

def fgGetTemp(dev):
  rawData=i2cRead(dev, 0xE0, 0x0A, 0x02)
  intVal=struct.unpack('<h', rawData)[0]
  if (intVal & 0x2000):
    intVal = ( -1 & ~0x3FFF ) | intVal
  realVal=intVal*1.0
  phyVal=realVal * 0.125
#  print("Temp {} {:x} {:d} {:f} {:f}C".format(rawData, intVal, intVal, realVal, phyVal))
  return phyVal

def fgSetMode(dev, run, cal):
  setv=0
  if run==True: 
    setv|=0x10
  if cal==True:
    setv|=0x08

  print (i2cWrite(dev, 0xE0, 0x00, bytes([setv])))

def fgSetCtrl(dev, iopin, reset, por):    
  setv=0
  if iopin==True: 
    setv|=0x01
  if reset==True:
    setv|=0x02
  if por==True:
    setv|=0x10
  print (i2cWrite(dev, 0xE0, 0x01, bytes([setv])))


ser=i2cOpen('/dev/ttyUSB1')

s = fgGetId(ser)
print("Serial ", s)        


fgSetMode(ser, True, False)
fgSetCtrl(ser, True, True, True)
time.sleep(.1)
fgSetCtrl(ser, False, False, False)
fgSetMode(ser, True, False)


#start the main loop
while True:
    #basic error handling, occasionally the device fails to respond. This keeps the 
    #loop running.
#    try:
        #wait for the range to finish
        time.sleep(.1)
        

        volt=fgGetVoltage(ser)
        cur =fgGetCurrent(ser)
        temp=fgGetTemp(ser)
        cnt =fgGetCount(ser)
        chg =fgGetCharge(ser)

        #clear the screen so we are not repeating up the screen
#        os.system('clear')
        
        print("Cycle {:d} \tVolt: {:f}V \tCurrent: {:f}A \tCharge: {:f}Ah \tTemp: {:f}".format(cnt, volt, cur, chg, temp))

        #slow the loop down a bit to give our eyes a chance to read the response
        time.sleep(1)
    
    #handle errors, the second "except" here takes all errors in it's stride and allows
    #the loop to continue. I did this because every now and again the USB-I2C device 
    #fails to respond and breaks the loop. By having a blanket error handling rule you 
    #could no longer interrupt the loop with a keyboard interrupt so I had to add an 
    #"except KeyboardInterrupt" rule to allow this to break the loop.  
 #   except KeyboardInterrupt:
 #       print (' Exiting...Keyboard interrupt')
 #       break
    
 #   except Exception as e:
 #       print ('unexpected error ', e)

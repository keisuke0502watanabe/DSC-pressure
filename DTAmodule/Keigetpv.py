#omron rs232c 
import serial
import time
import struct
# from operator import xor
import chksumKei
import setSerKei
import am

def getPv2000():
    
    ser=setSerKei.setSerKei2000()
    ser.open()

    #for command
    y=":FETCh?"
    x=y.encode()
    ser.write(x)
    
    x=b'\r'
    ser.write(x)
    
    #to receive data
    #print("recv data")
    pv=0
    c=""
    camma=0
    i=0
    while True:
        if ser.in_waiting > 0:
            recv_data=ser.read()
            a = struct.unpack_from("B",recv_data, 0)
            b=a[0]
            b=chr(b)
            c+=b
            if len(c) == 15:
                break

    ser.close()

    return c

def getPv2182A():
    
    ser=setSerKei.setSerKei2182A()
    ser.open()

    #for command
    y=":FETCh?"
    x=y.encode()
    ser.write(x)
    
    x=b'\r'
    ser.write(x)
    
    pv=0
    c=""
    camma=0
    i=0
    while True:
        if ser.in_waiting > 0:
            recv_data=ser.read()
            a = struct.unpack_from("B",recv_data, 0)
            b=a[0]
            b=chr(b)
            c+=b
            if len(c) == 15:
                break
    ser.close()
    return c

# while True:
#     getPv2000()
#     getPv2182A()
#     time.sleep(1)
    

# print(getPv2000())
print(getPv2182A())
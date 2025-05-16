import serial
import time
import struct


# ser = serial.Serial('/dev/ttyUSB0', baudrate=4800, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=0.2)

# ser = serial.Serial('/dev/ttyUSB0', baudrate=4800, bytesize=serial.SEVENBITS, parity=serial.PARITY_EVEN, stopbits=serial.STOPBITS_ONE, timeout=5)
 
with serial.Serial('/dev/ttyUSB1') as ser:
    ser.baudrate=4800
    ser.bytesize=serial.SEVENBITS
    ser.parity=serial.PARITY_EVEN
    ser.stopbits=serial.STOPBITS_ONE
    ser.timeout=5
    
def setSv(sv):
    ser.open()
    #STX
    x=[0x02]
    ser.write(x)

    y=" 2, 4,1,"+str(sv)+","
    x=y.encode()
    #print(type(x))
    ser.write(x)
   
    #check sum calculation before ETX
    i=0
    chkSum=0
    for i in range(len(y)):
        chkSum=chkSum + ord(y[i])

    #ETX
    x=[0x03]
    chkSum=chkSum+3
    ser.write(x)

    #check sum calculation after ETX
    a=hex(chkSum)
    chkSumU=a[-2:-1]
    chkSumD=a[-1:]
    chkSumValue=str.upper(chkSumD + chkSumU)
#     print(chkSumValue)
    #checksum + CR + LF
    x=chkSumValue.encode()
    ser.write(x)
    
    x=b'\r\n'
    ser.write(x)
    #print("recv data")
    pv=0
    c=""
    camma=0
    i=0
    while True:
        if ser.in_waiting > 0:
            recv_data=ser.read()
            a = struct.unpack_from("B",recv_data ,0)
            if a[0] ==10:
                   break

    ser.close()
    return

def getPv():
    ser.open()
    #STX
    x=[0x02]
    ser.write(x)

    y=" 1, 1,"
    x=y.encode()
    #print(type(x))
    ser.write(x)
   
    #check sum calculation before ETX
    i=0
    chkSum=0
    for i in range(len(y)):
        chkSum=chkSum + ord(y[i])

    #ETX
    x=[0x03]
    chkSum=chkSum+3
    ser.write(x)

    #check sum calculation after ETX
    a=hex(chkSum)
    chkSumU=a[-2:-1]
    chkSumD=a[-1:]
    chkSumValue=str.upper(chkSumD + chkSumU)
#     print(chkSumValue)
    #checksum + CR + LF
    x=chkSumValue.encode()
    ser.write(x)
    
    x=b'\r\n'
    ser.write(x)
    #print("recv data")
    pv=0
    c=""
    camma=0
    i=0
    while True:
        if ser.in_waiting > 0:
            recv_data=ser.read()
            a = struct.unpack_from("B",recv_data ,0)
            b=a[0]
            b=chr(b)
            if b ==",":
                camma += 1
                if camma == 5:
                    pv = (c[14:23])
                    #print("pv="+str(pv))
                    break
            c+=b
            i += 1
    ser.close()
    return float(pv)
    

#setSv(320)

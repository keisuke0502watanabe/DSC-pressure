import time
import Chino

def rate(Ti,Tf,rate):
    t0 = time.time()
    num = 0
    while True:
        c = num/60
        sv = Ti+c
        t1 = time.time()
        t2 = t1-t0
        print(round(sv,3),round(t2,3))
        time.sleep(1)
        Chino.setSv(sv)
        num += rate
#         mod = t2 % 60
#         if (mod >= 30 and mod < 31) or (mod >= 0 and mod < 1):
#              print(round(sv,3),round(t2,3))
        if rate > 0:
            if sv >= Tf:
                print("finish")
                break
        else:
            if sv <= Tf:
                print("finish")
                break
        
     

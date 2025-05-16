from DTAmodule.chino_control import ChinoController
import time
import datetime
import threading
import csv
import os
from DTAmodule import vttotemp
import am
import traceback
from natsort import natsorted
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pressure_control import PressureControl
from DTAmodule.visualize import DTAVisualizer
from DTAmodule.experiment_manager import ExperimentManager, ExperimentMetadata
from collections import deque
import keyboard
import matplotlib.pyplot as plt

def rate(Ti,Tf,rate):
    """温度を一定の速度で変化させる
    
    Args:
        Ti (float): 開始温度
        Tf (float): 終了温度
        rate (float): 温度変化速度
    """
    chino = ChinoController()
    chino.connect()
    sv = Ti
    num = 0
    t1 = time.time()
    t2 = 0
    while sv < Tf:
        t2 = time.time() - t1
        sv = Ti + rate * t2
        print(round(sv,3),round(t2,3))
        time.sleep(1)
        chino.set_temperature(sv)
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
        
     

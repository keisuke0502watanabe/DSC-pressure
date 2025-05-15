import Keigetpv
import Chino
import time
import datetime
import setScanrate
import threading
import csv
import os
import vttotemp
import am
import traceback
from natsort import natsorted
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pressure_control import PressureControl

#鍵 
key_name = '/home/pi/Desktop/json_file/teruyama/my-project-333708-dad962c8e2e4.json'
sheet_name = 'teruyama test1'
#APIにログイン
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(key_name, scope)
gc = gspread.authorize(credentials)

def columnSet(wks):
    cell_number1 = 'A1'
    input_value1 = 'set Temp. / K'
    #wks = gc.open(sheet_name).sheet1
    wks.update_acell(cell_number1, input_value1)
    cell_number2 = 'B1'
    input_value2 = 'time / s'
    wks.update_acell(cell_number2, input_value2)
    cell_number3 = 'C1'
    input_value3 = 'dt of Kei2000/ microvolts'
    wks.update_acell(cell_number3, input_value3)
    cell_number4 = 'D1'
    input_value4 = 'dt of Kei2182A/ microvolts'
    wks.update_acell(cell_number4, input_value4)
    cell_number5 = 'E1'
    input_value5 = 'dt of Kei2000/K'
    wks.update_acell(cell_number5, input_value5)
    cell_number6 = 'F1'
    input_value6 = 'dt of Kei2182A/K'
    wks.update_acell(cell_number6, input_value6)
    cell_number7 = 'G1'
    input_value7 = 'Heat or cool '
    wks.update_acell(cell_number7, input_value7)
    cell_number8 = 'H1'
    input_value8 = 'Run'
    wks.update_acell(cell_number8, input_value8)
    cell_number9 = 'I1'
    input_value9 = 'Date'
    wks.update_acell(cell_number9, input_value9)
    cell_number10 = 'J1'
    input_value10 = 'Date time'
    wks.update_acell(cell_number10, input_value10)
    cell_number11 = 'K1'
    input_value11 = 'Sample name'
    wks.update_acell(cell_number11, input_value11)
    cell_list = wks.range('A2:K11')

def wksUpdate(wks,cell_list):
    wks.update_cells(cell_list)

def cellListUpdate(wks,sheet_pointer):
            try:
                cell_list = wks.range('A'+str(sheet_pointer)+':K'+str(sheet_pointer+9))                
            except:
                wks.add_rows(10000)
                cell_list = wks.range('A'+str(sheet_pointer)+':K'+str(sheet_pointer+9))

def ambTh(t0, t1, pv2182A, pv2000, filenameError):
        try:
                am.amb(float(round(t1-t0,3)),float(pv2182A),float(vttotemp.VtToTemp(pv2000)))
        except:
                traceback.print_exc()
                f = open(str(filenameError), mode='a')
                f.write(str(time.time()))
                f.write(', row=145 \n')
                f.write(str(traceback.print_exc()))
                f.write('\n')
                f.close()
                
cell_list=[]
sheet_pointer =2
list_pointer = 0
wks = gc.open(sheet_name).sheet1
thread1 = threading.Thread(target=columnSet, args=(wks,))
thread2 = threading.Thread(target=wksUpdate, args=(wks,cell_list,))

thread3 = threading.Thread(target=cellListUpdate, args=(wks, sheet_pointer,))

print(sheet_name)

#　以下本文
m = 1
text = []
Q2 = input("Have you already measured? y/n:")
sampleName=input("What is the sample name?")
if Q2 == 'y':
    path='/home/pi/Desktop/Experiment_condition'
    os.chdir(path)
    list=os.listdir(path)
    list=natsorted(list)
    for i in range(len(list)):
        print(str(i) + " : " + list[i])
    
    num = int(input("What is the number of the condition file?:"))
    filenameExpCond = list[num]
    filenameResults = filenameExpCond.replace('ExpCond.csv','Results.csv')
    filenameError = filenameExpCond.replace('ExpCond.csv','Error.csv')
#     filenameResults = filenameExpCond+'_Results.csv'
#     filenameError = filenameExpCond+'Error.csv'

elif Q2 == 'n':
    samplename = input("What is name of the samle :")
    filenameExpCond = samplename + "ExpCond.csv"
    filenameResults = samplename + "Results.csv"
    filenameError = samplename + "Error.csv"
    f = open(str(filenameExpCond), mode='a')
    f.close()
    f = open(str(filenameError), mode='a')
    f.close()
print(os.getcwd())
with open(filenameExpCond,'r') as file:
    reader = csv.reader(file)
    line = [row for row in reader]
#     print(len(line))
    
for i in range(1,len(line)):
        print('exp. '+str(i) +' : ')
        print(line[i])
    
os.chdir("/home/pi/Desktop/Experiment_result")
print(os.path.exists(filenameResults))
print(os.listdir())
if not os.path.exists(filenameResults):
    thread1.start()
    f = open(str(filenameResults), mode='a')
    f.write("set Temp. / K\t time / s\t dt of Kei2000/ microvolts \tdt of Kei2182A/ microvolts\t dt of Kei2000/K \t dt of Kei2182A/K \t Heat or cool \t Run \t Date \t Time of Day \t Sample Name \n")
    f.close()


     
#Read exp. condition
Tsv=['Tsv']
Tf=['Tf']
rate=['rate']
wait=['wait']
dt=['dt']
pressure=['pressure']  # 圧力条件
pressure_tolerance=['pressure_tolerance']  # 圧力許容パーセント
timeExp=0
for k in range(1,len(line)):
    Tsv.append(float(line[k][1]))
    Tf.append(float(line[k][2]))
    rate.append(float(line[k][3]))
    wait.append(float(line[k][4]))
    dt.append(float(line[k][3])/60)
    pressure.append(float(line[k][5]))  # 圧力条件を読み込み
    pressure_tolerance.append(float(line[k][6]))  # 圧力許容パーセントを読み込み
    print(k,Tsv, Tf, rate, wait, dt, pressure, pressure_tolerance)
    timeExp=timeExp+abs((Tf[k]-Tsv[k])/rate[k])+wait[k]/60
    print(k, timeExp)
timeExp=timeExp-wait[k]/60
print(timeExp)

#csv sheet column settting
    #if i == 0:


#change temp. to first Tsv
Chino.setSv(Tsv[1])
Tsvtemp=Tsv[1]
wait1st=float(input("How long will you wait before 1st measurement? [sec]: "))
print("The measurement started at "+ str(datetime.datetime.now()))
td = datetime.timedelta(minutes=timeExp)
print("The measurement will finish at "+str(datetime.datetime.now()+td))
time.sleep(wait1st)

t0 = time.time()
t3 = t0

# 圧力制御の初期化
pressure_control = None
try:
    pressure_control = PressureControl()
except Exception as e:
    print("圧力制御の初期化に失敗しました: {}".format(e))

for k in range(1,len(line)):
    print("Run the measurement number " + str(k) +" ! Tsv= "+str(Tsv[k])+" K" )
    if k ==1:
        print("Wait for " + str(wait1st) +" sec.")
    else:
        print("Wait for " + str(wait[k-1]) +" sec.")
    print(rate[k])
    print(dt[k])
    
    print("Run", "Date and Time", "Tsv / K", "pv2000", "pv2182A", "Tpv2000", "Tpv2182A")

    while True:
        time.sleep(.5)
        a = Chino.getPv()  
        time.sleep(1)
        t1 = time.time()
        t2 = t1-t3
        t3 = t1
        
        if k==1:
            Tsvtemp = Tsvtemp + dt[k]*t2
            Chino.setSv(Tsvtemp)
        else:
            if t1 > t4+wait[k-1]:
                Tsvtemp = Tsvtemp + dt[k]*t2
                Chino.setSv(Tsvtemp)
        
        t1 = time.time()
        pv2000 = float(Keigetpv.getPv2000())*1000000
        pv2182A = float(Keigetpv.getPv2182A())*1000000
        vttotemp.VtToTemp(pv2000)
        a = vttotemp.VtToTemp(pv2000)
        vttotemp.VtToTemp(pv2182A)
        
        # 圧力の測定と制御
        current_pressure = None
        if pressure_control is not None:
            current_pressure = pressure_control.get_pressure()
            if current_pressure is not None:
                # 目標圧力との差が許容パーセントを超える場合は調整
                tolerance = pressure[k] * (pressure_tolerance[k] / 100.0)  # 許容範囲を計算
                if abs(current_pressure - pressure[k]) > tolerance:
                    pressure_control.set_target_pressure(pressure[k], tolerance=tolerance)
        
        # 結果の記録
        f = open(str(filenameResults), mode='a')
        if rate[k] > 0:
            hoc = "heat"
        elif rate[k] < 0:
            hoc = "cool"
        
        pressure_str = "{:.3f}".format(current_pressure) if current_pressure is not None else "N/A"
        print(k, datetime.datetime.now(), round(Tsvtemp,3), round(t1-t0,3), pv2000, pv2182A, 
              vttotemp.VtToTemp(pv2000), vttotemp.VtToTemp(pv2182A), pressure_str)
        
        try:
            result = "{:.3f}\t {:.3f}\t {:.10f}\t {:.10f}\t {:.10f}\t {:.10f}\t {}\t {} \t {} \t {} \t {} \t {}\n".format(
                float(Tsvtemp), float(t1-t0), pv2000, pv2182A, 
                vttotemp.VtToTemp(pv2000), vttotemp.VtToTemp(pv2182A),
                hoc, k, datetime.date.today(), datetime.datetime.now().time(),
                sampleName, pressure_str)
        except:
            pass
        f.write(result)
        f.close()
        try:
                    cell_list[list_pointer].value= float(Tsv[k])
                    cell_list[list_pointer+1].value=float(t1-t0)
                    cell_list[list_pointer+2].value=pv2000
                    cell_list[list_pointer+3].value=pv2182A
                    cell_list[list_pointer+4].value=vttotemp.VtToTemp(pv2000)
                    cell_list[list_pointer+5].value=vttotemp.VtToTemp(pv2182A)
                    cell_list[list_pointer+6].value=hoc
                    cell_list[list_pointer+7].value=k
                    cell_list[list_pointer+8].value=str(datetime.date.today())
                    cell_list[list_pointer+9].value=str(datetime.datetime.now().time())
                    cell_list[list_pointer+10].value=sampleName
                    
        except:
                    pass
        list_pointer+=11
        if list_pointer > 99:
            print('upload')
            print("Run", "Date and Time", "Tsv / K", "pv2000", "pv2182A", "Tpv2000", "Tpv2182A")
            try:
                thread2.start()
            except:
                pass
                #wks.update_cells(cell_list)
            list_pointer = 0
            sheet_pointer += 10
                        
#############  
# 2022/07/05 Watanabe commented out, modified
            try:
                thread3.start()
            except:
                pass

#############
        # 終了条件
        if (rate[k] > 0 and float(Tsvtemp) >= float(Tf[k])):
                print(k)
                print(rate[k])
                print("Run " + str(k) + " was finished")                           
                print("wait for" + str(wait[k]) + " sec.")
                #time.sleep(wait[k])
                t4 = time.time()
                break
                            
        elif (rate[k] < 0 and float(Tsvtemp) <= float(Tf[k])):
                print(k)
                print(Tsv[k])
                print(Tf[k])
                print("Run " + str(k) + " was finished")
                print("wait for" + str(wait[k]) + " sec.")     
                #time.sleep(wait[k])
                t4 = time.time()
                break

    
print("finished")

# プログラム終了時に圧力制御のリソースを解放
if pressure_control is not None:
    pressure_control.close()

import keithley_control
from DTAmodule.chino_control import ChinoController
import time
import datetime
import threading
import csv
import os
from DTAmodule import vttotemp
import traceback
from natsort import natsorted
from DTAmodule.pressure_control import PressureControl
from DTAmodule.visualize import DTAVisualizer
from DTAmodule.experiment_manager import ExperimentManager, ExperimentMetadata
from DTAmodule.plotter import MenuDrivenPlotter
from DTAmodule.keyboard_handler import KeyboardHandler
from DTAmodule.spreadsheet_manager import SpreadsheetManager
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from DTAmodule.emergency_handler import emergency_shutdown, MAX_TEMPERATURE, MAX_PRESSURE
from DTAmodule.experiment_conditions import ExperimentConditions

#鍵 
# key_name = '/home/pi/Desktop/json_file/olha/my-project-333708-dad962c8e2e4.json'
# sheet_name = 'teruyama test1'
# #APIにログイン
# scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
# credentials = ServiceAccountCredentials.from_json_keyfile_name(key_name, scope)
# gc = gspread.authorize(credentials)

# 実験管理システムの初期化
experiment_manager = ExperimentManager()

# 安全制限値の設定
ROOM_TEMPERATURE = 298.15  # K (25℃)

# スプレッドシート設定
SPREADSHEET_BUFFER_SIZE = 100  # バッファサイズ
SPREADSHEET_UPDATE_INTERVAL = 300  # 更新間隔（秒）

# グラフ更新設定
GRAPH_UPDATE_INTERVAL = 1000  # ミリ秒
MAX_DATA_POINTS = 1000  # 表示するデータポイントの最大数

# スプレッドシートマネージャーの初期化
spreadsheet_manager = SpreadsheetManager(
    key_name='/home/yasumotosuzuka/Desktop/json_file/olha/my-project-333708-dad962c8e2e4.json',
    sheet_name='teruyama test1'
)

# 実験条件の取得
experiment_conditions = ExperimentConditions()
filenameExpCond, sampleName = experiment_conditions.get_experiment_conditions()
filenameResults = filenameExpCond.replace('ExpCond.csv', 'Results.csv')
filenameError = filenameExpCond.replace('ExpCond.csv', 'Error.csv')

# メインプログラムの開始部分を修正
Q2 = input("Have you already measured? y/n:")
if Q2 == "y":
    filenameExpCond, filenameResults, filenameError = experiment_conditions.continue_experiment()
    if filenameExpCond is None:
        Q2 = "n"

elif Q2 == 'n':
    sample = input("サンプル名を入力してください: ")
    filenameExpCond = sample + "ExpCond.csv"
    filenameResults = sample + "Results.csv"
    filenameError = sample + "Error.csv"
    f = open(str(filenameExpCond), mode='a')
    f.close()
    f = open(str(filenameError), mode='a')
    f.close()
print(os.getcwd())
with open(filenameExpCond,'r') as file:
    reader = csv.reader(file)
    line = [row for row in reader]
#     print(len(line))
    
# 実験条件の読み込みと表示
for i in range(1,len(line)):
        print('exp. '+str(i) +' : ')
        print(line[i])
    
os.chdir("/home/yasumotosuzuka/Desktop/Experiment_result")
print(os.path.exists(filenameResults))
print(os.listdir())
if not os.path.exists(filenameResults):
    thread1.start()
    f = open(str(filenameResults), mode='a')
    f.write("set Temp. / K,time / s,dt of Kei2000/ microvolts,dt of Kei2182A/ microvolts,dt of Kei2000/K,dt of Kei2182A/K,Heat or cool,Run,Date,Time of Day,Sample Name\n")
    f.close()

# 実験条件の解析と設定値の計算
Tsv, Tf, rate, wait, dt, pressure, pressure_tolerance, timeExp = experiment_conditions.parse_experiment_conditions(filenameExpCond)

#change temp. to first Tsv
chino = ChinoController()
chino.connect()
chino.set_temperature(Tsv[1])
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

# 可視化オブジェクトの初期化
visualizer = DTAVisualizer()

# プロッターの初期化
plotter = MenuDrivenPlotter()

# 各実験条件での測定実行
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
        a = chino.get_temperature()  
        time.sleep(1)
        t1 = time.time()
        t2 = t1-t3
        t3 = t1
        
        if k==1:
            Tsvtemp = Tsvtemp + dt[k]*t2
            chino.set_temperature(Tsvtemp)
        else:
            if t1 > t4+wait[k-1]:
                Tsvtemp = Tsvtemp + dt[k]*t2
                chino.set_temperature(Tsvtemp)
        
        t1 = time.time()
        pv2000 = float(keithley_control.getPv2000())*1000000
        pv2182A = float(keithley_control.getPv2182A())*1000000
        vttotemp.VtToTemp(pv2000)
        a = vttotemp.VtToTemp(pv2000)
        vttotemp.VtToTemp(pv2182A)
        
        # 温度チェック
        current_temp = vttotemp.VtToTemp(pv2000)
        if current_temp > MAX_TEMPERATURE:
            emergency_shutdown(pressure_control, 
                             "温度が制限値 ({:.1f}K) を超えました: {:.1f}K".format(
                                 MAX_TEMPERATURE, current_temp))
        
        # 圧力の測定と制御
        current_pressure = None
        if pressure_control is not None:
            current_pressure = pressure_control.get_pressure()
            if current_pressure is not None:
                # 圧力チェック
                if current_pressure > MAX_PRESSURE:
                    emergency_shutdown(pressure_control,
                                     "圧力が制限値 ({:.1f}MPa) を超えました: {:.1f}MPa".format(
                                         MAX_PRESSURE, current_pressure))
                
                # 目標圧力との差が許容パーセントを超える場合は調整
                tolerance = pressure[k] * (pressure_tolerance[k] / 100.0)
                if abs(current_pressure - pressure[k]) > tolerance:
                    pressure_control.set_target_pressure(pressure[k], tolerance=tolerance)
        
        # 結果の記録
        try:
            # 初回のみヘッダーを保存
            if not os.path.exists(filenameResults):
                save_results_header(filenameResults, {
                    'id': experiment_manager.get_current_experiment_id(),
                    'sample_name': sampleName,
                    'lot': input("ロット番号を入力してください: "),
                    'experimenter': input("実験者名を入力してください: ")
                })
            
            # データの記録
            result = "{:.3f},{:.3f},{:.10f},{:.10f},{:.10f},{:.10f},{},{},{:.3f}\n".format(
                float(Tsvtemp), float(t1-t0), pv2000, pv2182A, 
                vttotemp.VtToTemp(pv2000), vttotemp.VtToTemp(pv2182A),
                hoc, k, current_pressure if current_pressure is not None else 0.0
            )
            f.write(result)
            
            # データの収集
            plotter.update_data(
                float(t1-t0),
                float(Tsvtemp),
                vttotemp.VtToTemp(pv2000),
                vttotemp.VtToTemp(pv2182A),
                current_pressure if current_pressure is not None else 0.0
            )
            
            # スプレッドシートへのデータ追加
            spreadsheet_data = {
                'temperature': float(Tsvtemp),
                'time': float(t1-t0),
                'pv2000': pv2000,
                'pv2182A': pv2182A,
                'temp2000': vttotemp.VtToTemp(pv2000),
                'temp2182A': vttotemp.VtToTemp(pv2182A),
                'heat_or_cool': hoc,
                'run': k,
                'date': str(datetime.date.today()),
                'time_of_day': str(datetime.datetime.now().time()),
                'sample_name': sampleName
            }
            spreadsheet_manager.add_data(spreadsheet_data)
            
        except Exception as e:
            print("データ記録エラー: {}".format(e))
        
        f.close()
        
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

    
# 測定終了後にグラフを生成
print("Generating plots...")
try:
    # DTA曲線のプロット
    visualizer.plot_dta_curve(filenameResults)
    # 圧力-温度プロファイルのプロット
    visualizer.plot_pressure_temperature(filenameResults)
    # 3D DTAプロット
    visualizer.plot_3d_dta(filenameResults)
    print("Plots have been saved in Experiment_result/plots/")
except Exception as e:
    print("Error generating plots: {}".format(e))

print("finished")

# プログラム終了時に圧力制御のリソースを解放
if pressure_control is not None:
    pressure_control.close()

# プログラム終了時にバッファをフラッシュ
spreadsheet_manager.flush()

# グラフの表示
plotter.show()

def save_results_header(filename, experiment_data):
    """実験結果ファイルのヘッダーを保存
    
    Args:
        filename (str): ファイル名
        experiment_data (dict): 実験データ
    """
    with open(filename, 'w') as f:
        # メタデータの保存
        f.write("ID,{}\n".format(experiment_data.get('id', '')))
        f.write("Sample Name,{}\n".format(experiment_data.get('sample_name', '')))
        f.write("Lot,{}\n".format(experiment_data.get('lot', '')))
        f.write("Experimenter,{}\n".format(experiment_data.get('experimenter', '')))
        f.write("Date,{}\n".format(datetime.datetime.now().strftime("%Y/%m/%d")))
        
        # データヘッダーの保存
        f.write("set Temp. / K,time / s,dt of Kei2000/ microvolts,dt of Kei2182A/ microvolts,dt of Kei2000/K,dt of Kei2182A/K,Heat or cool,Run,Pressure / MPa\n")

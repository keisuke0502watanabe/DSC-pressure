import os
import time
import datetime
import threading
import csv
import traceback
from natsort import natsorted
from DTAmodule.keithley_control import getTemperature, getVoltage2182A
from DTAmodule.chino_control import ChinoController
from DTAmodule.pressure_control import PressureControl
from DTAmodule.visualize import DTAVisualizer
from DTAmodule.experiment_manager import ExperimentManager, ExperimentMetadata
from DTAmodule.plotter import MenuDrivenPlotter
from DTAmodule.keyboard_handler import KeyboardHandler
# from DTAmodule.spreadsheet_manager import SpreadsheetManager
from collections import deque
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from DTAmodule.emergency_handler import emergency_shutdown, MAX_TEMPERATURE, MAX_PRESSURE
from DTAmodule.experiment_conditions import ExperimentConditions
from DTAmodule import vttotemp

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
# SPREADSHEET_BUFFER_SIZE = 100  # バッファサイズ
# SPREADSHEET_UPDATE_INTERVAL = 300  # 更新間隔（秒）

# グラフ更新設定
GRAPH_UPDATE_INTERVAL = 1000  # ミリ秒
MAX_DATA_POINTS = 1000  # 表示するデータポイントの最大数

# 実験条件の取得
experiment_conditions = ExperimentConditions()
filenameExpCond, sampleName = experiment_conditions.get_experiment_conditions()
filenameResults = filenameExpCond.replace('ExpCond.csv', 'Results.csv')
filenameError = filenameExpCond.replace('ExpCond.csv', 'Error.csv')

# 実験条件の解析と設定値の計算
Tsv, Tf, rate, wait, dt, pressure, pressure_tolerance, timeExp = experiment_conditions.parse_experiment_conditions(filenameExpCond)

# 現在の状態を表示
print("\n=== 現在の状態 ===")
try:
    # Chinoの温度を取得
    chino = ChinoController()
    chino.connect()
    chino_temp = chino.get_temperature()
    print("Chino設定温度: {:.2f} K".format(chino_temp))
except Exception as e:
    print("Chino温度取得エラー: {}".format(e))

try:
    # Keithley 2000の電圧を取得して温度に変換
    pv2000 = float(getTemperature())*1000000
    k2000_temp = vttotemp.VtToTemp(pv2000)
    print("Keithley 2000温度: {:.2f} K".format(k2000_temp))
except Exception as e:
    print("Keithley 2000温度取得エラー: {}".format(e))

try:
    # 圧力を取得
    if pressure_control is not None:
        current_pressure = pressure_control.get_pressure()
        if current_pressure is not None:
            print("現在の圧力: {:.2f} MPa".format(current_pressure))
        else:
            print("圧力取得エラー: 値が取得できません")
    else:
        print("圧力制御が初期化されていません")
except Exception as e:
    print("圧力取得エラー: {}".format(e))

print("================\n")

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

# 実験条件の読み込みと表示
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
    # Heat or Coolの判定
    hoc = "Heat" if rate[k] > 0 else "Cool"
    
    print("Run the measurement number " + str(k) +" ! Tsv= "+str(Tsv[k])+" K" )
    print("Mode: " + hoc)  # モードを表示
    if k ==1:
        print("Wait for " + str(wait1st) +" sec.")
    else:
        print("Wait for " + str(wait[k-1]) +" sec.")
    print("Heating/Cooling rate: " + str(rate[k]) + " K/min")
    print("Time interval: " + str(dt[k]) + " min")
    
    print("Run", "Date and Time", "Tsv / K", "pv2000", "pv2182A", "Tpv2000", "Tpv2182A")

    # 結果ファイルを開く
    with open(filenameResults, 'a') as f:
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
            pv2000 = float(getTemperature())*1000000
            pv2182A = float(getVoltage2182A())*1000000
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
                f.flush()  # バッファをフラッシュして即座に書き込み
                
                # データの収集
                plotter.update_data(
                    float(t1-t0),
                    float(Tsvtemp),
                    vttotemp.VtToTemp(pv2000),
                    vttotemp.VtToTemp(pv2182A),
                    current_pressure if current_pressure is not None else 0.0
                )
                
            except Exception as e:
                print("データ記録エラー: {}".format(e))
            
            # 終了条件
            if (rate[k] > 0 and float(Tsvtemp) >= float(Tf[k])):
                print(k)
                print(rate[k])
                print("Run " + str(k) + " was finished")                           
                print("wait for" + str(wait[k]) + " sec.")
                t4 = time.time()
                break
                            
            elif (rate[k] < 0 and float(Tsvtemp) <= float(Tf[k])):
                print(k)
                print(Tsv[k])
                print(Tf[k])
                print("Run " + str(k) + " was finished")
                print("wait for" + str(wait[k]) + " sec.")     
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

def check_current_status():
    """現在の温度と圧力を確認"""
    print("\n=== 現在の状態 ===")
    try:
        # Chinoの温度を取得
        chino = ChinoController()
        chino.connect()
        chino_temp = chino.get_temperature()
        print("Chino設定温度: {:.2f} K".format(chino_temp))
    except Exception as e:
        print("Chino温度取得エラー: {}".format(e))

    try:
        # Keithley 2000の電圧を取得して温度に変換
        pv2000 = float(getTemperature())*1000000
        k2000_temp = vttotemp.VtToTemp(pv2000)
        print("Keithley 2000温度: {:.2f} K".format(k2000_temp))
    except Exception as e:
        print("Keithley 2000温度取得エラー: {}".format(e))

    try:
        # 圧力を取得
        pressure_control = PressureControl()
        current_pressure = pressure_control.get_pressure()
        if current_pressure is not None:
            print("現在の圧力: {:.2f} MPa".format(current_pressure))
        else:
            print("圧力取得エラー: 値が取得できません")
        pressure_control.close()
    except Exception as e:
        print("圧力取得エラー: {}".format(e))

    print("================\n")

def load_experiment_conditions():
    """実験条件を入力またはファイルから読み込む"""
    print("\n=== 実験条件の入力 ===")
    print("1. 手動入力")
    print("2. ファイルから読み込み")
    choice = input("選択してください (1/2): ")
    
    if choice == "2":
        # ファイルから読み込み
        try:
            filename = input("実験条件ファイルのパスを入力してください: ")
            with open(filename, 'r') as f:
                reader = csv.DictReader(f)
                conditions = next(reader)
                return {
                    'sample_name': conditions['Sample Name'],
                    'experimenter': conditions['Experimenter'],
                    'start_temperature': float(conditions['Start Temperature']),
                    'end_temperature': float(conditions['End Temperature']),
                    'heating_rate': float(conditions['Heating Rate']),
                    'wait_time': float(conditions['Wait Time']),
                    'pressure': float(conditions['Pressure']),
                    'pressure_tolerance': float(conditions['Pressure Tolerance'])
                }
        except Exception as e:
            print("ファイル読み込みエラー: {}".format(e))
            print("手動入力に切り替えます。")
    
    # 手動入力
    return {
        'sample_name': input("サンプル名を入力してください: "),
        'experimenter': input("実験者名を入力してください: "),
        'start_temperature': float(input("開始温度 (K) を入力してください: ")),
        'end_temperature': float(input("終了温度 (K) を入力してください: ")),
        'heating_rate': float(input("昇温速度 (K/min) を入力してください: ")),
        'wait_time': float(input("待機時間 (min) を入力してください: ")),
        'pressure': float(input("目標圧力 (MPa) を入力してください: ")),
        'pressure_tolerance': float(input("圧力許容範囲 (%) を入力してください: "))
    }

def main():
    try:
        # 現在の状態を確認
        check_current_status()
        
        # 実験条件の設定
        experiment_data = load_experiment_conditions()

        # 実験条件の確認
        print("\n=== 実験条件 ===")
        print("サンプル名: {}".format(experiment_data['sample_name']))
        print("実験者: {}".format(experiment_data['experimenter']))
        print("開始温度: {:.2f} K".format(experiment_data['start_temperature']))
        print("終了温度: {:.2f} K".format(experiment_data['end_temperature']))
        print("昇温速度: {:.2f} K/min".format(experiment_data['heating_rate']))
        print("待機時間: {:.2f} min".format(experiment_data['wait_time']))
        print("目標圧力: {:.2f} MPa".format(experiment_data['pressure']))
        print("圧力許容範囲: {:.2f} %".format(experiment_data['pressure_tolerance']))
        print("================\n")

        # 実験開始の確認
        confirm = input("実験を開始しますか？ (y/n): ")
        if confirm.lower() != 'y':
            print("実験を中止します。")
            return

        # 実験マネージャーの初期化
        experiment_manager = ExperimentManager()
        
        # 実験IDの取得と実験条件ファイルの作成
        experiment_id = experiment_manager.add_experiment_history(experiment_data)
        exp_cond_file = experiment_manager.create_experiment_condition_file(experiment_data)
        results_file = experiment_manager.get_results_file_path(experiment_id)
        error_file = experiment_manager.get_error_file_path(experiment_id)

        # 実験条件の設定
        conditions = ExperimentConditions(
            start_temp=experiment_data['start_temperature'],
            end_temp=experiment_data['end_temperature'],
            heating_rate=experiment_data['heating_rate'],
            wait_time=experiment_data['wait_time'],
            pressure=experiment_data['pressure'],
            pressure_tolerance=experiment_data['pressure_tolerance']
        )

        # デバイスの初期化
        chino = ChinoController()
        chino.connect()
        pressure_control = PressureControl()
        
        # 測定データの初期化
        time_data = []
        temp_data = []
        press_data = []
        volt_data = []
        error_log = []
        
        # 測定開始
        start_time = time.time()
        current_temp = experiment_data['start_temperature']
        target_temp = experiment_data['end_temperature']
        heating_rate = experiment_data['heating_rate']
        
        while current_temp < target_temp:
            try:
                # 温度の更新
                current_temp += heating_rate * (time.time() - start_time) / 60.0
                chino.set_temperature(current_temp)
                
                # データの収集
                current_time = time.time() - start_time
                current_pressure = pressure_control.get_pressure()
                current_voltage = getTemperature()
                
                # データの保存
                time_data.append(current_time)
                temp_data.append(current_temp)
                press_data.append(current_pressure)
                volt_data.append(current_voltage)
                
                # 結果の保存
                with open(results_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([current_time, current_temp, current_pressure, current_voltage])
                
                time.sleep(1)  # 1秒待機
                
            except Exception as e:
                error_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                error_log.append([error_time, "Measurement Error", str(e)])
                print(f"測定エラー: {e}")
                continue
        
        # エラー情報の保存
        with open(error_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Time', 'Error Type', 'Message'])
            for error in error_log:
                writer.writerow(error)
        
        # デバイスの終了処理
        chino.disconnect()
        pressure_control.close()
        
        print("測定が完了しました。")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        traceback.print_exc()
        
        # エラーログの保存
        if 'error_file' in locals():
            with open(error_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Time', 'Error Type', 'Message'])
                writer.writerow([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                               "Fatal Error", str(e)])
        
        # デバイスの終了処理
        if 'chino' in locals():
            chino.disconnect()
        if 'pressure_control' in locals():
            pressure_control.close()
        
        raise  # エラーを再送出

if __name__ == "__main__":
    main()

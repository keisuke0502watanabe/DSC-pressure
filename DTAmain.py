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
from DTAmodule.visualize import DTAVisualizer
from DTAmodule.experiment_manager import ExperimentManager
from collections import deque
import keyboard
import matplotlib.pyplot as plt

#鍵 
key_name = '/home/pi/Desktop/json_file/teruyama/my-project-333708-dad962c8e2e4.json'
sheet_name = 'teruyama test1'
#APIにログイン
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name(key_name, scope)
gc = gspread.authorize(credentials)

# 実験管理システムの初期化
experiment_manager = ExperimentManager()

# 安全制限値の設定
MAX_TEMPERATURE = 440.0  # K
MAX_PRESSURE = 200.0    # MPa
ROOM_TEMPERATURE = 298.15  # K (25℃)

# スプレッドシート設定
SPREADSHEET_BUFFER_SIZE = 100  # バッファサイズ
SPREADSHEET_UPDATE_INTERVAL = 300  # 更新間隔（秒）

# グラフ更新設定
GRAPH_UPDATE_INTERVAL = 1000  # ミリ秒
MAX_DATA_POINTS = 1000  # 表示するデータポイントの最大数

class SpreadsheetManager:
    def __init__(self, key_name, sheet_name):
        """スプレッドシート管理クラス
        
        Args:
            key_name (str): 認証キーファイルのパス
            sheet_name (str): スプレッドシート名
        """
        self.key_name = key_name
        self.sheet_name = sheet_name
        self.buffer = deque(maxlen=SPREADSHEET_BUFFER_SIZE)
        self.last_update = time.time()
        self.wks = None
        self.sheet_pointer = 2
        self.initialize_sheet()
    
    def initialize_sheet(self):
        """スプレッドシートの初期化"""
        try:
            scope = ['https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive']
            credentials = ServiceAccountCredentials.from_json_keyfile_name(
                self.key_name, scope)
            gc = gspread.authorize(credentials)
            self.wks = gc.open(self.sheet_name).sheet1
            self.set_column_headers()
        except Exception as e:
            print("スプレッドシートの初期化エラー: {}".format(e))
    
    def set_column_headers(self):
        """カラムヘッダーの設定"""
        headers = {
            'A1': 'set Temp. / K',
            'B1': 'time / s',
            'C1': 'dt of Kei2000/ microvolts',
            'D1': 'dt of Kei2182A/ microvolts',
            'E1': 'dt of Kei2000/K',
            'F1': 'dt of Kei2182A/K',
            'G1': 'Heat or cool',
            'H1': 'Run',
            'I1': 'Date',
            'J1': 'Date time',
            'K1': 'Sample name',
            'L1': 'Pressure / MPa'
        }
        for cell, value in headers.items():
            self.wks.update_acell(cell, value)
    
    def add_data(self, data):
        """データのバッファへの追加
        
        Args:
            data (dict): 追加するデータ
        """
        self.buffer.append(data)
        
        # バッファが一杯になったか、更新間隔が経過した場合に更新
        current_time = time.time()
        if (len(self.buffer) >= SPREADSHEET_BUFFER_SIZE or 
            current_time - self.last_update >= SPREADSHEET_UPDATE_INTERVAL):
            self.flush()
    
    def flush(self):
        """バッファのデータをスプレッドシートに書き込む"""
        if not self.buffer:
            return
        
        try:
            # データの準備
            rows = []
            for data in self.buffer:
                row = [
                    data['temperature'],
                    data['time'],
                    data['pv2000'],
                    data['pv2182A'],
                    data['temp2000'],
                    data['temp2182A'],
                    data['heat_or_cool'],
                    data['run'],
                    data['date'],
                    data['time_of_day'],
                    data['sample_name'],
                    data['pressure']
                ]
                rows.append(row)
            
            # 一括更新
            cell_range = 'A{}:L{}'.format(
                self.sheet_pointer,
                self.sheet_pointer + len(rows) - 1
            )
            self.wks.update(cell_range, rows)
            
            # ポインタの更新
            self.sheet_pointer += len(rows)
            
            # バッファのクリアと最終更新時刻の更新
            self.buffer.clear()
            self.last_update = time.time()
            
        except Exception as e:
            print("スプレッドシート更新エラー: {}".format(e))
            # エラーが発生した場合、バッファは保持される

# スプレッドシートマネージャーの初期化
spreadsheet_manager = SpreadsheetManager(
    key_name='/home/pi/Desktop/json_file/teruyama/my-project-333708-dad962c8e2e4.json',
    sheet_name='teruyama test1'
)

def emergency_shutdown(pressure_control, error_message):
    """緊急停止処理
    
    Args:
        pressure_control: 圧力制御オブジェクト
        error_message (str): エラーメッセージ
    """
    print("\n!!! 緊急停止 !!!")
    print("理由: {}".format(error_message))
    
    # 温度を室温に設定
    try:
        Chino.setSv(ROOM_TEMPERATURE)
        print("温度を室温 ({:.1f}K) に設定しました".format(ROOM_TEMPERATURE))
    except Exception as e:
        print("温度設定エラー: {}".format(e))
    
    # 圧力制御の停止
    if pressure_control is not None:
        try:
            pressure_control.close()
            print("圧力制御を停止しました")
        except Exception as e:
            print("圧力制御停止エラー: {}".format(e))
    
    # エラーログの記録
    try:
        with open("emergency_shutdown.log", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("[{}] {}\n".format(timestamp, error_message))
    except Exception as e:
        print("ログ記録エラー: {}".format(e))
    
    print("\nシステムを終了します")
    os._exit(1)  # 強制終了

def get_experiment_conditions():
    """実験条件の取得"""
    print("\n実験条件の設定")
    print("1: 新しい実験条件を入力")
    print("2: 過去の実験条件から選択")
    
    choice = input("選択してください (1/2): ")
    
    if choice == "1":
        # 新しい実験条件の入力
        print("\n実験IDの設定")
        print("1: 自動生成")
        print("2: 手動入力")
        id_choice = input("選択してください (1/2): ")
        
        experiment_id = None
        if id_choice == "2":
            try:
                experiment_id = int(input("実験IDを入力してください: "))
            except ValueError:
                print("無効な実験IDです。自動生成を使用します。")
                experiment_id = experiment_manager.get_next_available_id()
        
        experiment_data = {
            "sample_name": input("サンプル名を入力してください: "),
            "experimenter": input("実験者名を入力してください: "),
            "start_temperature": float(input("開始温度 (K) を入力してください: ")),
            "end_temperature": float(input("終了温度 (K) を入力してください: ")),
            "heating_rate": float(input("昇温速度 (K/min) を入力してください: ")),
            "wait_time": float(input("待機時間 (min) を入力してください: ")),
            "pressure": float(input("目標圧力 (MPa) を入力してください: ")),
            "pressure_tolerance": float(input("圧力許容範囲 (%) を入力してください: "))
        }
        
        try:
            # 実験条件ファイルの作成
            filenameExpCond = experiment_manager.create_experiment_condition_file(experiment_data)
            
            # 実験履歴に追加
            experiment_id = experiment_manager.add_experiment_history(experiment_data, experiment_id)
            print("実験ID: {} で保存されました".format(experiment_id))
            
            return filenameExpCond, experiment_data["sample_name"]
        except ValueError as e:
            print("エラー: {}".format(e))
            return get_experiment_conditions()
    
    elif choice == "2":
        # 過去の実験条件の表示
        history = experiment_manager.get_experiment_history()
        if not history:
            print("過去の実験条件がありません")
            return get_experiment_conditions()
        
        print("\n過去の実験条件:")
        for exp in history:
            print("ID: {}".format(exp['id']))
            print("サンプル名: {}".format(exp['sample_name']))
            print("実験者: {}".format(exp['experimenter']))
            print("日時: {}".format(exp['timestamp']))
            print("---")
        
        exp_id = int(input("使用する実験IDを入力してください: "))
        exp_data = experiment_manager.get_experiment_by_id(exp_id)
        
        if exp_data is None:
            print("無効な実験IDです")
            return get_experiment_conditions()
        
        # 実験条件ファイルの作成
        filenameExpCond = experiment_manager.create_experiment_condition_file(exp_data)
        return filenameExpCond, exp_data["sample_name"]
    
    else:
        print("無効な選択です")
        return get_experiment_conditions()

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

# 実験条件の取得
filenameExpCond, sampleName = get_experiment_conditions()
filenameResults = filenameExpCond.replace('ExpCond.csv', 'Results.csv')
filenameError = filenameExpCond.replace('ExpCond.csv', 'Error.csv')

# メインプログラムの開始部分を修正
Q2 = input("Have you already measured? y/n:")
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

# 可視化オブジェクトの初期化
visualizer = DTAVisualizer()

# 手動プロッターの初期化
class ManualPlotter:
    def __init__(self):
        """手動プロッターの初期化"""
        self.current_data = {
            'times': [],
            'chino_temps': [],
            'k2000_temps': [],
            'dta_signals': [],
            'pressures': []
        }
        self.historical_data = {}  # 過去の実験データを保存
        self.active_plots = set()  # 現在表示中の実験ID
        
        # キーボードイベントの設定
        keyboard.on_press(self.handle_keyboard)
        
        # プロットウィンドウの初期化
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(10, 8))
        plt.ion()  # インタラクティブモードを有効化
    
    def load_historical_data(self, experiment_id, data_file):
        """過去の実験データを読み込む
        
        Args:
            experiment_id (str): 実験ID
            data_file (str): データファイルのパス
        """
        try:
            data = {
                'times': [],
                'chino_temps': [],
                'k2000_temps': [],
                'dta_signals': [],
                'pressures': []
            }
            
            with open(data_file, 'r') as f:
                reader = csv.reader(f, delimiter='\t')
                next(reader)  # ヘッダーをスキップ
                for row in reader:
                    if len(row) >= 12:  # 必要な列数があることを確認
                        data['times'].append(float(row[1]))
                        data['chino_temps'].append(float(row[0]))
                        data['k2000_temps'].append(float(row[4]))
                        data['dta_signals'].append(float(row[5]))
                        data['pressures'].append(float(row[11]) if row[11] != 'N/A' else 0.0)
            
            self.historical_data[experiment_id] = data
            print("実験ID {} のデータを読み込みました".format(experiment_id))
            
        except Exception as e:
            print("データ読み込みエラー: {}".format(e))
    
    def update_data(self, time_val, chino_temp, k2000_temp, dta, pressure):
        """現在のデータを更新
        
        Args:
            time_val (float): 時間
            chino_temp (float): Chinoの温度
            k2000_temp (float): K2000の温度
            dta (float): DTA信号
            pressure (float): 圧力
        """
        self.current_data['times'].append(time_val)
        self.current_data['chino_temps'].append(chino_temp)
        self.current_data['k2000_temps'].append(k2000_temp)
        self.current_data['dta_signals'].append(dta)
        self.current_data['pressures'].append(pressure)
    
    def update_plot(self):
        """プロットの更新"""
        self.ax1.clear()
        self.ax2.clear()
        
        # 現在のデータをプロット
        self.ax1.plot(self.current_data['times'], self.current_data['chino_temps'], 
                     'b-', label='Current Chino Temperature')
        self.ax1.plot(self.current_data['times'], self.current_data['k2000_temps'], 
                     'c-', label='Current K2000 Temperature')
        self.ax1.plot(self.current_data['times'], self.current_data['pressures'], 
                     'g-', label='Current Pressure')
        
        # 過去のデータをプロット
        for exp_id in self.active_plots:
            if exp_id in self.historical_data:
                data = self.historical_data[exp_id]
                self.ax1.plot(data['times'], data['chino_temps'], 
                            'b--', alpha=0.5, label='Exp {} Chino'.format(exp_id))
                self.ax1.plot(data['times'], data['k2000_temps'], 
                            'c--', alpha=0.5, label='Exp {} K2000'.format(exp_id))
                self.ax1.plot(data['times'], data['pressures'], 
                            'g--', alpha=0.5, label='Exp {} Pressure'.format(exp_id))
                self.ax2.plot(data['times'], data['dta_signals'], 
                            'r--', alpha=0.5, label='Exp {} DTA'.format(exp_id))
        
        # 現在のDTA信号をプロット
        self.ax2.plot(self.current_data['times'], self.current_data['dta_signals'], 
                     'r-', label='Current DTA Signal')
        
        # 軸の設定
        self.ax1.set_ylabel('Temperature (K) / Pressure (MPa)')
        self.ax1.set_title('DTA Measurement')
        self.ax1.grid(True)
        self.ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        self.ax2.set_xlabel('Time (s)')
        self.ax2.set_ylabel('DTA Signal (K)')
        self.ax2.grid(True)
        self.ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 軸の範囲の自動調整
        all_times = self.current_data['times'].copy()
        all_temps = (self.current_data['chino_temps'] + 
                    self.current_data['k2000_temps'] + 
                    self.current_data['pressures'])
        all_dta = self.current_data['dta_signals'].copy()
        
        for exp_id in self.active_plots:
            if exp_id in self.historical_data:
                data = self.historical_data[exp_id]
                all_times.extend(data['times'])
                all_temps.extend(data['chino_temps'] + data['k2000_temps'] + data['pressures'])
                all_dta.extend(data['dta_signals'])
        
        if all_times:
            self.ax1.set_xlim(min(all_times), max(all_times))
            self.ax2.set_xlim(min(all_times), max(all_times))
            
            temp_min = min(all_temps)
            temp_max = max(all_temps)
            self.ax1.set_ylim(temp_min * 0.95, temp_max * 1.05)
            
            dta_min = min(all_dta)
            dta_max = max(all_dta)
            self.ax2.set_ylim(dta_min * 1.05, dta_max * 1.05)
        
        plt.tight_layout()
        plt.draw()
        plt.pause(0.1)
    
    def handle_keyboard(self, event):
        """キーボードイベントの処理
        
        Args:
            event: キーボードイベント
        """
        if event.name == 'u':  # 更新
            self.update_plot()
            print("グラフを更新しました")
        elif event.name == 'r':  # リセット
            self.current_data = {k: [] for k in self.current_data}
            self.active_plots.clear()
            self.update_plot()
            print("グラフをリセットしました")
        elif event.name == 's':  # 保存
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            plt.savefig("dta_plot_{}.png".format(timestamp), dpi=300, bbox_inches='tight')
            print("グラフを保存しました: dta_plot_{}.png".format(timestamp))
        elif event.name == 'q':  # 終了
            plt.close('all')
            print("グラフ表示を終了します")
        elif event.name == 'l':  # 過去データの読み込み
            exp_id = input("読み込む実験IDを入力してください: ")
            data_file = input("データファイルのパスを入力してください: ")
            self.load_historical_data(exp_id, data_file)
            self.active_plots.add(exp_id)
            self.update_plot()
        elif event.name == 'h':  # 過去データの表示/非表示
            exp_id = input("表示/非表示を切り替える実験IDを入力してください: ")
            if exp_id in self.active_plots:
                self.active_plots.remove(exp_id)
                print("実験ID {} の表示を非表示にしました".format(exp_id))
            else:
                self.active_plots.add(exp_id)
                print("実験ID {} の表示を表示にしました".format(exp_id))
            self.update_plot()
    
    def show(self):
        """グラフの表示"""
        plt.show(block=True)

plotter = ManualPlotter()

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
            f.write(result)
            
            # スプレッドシートへのデータ追加
            spreadsheet_manager.add_data({
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
                'sample_name': sampleName,
                'pressure': current_pressure if current_pressure is not None else 0.0
            })
            
            # データの収集（グラフ更新はキーボード入力で行う）
            plotter.update_data(
                float(t1-t0),
                float(Tsvtemp),  # Chinoの温度
                vttotemp.VtToTemp(pv2000),  # K2000の温度
                vttotemp.VtToTemp(pv2182A),  # DTA信号
                current_pressure if current_pressure is not None else 0.0
            )
            
        except Exception as e:
            print("データ記録エラー: {}".format(e))
        
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

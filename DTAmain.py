import Keigetpv
from DTAmodule.chino_control import ChinoController
import time
import datetime
import threading
import csv
import os
import vttotemp
import traceback
from natsort import natsorted
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
from pressure_control import PressureControl
from DTAmodule.visualize import DTAVisualizer
from DTAmodule.experiment_manager import ExperimentManager, ExperimentMetadata
from collections import deque
import matplotlib.pyplot as plt

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
        self.connection_error = False
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        self.initialize_sheet()
    
    def initialize_sheet(self):
        """スプレッドシートの初期化"""
        try:
            # scope = ['https://spreadsheets.google.com/feeds',
            #         'https://www.googleapis.com/auth/drive']
            # credentials = ServiceAccountCredentials.from_json_keyfile_name(
            #     self.key_name, scope)
            # gc = gspread.authorize(credentials)
            self.wks = None
            self.set_column_headers()
            self.connection_error = False
            self.retry_count = 0
        except Exception as e:
            print("スプレッドシートの初期化エラー: {}".format(e))
            self.connection_error = True
            self._log_error("スプレッドシート初期化エラー", e)
    
    def set_column_headers(self):
        """カラムヘッダーの設定"""
        pass  # 一時的に無効化
    
    def add_data(self, data):
        """データのバッファへの追加"""
        pass  # 一時的に無効化
    
    def flush(self):
        """バッファのデータをスプレッドシートに書き込む"""
        pass  # 一時的に無効化
    
    def _log_error(self, error_type, error):
        """エラーをログファイルに記録
        
        Args:
            error_type (str): エラーの種類
            error (Exception): エラーオブジェクト
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("spreadsheet_errors.log", "a") as f:
                f.write("[{}] {}: {}\n".format(timestamp, error_type, str(error)))
        except:
            pass  # ログ記録に失敗してもプログラムは継続
    
    def check_connection(self):
        """スプレッドシートへの接続を確認"""
        if self.connection_error:
            try:
                self.initialize_sheet()
                if not self.connection_error:
                    print("スプレッドシートへの接続が回復しました。")
                    return True
            except:
                pass
        return not self.connection_error

# スプレッドシートマネージャーの初期化
spreadsheet_manager = SpreadsheetManager(
    key_name='/home/pi/Desktop/json_file/olha/my-project-333708-dad962c8e2e4.json',
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
        chino = ChinoController()
        chino.connect()
        chino.set_temperature(ROOM_TEMPERATURE)
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
wks = None
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

class KeyboardHandler:
    """keyboardライブラリの代替クラス"""
    
    def __init__(self):
        self.callback = None
        self.running = False
        self.thread = None
    
    def on_press(self, callback):
        """キープレスのコールバックを設定"""
        self.callback = callback
        
    def start_listener(self):
        """キーボードリスナーを開始"""
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_listener(self):
        """キーボードリスナーを停止"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _listen_loop(self):
        """キー入力を監視するループ"""
        print("\nキーボードコマンド:")
        print("u: グラフ更新")
        print("r: グラフリセット")
        print("s: グラフ保存")
        print("q: 終了")
        print("l: 過去データの読み込み")
        print("h: 過去データの表示/非表示切り替え")
        print("a: 過去データの透明度調整")
        print("e: 実験履歴のエクスポート")
        print("コマンドを入力してください (Enter後に実行されます):")
        
        while self.running:
            try:
                command = input().strip().lower()
                if command and self.callback:
                    class Event:
                        def __init__(self, name):
                            self.name = name
                    
                    event = Event(command)
                    self.callback(event)
                    
                    if command == 'q':
                        self.running = False
                        break
                        
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

class MenuDrivenPlotter:
    """メニュー形式のプロッター（keyboardライブラリ不要）"""
    
    def __init__(self):
        self.current_data = {
            'times': [],
            'chino_temps': [],
            'k2000_temps': [],
            'dta_signals': [],
            'pressures': []
        }
        self.historical_data = {}
        self.active_plots = set()
        self.plot_alpha = 0.5
        self.running = True
        
        # プロットウィンドウの初期化
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        plt.ion()
    
    def show_menu(self):
        """メニューを表示"""
        print("\n=== DTA プロッター ===")
        print("1. グラフ更新")
        print("2. グラフリセット")
        print("3. グラフ保存")
        print("4. 過去データの読み込み")
        print("5. 過去データの表示/非表示切り替え")
        print("6. 透明度調整")
        print("7. 実験履歴のエクスポート")
        print("0. 終了")
        print("==================")
    
    def run(self):
        """メニュー駆動のメインループ"""
        while self.running:
            self.show_menu()
            choice = input("選択してください (0-7): ")
            
            if choice == '1':
                self.update_plot()
                print("グラフを更新しました")
            elif choice == '2':
                self.reset_plot()
                print("グラフをリセットしました")
            elif choice == '3':
                self.save_plot()
            elif choice == '4':
                self.load_historical_data()
            elif choice == '5':
                self.toggle_plot_visibility()
            elif choice == '6':
                self.adjust_transparency()
            elif choice == '7':
                self.export_history()
            elif choice == '0':
                self.running = False
                print("プロッターを終了します")
            else:
                print("無効な選択です")
    
    def update_plot(self):
        """グラフを更新"""
        # 既存のupdate_plotメソッドの実装
        pass
    
    def reset_plot(self):
        """グラフをリセット"""
        self.current_data = {k: [] for k in self.current_data}
        self.active_plots.clear()
        self.update_plot()
    
    def save_plot(self):
        """グラフを保存"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig("dta_plot_{}.png".format(timestamp), dpi=300, bbox_inches='tight')
        print("グラフを保存しました: dta_plot_{}.png".format(timestamp))
    
    def load_historical_data(self):
        """過去データを読み込む"""
        # 既存のload_historical_dataメソッドの実装
        pass
    
    def toggle_plot_visibility(self):
        """過去データの表示/非表示を切り替え"""
        # 既存のtoggle_plot_visibilityメソッドの実装
        pass
    
    def adjust_transparency(self):
        """透明度を調整"""
        try:
            alpha = float(input("過去データの透明度を入力してください (0.0-1.0): "))
            if 0.0 <= alpha <= 1.0:
                self.plot_alpha = alpha
                self.update_plot()
                print("透明度を {} に設定しました".format(alpha))
            else:
                print("透明度は0.0から1.0の間で指定してください")
        except ValueError:
            print("無効な入力です")
    
    def export_history(self):
        """実験履歴をエクスポート"""
        # 既存のexport_historyメソッドの実装
        pass

plotter = MenuDrivenPlotter()

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
            result = "{:.3f}\t{:.3f}\t{:.10f}\t{:.10f}\t{:.10f}\t{:.10f}\t{}\t{}\t{:.3f}\n".format(
                float(Tsvtemp), float(t1-t0), pv2000, pv2182A, 
                vttotemp.VtToTemp(pv2000), vttotemp.VtToTemp(pv2182A),
                hoc, k, current_pressure if current_pressure is not None else 0.0
            )
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
                'pressure': current_pressure if current_pressure is not None else 0.0
            })
            
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

def save_results_header(filename, experiment_data):
    """実験結果ファイルのヘッダーを保存
    
    Args:
        filename (str): ファイル名
        experiment_data (dict): 実験データ
    """
    with open(filename, 'w') as f:
        # メタデータの保存
        f.write("ID\t{}\n".format(experiment_data.get('id', '')))
        f.write("Sample Name\t{}\n".format(experiment_data.get('sample_name', '')))
        f.write("Lot\t{}\n".format(experiment_data.get('lot', '')))
        f.write("Experimenter\t{}\n".format(experiment_data.get('experimenter', '')))
        f.write("Date\t{}\n".format(datetime.datetime.now().strftime("%Y/%m/%d")))
        
        # データヘッダーの保存
        f.write("set Temp. / K\ttime / s\tdt of Kei2000/ microvolts\tdt of Kei2182A/ microvolts\tdt of Kei2000/K\tdt of Kei2182A/K\tHeat or cool\tRun\tPressure / MPa\n")

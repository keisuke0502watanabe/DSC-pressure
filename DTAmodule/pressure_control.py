import serial
import time

class PressureController:
    def __init__(self, port='/dev/ttyUSB0', baudrate=9600):
        """圧力制御器の初期化
        
        Args:
            port (str): シリアルポート
            baudrate (int): ボーレート
        """
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect(self):
        """シリアル接続を確立"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=2
            )
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            return False
    
    def disconnect(self):
        """シリアル接続を切断"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, command):
        """コマンドを送信
        
        Args:
            command (str): 送信するコマンド
        """
        if not self.ser or not self.ser.is_open:
            if not self.connect():
                return None
        
        try:
            self.ser.write((command + "\n").encode())
            time.sleep(0.1)
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def get_pressure(self):
        """現在の圧力を取得
        
        Returns:
            float: 測定された圧力値 (MPa)
        """
        try:
            # リセット
            self.send_command("*RST")
            
            # DC電圧測定モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            
            # ノイズ低減設定
            self.send_command("VOLT:DC:NPLC 10")
            
            # 測定範囲設定
            self.send_command("VOLT:DC:RANG 0.1")
            
            # 継続測定開始
            self.send_command("INIT:CONT ON")
            
            # 設定が反映されるのを待つ
            time.sleep(0.5)
            
            # データ取得
            response = self.send_command("FETC?")
            
            if response:
                # 電圧値を圧力に変換
                voltage = float(response)
                pressure = (voltage - 0.00001) * 133400 / 5.12285 + 0.1
                return pressure
            return None
        except Exception as e:
            print("圧力取得エラー: {}".format(e))
            return None
    
    def set_pressure(self, pressure):
        """目標圧力を設定
        
        Args:
            pressure (float): 設定する圧力値 (MPa)
        """
        try:
            # 圧力値を電圧に変換
            voltage = ((pressure - 0.1) * 5.12285 / 133400) + 0.00001
            
            # リセット
            self.send_command("*RST")
            
            # DC電圧出力モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            
            # 出力範囲設定
            self.send_command("VOLT:DC:RANG 0.1")
            
            # 電圧を設定
            self.send_command("VOLT:DC {}".format(voltage))
            
            # 出力開始
            self.send_command("OUTP ON")
            
            return True
        except Exception as e:
            print("圧力設定エラー: {}".format(e))
            return False

# グローバルインスタンス
pressure = PressureController()

def getPressure():
    """圧力を取得
    
    Returns:
        float: 測定された圧力値 (MPa)
    """
    return pressure.get_pressure()

def setPressure(pressure_value):
    """目標圧力を設定
    
    Args:
        pressure_value (float): 設定する圧力値 (MPa)
    """
    return pressure.set_pressure(pressure_value) 
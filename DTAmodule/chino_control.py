import serial
import time

class ChinoController:
    def __init__(self, port='/dev/ttyUSB1', baudrate=9600):
        """Chino温度制御器の初期化
        
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
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
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
            self.ser.write("{}\r\n".format(command).encode())
            time.sleep(0.1)
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def get_temperature(self):
        """現在の温度を取得
        
        Returns:
            float: 測定された温度値
        """
        response = self.send_command("PV?")
        try:
            return float(response)
        except:
            return 0.0
    
    def set_temperature(self, temp):
        """目標温度を設定
        
        Args:
            temp (float): 設定する温度値
        """
        command = "SV{}".format(temp)
        return self.send_command(command)

# グローバルインスタンス
chino = ChinoController()

def getChinoTemp():
    """Chinoの温度を取得
    
    Returns:
        float: 測定された温度値
    """
    return chino.get_temperature()

def setChinoTemp(temp):
    """Chinoの目標温度を設定
    
    Args:
        temp (float): 設定する温度値
    """
    return chino.set_temperature(temp) 
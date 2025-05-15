import serial
import time

class Keithley2000:
    def __init__(self, port='/dev/ttyUSB2', baudrate=9600):
        """Keithley 2000の初期化
        
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
            self.ser.write("{}\n".format(command).encode())
            time.sleep(0.1)
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def get_voltage(self):
        """電圧を測定
        
        Returns:
            float: 測定された電圧値
        """
        response = self.send_command(":MEAS:VOLT:DC?")
        try:
            return float(response)
        except:
            return 0.0

class Keithley2182A:
    def __init__(self, port='/dev/ttyUSB3', baudrate=9600):
        """Keithley 2182Aの初期化"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect(self):
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            return False
    
    def disconnect(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def send_command(self, command):
        if not self.ser or not self.ser.is_open:
            if not self.connect():
                return None
        
        try:
            self.ser.write("{}\n".format(command).encode())
            time.sleep(0.1)
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def get_voltage(self):
        response = self.send_command(":MEAS:VOLT:DC?")
        try:
            return float(response)
        except:
            return 0.0

# グローバルインスタンス
k2000 = Keithley2000()
k2182a = Keithley2182A()

def getPv2000():
    """Keithley 2000の電圧を取得
    
    Returns:
        float: 測定された電圧値
    """
    return k2000.get_voltage()

def getPv2182A():
    """Keithley 2182Aの電圧を取得
    
    Returns:
        float: 測定された電圧値
    """
    return k2182a.get_voltage() 
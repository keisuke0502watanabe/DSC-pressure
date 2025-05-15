import serial
import time

class Keithley2000:
    def __init__(self, port='/dev/ttyUSB3', baudrate=9600):
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
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
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
    
    def initialize(self):
        """機器の初期化と設定"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.1)
            
            # RS-232C設定
            self.send_command("SYST:COMM:SER:BAUD {}".format(self.baudrate))
            self.send_command("SYST:COMM:SER:PAR NONE")
            self.send_command("SYST:COMM:SER:SBIT 1")
            self.send_command("SYST:COMM:SER:TERM LF")
            
            # DC電圧測定モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            
            # ノイズ低減設定
            self.send_command("VOLT:DC:NPLC 10")
            
            # 測定範囲設定
            self.send_command("VOLT:DC:RANG 0.1")
            
            # 継続測定開始
            self.send_command("INIT:CONT ON")
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False
    
    def get_voltage(self):
        """電圧を測定
        
        Returns:
            float: 測定された電圧値
        """
        try:
            # 初期化
            if not self.initialize():
                return None
            
            # 設定が反映されるのを待つ
            time.sleep(0.5)
            
            # データ取得
            response = self.send_command("FETC?")
            
            if response:
                return float(response)
            return None
        except Exception as e:
            print("電圧取得エラー: {}".format(e))
            return None

class Keithley2182A:
    def __init__(self, port='/dev/ttyUSB2', baudrate=9600):
        """Keithley 2182Aの初期化"""
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2
            )
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
            self.ser.write((command + "\n").encode())
            time.sleep(0.1)
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def initialize(self):
        """機器の初期化と設定"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.1)
            
            # RS-232C設定
            self.send_command("SYST:COMM:SER:BAUD {}".format(self.baudrate))
            self.send_command("SYST:COMM:SER:PAR NONE")
            self.send_command("SYST:COMM:SER:SBIT 1")
            self.send_command("SYST:COMM:SER:TERM LF")
            
            # DC電圧測定モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            
            # ノイズ低減設定
            self.send_command("VOLT:DC:NPLC 10")
            
            # 測定範囲設定
            self.send_command("VOLT:DC:RANG 0.1")
            
            # 継続測定開始
            self.send_command("INIT:CONT ON")
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False
    
    def get_voltage(self):
        """電圧を測定
        
        Returns:
            float: 測定された電圧値
        """
        try:
            # 初期化
            if not self.initialize():
                return None
            
            # 設定が反映されるのを待つ
            time.sleep(0.5)
            
            # データ取得
            response = self.send_command("FETC?")
            
            if response:
                return float(response)
            return None
        except Exception as e:
            print("電圧取得エラー: {}".format(e))
            return None

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
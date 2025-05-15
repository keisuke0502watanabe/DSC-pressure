import serial
import time
import struct

class ChinoController:
    def __init__(self, port='/dev/ttyUSB1', baudrate=4800):
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
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=5
            )
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            return False
    
    def disconnect(self):
        """シリアル接続を切断"""
        if self.ser and self.ser.is_open:
            self.ser.close()
    
    def calculate_checksum(self, data):
        """チェックサムを計算
        
        Args:
            data (str): チェックサムを計算するデータ
            
        Returns:
            str: チェックサム値（16進数文字列）
        """
        chkSum = 0
        for char in data:
            chkSum += ord(char)
        chkSum += 3  # ETXの値
        
        # 16進数に変換し、上位バイトと下位バイトを入れ替え
        hex_sum = hex(chkSum)[2:].upper().zfill(2)
        return hex_sum[1] + hex_sum[0]
    
    def send_command(self, command):
        """コマンドを送信
        
        Args:
            command (str): 送信するコマンド
        """
        if not self.ser or not self.ser.is_open:
            if not self.connect():
                return None
        
        try:
            # STX
            self.ser.write(bytes([0x02]))
            
            # コマンド
            self.ser.write(command.encode())
            
            # チェックサム計算
            chkSum = self.calculate_checksum(command)
            
            # ETX
            self.ser.write(bytes([0x03]))
            
            # チェックサム送信
            self.ser.write(chkSum.encode())
            
            # CR+LF
            self.ser.write(b'\r\n')
            
            # 応答待ち
            response = ""
            comma_count = 0
            while True:
                if self.ser.in_waiting > 0:
                    recv_data = self.ser.read()
                    value = struct.unpack_from("B", recv_data, 0)[0]
                    char = chr(value)
                    
                    if char == ",":
                        comma_count += 1
                        if comma_count == 5:  # PV値の位置
                            pv = response[14:23]
                            return float(pv)
                    response += char
                    
                    if value == 10:  # LF
                        break
            
            return None
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None
    
    def get_temperature(self):
        """現在の温度を取得
        
        Returns:
            float: 測定された温度値
        """
        command = " 1, 1,"
        return self.send_command(command)
    
    def set_temperature(self, temp):
        """目標温度を設定
        
        Args:
            temp (float): 設定する温度値
        """
        command = " 2, 4,1,{:.1f},".format(temp)
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
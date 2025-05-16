#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time

class Keithley2000Pressure:
    """圧力測定用K2000制御クラス"""
    def __init__(self, port='/dev/ttyUSB0'):
        self.port = port
        self.ser = None
        self.connected = False

    def connect(self):
        """シリアルポートに接続"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,
                write_timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            self.connected = True
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            self.connected = False
            return False

    def disconnect(self):
        """シリアルポートを切断"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False

    def send_command(self, command):
        """コマンドを送信して応答を取得"""
        if not self.connected:
            raise Exception("デバイスに接続されていません")
        
        try:
            # コマンドを送信
            self.ser.write((command + '\n').encode())
            time.sleep(0.1)
            
            # 応答を読み取り
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None

    def initialize(self):
        """圧力測定用の初期化"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.1)
            
            # DC電圧測定モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            time.sleep(0.1)
            
            # ノイズ低減設定
            self.send_command("VOLT:DC:NPLC 1")
            time.sleep(0.1)
            
            # 測定範囲を自動に設定
            self.send_command("VOLT:DC:RANG:AUTO ON")
            time.sleep(0.1)
            
            # 連続測定を開始
            self.send_command("INIT:CONT ON")
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False

    def get_voltage(self):
        """電圧を測定"""
        try:
            # 最新の測定値を取得
            voltage = float(self.send_command("FETCH?"))
            return voltage
        except Exception as e:
            print("電圧測定エラー: {}".format(e))
            return None

class Keithley2000Temperature:
    """電圧測定用K2000制御クラス"""
    def __init__(self, port='/dev/ttyUSB2'):
        self.port = port
        self.ser = None
        self.connected = False

    def connect(self):
        """シリアルポートに接続"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,
                write_timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            self.connected = True
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            self.connected = False
            return False

    def disconnect(self):
        """シリアルポートを切断"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False

    def send_command(self, command):
        """コマンドを送信して応答を取得"""
        if not self.connected:
            raise Exception("デバイスに接続されていません")
        
        try:
            # コマンドを送信
            self.ser.write((command + '\n').encode())
            time.sleep(0.1)
            
            # 応答を読み取り
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None

    def initialize(self):
        """電圧測定用の初期化"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.1)
            
            # DC電圧測定モードに設定
            self.send_command("FUNC 'VOLT:DC'")
            time.sleep(0.1)
            
            # ノイズ低減設定
            self.send_command("VOLT:DC:NPLC 1")
            time.sleep(0.1)
            
            # 測定範囲を自動に設定
            self.send_command("VOLT:DC:RANG:AUTO ON")
            time.sleep(0.1)
            
            # 連続測定を開始
            self.send_command("INIT:CONT ON")
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False

    def get_voltage(self):
        """電圧を測定"""
        try:
            # 最新の測定値を取得
            voltage = float(self.send_command("FETCH?"))
            return voltage
        except Exception as e:
            print("電圧測定エラー: {}".format(e))
            return None

class Keithley2182A:
    """2182A制御クラス"""
    def __init__(self, port='/dev/ttyUSB1'):
        self.port = port
        self.ser = None
        self.connected = False

    def connect(self):
        """シリアルポートに接続"""
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=2,
                write_timeout=2,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False
            )
            self.connected = True
            return True
        except Exception as e:
            print("接続エラー: {}".format(e))
            self.connected = False
            return False

    def disconnect(self):
        """シリアルポートを切断"""
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.connected = False

    def send_command(self, command):
        """コマンドを送信して応答を取得"""
        if not self.connected:
            raise Exception("デバイスに接続されていません")
        
        try:
            # コマンドを送信
            self.ser.write((command + '\n').encode())
            time.sleep(0.1)
            
            # 応答を読み取り
            response = self.ser.readline().decode().strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None

    def initialize(self):
        """初期化"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.5)  # リセット後の待機時間を延長
            
            # DC電圧測定モードに設定
            self.send_command("SENS:FUNC 'VOLT:DC'")
            time.sleep(0.2)
            
            # ノイズ低減設定
            self.send_command("SENS:VOLT:DC:NPLC 1")
            time.sleep(0.1)
            
            # 測定範囲を自動に設定
            self.send_command("SENS:VOLT:DC:RANG:AUTO ON")
            time.sleep(0.1)
            
            # 連続測定を開始
            self.send_command("INIT:CONT ON")
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False

    def get_voltage(self):
        """電圧を測定"""
        try:
            # 最新の測定値を取得
            voltage = float(self.send_command("FETCH?"))
            return voltage
        except Exception as e:
            print("電圧測定エラー: {}".format(e))
            return None

# グローバルインスタンス
k2000_pressure = Keithley2000Pressure()
k2000_temperature = Keithley2000Temperature()
k2182a = Keithley2182A()

def getPressure():
    """圧力センサーの電圧を取得し、圧力に変換
    
    Returns:
        tuple: (電圧値（V）, 圧力値（Pa）)
        None: 測定に失敗した場合
    """
    try:
        if not k2000_pressure.connected:
            k2000_pressure.connect()
            k2000_pressure.initialize()
        
        # 電圧を取得
        voltage = k2000_pressure.get_voltage()
        if voltage is None:
            return None
            
        # 圧力に変換（V → Pa）
        pressure = (voltage - 0.00001) * 133400 / 5.12285 + 0.1
        return (voltage, pressure)
    except Exception as e:
        print("圧力測定エラー: {}".format(e))
        return None

def getTemperature():
    """温度センサーの電圧を取得
    
    Returns:
        float: 温度センサーの電圧値（V）
        None: 測定に失敗した場合
    """
    try:
        if not k2000_temperature.connected:
            k2000_temperature.connect()
            k2000_temperature.initialize()
        return k2000_temperature.get_voltage()
    except Exception as e:
        print("温度測定エラー: {}".format(e))
        return None

def getVoltage2182A():
    """2182Aの電圧を取得
    
    Returns:
        float: 2182Aの電圧値（V）
        None: 測定に失敗した場合
    """
    try:
        if not k2182a.connected:
            k2182a.connect()
            k2182a.initialize()
        return k2182a.get_voltage()
    except Exception as e:
        print("2182A測定エラー: {}".format(e))
        return None 
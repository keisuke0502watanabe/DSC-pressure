#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import sys

class ChinoController:
    """Chino制御クラス"""
    def __init__(self, port='/dev/ttyUSB3'):
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
            # コマンドを送信（ASCIIエンコーディング）
            self.ser.write((command + '\r\n').encode('ascii'))
            time.sleep(0.1)
            
            # 応答を読み取り（ASCIIエンコーディング）
            response = self.ser.readline().decode('ascii').strip()
            return response
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None

    def initialize(self):
        """初期化"""
        try:
            # リセット
            self.send_command("*RST")
            time.sleep(0.5)
            
            # 出力をオフ
            self.send_command("OUTP OFF")
            time.sleep(0.1)
            
            # 温度単位をケルビンに設定
            self.send_command("UNIT:TEMP K")
            time.sleep(0.1)
            
            return True
        except Exception as e:
            print("初期化エラー: {}".format(e))
            return False

    def set_temperature(self, temp):
        """温度を設定
        
        Args:
            temp (float): 設定温度（K）
        """
        try:
            command = "SOUR:TEMP {:.1f}".format(temp)
            self.send_command(command)
            time.sleep(0.1)
        except Exception as e:
            print("温度設定エラー: {}".format(e))

    def get_temperature(self):
        """現在の温度を取得
        
        Returns:
            float: 現在の温度（K）
            None: 測定に失敗した場合
        """
        try:
            response = self.send_command("MEAS:TEMP?")
            if response:
                return float(response)
            return None
        except Exception as e:
            print("温度取得エラー: {}".format(e))
            return None

    def output_on(self):
        """出力をオン"""
        try:
            self.send_command("OUTP ON")
            time.sleep(0.1)
        except Exception as e:
            print("出力オンエラー: {}".format(e))

    def output_off(self):
        """出力をオフ"""
        try:
            self.send_command("OUTP OFF")
            time.sleep(0.1)
        except Exception as e:
            print("出力オフエラー: {}".format(e))

def main():
    # Chinoコントローラーのインスタンスを作成
    chino = ChinoController()
    
    try:
        # 接続
        if not chino.connect():
            print("Chinoへの接続に失敗しました")
            return
        
        # 初期化
        if not chino.initialize():
            print("初期化に失敗しました")
            return
        
        print("Chino制御テストを開始します")
        print("1: 温度設定")
        print("2: 現在の温度取得")
        print("3: 出力オン")
        print("4: 出力オフ")
        print("q: 終了")
        
        while True:
            cmd = input("コマンドを入力してください: ")
            
            if cmd == '1':
                temp = float(input("設定温度（K）を入力してください: "))
                chino.set_temperature(temp)
                print("温度を {}K に設定しました".format(temp))
            
            elif cmd == '2':
                temp = chino.get_temperature()
                if temp is not None:
                    print("現在の温度: {}K".format(temp))
                else:
                    print("温度の取得に失敗しました")
            
            elif cmd == '3':
                chino.output_on()
                print("出力をオンにしました")
            
            elif cmd == '4':
                chino.output_off()
                print("出力をオフにしました")
            
            elif cmd.lower() == 'q':
                break
            
            else:
                print("無効なコマンドです")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
    
    finally:
        # 出力をオフにして切断
        chino.output_off()
        chino.disconnect()
        print("Chinoとの接続を切断しました")

if __name__ == "__main__":
    main() 
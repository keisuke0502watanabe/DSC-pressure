#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import serial
import time
import sys
import struct

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
                bytesize=serial.SEVENBITS,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                timeout=5,
                write_timeout=5,
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
        """コマンドを送信して応答を取得"""
        if not self.connected:
            raise Exception("デバイスに接続されていません")
        
        try:
            # STX
            self.ser.write(bytes([0x02]))
            
            # コマンド
            self.ser.write(command.encode('ascii'))
            
            # チェックサム計算
            chkSum = self.calculate_checksum(command)
            
            # ETX
            self.ser.write(bytes([0x03]))
            
            # チェックサム送信
            self.ser.write(chkSum.encode('ascii'))
            
            # CR+LF
            self.ser.write(b'\r\n')
            
            # 応答待ち
            c = ""
            camma = 0
            i = 0
            while True:
                if self.ser.in_waiting > 0:
                    recv_data = self.ser.read()
                    a = struct.unpack_from("B", recv_data, 0)
                    b = a[0]
                    b = chr(b)
                    if b == ",":
                        camma += 1
                        if camma == 5:
                            pv = c[14:23]
                            try:
                                return float(pv)
                            except ValueError:
                                print("温度値の変換に失敗しました: {}".format(pv))
                                print("応答全体: {}".format(c))
                                return None
                    c += b
                    i += 1
            
            print("応答が受信できませんでした")
            return None
        except Exception as e:
            print("コマンド送信エラー: {}".format(e))
            return None

    def initialize(self):
        """初期化"""
        try:
            # シリアルバッファをクリア
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # リアルデータ要求
            self.send_command(" 1, 1,")  # リアルデータ要求
            time.sleep(0.1)
            
            # 応答を読み捨て
            while self.ser.in_waiting > 0:
                self.ser.read()
            
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
            # シリアルバッファをクリア
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            # STX
            self.ser.write(bytes([0x02]))
            
            # コマンド
            command = " 2, 4,1," + str(temp) + ","
            print("送信コマンド: {}".format(command))
            self.ser.write(command.encode('ascii'))
            
            # チェックサム計算
            chkSum = 0
            for char in command:
                chkSum += ord(char)
            chkSum += 3  # ETXの値
            
            # ETX
            self.ser.write(bytes([0x03]))
            
            # チェックサム送信
            hex_sum = hex(chkSum)[2:].upper().zfill(2)
            chkSumValue = hex_sum[1] + hex_sum[0]
            print("チェックサム: {}".format(chkSumValue))
            self.ser.write(chkSumValue.encode('ascii'))
            
            # CR+LF
            self.ser.write(b'\r\n')
            
            # 応答待ち
            time.sleep(0.1)
            
            # 応答を読み取り
            response = ""
            while self.ser.in_waiting > 0:
                recv_data = self.ser.read()
                value = struct.unpack_from("B", recv_data, 0)[0]
                char = chr(value)
                response += char
                if value == 10:  # LF
                    break
            
            print("応答: {}".format(response))
            
        except Exception as e:
            print("温度設定エラー: {}".format(e))

    def get_temperature(self):
        """現在の温度を取得
        
        Returns:
            float: 現在の温度（K）
            None: 測定に失敗した場合
        """
        try:
            # シリアルバッファをクリア
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            
            command = " 1, 1,"  # 温度取得コマンド
            temp = self.send_command(command)
            if temp is not None:
                print("取得した温度値: {}K".format(temp))
            return temp
        except Exception as e:
            print("温度取得エラー: {}".format(e))
            return None

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
            
            elif cmd.lower() == 'q':
                break
            
            else:
                print("無効なコマンドです")
            
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\nプログラムを終了します")
    
    finally:
        chino.disconnect()
        print("Chinoとの接続を切断しました")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import serial
from Keigetpv import Keithley2000

def check_port_exists(port):
    """USBポートの存在を確認"""
    try:
        with serial.Serial(port) as ser:
            return True
    except:
        return False

def check_communication_settings(k2000):
    """通信設定を確認"""
    try:
        # 現在の設定を確認
        print("\n現在の通信設定:")
        
        # ボーレート確認
        baud = k2000.send_command("SYST:COMM:SER:BAUD?")
        print("ボーレート: {}".format(baud))
        
        # パリティ確認
        parity = k2000.send_command("SYST:COMM:SER:PAR?")
        print("パリティ: {}".format(parity))
        
        # データビット確認
        data_bits = k2000.send_command("SYST:COMM:SER:SBIT?")
        print("ストップビット: {}".format(data_bits))
        
        # 終端文字確認
        term = k2000.send_command("SYST:COMM:SER:TERM?")
        print("終端文字: {}".format(term))
        
        return True
    except Exception as e:
        print("通信設定の確認に失敗しました: {}".format(e))
        return False

def set_communication_settings(k2000):
    """通信設定を行う"""
    try:
        print("\n通信設定を更新します...")
        
        # ボーレート設定
        k2000.send_command("SYST:COMM:SER:BAUD 9600")
        time.sleep(0.1)
        
        # 終端文字設定
        k2000.send_command("SYST:COMM:SER:TERM LF")
        time.sleep(0.1)
        
        print("通信設定を更新しました")
        return True
    except Exception as e:
        print("通信設定の更新に失敗しました: {}".format(e))
        return False

def main():
    """K2000を使用した温度測定のテスト"""
    print("K2000温度測定テストを開始します...")
    
    # K2000のインスタンスを作成
    k2000 = Keithley2000()
    reconnect_attempts = 0
    max_reconnect_attempts = 3
    
    while True:
        try:
            # ポートの存在を確認
            if not check_port_exists(k2000.port):
                print("\nUSBポートが見つかりません: {}".format(k2000.port))
                print("USBケーブルを再接続してください...")
                time.sleep(5)  # 5秒待機
                continue
            
            # 接続を確立
            if not k2000.connect():
                print("K2000への接続に失敗しました")
                time.sleep(2)
                continue
            
            print("K2000に接続しました")
            reconnect_attempts = 0  # 接続成功したらリセット
            
            # 通信設定の設定
            if not set_communication_settings(k2000):
                print("通信設定の更新に失敗しました")
                k2000.disconnect()
                time.sleep(2)
                continue
            
            # 初期化
            if not k2000.initialize():
                print("K2000の初期化に失敗しました")
                k2000.disconnect()
                time.sleep(2)
                continue
            
            print("K2000の初期化が完了しました")
            
            # 測定開始
            print("\n温度測定を開始します...")
            print("Ctrl+Cで終了できます")
            
            while True:
                try:
                    # 電圧を測定
                    voltage = k2000.get_voltage()
                    
                    if voltage is not None:
                        # 電圧から温度に変換（K型熱電対の場合）
                        temperature = voltage * 25.0  # 仮の変換係数
                        print("\r現在の温度: {:.2f}°C (電圧: {:.6f}V)".format(temperature, voltage), end="")
                    else:
                        print("\r測定エラー", end="")
                        raise Exception("測定値が取得できません")
                    
                    time.sleep(1)  # 1秒待機
                    
                except KeyboardInterrupt:
                    print("\n測定を終了します")
                    return
                except Exception as e:
                    print("\nエラーが発生しました: {}".format(e))
                    break
            
        except KeyboardInterrupt:
            print("\n測定を終了します")
            break
        except Exception as e:
            print("\n予期せぬエラーが発生しました: {}".format(e))
            reconnect_attempts += 1
            
            if reconnect_attempts >= max_reconnect_attempts:
                print("再接続の試行回数が上限に達しました。プログラムを終了します。")
                break
            
            print("再接続を試みます... (試行回数: {}/{})".format(
                reconnect_attempts, max_reconnect_attempts))
            time.sleep(2)
        
        finally:
            # 接続を切断
            try:
                k2000.disconnect()
                print("K2000との接続を切断しました")
            except:
                pass

if __name__ == "__main__":
    main() 
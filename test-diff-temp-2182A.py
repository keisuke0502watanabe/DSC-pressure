#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import serial
from Keigetpv import Keithley2182A

def check_port_exists(port):
    """USBポートの存在を確認"""
    try:
        with serial.Serial(port) as ser:
            return True
    except:
        return False

def check_2182a_settings(k2182a):
    """2182Aの設定を確認"""
    try:
        print("\n2182Aの設定を確認します...")
        
        # 機器の識別情報
        idn = k2182a.send_command("*IDN?")
        print("機器情報: {}".format(idn))
        
        # 現在の測定モード
        func = k2182a.send_command("FUNC?")
        print("測定モード: {}".format(func))
        
        # 測定範囲
        range_val = k2182a.send_command("VOLT:DC:RANG?")
        print("測定範囲: {}".format(range_val))
        
        # ノイズ低減設定
        nplc = k2182a.send_command("VOLT:DC:NPLC?")
        print("NPLC設定: {}".format(nplc))
        
        return True
    except Exception as e:
        print("設定の確認に失敗しました: {}".format(e))
        return False

def main():
    """2182Aを使用した電圧測定のテスト"""
    print("2182A電圧測定テストを開始します...")
    
    # 2182Aのインスタンスを作成
    k2182a = Keithley2182A(port='/dev/ttyUSB2')
    reconnect_attempts = 0
    max_reconnect_attempts = 3
    
    while True:
        try:
            # ポートの存在を確認
            if not check_port_exists(k2182a.port):
                print("\nUSBポートが見つかりません: {}".format(k2182a.port))
                print("USBケーブルを再接続してください...")
                time.sleep(5)  # 5秒待機
                continue
            
            # 接続を確立
            if not k2182a.connect():
                print("2182Aへの接続に失敗しました")
                time.sleep(2)
                continue
            
            print("2182Aに接続しました")
            reconnect_attempts = 0  # 接続成功したらリセット
            
            # 設定の確認
            if not check_2182a_settings(k2182a):
                print("設定の確認に失敗しました")
                k2182a.disconnect()
                time.sleep(2)
                continue
            
            # 初期化
            if not k2182a.initialize():
                print("2182Aの初期化に失敗しました")
                k2182a.disconnect()
                time.sleep(2)
                continue
            
            print("2182Aの初期化が完了しました")
            
            # 測定開始
            print("\n電圧測定を開始します...")
            print("Ctrl+Cで終了できます")
            
            while True:
                try:
                    # 電圧を測定
                    voltage = k2182a.get_voltage()
                    
                    if voltage is not None:
                        print("\r現在の電圧: {:.6f}V".format(voltage), end="")
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
                k2182a.disconnect()
                print("2182Aとの接続を切断しました")
            except:
                pass

if __name__ == "__main__":
    main() 
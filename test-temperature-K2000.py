#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
import serial
from Keigetpv import Keithley2000Temperature

def check_port_exists(port):
    """USBポートの存在を確認"""
    try:
        with serial.Serial(port) as ser:
            return True
    except:
        return False

def check_k2000_settings(k2000):
    """K2000の設定を確認"""
    try:
        print("\nK2000の設定を確認します...")
        
        # 機器の識別情報
        idn = k2000.send_command("*IDN?")
        print("機器情報: {}".format(idn))
        
        # 現在の測定モード
        func = k2000.send_command("FUNC?")
        print("測定モード: {}".format(func))
        
        # 熱電対タイプ
        tc_type = k2000.send_command("TEMP:TC:TYPE?")
        print("熱電対タイプ: {}".format(tc_type))
        
        # ノイズ低減設定
        nplc = k2000.send_command("TEMP:NPLC?")
        print("NPLC設定: {}".format(nplc))
        
        # エラー状態
        error = k2000.send_command("SYST:ERR?")
        print("エラー状態: {}".format(error))
        
        return True
    except Exception as e:
        print("設定の確認に失敗しました: {}".format(e))
        return False

def main():
    """K2000を使用した温度測定のテスト"""
    print("K2000温度測定テストを開始します...")
    
    # K2000のインスタンスを作成（ポートをttyUSB1に変更）
    k2000 = Keithley2000Temperature(port='/dev/ttyUSB1')
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
            
            # 設定の確認
            if not check_k2000_settings(k2000):
                print("設定の確認に失敗しました")
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
                    # 温度を測定
                    temperature = k2000.get_temperature()
                    
                    if temperature is not None:
                        print("\r現在の温度: {:.2f}°C".format(temperature), end="")
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
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys
from Keigetpv import Keithley2000

def main():
    """K2000を使用した温度測定のテスト"""
    print("K2000温度測定テストを開始します...")
    
    # K2000のインスタンスを作成
    k2000 = Keithley2000()
    
    try:
        # 接続を確立
        if not k2000.connect():
            print("K2000への接続に失敗しました")
            return
        
        print("K2000に接続しました")
        
        # 初期化
        if not k2000.initialize():
            print("K2000の初期化に失敗しました")
            return
        
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
                    # 電圧から温度への変換係数は使用する熱電対の種類によって異なります
                    # ここでは例として、K型熱電対の近似式を使用
                    temperature = voltage * 25.0  # 仮の変換係数
                    
                    print("\r現在の温度: {:.2f}°C (電圧: {:.6f}V)".format(temperature, voltage), end="")
                else:
                    print("\r測定エラー", end="")
                
                time.sleep(1)  # 1秒待機
                
            except KeyboardInterrupt:
                print("\n測定を終了します")
                break
            except Exception as e:
                print("\nエラーが発生しました: {}".format(e))
                break
    
    finally:
        # 接続を切断
        k2000.disconnect()
        print("K2000との接続を切断しました")

if __name__ == "__main__":
    main() 
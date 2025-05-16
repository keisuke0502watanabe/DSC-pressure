import os
import datetime
from DTAmodule.chino_control import ChinoController

# 安全制限値の設定
MAX_TEMPERATURE = 440.0  # K
MAX_PRESSURE = 200.0    # MPa
ROOM_TEMPERATURE = 298.15  # K (25℃)

def emergency_shutdown(pressure_control, error_message):
    """緊急停止処理
    
    Args:
        pressure_control: 圧力制御オブジェクト
        error_message (str): エラーメッセージ
    """
    print("\n!!! 緊急停止 !!!")
    print("理由: {}".format(error_message))
    
    # 温度を室温に設定
    try:
        chino = ChinoController()
        chino.connect()
        chino.set_temperature(ROOM_TEMPERATURE)
        print("温度を室温 ({:.1f}K) に設定しました".format(ROOM_TEMPERATURE))
    except Exception as e:
        print("温度設定エラー: {}".format(e))
    
    # 圧力制御の停止
    if pressure_control is not None:
        try:
            pressure_control.close()
            print("圧力制御を停止しました")
        except Exception as e:
            print("圧力制御停止エラー: {}".format(e))
    
    # エラーログの記録
    try:
        with open("emergency_shutdown.log", "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write("[{}] {}\n".format(timestamp, error_message))
    except Exception as e:
        print("ログ記録エラー: {}".format(e))
    
    print("\nシステムを終了します")
    os._exit(1)  # 強制終了 
import time
from Keigetpv import getPv2000, getPv2182A
from DTAmodule.chino_control import getChinoTemp, setChinoTemp
from DTAmodule.pressure_control import getPressure, setPressure

def test_devices():
    print("機器との通信テストを開始します...")
    
    # 各機器の値を取得
    try:
        print("\n1. 温度測定 (K2000):")
        temp_k2000 = getPv2000()
        print("K2000温度: {} V".format(temp_k2000))
        
        print("\n2. 温度差測定 (2182A):")
        temp_diff = getPv2182A()
        print("温度差: {} V".format(temp_diff))
        
        print("\n3. Chino温度制御器:")
        temp_chino = getChinoTemp()
        print("現在の温度: {} °C".format(temp_chino))
        
        print("\n4. 圧力制御器:")
        pressure = getPressure()
        print("現在の圧力: {} MPa".format(pressure))
        
    except Exception as e:
        print("エラーが発生しました: {}".format(e))
        return
    
    print("\nテスト完了！")

if __name__ == "__main__":
    test_devices() 
import serial
import time
import gpiod

class PressureControl:
    def __init__(self, port="/dev/ttyUSB0", baudrate=9600, timeout=2):
        # KEITHLEY 2000-2の初期化
        self.ser = serial.Serial(port, baudrate, timeout=timeout)
        
        # GPIO設定
        self.CW_PIN = 18
        self.CCW_PIN = 17
        self.pulse_count = 200
        self.pulse_width = 0.0005
        self.pulse_delay = 0.0005
        
        # GPIOチップの初期化
        self.chip_path = None
        for i in range(10):
            try:
                chip = gpiod.Chip('gpiochip{}'.format(i), gpiod.Chip.OPEN_BY_NAME)
                self.chip_path = 'gpiochip{}'.format(i)
                chip.close()
                break
            except:
                continue
        
        if self.chip_path is None:
            raise Exception("使用可能なGPIOチップが見つかりませんでした")
        
        self.chip = gpiod.Chip(self.chip_path, gpiod.Chip.OPEN_BY_NAME)
        self.cw_line = self.chip.get_line(self.CW_PIN)
        self.ccw_line = self.chip.get_line(self.CCW_PIN)
        
        # GPIOを出力モードに設定
        self.cw_line.request(consumer="motor_control", type=gpiod.LINE_REQ_DIR_OUT)
        self.ccw_line.request(consumer="motor_control", type=gpiod.LINE_REQ_DIR_OUT)
        
        # 初期状態は0
        self.cw_line.set_value(0)
        self.ccw_line.set_value(0)
        
        # KEITHLEY 2000-2の初期設定
        self._setup_keithley()
    
    def _setup_keithley(self):
        """KEITHLEY 2000-2の初期設定"""
        self.send_command("*RST")
        self.send_command("FUNC 'VOLT:DC'")
        self.send_command("VOLT:DC:NPLC 10")
        self.send_command("VOLT:DC:RANG 0.1")
        self.send_command("INIT:CONT ON")
        time.sleep(0.5)
    
    def send_command(self, command):
        """KEITHLEY 2000-2にコマンドを送信"""
        self.ser.write((command + "\n").encode())
        time.sleep(0.1)
        response = self.ser.readline().decode().strip()
        return response
    
    def get_pressure(self):
        """現在の圧力を取得"""
        response = self.send_command("FETC?")
        try:
            voltage = float(response)
            pressure = (voltage - 0.00001) * 133400 / 5.12285 + 0.1
            return pressure
        except ValueError:
            return None
    
    def send_pulses(self, line, pulses):
        """モーターにパルスを送信"""
        for i in range(pulses):
            line.set_value(1)
            time.sleep(self.pulse_width)
            line.set_value(0)
            time.sleep(self.pulse_delay)
    
    def increase_pressure(self):
        """圧力を上げる"""
        self.send_pulses(self.cw_line, self.pulse_count)
    
    def decrease_pressure(self):
        """圧力を下げる"""
        self.send_pulses(self.ccw_line, self.pulse_count)
    
    def set_target_pressure(self, target_pressure, tolerance=0.1, max_attempts=10):
        """目標圧力に設定
        
        Args:
            target_pressure (float): 目標圧力 (MPa)
            tolerance (float): 許容誤差 (MPa)
            max_attempts (int): 最大試行回数
        """
        for _ in range(max_attempts):
            current_pressure = self.get_pressure()
            if current_pressure is None:
                continue
            
            if abs(current_pressure - target_pressure) <= tolerance:
                return True
            
            if current_pressure < target_pressure:
                self.increase_pressure()
            else:
                self.decrease_pressure()
            
            time.sleep(1)  # 圧力が安定するのを待つ
        
        return False
    
    def close(self):
        """リソースを解放"""
        try:
            self.cw_line.release()
            self.ccw_line.release()
        except:
            pass
        self.chip.close()
        self.ser.close() 
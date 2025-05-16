import time
import datetime
from collections import deque

# スプレッドシート設定
SPREADSHEET_BUFFER_SIZE = 100  # バッファサイズ
SPREADSHEET_UPDATE_INTERVAL = 300  # 更新間隔（秒）

class SpreadsheetManager:
    def __init__(self, key_name, sheet_name):
        """スプレッドシート管理クラス
        
        Args:
            key_name (str): 認証キーファイルのパス
            sheet_name (str): スプレッドシート名
        """
        self.key_name = key_name
        self.sheet_name = sheet_name
        self.buffer = deque(maxlen=SPREADSHEET_BUFFER_SIZE)
        self.last_update = time.time()
        self.wks = None
        self.sheet_pointer = 2
        self.connection_error = False
        self.retry_count = 0
        self.max_retries = 3
        self.retry_delay = 5  # 秒
        self.initialize_sheet()
    
    def initialize_sheet(self):
        """スプレッドシートの初期化"""
        try:
            # scope = ['https://spreadsheets.google.com/feeds',
            #         'https://www.googleapis.com/auth/drive']
            # credentials = ServiceAccountCredentials.from_json_keyfile_name(
            #     self.key_name, scope)
            # gc = gspread.authorize(credentials)
            self.wks = None
            self.set_column_headers()
            self.connection_error = False
            self.retry_count = 0
        except Exception as e:
            print("スプレッドシートの初期化エラー: {}".format(e))
            self.connection_error = True
            self._log_error("スプレッドシート初期化エラー", e)
    
    def set_column_headers(self):
        """カラムヘッダーの設定"""
        if self.wks is None:
            return
            
        headers = {
            'A1': 'set Temp. / K',
            'B1': 'time / s',
            'C1': 'dt of Kei2000/ microvolts',
            'D1': 'dt of Kei2182A/ microvolts',
            'E1': 'dt of Kei2000/K',
            'F1': 'dt of Kei2182A/K',
            'G1': 'Heat or cool',
            'H1': 'Run',
            'I1': 'Date',
            'J1': 'Date time',
            'K1': 'Sample name'
        }
        
        for cell, value in headers.items():
            self.wks.update_acell(cell, value)
    
    def update_cells(self, cell_list):
        """セルの更新
        
        Args:
            cell_list: 更新するセルのリスト
        """
        if self.wks is None:
            return
        self.wks.update_cells(cell_list)
    
    def get_cell_range(self, start_row, num_rows=10):
        """セル範囲の取得
        
        Args:
            start_row (int): 開始行
            num_rows (int): 取得する行数
        
        Returns:
            list: セルのリスト
        """
        if self.wks is None:
            return None
            
        try:
            return self.wks.range('A{}:K{}'.format(start_row, start_row + num_rows - 1))
        except:
            self.wks.add_rows(10000)
            return self.wks.range('A{}:K{}'.format(start_row, start_row + num_rows - 1))
    
    def add_data(self, data):
        """データのバッファへの追加"""
        self.buffer.append(data)
        current_time = time.time()
        if (current_time - self.last_update) >= SPREADSHEET_UPDATE_INTERVAL:
            self.flush()
    
    def flush(self):
        """バッファのデータをスプレッドシートに書き込む"""
        if not self.buffer or self.wks is None:
            return
            
        try:
            while self.buffer:
                data = self.buffer.popleft()
                # データの書き込み処理
                pass
            self.last_update = time.time()
        except Exception as e:
            print("スプレッドシート更新エラー: {}".format(e))
            self._log_error("スプレッドシート更新エラー", e)
    
    def _log_error(self, error_type, error):
        """エラーをログファイルに記録
        
        Args:
            error_type (str): エラーの種類
            error (Exception): エラーオブジェクト
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open("spreadsheet_errors.log", "a") as f:
                f.write("[{}] {}: {}\n".format(timestamp, error_type, str(error)))
        except:
            pass  # ログ記録に失敗してもプログラムは継続
    
    def check_connection(self):
        """スプレッドシートへの接続を確認"""
        if self.connection_error:
            try:
                self.initialize_sheet()
                if not self.connection_error:
                    print("スプレッドシートへの接続が回復しました。")
                    return True
            except:
                pass
        return not self.connection_error 
import threading

class KeyboardHandler:
    """keyboardライブラリの代替クラス"""
    
    def __init__(self):
        self.callback = None
        self.running = False
        self.thread = None
    
    def on_press(self, callback):
        """キープレスのコールバックを設定"""
        self.callback = callback
        
    def start_listener(self):
        """キーボードリスナーを開始"""
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop)
        self.thread.daemon = True
        self.thread.start()
    
    def stop_listener(self):
        """キーボードリスナーを停止"""
        self.running = False
        if self.thread:
            self.thread.join()
    
    def _listen_loop(self):
        """キー入力を監視するループ"""
        print("\nキーボードコマンド:")
        print("u: グラフ更新")
        print("r: グラフリセット")
        print("s: グラフ保存")
        print("q: 終了")
        print("l: 過去データの読み込み")
        print("h: 過去データの表示/非表示切り替え")
        print("a: 過去データの透明度調整")
        print("e: 実験履歴のエクスポート")
        print("コマンドを入力してください (Enter後に実行されます):")
        
        while self.running:
            try:
                command = input().strip().lower()
                if command and self.callback:
                    class Event:
                        def __init__(self, name):
                            self.name = name
                    
                    event = Event(command)
                    self.callback(event)
                    
                    if command == 'q':
                        self.running = False
                        break
                        
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break 
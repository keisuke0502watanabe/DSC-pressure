import threading
import matplotlib.pyplot as plt
import datetime

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

class MenuDrivenPlotter:
    """メニュー形式のプロッター（keyboardライブラリ不要）"""
    
    def __init__(self):
        self.current_data = {
            'times': [],
            'chino_temps': [],
            'k2000_temps': [],
            'dta_signals': [],
            'pressures': []
        }
        self.historical_data = {}
        self.active_plots = set()
        self.plot_alpha = 0.5
        self.running = True
        
        # プロットウィンドウの初期化
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        plt.ion()
    
    def show_menu(self):
        """メニューを表示"""
        print("\n=== DTA プロッター ===")
        print("1. グラフ更新")
        print("2. グラフリセット")
        print("3. グラフ保存")
        print("4. 過去データの読み込み")
        print("5. 過去データの表示/非表示切り替え")
        print("6. 透明度調整")
        print("7. 実験履歴のエクスポート")
        print("0. 終了")
        print("==================")
    
    def run(self):
        """メニュー駆動のメインループ"""
        while self.running:
            self.show_menu()
            choice = input("選択してください (0-7): ")
            
            if choice == '1':
                self.update_plot()
                print("グラフを更新しました")
            elif choice == '2':
                self.reset_plot()
                print("グラフをリセットしました")
            elif choice == '3':
                self.save_plot()
            elif choice == '4':
                self.load_historical_data()
            elif choice == '5':
                self.toggle_plot_visibility()
            elif choice == '6':
                self.adjust_transparency()
            elif choice == '7':
                self.export_history()
            elif choice == '0':
                self.running = False
                print("プロッターを終了します")
            else:
                print("無効な選択です")
    
    def update_plot(self):
        """グラフを更新"""
        # 既存のupdate_plotメソッドの実装
        pass
    
    def reset_plot(self):
        """グラフをリセット"""
        self.current_data = {k: [] for k in self.current_data}
        self.active_plots.clear()
        self.update_plot()
    
    def save_plot(self):
        """グラフを保存"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        plt.savefig("dta_plot_{}.png".format(timestamp), dpi=300, bbox_inches='tight')
        print("グラフを保存しました: dta_plot_{}.png".format(timestamp))
    
    def load_historical_data(self):
        """過去データを読み込む"""
        # 既存のload_historical_dataメソッドの実装
        pass
    
    def toggle_plot_visibility(self):
        """過去データの表示/非表示を切り替え"""
        # 既存のtoggle_plot_visibilityメソッドの実装
        pass
    
    def adjust_transparency(self):
        """透明度を調整"""
        try:
            alpha = float(input("過去データの透明度を入力してください (0.0-1.0): "))
            if 0.0 <= alpha <= 1.0:
                self.plot_alpha = alpha
                self.update_plot()
                print("透明度を {} に設定しました".format(alpha))
            else:
                print("透明度は0.0から1.0の間で指定してください")
        except ValueError:
            print("無効な入力です")
    
    def export_history(self):
        """実験履歴をエクスポート"""
        # 既存のexport_historyメソッドの実装
        pass 
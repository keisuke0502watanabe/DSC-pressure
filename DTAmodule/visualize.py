import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from datetime import datetime
import os

class DTAVisualizer:
    def __init__(self, save_dir="Experiment_result/plots"):
        """DTAデータの可視化クラス
        
        Args:
            save_dir (str): グラフの保存ディレクトリ
        """
        self.save_dir = save_dir
        os.makedirs(save_dir, exist_ok=True)
        
        # グラフのスタイル設定
        plt.style.use('seaborn')
        self.colors = plt.cm.tab10.colors
        
        # メモリ使用量を抑えるための設定
        plt.rcParams['figure.max_open_warning'] = 10  # 同時に開く図の最大数を制限
        plt.rcParams['figure.dpi'] = 150  # DPIを下げてメモリ使用量を削減
    
    def plot_dta_curve(self, data_file, save_name=None):
        """DTA曲線をプロット
        
        Args:
            data_file (str): データファイルのパス
            save_name (str, optional): 保存するファイル名
        """
        # データの読み込み（必要な列のみ）
        df = pd.read_csv(data_file, sep='\t', usecols=['set Temp. / K', 'time / s', 'dt of Kei2182A/K', 'Sample Name'])
        
        # プロットの作成
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10), sharex=True)
        
        # 温度プロット
        ax1.plot(df['time / s'], df['set Temp. / K'], 
                label='Set Temperature', color=self.colors[0])
        ax1.set_ylabel('Temperature (K)')
        ax1.legend()
        ax1.grid(True)
        
        # DTA信号プロット
        ax2.plot(df['time / s'], df['dt of Kei2182A/K'], 
                label='DTA Signal', color=self.colors[1])
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('DTA Signal (K)')
        ax2.legend()
        ax2.grid(True)
        
        # タイトルの設定
        sample_name = df['Sample Name'].iloc[0]
        plt.suptitle('DTA Curve - {}'.format(sample_name))
        
        # グラフの保存
        if save_name is None:
            save_name = "dta_curve_{}.png".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        plt.savefig(os.path.join(self.save_dir, save_name), dpi=150, bbox_inches='tight')
        plt.close(fig)
    
    def plot_pressure_temperature(self, data_file, save_name=None):
        """圧力と温度の関係をプロット
        
        Args:
            data_file (str): データファイルのパス
            save_name (str, optional): 保存するファイル名
        """
        # データの読み込み（必要な列のみ）
        df = pd.read_csv(data_file, sep='\t', usecols=['set Temp. / K', 'time / s', 'pressure', 'Sample Name'])
        
        # プロットの作成
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 10), sharex=True)
        
        # 温度プロット
        ax1.plot(df['time / s'], df['set Temp. / K'], 
                label='Temperature', color=self.colors[0])
        ax1.set_ylabel('Temperature (K)')
        ax1.legend()
        ax1.grid(True)
        
        # 圧力プロット
        ax2.plot(df['time / s'], df['pressure'], 
                label='Pressure', color=self.colors[2])
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Pressure (MPa)')
        ax2.legend()
        ax2.grid(True)
        
        # タイトルの設定
        sample_name = df['Sample Name'].iloc[0]
        plt.suptitle('Pressure-Temperature Profile - {}'.format(sample_name))
        
        # グラフの保存
        if save_name is None:
            save_name = "pressure_temp_{}.png".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        plt.savefig(os.path.join(self.save_dir, save_name), dpi=150, bbox_inches='tight')
        plt.close(fig)
    
    def plot_3d_dta(self, data_file, save_name=None):
        """3D DTAプロット（温度、圧力、DTA信号）
        
        Args:
            data_file (str): データファイルのパス
            save_name (str, optional): 保存するファイル名
        """
        # データの読み込み（必要な列のみ）
        df = pd.read_csv(data_file, sep='\t', usecols=['set Temp. / K', 'pressure', 'dt of Kei2182A/K', 'time / s', 'Sample Name'])
        
        # データのサンプリング（メモリ使用量削減のため）
        if len(df) > 1000:
            df = df.iloc[::len(df)//1000]
        
        # 3Dプロットの作成
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
        
        # データのプロット
        scatter = ax.scatter(df['set Temp. / K'], 
                           df['pressure'],
                           df['dt of Kei2182A/K'],
                           c=df['time / s'],
                           cmap='viridis',
                           s=20)  # マーカーサイズを小さく
        
        # 軸ラベルの設定
        ax.set_xlabel('Temperature (K)')
        ax.set_ylabel('Pressure (MPa)')
        ax.set_zlabel('DTA Signal (K)')
        
        # カラーバーの追加
        plt.colorbar(scatter, label='Time (s)')
        
        # タイトルの設定
        sample_name = df['Sample Name'].iloc[0]
        plt.title('3D DTA Plot - {}'.format(sample_name))
        
        # グラフの保存
        if save_name is None:
            save_name = "3d_dta_{}.png".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        plt.savefig(os.path.join(self.save_dir, save_name), dpi=150, bbox_inches='tight')
        plt.close(fig) 
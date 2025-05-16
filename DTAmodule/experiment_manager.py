import json
import os
from datetime import datetime
import pandas as pd
import csv
from typing import Dict, List, Optional

class ExperimentManager:
    def __init__(self):
        self.experiment_dir = "Experimental_result"
        self._ensure_experiment_directory()
        self.history_file = os.path.join(self.experiment_dir, "experiment_history.json")
        self._load_history()
    
    def _ensure_experiment_directory(self):
        """実験結果ディレクトリの存在確認と作成"""
        if not os.path.exists(self.experiment_dir):
            os.makedirs(self.experiment_dir)
    
    def _get_experiment_dir(self, experiment_id: int) -> str:
        """実験IDに対応するディレクトリパスを取得
        
        Args:
            experiment_id (int): 実験ID
            
        Returns:
            str: 実験ディレクトリのパス
        """
        exp_dir = os.path.join(self.experiment_dir, str(experiment_id))
        if not os.path.exists(exp_dir):
            os.makedirs(exp_dir)
        return exp_dir
    
    def create_experiment_condition_file(self, experiment_data: Dict) -> str:
        """実験条件ファイルの作成
        
        Args:
            experiment_data (Dict): 実験データ
            
        Returns:
            str: 作成したファイルのパス
        """
        experiment_id = self.get_next_available_id()
        exp_dir = self._get_experiment_dir(experiment_id)
        filename = os.path.join(exp_dir, f"ExpCond_{experiment_id}.csv")
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Sample Name', 'Experimenter', 'Start Temperature', 'End Temperature', 
                           'Heating Rate', 'Wait Time', 'Pressure', 'Pressure Tolerance'])
            writer.writerow([
                experiment_data['sample_name'],
                experiment_data['experimenter'],
                experiment_data['start_temperature'],
                experiment_data['end_temperature'],
                experiment_data['heating_rate'],
                experiment_data['wait_time'],
                experiment_data['pressure'],
                experiment_data['pressure_tolerance']
            ])
        
        return filename
    
    def get_results_file_path(self, experiment_id: int) -> str:
        """結果ファイルのパスを取得
        
        Args:
            experiment_id (int): 実験ID
            
        Returns:
            str: 結果ファイルのパス
        """
        exp_dir = self._get_experiment_dir(experiment_id)
        return os.path.join(exp_dir, f"Results_{experiment_id}.csv")
    
    def get_error_file_path(self, experiment_id: int) -> str:
        """エラーファイルのパスを取得
        
        Args:
            experiment_id (int): 実験ID
            
        Returns:
            str: エラーファイルのパス
        """
        exp_dir = self._get_experiment_dir(experiment_id)
        return os.path.join(exp_dir, f"Error_{experiment_id}.csv")
    
    def _load_history(self):
        """実験履歴の読み込み"""
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
        else:
            self.history = []
    
    def _save_history(self):
        """実験履歴の保存"""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=4)
    
    def get_next_available_id(self) -> int:
        """次の利用可能な実験IDを取得
        
        Returns:
            int: 次の実験ID
        """
        if not self.history:
            return 1
        return max(exp['id'] for exp in self.history) + 1
    
    def add_experiment_history(self, experiment_data: Dict, experiment_id: Optional[int] = None) -> int:
        """実験履歴に追加
        
        Args:
            experiment_data (Dict): 実験データ
            experiment_id (Optional[int]): 実験ID（指定がない場合は自動生成）
            
        Returns:
            int: 実験ID
        """
        if experiment_id is None:
            experiment_id = self.get_next_available_id()
        
        experiment_record = {
            'id': experiment_id,
            'sample_name': experiment_data['sample_name'],
            'experimenter': experiment_data['experimenter'],
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'start_temperature': experiment_data['start_temperature'],
            'end_temperature': experiment_data['end_temperature'],
            'heating_rate': experiment_data['heating_rate'],
            'wait_time': experiment_data['wait_time'],
            'pressure': experiment_data['pressure'],
            'pressure_tolerance': experiment_data['pressure_tolerance']
        }
        
        self.history.append(experiment_record)
        self._save_history()
        return experiment_id
    
    def get_experiment_history(self) -> List[Dict]:
        """実験履歴の取得
        
        Returns:
            List[Dict]: 実験履歴のリスト
        """
        return self.history
    
    def get_experiment_by_id(self, experiment_id: int) -> Optional[Dict]:
        """実験IDから実験データを取得
        
        Args:
            experiment_id (int): 実験ID
            
        Returns:
            Optional[Dict]: 実験データ（存在しない場合はNone）
        """
        for exp in self.history:
            if exp['id'] == experiment_id:
                return exp
        return None
    
    def get_current_experiment_id(self) -> int:
        """現在の実験IDを取得
        
        Returns:
            int: 現在の実験ID
        """
        return self.get_next_available_id() - 1

class ExperimentMetadata:
    def __init__(self, metadata_file="Experiment_result/experiment_metadata.json"):
        """実験メタデータ管理クラス
        
        Args:
            metadata_file (str): メタデータファイルのパス
        """
        self.metadata_file = metadata_file
        self.metadata = self._load_metadata()
    
    def _load_metadata(self):
        """メタデータを読み込む"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """メタデータを保存"""
        os.makedirs(os.path.dirname(self.metadata_file), exist_ok=True)
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=4)
    
    def add_experiment(self, experiment_id, data):
        """実験メタデータを追加
        
        Args:
            experiment_id (str): 実験ID
            data (dict): メタデータ
        """
        self.metadata[experiment_id] = {
            'id': experiment_id,
            'sample_name': data.get('sample_name', ''),
            'lot': data.get('lot', ''),
            'experimenter': data.get('experimenter', ''),
            'date': datetime.datetime.now().strftime("%Y/%m/%d"),
            'data_file': f"{experiment_id}_Results.csv",
            'conditions': data.get('conditions', {})
        }
        self._save_metadata()
    
    def get_experiment(self, experiment_id):
        """実験メタデータを取得
        
        Args:
            experiment_id (str): 実験ID
        
        Returns:
            dict: メタデータ
        """
        return self.metadata.get(experiment_id)
    
    def list_experiments(self):
        """実験一覧を取得
        
        Returns:
            list: 実験IDとメタデータのリスト
        """
        return [(exp_id, data) for exp_id, data in sorted(self.metadata.items())]
    
    def search_experiments(self, **kwargs):
        """条件に合う実験を検索
        
        Args:
            **kwargs: 検索条件（例：sample_name="Ionic liquids"）
        
        Returns:
            list: 条件に合う実験IDとメタデータのリスト
        """
        results = []
        for exp_id, data in self.metadata.items():
            match = True
            for key, value in kwargs.items():
                if data.get(key) != value:
                    match = False
                    break
            if match:
                results.append((exp_id, data))
        return results
    
    def export_to_csv(self, output_file="Experiment_result/experiment_history.csv"):
        """実験履歴をCSVファイルにエクスポート
        
        Args:
            output_file (str): 出力ファイルのパス
        """
        if not self.metadata:
            return
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # ヘッダーの書き込み
            headers = ['ID', 'Sample Name', 'Lot', 'Experimenter', 'Date', 'Data File']
            writer.writerow(headers)
            
            # データの書き込み
            for exp_id, data in sorted(self.metadata.items()):
                row = [
                    exp_id,
                    data.get('sample_name', ''),
                    data.get('lot', ''),
                    data.get('experimenter', ''),
                    data.get('date', ''),
                    data.get('data_file', '')
                ]
                writer.writerow(row) 
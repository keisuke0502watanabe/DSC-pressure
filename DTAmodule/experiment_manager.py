import json
import os
from datetime import datetime
import pandas as pd
import csv

class ExperimentManager:
    def __init__(self, config_dir="Experiment_condition"):
        """実験条件を管理するクラス
        
        Args:
            config_dir (str): 設定ファイルの保存ディレクトリ
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, "experiment_config.json")
        self.history_file = os.path.join(config_dir, "experiment_history.json")
        os.makedirs(config_dir, exist_ok=True)
        
        # 設定ファイルの初期化
        if not os.path.exists(self.config_file):
            self._initialize_config()
        
        # 履歴ファイルの初期化
        if not os.path.exists(self.history_file):
            self._initialize_history()
    
    def _initialize_config(self):
        """設定ファイルの初期化"""
        config = {
            "last_experiment": None,
            "default_conditions": {
                "heating_rate": 5.0,  # K/min
                "pressure_tolerance": 1.0,  # %
                "wait_time": 10  # min
            }
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=4)
    
    def _initialize_history(self):
        """履歴ファイルの初期化"""
        history = {
            "experiments": []
        }
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)
    
    def get_experiment_conditions(self):
        """実験条件の取得
        
        Returns:
            dict: 実験条件
        """
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        return config
    
    def save_experiment_conditions(self, conditions):
        """実験条件の保存
        
        Args:
            conditions (dict): 実験条件
        """
        with open(self.config_file, 'w') as f:
            json.dump(conditions, f, indent=4)
    
    def add_experiment_history(self, experiment_data, experiment_id=None):
        """実験履歴の追加
        
        Args:
            experiment_data (dict): 実験データ
            experiment_id (int, optional): 指定する実験ID
        
        Returns:
            int: 実験ID
        """
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        
        # 実験IDの生成または指定
        if experiment_id is None:
            # 自動生成の場合、最大ID + 1を使用
            existing_ids = [exp.get("id", 0) for exp in history["experiments"]]
            experiment_id = max(existing_ids, default=0) + 1
        else:
            # 指定されたIDが既に存在する場合はエラー
            if any(exp.get("id") == experiment_id for exp in history["experiments"]):
                raise ValueError("指定された実験IDは既に使用されています")
        
        experiment_data["id"] = experiment_id
        experiment_data["timestamp"] = datetime.now().isoformat()
        
        history["experiments"].append(experiment_data)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=4)
        
        return experiment_id
    
    def get_experiment_history(self):
        """実験履歴の取得
        
        Returns:
            list: 実験履歴のリスト
        """
        with open(self.history_file, 'r') as f:
            history = json.load(f)
        return history["experiments"]
    
    def get_experiment_by_id(self, experiment_id):
        """IDによる実験データの取得
        
        Args:
            experiment_id (int): 実験ID
        
        Returns:
            dict: 実験データ
        """
        history = self.get_experiment_history()
        for exp in history:
            if exp["id"] == experiment_id:
                return exp
        return None
    
    def get_next_available_id(self):
        """次に使用可能な実験IDを取得
        
        Returns:
            int: 次に使用可能な実験ID
        """
        history = self.get_experiment_history()
        existing_ids = [exp.get("id", 0) for exp in history["experiments"]]
        return max(existing_ids, default=0) + 1
    
    def create_experiment_condition_file(self, experiment_data):
        """実験条件ファイルの作成
        
        Args:
            experiment_data (dict): 実験データ
        
        Returns:
            str: 作成されたファイルのパス
        """
        # ファイル名の生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "{}_{}_ExpCond.csv".format(experiment_data['sample_name'], timestamp)
        filepath = os.path.join(self.config_dir, filename)
        
        # ヘッダーの作成
        headers = [
            "Run", "Tsv (K)", "Tf (K)", "Rate (K/min)", "Wait (min)",
            "Pressure (MPa)", "Pressure Tolerance (%)"
        ]
        
        # データフレームの作成
        df = pd.DataFrame(columns=headers)
        
        # 温度プロファイルの生成
        start_temp = experiment_data["start_temperature"]
        end_temp = experiment_data["end_temperature"]
        heating_rate = experiment_data["heating_rate"]
        wait_time = experiment_data["wait_time"]
        
        # 昇温プロファイル
        current_temp = start_temp
        run_number = 1
        
        while current_temp < end_temp:
            next_temp = min(current_temp + 50, end_temp)  # 50Kごとに区切る
            df.loc[len(df)] = [
                run_number,
                current_temp,
                next_temp,
                heating_rate,
                wait_time,
                experiment_data["pressure"],
                experiment_data["pressure_tolerance"]
            ]
            current_temp = next_temp
            run_number += 1
        
        # ファイルの保存
        df.to_csv(filepath, index=False)
        return filepath

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
import os
import csv
from DTAmodule.experiment_manager import ExperimentManager

class ExperimentConditions:
    def __init__(self):
        self.experiment_manager = ExperimentManager()
    
    def get_experiment_conditions(self):
        """実験条件の取得
        
        Returns:
            tuple: (filenameExpCond, sampleName) 実験条件ファイル名とサンプル名
        """
        print("\n実験条件の設定")
        print("1: 新しい実験条件を入力")
        print("2: 過去の実験条件から選択")
        
        choice = input("選択してください (1/2): ")
        
        if choice == "1":
            return self._create_new_experiment()
        elif choice == "2":
            return self._select_existing_experiment()
        else:
            print("無効な選択です")
            return self.get_experiment_conditions()
    
    def _create_new_experiment(self):
        """新しい実験条件の作成
        
        Returns:
            tuple: (filenameExpCond, sampleName) 実験条件ファイル名とサンプル名
        """
        print("\n実験IDの設定")
        print("1: 自動生成")
        print("2: 手動入力")
        id_choice = input("選択してください (1/2): ")
        
        experiment_id = None
        if id_choice == "2":
            try:
                experiment_id = int(input("実験IDを入力してください: "))
            except ValueError:
                print("無効な実験IDです。自動生成を使用します。")
                experiment_id = self.experiment_manager.get_next_available_id()
        
        experiment_data = {
            "sample_name": input("サンプル名を入力してください: "),
            "experimenter": input("実験者名を入力してください: "),
            "start_temperature": float(input("開始温度 (K) を入力してください: ")),
            "end_temperature": float(input("終了温度 (K) を入力してください: ")),
            "heating_rate": float(input("昇温速度 (K/min) を入力してください: ")),
            "wait_time": float(input("待機時間 (min) を入力してください: ")),
            "pressure": float(input("目標圧力 (MPa) を入力してください: ")),
            "pressure_tolerance": float(input("圧力許容範囲 (%) を入力してください: "))
        }
        
        try:
            # 実験条件ファイルの作成
            filenameExpCond = self.experiment_manager.create_experiment_condition_file(experiment_data)
            
            # 実験履歴に追加
            experiment_id = self.experiment_manager.add_experiment_history(experiment_data, experiment_id)
            print("実験ID: {} で保存されました".format(experiment_id))
            
            return filenameExpCond, experiment_data["sample_name"]
        except ValueError as e:
            print("エラー: {}".format(e))
            return self.get_experiment_conditions()
    
    def _select_existing_experiment(self):
        """既存の実験条件の選択
        
        Returns:
            tuple: (filenameExpCond, sampleName) 実験条件ファイル名とサンプル名
        """
        history = self.experiment_manager.get_experiment_history()
        if not history:
            print("過去の実験条件がありません")
            return self.get_experiment_conditions()
        
        print("\n過去の実験条件:")
        for exp in history:
            print("ID: {}".format(exp['id']))
            print("サンプル名: {}".format(exp['sample_name']))
            print("実験者: {}".format(exp['experimenter']))
            print("日時: {}".format(exp['timestamp']))
            print("---")
        
        exp_id = int(input("使用する実験IDを入力してください: "))
        exp_data = self.experiment_manager.get_experiment_by_id(exp_id)
        
        if exp_data is None:
            print("無効な実験IDです")
            return self.get_experiment_conditions()
        
        # 実験条件ファイルの作成
        filenameExpCond = self.experiment_manager.create_experiment_condition_file(exp_data)
        return filenameExpCond, exp_data["sample_name"]
    
    def continue_experiment(self):
        """既存の実験の続行
        
        Returns:
            tuple: (filenameExpCond, filenameResults, filenameError) 各ファイル名
        """
        print("Please input the number of the experiment you want to continue.")
        print("The number is shown in the file name of the experiment.")
        print("For example, if the file name is 'ExpCond_1.csv', the number is 1.")
        print("If you want to start a new experiment, please input 'n'.")
        Q3 = input("Please input the number or 'n':")
        
        if Q3 == "n":
            return None, None, None
        
        try:
            exp_num = int(Q3)
            filenameExpCond = "ExpCond_{}.csv".format(exp_num)
            filenameResults = "Results_{}.csv".format(exp_num)
            filenameError = "Error_{}.csv".format(exp_num)
            return filenameExpCond, filenameResults, filenameError
        except ValueError:
            print("Invalid input. Starting a new experiment.")
            return None, None, None 
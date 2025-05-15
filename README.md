# 高圧DTA測定システム

このプロジェクトは、高圧下での示差熱分析（DTA）測定を自動化するためのシステムです。

## 機能

- 温度制御（Chino KP）
- 温度差測定（KEITHLEY 2182A）
- 温度測定（KEITHLEY 2000-1）
- 圧力測定（KEITHLEY 2000-2）
- 圧力制御（サーボモータ）
- データ記録（CSV、Google Spreadsheet）

## 必要な機器

1. KEITHLEY nanovoltmeter 2182A
   - 温度差測定用
2. KEITHLEY 2000-1
   - 温度測定用
3. Chino KP
   - 温度制御用
4. KEITHLEY 2000-2
   - 圧力測定用
5. サーボモータ
   - 圧力制御用

## セットアップ

1. 必要なPythonパッケージのインストール：
```bash
pip install -r requirements.txt
```

2. Google Spreadsheet APIの設定：
   - `json_file`ディレクトリに認証用JSONファイルを配置
   - スプレッドシートの共有設定を確認

3. シリアルポートの設定：
   - 各機器のシリアルポートを確認
   - 必要に応じて`pressure_control.py`のポート設定を変更

## 使用方法

1. 実験条件ファイルの作成：
   - CSVファイルに測定条件を記述
   - 形式：`Tsv,Tf,rate,wait,pressure,pressure_tolerance`

2. プログラムの実行：
```bash
python DTAmain.py
```

3. 測定結果の確認：
   - CSVファイル：`Experiment_result`ディレクトリ
   - Google Spreadsheet：指定したスプレッドシート

## バージョン履歴

### v1.0.0 (2024-03-XX)
- 初期リリース
- 基本的なDTA測定機能
- 圧力制御機能の追加
- Google Spreadsheet連携

## 注意事項

- 圧力制御の精度は約±0.1 MPa
- 許容パーセントの推奨値は2-5%
- 実験データは自動的にバックアップされます 
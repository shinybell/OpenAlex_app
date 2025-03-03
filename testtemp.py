
import os
import glob
import pandas as pd
import ast

# CSVファイルが格納されているディレクトリパス
data_dir = "/Users/ichikawatomohiro/Documents/OpenAlex_app/成功データ"
# 対象のCSVファイルを検索
csv_files = glob.glob(os.path.join(data_dir, "*.csv"))

# 出力先のリスト（起業研究者用と sample 研究者用）
entrepreneur_data_list = []
nonentrepreneur_data_list = []

for file in csv_files:
    try:
        df = pd.read_csv(file, encoding="utf-8")
    except Exception as e:
        print(f"ファイル {file} の読み込みに失敗しました: {e}")
        continue
    
    # 行が不足しているファイルはスキップ（最低でも2行必要）
    if df.shape[0] < 2:
        continue
    
    # 1行目（index=0）が起業研究者
    entrepreneur_row = df.iloc[0]
    # "papers_info" に含まれる辞書リストを取得
    try:
        e_papers_info = ast.literal_eval(entrepreneur_row["papers_info"])
    except Exception as e:
        print(f"papers_info の解析に失敗しました: {e}")
        continue
    
    # 取得した辞書リストを entrepreneur_data_list に追加
    entrepreneur_data_list.append(e_papers_info)
    
    # 2行目以降を sample 研究者とするが、今回使用するのは最大3行のみ
    sample_rows = df.iloc[1:4]  # 2行目(インデックス1)から4行目(インデックス3)まで
    for _, sample_row in sample_rows.iterrows():
        try:
            s_papers_info = ast.literal_eval(sample_row["papers_info"])
        except Exception as e:
            print(f"papers_info の解析に失敗しました: {e}")
            continue
        
        # 取得した辞書リストを nonentrepreneur_data_list に追加
        nonentrepreneur_data_list.append(s_papers_info)

# 取得した結果を確認
print("=== 起業研究者 ===")
print(entrepreneur_data_list)
# print("\n=== sample 研究者（最大3行/CSV）===")
# print(nonentrepreneur_data_list)
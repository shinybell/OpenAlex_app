import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import pickle
import numpy as np
import datetime
import numpy as np
import pandas as pd
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing.sequence import pad_sequences

# 事前に用意されている paper_title をベクトル化する関数をインポート
# （utils/aggregate_vectors_spacy.py 内に定義されているものとします）
# from utils.aggregate_vectors_spacy import vectorize_text

# 保存済みモデルの読み込み
# tomo_model = load_model("config/entrepreneur_model_full.h5")
with open("config/rf_model.pkl", "rb") as f:
    rui_model = pickle.load(f)

    
# def process_researcher_data(papers):
#     """
#     1人の研究者の論文リスト（各論文は辞書）を受け取り、publication_dateで昇順に並び替えた上で、
#     各論文の特徴ベクトルを作成する関数。
    
#     各論文の特徴ベクトルは以下の要素から構成されます：
#       - paper_title を spaCy でベクトル化したベクトル（例：200次元程度）
#       - position の one-hot エンコーディング（'first': [1,0,0], 'middle': [0,1,0], 'last': [0,0,1]；不明な値は'middle'として扱う）
#       - total_citations（数値）
#       - d_index（浮動小数点数）
#       - publication_date： 'YYYY-MM-DD' の文字列を、1970-01-01 からの日数に変換した数値
      
#     ※ publication_date のパースに失敗した場合、その論文はスキップします。
    
#     戻り値： numpy.array (shape: (num_papers, feature_dim))
#     """
#     # 発行日の古い順に並び替え
#     try:
#         papers_sorted = sorted(
#             papers,
#             key=lambda x: datetime.datetime.strptime(x['publication_date'], "%Y-%m-%d")
#         )
#     except Exception as e:
#         print("publication_dateのパースでエラー:", e)
#         return np.array([])  # 何も処理できなかった場合

#     sequence = []
#     baseline_date = datetime.datetime(1970, 1, 1)
#     for paper in papers_sorted:
#         # paper_title の取得
#         title = paper.get('paper_title', None)
#         if not title or not isinstance(title, str):
#             continue  # タイトルが無い場合はスキップ

#         # position の one-hot エンコーディング
#         position_str = paper.get('position', 'middle')
#         if position_str == 'first':
#             position_vec = [1.0, 0.0, 0.0]
#         elif position_str == 'last':
#             position_vec = [0.0, 0.0, 1.0]
#         else:
#             position_vec = [0.0, 1.0, 0.0]

#         # total_citations と d_index の取得
#         total_citations = paper.get('total_citations', 0)
#         d_index = paper.get('d_index', 0.0)

#         # publication_date の数値化
#         pub_date_str = paper.get('publication_date', "")
#         try:
#             pub_date = datetime.datetime.strptime(pub_date_str, "%Y-%m-%d")
#             date_value = (pub_date - baseline_date).days
#         except Exception:
#             # パースに失敗した場合、その論文はスキップ
#             continue

#         # paper_title のベクトル化
#         title_vector = vectorize_text(title)  # 例：np.array(shape=(200,))

#         # 追加の数値特徴の連結
#         # position_vec (3次元) + total_citations (1次元) + d_index (1次元) + date_value (1次元)
#         numeric_features = np.array(position_vec + [total_citations, d_index, date_value], dtype=np.float32)
        
#         # タイトルベクトルと数値特徴を連結
#         feature_vector = np.concatenate([title_vector, numeric_features])
#         sequence.append(feature_vector)
    
#     return np.array(sequence)

# def predict_entrepreneur_percentage(papers):
#     try:
#         """
#         入力された論文情報の辞書リスト（1人分のデータ）を元に、
#         起業研究者である確率をパーセンテージで返す関数。

#         Parameters:
#         papers: list of dict
#             1人の研究者の論文情報リスト。各辞書は以下のキーを含む:
#                 - 'paper_title'
#                 - 'position'
#                 - 'total_citations'
#                 - 'd_index'
#                 - 'publication_date'
        
#         Returns:
#         percentage: float
#             起業研究者である確率（%）。例：75.32
#             もし有効なデータがなければ、None を返す。
#         """
        
#         # 論文情報リストから特徴ベクトルのシーケンスを生成
#         sequence = process_researcher_data(papers)
#         if sequence.size == 0:
#             print("有効な論文情報が見つかりませんでした。")
#             return None

#         # 学習時は全データを最大シーケンス長（例：1500）にパディングしているため、
#         # ここでも同じ長さに調整する。※ maxlen を指定しない場合、最も長いシーケンスに合わせるが、
#         # モデルの入力形状が固定なので、ここでは学習時と同じ maxlen（1500）を明示的に指定します。
#         max_seq_length = 1500
#         padded_sequence = pad_sequences([sequence.tolist()], maxlen=max_seq_length, padding='post', dtype='float32')
        
#         # モデルに入力して予測を実施
#         prob = tomo_model.predict(padded_sequence)
#         # 出力は (1, 1) の確率なので、100倍してパーセンテージに
#         percentage = prob[0, 0] * 100
#         return round(percentage,1)
    
#     except Exception as e:
#         print(f"predict_entrepreneur_percentageの中でエラー:{e}")

def predict_bibliometric_percentage(last_5_year_h_index, total_works_citations, first_paper_count):
    """
    入力された指標から、rui_model（文献計量モデル）を用いて起業していない確率を求め、
    その補数（起業している確率）をパーセンテージで返す関数。

    Parameters:
      last_5_year_h_index: 数値
      total_works_citations: 数値
      first_paper_count: 数値

    Returns:
      result: float
          起業している確率（%）を少数第2位までに丸めた値
    """
    try:
        import numpy as np
        columns = ['last_5_year_h_index', 'total_works_citations', 'first_paper_count']
        features = pd.DataFrame([[last_5_year_h_index, total_works_citations, first_paper_count]], columns=columns)
        probability = rui_model.predict_proba(features)[0, 1]
        result = round((1 - probability) * 100, 2)
        return result
    except Exception as e:
        print(f"predict_bibliometric_percentageの中でエラー:{e}")
        return 0
   



# 例: 以下のように使用できます。
if __name__ == "__main__":
    # サンプルの辞書リスト（1人分の研究者の論文情報の例）
    sample_papers = [
        {
            'paper_title': 'Deep learning in medical imaging: Overview and future promise',
            'position': 'first',
            'total_citations': 25,
            'd_index': -150.0,
            'publication_date': '2018-03-15'
        },
        {
            'paper_title': 'A review of convolutional neural networks for medical image analysis',
            'position': 'middle',
            'total_citations': 40,
            'd_index': -130.0,
            'publication_date': '2019-07-20'
        },
        {
            'paper_title': 'Advances in neural networks for computer vision tasks',
            'position': 'last',
            'total_citations': 10,
            'd_index': -200.0,
            'publication_date': '2020-11-05'
        }
        # 必要に応じてさらに論文情報を追加
    ]

    # result_percentage = predict_entrepreneur_percentage(sample_papers)
    # if result_percentage is not None:
    #     #print("Entrepreneur probability: {:.2f}%".format(result_percentage))
    #     print(result_percentage)
    
    # last_5_year_h_index=5
    # total_works_citations = 80
    # first_paper_count = 3
    # print(predict_bibliometric_percentage(last_5_year_h_index,total_works_citations,first_paper_count))
   
    
    
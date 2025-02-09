import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import numpy as np
import datetime
import spacy

# spaCy モデル "en_core_sci_lg" の読み込み
nlp = spacy.load("en_core_sci_lg")
    
def aggregate_vectors(data, baseline_date=None):
    """
    data: 論文情報が格納された辞書のリスト
          各辞書は 'paper_id', 'paper_title', 'publication_date' を持つ。
    nlp: 事前に読み込んだ spaCy モデル（例: spacy.load("en_core_sci_lg")）
    baseline_date: 基準日。文字列（"YYYY-MM-DD"）または datetime.datetime オブジェクト。
                   指定がない場合は 2024-12-31 を基準日として使用する。
    
    各論文の paper_title を spaCy でベクトル化し、
      - "vector_all": 全論文のベクトルの和
      - "vector_10": 基準日から過去10年以内の論文のベクトルの和
      - "vector_5": 基準日から過去5年以内の論文のベクトルの和
    を1つの辞書にまとめて返す。
    """
    if baseline_date is None or baseline_date == "":
       # data内の各論文のpublication_dateを集める
        dates = []
        for paper in data:
            pub_date_str = paper.get('publication_date', '')
            if pub_date_str:
                try:
                    pub_date = datetime.datetime.strptime(pub_date_str, "%Y-%m-%d")
                    dates.append(pub_date)
                except Exception:
                    continue
        # 集めた日付があれば最新の日付をbaseline_dateに設定、なければデフォルト値を使用
        if dates:
            baseline_date = max(dates)
        else:
           baseline_date = datetime.datetime(2024, 12, 31)

    # baseline_date が文字列の場合はパースする（形式は "YYYY-MM-DD"）
    elif isinstance(baseline_date, str):
        try:
            baseline_date = datetime.datetime.strptime(baseline_date, "%Y-%m-%d")
        except Exception as e:
            raise ValueError("baseline_date は 'YYYY-MM-DD' の形式で指定してください。")
    
    # 基準日から10年および5年分の閾値を計算
    threshold_10 = baseline_date - datetime.timedelta(days=10 * 365)
    threshold_5  = baseline_date - datetime.timedelta(days=5 * 365)
    
    # spaCy のベクトル次元を取得（モデル固有の固定長）
    dim = nlp.vocab.vectors_length
    # 集計用のベクトルをゼロベクトルで初期化
    agg_all = np.zeros(dim)
    agg_10  = np.zeros(dim)
    agg_5   = np.zeros(dim)
    
    for paper in data:
        title = paper.get('paper_title', '')
        pub_date_str = paper.get('publication_date', '')
        if not title:
            continue
        
        # 公開日を datetime 型に変換（形式は "YYYY-MM-DD"）
        try:
            pub_date = datetime.datetime.strptime(pub_date_str, "%Y-%m-%d")
        except Exception as e:
            continue
        
        # spaCy でタイトルを解析しトークン化
        doc = nlp(title)
        tokens = list(doc)
        if tokens:
            # 各トークンのベクトルの平均をタイトルのベクトルとする
            vector = np.sum([token.vector for token in tokens], axis=0) / len(tokens)
        else:
            vector = np.zeros(dim)
        
        # 全論文の集計
        agg_all += vector
        # 基準日から過去10年以内なら agg_10 に加算
        if pub_date >= threshold_10:
            agg_10 += vector
        # 基準日から過去5年以内なら agg_5 に加算
        if pub_date >= threshold_5:
            agg_5 += vector
    
    # ３種類の集計結果を辞書で返す（list に変換）
    result = {
        "vector_all": agg_all.tolist(),
        "vector_10": agg_10.tolist(),
        "vector_5": agg_5.tolist()
    }
    return result

# ======= 使用例 =======
if __name__ == "__main__":
    data = []
# # サンプル論文データ（必要に応じて拡張してください）
# data = [
#     {
#         'paper_id': 'https://openalex.org/W4406433289',
#         'paper_title': 'CRISPR/Cas9-mediated genomic insertion of functional genes into Lactiplantibacillus plantarum WCFS1',
#         'publication_date': '2025-01-16'
#     },
#     {
#         'paper_id': 'https://openalex.org/W4406288394',
#         'paper_title': 'Identification and Characterization of a New Thermophilic κ-Carrageenan Sulfatase',
#         'publication_date': '2025-01-11'
#     },
#     # ... 他の論文データ
# ]

    # baseline_date を指定しない場合 → 2024-12-31 を基準とする
    aggregated_vectors_default = aggregate_vectors(data,baseline_date="")
    print(aggregated_vectors_default)

    # # baseline_date を "2025-01-01" として指定する例
    # aggregated_vectors_custom = aggregate_vectors(data, baseline_date="2025-01-01")
    # print("Custom baseline (2025-01-01):", aggregated_vectors_custom)
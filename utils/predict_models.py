import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import pickle
import numpy as np
import datetime
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


def get_education_value(data):
    """
    'education'の値を辞書から取得します。
    dataが辞書でない場合はJSONとしてパースを試みます。
    """
    if isinstance(data, dict):
        return data.get("education", 0)
    else:
        try:
            import json
            d = json.loads(data)
            return d.get("education", 0)
        except Exception:
            return 0


def get_jp_value(data):
    """
    'JP'の値を辞書から取得します。
    dataが辞書でない場合はJSONとしてパースを試みます。
    """
    if isinstance(data, dict):
        return data.get("JP", 0)
    else:
        try:
            import json
            d = json.loads(data)
            return d.get("JP", 0)
        except Exception:
            return 0


def rui_predict_model(last_5_year_h_index: float,
                      career_year_adjust_coauthor_count: float,
                      career_year_adjust_education: float,
                      career_year_adjust_coauthor_education: float,
                      career_year_adjust_JP: float,
                      career_year_adjust_first_paper_count: float,
                      career_year_adjust_citations: float) -> float:
    """
    与えられた加工済みの特徴量から、保存済みのモデルを用いて起業可能性（パーセンテージ）を予測する関数。
    
    特徴量の順序は以下の通り：
      1. last_5_year_h_index
      2. career_year_adjust_coauthor_count
      3. career_year_adjust_education
      4. career_year_adjust_coauthor_education
      5. career_year_adjust_JP
      6. career_year_adjust_first_paper_count
      7. career_year_adjust_citations
    """
    import pandas as pd

    # 学習時と同じ特徴名を指定
    feature_names = [
        "last_5_year_h_index",
        "career_year_adjust_coauthor_count",
        "career_year_adjust_education",
        "career_year_adjust_coauthor_education",
        "career_year_adjust_JP",
        "career_year_adjust_first_paper_count",
        "career_year_adjust_citations"
    ]
    # 1行のデータをDataFrameとして作成
    data = pd.DataFrame([[last_5_year_h_index,
                          career_year_adjust_coauthor_count,
                          career_year_adjust_education,
                          career_year_adjust_coauthor_education,
                          career_year_adjust_JP,
                          career_year_adjust_first_paper_count,
                          career_year_adjust_citations]],
                        columns=feature_names)

    probability = rui_model.predict_proba(data)[0, 1]
    startup_probability = (1 - probability) * 100
    return startup_probability



def extract_keys_from_dict(data: dict, key_list: list) -> dict:
    """
    data の中から、key_list に含まれるキーが全て存在する場合、
    そのキーと値のみを含む辞書を返す。
    もし、key_list にあるキーが一つでも data に存在しなければ None を返す。
    """
    if not all(key in data for key in key_list):
        return None
    return {key: data[key] for key in key_list}


if __name__ == "__main__":
    # 生の入力値
    raw_total_works_citations = 343.7
    raw_career_years = 12
    raw_coauthor_count = 532
    raw_first_paper_count = 7
    raw_country_affiliation_count = {"JP": 1}
    raw_affiliation_type = {"education": 2}
    raw_coauthor_type_counter = {"education": 7}
    raw_last_5_year_h_index = 12

    # 加工済みの値を算出
    
    processed_last_5_year_h_index = raw_last_5_year_h_index
    processed_career_year_adjust_coauthor_count = (raw_coauthor_count / raw_career_years)
    processed_career_year_adjust_education = get_education_value(raw_affiliation_type)
    processed_career_year_adjust_coauthor_education = get_education_value(raw_coauthor_type_counter) 
    processed_career_year_adjust_JP = get_jp_value(raw_country_affiliation_count) 
    processed_career_year_adjust_first_paper_count = raw_first_paper_count
    processed_career_year_adjust_citations = raw_total_works_citations

    prediction = rui_predict_model(
        processed_last_5_year_h_index,
        processed_career_year_adjust_coauthor_count,
        processed_career_year_adjust_education,
        processed_career_year_adjust_coauthor_education,
        processed_career_year_adjust_JP,
        processed_career_year_adjust_first_paper_count,
        processed_career_year_adjust_citations
    )

    print("Predicted startup probability: {:.2f}%".format(prediction))
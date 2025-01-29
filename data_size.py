import requests
import sys

# APIエンドポイントとパラメータ
endpoint_url = "https://api.openalex.org/works"
author_id = "https://openalex.org/authors/A5038138665"
params = {
    "filter": f"author.id:{author_id}",
    "page": 1,
    "per_page": 200,
}

try:
    # APIリクエスト
    response = requests.get(endpoint_url, params=params)
    response.raise_for_status()  # エラーチェック

    # レスポンスのサイズを取得
    response_size_bytes = len(response.content)

    # バイトからGBに変換
    response_size_gb = response_size_bytes / (1024**3)

    # 結果を表示
    print(f"データ転送量: {response_size_gb:.6f} GB")

except requests.exceptions.RequestException as e:
    print(f"エラーが発生しました: {e}")
from executables.execute_feach_japanese import execute
from typing import List
from pydantic import BaseModel
import os, asyncio, sys, json
import pandas as pd


class RequestData(BaseModel):
    topic_id: List[str] =[] # トピックID（リスト）
    primary: bool =True
    citation_count: int =-1 # 引用数（整数）
    publication_year: int =-1 # 出版年（整数）
    title_and_abstract_search: str =""
    di_calculation: bool =False # DI計算（真偽値）
    output_sheet_name: str =""  # 出力シート名
    stop_control:bool=False #実行後に自動でインスタンスを閉じる。
    use_API_key:bool=True
    output_mode:str=""


async def process_feach_japanese(request_data: RequestData):
    try:

        result= await execute(
                topic_ids=request_data.topic_id,
                primary=request_data.primary,  # 固定値
                threshold=request_data.citation_count,
                year_threshold=request_data.publication_year,
                title_and_abstract_search=request_data.title_and_abstract_search,
                di_calculation=request_data.di_calculation,
                output_sheet_name=request_data.output_sheet_name,
                use_API_key = request_data.use_API_key,
                output_mode = request_data.output_mode
                )


    except Exception as e:
        print(f"エラーが発生したため、処理が中断されました。{e}")  # ログの追加


if __name__ == "__main__":
    # 非同期関数を呼び出すためにイベントループを使用

    # 実行時引数にjsonファイルが指定されている場合
    if len(sys.argv) > 1:

        # 引数からjsonファイルのパスを取得
        json_file_path = sys.argv[1]
        # jsonファイルを読み込む
        with open(json_file_path, 'r', encoding='utf-8') as f:
            request_data = json.load(f)
        # jsonファイルの内容をRequestDataに変換
        request_data = RequestData(**request_data)
    # 引数が指定されていない場合はデフォルトのリクエストデータを使用
    else:
        # デフォルトのリクエストデータ
        request_data = {
            "topic_id": [],
            "primary": True,
            "citation_count": 50,
            "publication_year": 2022,
            "title_and_abstract_search": "AI,machine",
            "di_calculation": False,
            "output_sheet_name": "テスト2",
            # "use_API_key":True,
            "use_API_key": False,
            "output_mode":"detail"
        }

    async def main():
        # 非同期関数を直接実行
        #process_count_japanese
        #process_feach_japanese
        await process_feach_japanese(RequestData(**request_data))

    # イベントループで実行
    asyncio.run(main())

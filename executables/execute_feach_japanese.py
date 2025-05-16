import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scraping.jglobal_selenium_search import JGlobalSeleniumSearch
# from utils.outputer import Outputer
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
# from utils.async_log_to_sheet import append_log_async
from utils.common_method import extract_id_from_url
from utils.predict_models import extract_keys_from_dict, get_education_value, get_jp_value, rui_predict_model
import asyncio
import time
import csv
import openpyxl
from datetime import datetime

secret = SecretManager()

class LocalOutputer():
    def __init__(self, results_list):
        self.results_list = results_list

    async def batch_execute_for_display(self, output_mode=""):
        if output_mode == "sample":
            header,results_list = self.__adjust_indicators_for_sample(self.results_list)
            header,results_list = self.prepend_sample_evaluation(header,results_list)
            LocalOutputer.output_csv_to_local(results_list,file_name=self.file_name)
            print(f"ローカルにCSVを出力しました。")

    def __adjust_indicators_for_sample(self,dict_list):
        not_need_keys =[]
        # dict_list 内の各辞書から not_need_keys に含まれるキーを削除する
        for item in dict_list:
            for key in not_need_keys:
                # キーが存在する場合に削除（存在しない場合は何もしない）
                item.pop(key, None)
        # ヘッダーは最初の辞書のキー一覧から取得
        header = list(dict_list[0].keys())
        return header, dict_list

    #データ分析用で使用する関数
    def prepend_sample_evaluation(self,header,dict_list):
        try:
            header = [col for col in header if col not in ("topic_score")]
            header = ["career_first_year","topic_score","Top5_topic_ids","Japan_score"]+header
            new_list = []
            for item in dict_list:

                topics_detail = item.get("topics_detail", [])
                if isinstance(topics_detail, list):
                    top_five_topics_ids = [extract_id_from_url(topic["Topic ID"]) for topic in topics_detail[:5] if "Topic ID" in topic]
                else:
                    print(f"author_idが{item['author_id']}のtopics_detailが、{item['topics_detail']}です。")
                    top_five_topics_ids = []

                temp_box = item.pop("topic_score", None)

                jp_score = self.__compute_jp_score(item["country_affiliation_count"])

                new_data ={
                    "career_first_year":self.__get_earliest_year(item["detail_of_affiliation"]),
                    "topic_score":temp_box,
                    "Top5_topic_ids":top_five_topics_ids,
                    "Japan_score":jp_score,
                }
                combined_data = {**new_data, **item}
                new_list.append(combined_data)

            return header,new_list
        except Exception as e:
            raise Exception(f"prepend_sample_evaluationでエラー:{e}")

    def __compute_jp_score(self,country_affiliation_count: dict) -> float:
        """
        country_affiliation_count の辞書から、JP の割合をスコアとして返す関数。
        例: {'JP': 12, 'US': 3} なら 12 / (12+3) = 0.8
        """
        try:
            jp_count = country_affiliation_count.get("JP", 0)  # JP の件数を取得（なければ 0）
            total_count = sum(country_affiliation_count.values())  # 全件数の合計
            if total_count == 0:
                return 0.0  # 全件数が 0 の場合は 0 を返す
            score = jp_count / total_count
            return round(score, 4)  # 少数第4位まで丸める
        except Exception as e:
            raise Exception(f"__compute_jp_scoreのエラー:{e}\ncountry_affiliation_count:{country_affiliation_count}")
    def __get_earliest_year(self,institutions: list) -> int:
        """
        institutions: 各辞書は 'Years' キーに年のリストを持つ
        すべての 'Years' の中で最も古い年を返す
        """
        try:
            earliest = float('inf')
            for inst in institutions:
                years = inst.get("Years", [])
                if years:
                    # 現在の辞書内の最小の年を取得
                    min_year = min(years)
                    if min_year < earliest:
                        earliest = min_year
            # 該当する年がない場合は None を返す（ここでは int を返すことを前提）
            return earliest if earliest != float('inf') else None
        except Exception as e:
            raise Exception(f"__get_earliest_yearのエラー:{e}\ninstitutions:{institutions}")

    @staticmethod
    def output_csv_to_local(profile_dict_list,file_name):
        # 現在の日時を取得し、数字のみの形式でフォーマット（例: 202502201010）
        now = datetime.now()
        formatted_numeric = now.strftime("%Y%m%d%H%M")

        # CSVファイルの保存先パスを指定（例: Downloadsフォルダに保存）
        csv_file_path = f"{file_name}.csv"

        try:
            # CSVファイルを新規作成（または上書き）するためにオープン
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                # 辞書リストが空の場合は何も書き込まずに終了
                if not profile_dict_list:
                    print("書き込むデータがありません。")
                    return

                # ヘッダー行の作成：最初の辞書のキーを利用する
                fieldnames = list(profile_dict_list[0].keys())

                # DictWriterオブジェクトを作成。fieldnamesによりCSVのヘッダーが決まる
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                # ヘッダーを書き込む
                writer.writeheader()

                # 各辞書をCSVの1行として書き込む
                for row in profile_dict_list:
                    writer.writerow(row)

            print(f"データをCSVファイルに保存しました: {csv_file_path}")
        except Exception as e:
            print(f"CSVファイルの保存中にエラーが発生しました: {e}")



#条件を指定して研究者リスト作成する
async def execute(topic_ids,primary=True,threshold=15,year_threshold=2015,title_and_abstract_search='',di_calculation=False,output_sheet_name="API動作確認",use_API_key = False,output_mode=""):

    start_time = time.time()  # 実行開始時間を記録
    try:
        print(f"")
        print(f"処理を開始します。")

        file_name = os.getenv('FIXED_SPREADSHEET_NAME')
        # sheet_manager = SpreadsheetManager(file_name, output_sheet_name)
        # sheet_manager.clear_rows_from_second()
        count_cores = count_logical_cores()
        if use_API_key:
            max_works = count_cores*20
        else:
            max_works = count_cores*10

        creater = CreateAuthorIdList(topic_ids=topic_ids,primary=primary,threshold=threshold,year_threshold=year_threshold,title_and_abstract_search=title_and_abstract_search,max_works=max_works,use_API_key=use_API_key)
        print(f"論文の検索")  # ログの追加
        creater.run_get_works()
        creater.extract_authors()
        print(f"論文数:{len(creater.all_results)},研究者数:{len(creater.authors_id_list)}")  # ログの追加
        if len(creater.authors_id_list)<=0:
            print("検索結果がありませんでした。")
            return {"count_authors":0}

        global_hindex_ranking_list = await creater.create_hindex_ranking()
        print(f"global_hindex_ranking_listの数:{len(global_hindex_ranking_list)}")
        creater.extract_authors(only_japanese=True)
        print(f"日本人著者数:{len(creater.authors_id_list)}")  #ログの追加

        person_num = 8 if use_API_key else 4
        max_workers=max_works//person_num

        def process_author(author_id):
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(author_id, "の調査")
                author = GatherAuthorData(author_id=author_id,max_workers=max_workers,use_API_key=use_API_key)
                author.run_fetch_works()

                if not author.article_dict_list:
                    return {}

                if di_calculation and output_mode!="simple":
                    author.di_calculation()

                profile = author.gathering_author_data()
                profile.h_index_ranking = next(
                    (
                        entry["h_index_ranking"]  # 計算せず、値をそのまま使用する
                        for entry in global_hindex_ranking_list
                        if extract_id_from_url(entry["id"]) == extract_id_from_url(author_id)
                    ),
                    -100  # 条件に合致するものがなかった場合は -100 を返す
                )

                profile.all_author_count = len(global_hindex_ranking_list)
                profile_dict = profile.to_dict()
                works_data_dict = author.get_top_three_article()
                top_searched_article = creater.get_top_article(author_id)
                profile_dict.update(top_searched_article)
                profile_dict.update(works_data_dict)
                raw_keys = [
                    "total_works_citations",
                    "career_years",
                    "coauthor_count",
                    "first_paper_count",
                    "country_affiliation_count",
                    "affiliation_type",
                    "coauthor_type_counter",
                    "last_5_year_h_index"
                ]

                # raw な値だけの
                dict_for_rui_model = extract_keys_from_dict(profile_dict, raw_keys)
                if dict_for_rui_model is None:
                    predict_dict = {
                        "predict_model": -200,
                    }
                    print("extract_keys_from_dictが失敗")
                else:
                     # 各 raw 値を取得し、float 化（辞書型の値は必要に応じて get_jp_value, get_education_value を使用）
                    career_years = float(dict_for_rui_model["career_years"])
                    processed_last_5_year_h_index = float(dict_for_rui_model["last_5_year_h_index"])
                    processed_career_year_adjust_coauthor_count = float(dict_for_rui_model["coauthor_count"]) / career_years
                    processed_career_year_adjust_first_paper_count = float(dict_for_rui_model["first_paper_count"]) / career_years
                    processed_career_year_adjust_JP = get_jp_value(dict_for_rui_model["country_affiliation_count"]) / career_years
                    processed_career_year_adjust_education = get_education_value(dict_for_rui_model["affiliation_type"]) / career_years
                    processed_career_year_adjust_coauthor_education = get_education_value(dict_for_rui_model["coauthor_type_counter"])
                    processed_career_year_adjust_citations = float(dict_for_rui_model["total_works_citations"]) / career_years

                    args = [
                        processed_last_5_year_h_index,
                        processed_career_year_adjust_coauthor_count,
                        processed_career_year_adjust_education,
                        processed_career_year_adjust_coauthor_education,
                        processed_career_year_adjust_JP,
                        processed_career_year_adjust_first_paper_count,
                        processed_career_year_adjust_citations
                    ]
                    predict_dict = {
                        "predict_model": rui_predict_model(*args),
                    }

                profile_dict.update(predict_dict)

                return profile_dict

            except Exception as e:
                raise Exception(f"process_author内でエラー発生 (author_id: {author_id}): {e}") # エラーを再スローして上位で処理

        # 並列処理
        results_list = []
        length = 5
        with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, author_id): author_id for author_id in creater.authors_id_list}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    results_list.append(result)

                    if len(results_list) >= length:
                        print(f"著者{length}人の処理が完了しました。")  #ログの追加
                        length+=5

                    # イベントループに制御を戻す
                    await asyncio.sleep(0)

                except Exception as e:
                    # メインスレッドでのエラーハンドリング
                    print(f"{author_id} の処理中にエラーが発生しました: {e}") #ログの追加
                    # イベントループに制御を戻す
                    await asyncio.sleep(0)


        #GoogleCustomSearchとSeleniumをつかて、特許件数とJ-GLOBALでのresearcherリンクを取得
        #EC2では動作しないのでコメントアウツ中。必要に応じて追加開発して下さい。
        #if need_J_Global:
            # print(f"J-GLOBALからデータを取得します。") #ログの追加
            # GetJGlobalData(results_list,method="selenium")#selenium or search

        end_time = time.time()  # 実行終了時間を記録
        elapsed_time = end_time - start_time  # 実行時間を計算
        # 時間、分、秒に変換
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)


        # フォーマット済みの文字列を作成
        formatted_time = f"{hours}時間{minutes}分{seconds}秒"
        print(f"処理が終了しました。処理にかかった時間:{formatted_time}")  # ログの追加
        print(f"スプレットシートに追加します。")
        # outputer = Outputer(sheet_manager,results_list)
        # await outputer.batch_execute_for_display(output_mode=output_mode)
        # ローカルのexcelに出力
        # print(f"ローカルのExcelに出力します。")
        # ここにローカルのExcelに出力するコードを追加
        outputer = LocalOutputer(results_list)
        outputer.file_name = "sample_output"
        await outputer.batch_execute_for_display(output_mode='sample')
        # print(f"ローカルのExcelに出力しました。")

        return {"count_authors":len(results_list)}

    except ValueError as e:
        print(f"エラーにより処理が中断しました。:{e}")
        return e
    except Exception as e:
        print(f"予期しないエラーにより処理が中断しました。:{e}")
        return e

import os
import csv
from datetime import datetime
from utils.async_log_to_sheet import append_log_async
from urllib.parse import quote
from utils.common_method import extract_id_from_url

class Outputer:
        
    def __init__(self,sheet_manager,results_list,file_name=""):
        self.sheet_manager = sheet_manager
        self.results_list = results_list
        self.file_name = file_name
        
    async def batch_execute_for_display(self,analysis=False):
        try:
            if analysis=="sample":
                header,results_list = self.__adjust_indicators(self.results_list,analysis=True)
                header,results_list = self.prepend_sample_evaluation(header,results_list)
                Outputer.output_csv_to_local(results_list,file_name=self.file_name)
                rows = Outputer.dict_list_to_string_rows(results_list)
                await self.__output_to_spread_sheet(header,rows) #スプレットシートに追加。
            
            else:
                header,results_list = self.__adjust_indicators(self.results_list)
                header,results_list = self.prepend_five_evaluation(header,results_list)
                results_list = self.sort_dict_list_by_key(results_list,"total_works_citations")
                rows = Outputer.dict_list_to_string_rows(results_list)
                await self.__output_to_spread_sheet(header,rows) #スプレットシートに追加。
        except Exception as e:
            raise ValueError(f"batch_execute_for_display関数内でエラーが起きました。:{e}")
    def __adjust_indicators(self,dict_list,analysis=False):
        # 新しい辞書リストを格納するリスト
        if analysis:  
            not_need_keys =["annual_citation_count","annual_citation_growth_rate"]
            # dict_list 内の各辞書から not_need_keys に含まれるキーを削除する
            for item in dict_list:
                for key in not_need_keys:
                    # キーが存在する場合に削除（存在しない場合は何もしない）
                    item.pop(key, None)
            # ヘッダーは最初の辞書のキー一覧から取得
            header = list(dict_list[0].keys())
            return header, dict_list
        
        else:
            new_list = []
            header = ["研究者ID", "名前", "最新の所属", "キャリア年数", "出版数", "全ての出版の被引用数","h-indexランキング","研究者検索結果総数","H-Index", "過去5年H-index", "企業との共著数", "first論文数", "対応(last)論文数", "DI0.8以上のworks数","STP.論文ID", "STP.論文タイトル", "STP.論文出版年月", "STP.論文被引用数","引用数ランキング","論文検索結果総数","CTP.論文ID", "CTP.論文タイトル", "CTP.論文出版年月", "CTP.論文被引用数"]
            # 必要なキー
            need_keys = [
                "author_id", "name", "latest_affiliation",
                "career_years", "works_count", "total_works_citations","h_index_ranking","all_author_count",
                "h_index", "last_5_year_h_index", "coauthor_from_company_count", "first_paper_count",
                "corresponding_paper_count", "disruption_index_above_08",
                "条件論文1:ID","条件論文1:タイトル","条件論文1:出版年月","条件論文1:被引用数","引用数ランキング","総数",
                "論文1:ID","論文1:タイトル","論文1:出版年月","論文1:被引用数","j_global_link","patents_count"
                # "論文2:ID","論文2:タイトル","論文2:出版年月","論文2:被引用数",
                # "論文3:ID","論文3:タイトル","論文3:出版年月","論文3:被引用数",
            ]
            
            # 入力リスト内の各辞書について処理
            for original_dict in dict_list:
                # 新しい辞書を作成して、必要なキーとその値だけをコピー
                new_dict = {key: original_dict[key] for key in need_keys if key in original_dict}
                new_list.append(new_dict)

            return header ,new_list

    
    async def __output_to_spread_sheet(self,header,rows):
        #スプレッドシートは１セルあたり5万文字までなので5万文字以内に調整します。
        rows = self.__truncate_and_report_long_cells(rows)
        
        attempt = 1
        max_retries = 6
        while attempt < max_retries:
            try:
                self.sheet_manager.sheet.update('A1',[header])
                break
            except Exception as e:
                await append_log_async(f"headerの追加をやり直す。エラー:{e}") 
        
        
        for i in range(0, len(rows), 1000):
            attempt = 1
            max_retries = 6
            while attempt < max_retries:
                try:
                    self.sheet_manager.append_rows(rows[i:i+1000])
                    await append_log_async(f"[{i}:{i+1000}]を追加しました。") 
                    break
                except Exception as e:
                    await append_log_async(f"[{i}:{i+1000}]をやり直す。エラー:{e}") 
                attempt+=1
                
            if attempt < max_retries:
                continue
            else:
                raise ValueError(f"スプレットシートに追加できませんでした。エラー:{e}")
                
    #スプレッドシートは１セルあたり5万文字までなので5万文字以内に調整します。
    def __truncate_and_report_long_cells(self,data, limit=50000):
        try:
            for i, row in enumerate(data):
                for j, cell in enumerate(row):
                    if len(cell) > limit:
                        data[i][j] = cell[:limit]  # セルの内容をlimit文字に切り捨て
        except Exception as e:
            raise ValueError(f"truncate_and_report_long_cells関数の使い方に問題があります。エラー:{e}")
        return data


    #スプレットシートにアップするために、各要素はstr型の２次元リストに変換。
    @staticmethod
    def dict_list_to_string_rows(dict_list):
        try:
            rows =[]
            for result in dict_list:
                row = [str(value) for value in result.values()]
                rows.append(row)
            return rows
        except Exception as e:
            raise Exception(f"dict_list_to_string_rowsの中でエラー:{e}")


    def prepend_five_evaluation(self,header,dict_list):
        try:
            header = ["検索リンク","研究の質","h-index世界ランク","若さ","特許件数","革新性"]+header
            new_list = []
            for item in dict_list:
                # item から "j_global_link" を取得（存在すれば取得して削除、存在しなければ None）
                search_query = item.pop("j_global_link", None)
                # search_query が存在しなければ、Google検索用のクエリを作成する
                if not search_query:
                    search_query = self.__create_google_search_query(item)
                                    
                    
                # 若さ（キャリア年数の逆数）
                career_years = item.get("career_years", 0)
                youth_index = round(1 / career_years, 4) if career_years > 0 else 0  # 0除算を回避し、少数第4位に丸める
                #特許件数
                patents_count = item.pop("patents_count", -200)
                
                # 新しいキーとその値
                new_data = {
                    "Google検索": search_query,
                    "研究の質（h-index）": item.get("h_index", ""),
                    "h-index世界ランク": item.get("h_index_ranking", ""),
                    "若さ（逆数）": youth_index,
                    "特許件数": patents_count, 
                    "革新性（DI0.8以上のworks数）": item.get("disruption_index_above_08", "")
                }
                # 既存のデータを新しいデータの後に追加
                combined_data = {**new_data, **item}
                new_list.append(combined_data)
            
            return header,new_list
        
        except Exception as e:
            raise ValueError(f"prepend_five_evaluation関数内でエラーが起きました:{e}")

    def prepend_sample_evaluation(self,header,dict_list):
        try:
            header = [col for col in header if col not in ("j_global_link", "patents_count","topic_score")]
            header = ["search_link","career_first_year","topic_score","Top5_topic_ids","Japan_score","patents_count"]+header
            new_list = []
            for item in dict_list:
                search_query = item.pop("j_global_link", None)
                if not search_query:
                    search_query = self.__create_google_search_query(item)
                #特許件数
                patents_count = item.pop("patents_count", -200)

                topics_detail = item.get("topics_detail", [])
                if isinstance(topics_detail, list):
                    top_five_topics_ids = [extract_id_from_url(topic["Topic ID"]) for topic in topics_detail[:5] if "Topic ID" in topic]
                else:
                    print(f"author_idが{item['author_id']}のtopics_detailが、{item['topics_detail']}です。")
                    top_five_topics_ids = []
                
                temp_box = item["topic_score"]
                del item["topic_score"]
                
                jp_score = self.__compute_jp_score(item["country_affiliation_count"])
                
                new_data ={
                    "search_link": search_query,
                    "career_first_year":self.__get_earliest_year(item["detail_of_affiliation"]),
                    "topic_score":temp_box,
                    "Top5_topic_ids":top_five_topics_ids,
                    "Japan_score":jp_score,
                    "patents_count":patents_count
                }
                combined_data = {**new_data, **item}
                new_list.append(combined_data)
                
            return header,new_list
        except Exception as e:
            raise Exception(f"prepend_sample_evaluationでエラー:{e}")

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

    def __create_google_search_query(self,item):
        try:
            name = item.get("name", "")
            latest_affiliation = item.get("latest_affiliation", [""])
            # 空白や特殊文字をエンコード
            encoded_name = quote(name)
            encoded_affiliation = quote(latest_affiliation[0]) if latest_affiliation else ""
            search_query = f"https://www.google.com/search?q={encoded_name}+{encoded_affiliation}" if latest_affiliation else ""
            return search_query
        except Exception as e:
            raise Exception(f"__create_google_search_queryのエラー:{e}\n:item{item}")
        
        
    def sort_dict_list_by_key(self,dict_list, sort_key):
        """
        辞書リストを指定したキーの値で降順にソートする関数。

        :param dict_list: 辞書リスト (List[dict])
        :param sort_key: ソートの基準となるキー名 (str)
        :return: ソートされた辞書リスト (List[dict])
        """
        try:
            sorted_list = sorted(dict_list, key=lambda x: x.get(sort_key, 0), reverse=True)
            return sorted_list
        except Exception as e:
            raise Exception(f"ソートに失敗しました。エラー: {e}")
        
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


# 例: 辞書リストを用意して関数を呼び出す
if __name__ == "__main__":
    sample_data = [
        {"researcher_id": "R001", "name": "Alice", "career_years": 5},
        {"researcher_id": "R002", "name": "Bob", "career_years": 10},
        {"researcher_id": "R003", "name": "Charlie", "career_years": 7},
    ]
    Outputer.output_csv_to_local(sample_data)
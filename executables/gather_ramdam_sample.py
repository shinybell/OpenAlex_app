import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import pandas as pd
import time
import concurrent.futures

# 必要なモジュールのインポート
from services.gather_authors_data import GatherAuthorData
from api.list_openAlex_fetcher import OpenAlexPagenationDataFetcher
from utils.common_method import extract_id_from_url


class GatheringRandomSampleAuthor:
    def __init__(self, concept_id: str, sample_size: int = 100,use_API_key: bool = True):
        """
        Parameters:
            concept_id (str): 対象のConcept ID（URLの場合はextract_id_from_urlで整形）
            sample_size (int): 取得したい著者数
            max_works (int): 各著者の論文取得件数上限
            use_API_key (bool): APIキー利用の有無
        """
        self.concept_id = extract_id_from_url(concept_id)
        self.sample_size = sample_size
        self.use_API_key = use_API_key

    def fetch_author_ids(self) -> list:
        """
        OpenAlexPagenationDataFetcherを利用して、指定Conceptに関連する著者情報を取得し、
        extract_id_from_urlを使って著者ID（リンク部分を除いたIDのみ）を抽出します。
        ※max_worksには20を、max_count_10000はTrueに設定して、ページネーションの並列処理のスレッド数と上限を指定します。
        """
        base_url = "https://api.openalex.org/authors"
        filter_str = f"concepts.id:{self.concept_id},last_known_institutions.country_code:JP"
        params = {
            "sample": self.sample_size,
            "filter": filter_str,
            "per_page": 200,
            "page": 1,
            "seed": 1
        }
        fetcher = OpenAlexPagenationDataFetcher(
            base_url, params, id=self.concept_id, max_works=20, use_API_key=self.use_API_key, max_count_10000=True
        )
        all_results = fetcher.all_results

        # 各結果から著者IDを抽出（extract_id_from_urlを利用して、ID部分のみ取得）
        author_ids = [
            extract_id_from_url(author.get("id"))
            for author in all_results if author.get("id")
        ]
        return author_ids[:self.sample_size]

    def fetch_detailed_info(self, author_ids: list) -> list:
        """
        取得済みの著者IDリストに対して、各著者の詳細情報を並列処理で取得します。
        use_API_keyがTrueの場合はmax_workers=8、Falseの場合は4を使用します。
        """
        detailed_info_list = []
        max_workers_value = 8 if self.use_API_key else 4
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers_value) as executor:
            future_to_author = {executor.submit(self.get_author_profile, author_id): author_id for author_id in author_ids}
            for future in concurrent.futures.as_completed(future_to_author):
                author_id = future_to_author[future]
                try:
                    profile = future.result()
                    if profile is not None:
                        detailed_info_list.append(profile)
                        print(f"{len(detailed_info_list)}人目")
                except Exception as e:
                    print(f"{author_id} の詳細情報取得でエラー: {e}")
        return detailed_info_list

    def get_author_profile(self, author_id: str) -> dict:
        """
        GatherAuthorDataを用いて1人の著者の詳細情報を取得します。
        ※以下の追加処理を実施しています。
          - di_calculation() を実行してDisruption Indexを計算
          - coauthors_coauthor_data() を実行して共著者情報を取得し、キーにプレフィックスを付与して統合
        常に profile.to_dict() を用いて辞書化しています。
        ※found_dateは使用しません。
        """
        try:
            # found_dateは使用しないので、引数から除外しています。
            author_data = GatherAuthorData(author_id, max_workers=20, use_API_key=self.use_API_key)
            author_data.run_fetch_works()
            if not author_data.article_dict_list:
                print(f"{author_id} の論文データが取得できませんでした。")
                return None

            # Disruption Indexなどの計算を実行
            author_data.di_calculation()

            # 詳細情報を取得（get_type_counts_info=True, release=True の設定）
            profile = author_data.gathering_author_data(get_type_counts_info=True, release=True)
            profile_dict = profile.to_dict()  # 常にto_dict()を使用

            # 共著者情報を取得して、キーに"coauthors_total_"を付与した上で統合
            coauthor_keys = ["works_count", "total_works_citations", "h_index", "last_5_year_h_index", "coauthor_from_company_count", "first_paper_count", "corresponding_paper_count"]
            coauthor_data = author_data.coauthors_coauthor_data(coauthor_keys)
            coauthor_data = {f"coauthors_total_{key}": value for key, value in coauthor_data.items()}
            profile_dict.update(coauthor_data)

            return profile_dict
        except Exception as e:
            print(f"{author_id} のデータ取得中にエラー: {e}")
            return None

if __name__ == "__main__":
    # 例：医学分野のConcept ID "C71924100" を指定（必要に応じて変更）
    urls = [
        # "https://openalex.org/C24326235",
        # "https://openalex.org/C119599485",
        # "https://openalex.org/C115903868",
       # "https://openalex.org/C199360897",
        #"https://openalex.org/C107457646",
        #"https://openalex.org/C150903083",#ローカルで実行中
        "https://openalex.org/C502942594",
        #"https://openalex.org/C98274493",現在3で実行中
       # "https://openalex.org/C133731056",#1で完了
        #"https://openalex.org/C78519656",#1で完了
        #"https://openalex.org/C149635348",#1で実行中
        #"https://openalex.org/C136229726",#2で完了
        #"https://openalex.org/C19527891",#2で完了
        #"https://openalex.org/C87717796",#2で実行中
        #"https://openalex.org/C107826830",#3で完了
    ]
    sample_size =1000   #取得したい著者数

    for concept_id in urls:
        # GatheringRandomSampleAuthorのインスタンスを生成
        random_sampler = GatheringRandomSampleAuthor(concept_id, sample_size=sample_size, use_API_key=True)

        print("ランダムサンプル著者IDの取得を開始します。")
        author_ids = random_sampler.fetch_author_ids()
        print(f"合計 {len(author_ids)} 件の著者IDを取得しました。")

        print("各著者の詳細情報の取得を開始します。")
        detailed_info = random_sampler.fetch_detailed_info(author_ids)
        print(f"詳細情報を取得した著者数: {len(detailed_info)}")

        # 取得した詳細情報の辞書リストをDataFrameに変換し、CSVファイルとして出力
        df = pd.DataFrame(detailed_info)
        output_filename = f"{extract_id_from_url(concept_id)}.csv"
        df.to_csv(output_filename, index=False)
        print(f"著者の詳細情報をCSVファイル '{output_filename}' に出力しました。")
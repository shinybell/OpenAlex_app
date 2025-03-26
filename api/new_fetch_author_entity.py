import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from utils.common_method import get_type_counts,extract_id_from_url
import requests


#https://api.openalex.org/authors?filter=works_count:%3C513,works_count:%3E342,summary_stats.h_index:%3C69,summary_stats.h_index:%3E46,topics.id:T11403,affiliations.institution.country_code:JP

class NewFetchAuthorEntity:
    """
    ・author_ids をリストで受け取り、各 ID は extract_id_from_url で統一済みの形式に変換します。
    ・コンストラクタで API へリクエストを実行し、取得したデータを self.data に格納します。
    ・use_api_key の True/False により、API キー使用の有無を切り替えられます（api_key が指定されている場合）。
    ・各関数は、引数として与えられる著者 ID（URL 形式でも可）を extract_id_from_url で統一してから対象データを返します。
    
    追加関数：
      - calculate_country_counts
      - calculate_type_counts
      - calculate_growth_rates
      - get_author_id
      - get_display_name
      - get_topics
      - get_top3_topic_ids
      - get_top3_topics
    """

    def __init__(self, author_ids: list, use_api_key: bool = False):
        """
        コンストラクタ
         - 渡された著者 ID リストを extract_id_from_url を用いて統一
         - 統一済み ID を用いて filter パラメータを作成し、API へリクエスト
         - use_api_key が True かつ api_key が指定されている場合、Authorization ヘッダーに API キーを設定
         - 取得した JSON レスポンスを self.data に格納
        :param author_ids: OpenAlex の著者 ID のリスト（URL形式も可）
        :param use_api_key: API キーを使用する場合は True（デフォルトは False）
        :param api_key: 使用する API キー（use_api_key=True の場合のみ有効）
        """
        if len(author_ids)>100:
            raise Exception(f"NewFetchAuthorEntityのauthor_idsのリストは100件までです。入力された長さ:{author_ids}")
        # 各著者IDを extract_id_from_url で統一
        self.author_ids = [extract_id_from_url(aid) for aid in author_ids]

        # filter パラメータの作成例: "id:A5100705073|A5106315809"
        filter_value = "id:" + "|".join(self.author_ids)
        url = "https://api.openalex.org/authors"
        params = {
            "filter": filter_value,
            "per_page":100
            }

        # API キー使用の場合はヘッダーに Authorization を設定（Bearerトークン形式）
    
        if use_api_key:
            API_KEY = os.getenv('API_KEY') 
            if not API_KEY:
                raise ValueError("API_KEYが環境変数に設定されていません。")
            params["api_key"] = API_KEY
            #params["mailto"] = "t.ichikawa.bnv@gmail.com"
        
        retrial_num=0
        while True:
            try:
                response = requests.get(url, params=params, timeout=5)
                if response.status_code == 200:  
                    self.data = response.json()
                    break
                if retrial_num>=25:
                    self.data ={}
                    break
            except requests.exceptions.Timeout:
                print("リクエストがタイムアウトしました。再試行します。")
            
            except Exception as e:
                print("再試行します。エラー:",e)
            finally:
                retrial_num+=1
                time.sleep(1)
                print(f"NewFetchAuthorEntity retrial_num:{retrial_num}")
                
                


    def _find_author(self, author_id: str):
        """
        与えられた author_id で、self.data["results"] から該当する著者データを検索して返します。
        :param author_id: 対象とする著者の ID（URL形式も可）
        :return: 該当する著者のデータ（辞書）、見つからなければ None
        """
        standardized_id = extract_id_from_url(author_id)
        for author in self.data.get("results", []):
            if extract_id_from_url(author.get("id")) == standardized_id:
                return author
        return None

    def calculate_country_counts(self, author_id: str = None):
        """
        著者の国情報を集計して返します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、国ごとの出現回数を返す。
        :return: 全件の場合は {国: 出現回数} の辞書、特定の場合は {国: 1}（国情報がある場合）
        """
        results = self.data.get("results", [])
        if author_id is None:
            counts = {}
            for author in results:
                country = author.get("country")
                if country:
                    counts[country] = counts.get(country, 0) + 1
            return counts
        else:
            author = self._find_author(author_id)
            if author:
                country = author.get("country")
                return {country: 1} if country else {}
            return {}

    def calculate_type_counts(self, author_id: str = None):
        """
        著者のタイプ情報を集計して返します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、タイプごとの出現回数を返す。
        :return: 全件の場合は {タイプ: 出現回数} の辞書、特定の場合は {タイプ: 1}（タイプ情報がある場合）
        """
        results = self.data.get("results", [])
        if author_id is None:
            counts = {}
            for author in results:
                a_type = author.get("type")
                if a_type:
                    counts[a_type] = counts.get(a_type, 0) + 1
            return counts
        else:
            author = self._find_author(author_id)
            if author:
                a_type = author.get("type")
                return {a_type: 1} if a_type else {}
            return {}

    def calculate_growth_rates(self, author_id: str = None):
        """
        各著者の成長率（cited_by_count / works_count）を計算して返します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、{著者ID: 成長率} の辞書を返す。
        :return: works_count が 0 の場合は 0、それ以外は計算値を返す。
        """
        results = self.data.get("results", [])
        if author_id is None:
            rates = {}
            for author in results:
                works_count = author.get("works_count", 0)
                cited_by_count = author.get("cited_by_count", 0)
                growth_rate = cited_by_count / works_count if works_count else 0
                rates[author.get("id")] = growth_rate
            return rates
        else:
            author = self._find_author(author_id)
            if author:
                works_count = author.get("works_count", 0)
                cited_by_count = author.get("cited_by_count", 0)
                growth_rate = cited_by_count / works_count if works_count else 0
                return {author.get("id"): growth_rate}
            return {}

    def get_author_id(self, author_id: str = None):
        """
        API レスポンスから著者の ID を取得します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件の ID リストを返す。
        :return: 全件の場合は ID のリスト、特定の場合はその ID（文字列）
        """
        results = self.data.get("results", [])
        if author_id is None:
            return [author.get("id") for author in results]
        else:
            author = self._find_author(author_id)
            return author.get("id") if author else None

    def get_display_name(self, author_id: str = None):
        """
        API レスポンスから著者の表示名を取得します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件の表示名リストを返す。
        :return: 全件の場合は表示名のリスト、特定の場合はその表示名（文字列）
        """
        results = self.data.get("results", [])
        if author_id is None:
            return [author.get("display_name") for author in results]
        else:
            author = self._find_author(author_id)
            return author.get("display_name") if author else None

    def get_topics(self, author_id: str = None):
        """
        API レスポンスから著者のトピック情報を取得します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、各著者のトピックリストのリストを返す。
        :return: 全件の場合は各著者のトピックリスト、特定の場合はその著者のトピックリスト（リスト）
        """
        results = self.data.get("results", [])
        if author_id is None:
            return [author.get("topics", []) for author in results]
        else:
            author = self._find_author(author_id)
            return author.get("topics", []) if author else []

    def get_top3_topic_ids(self, author_id: str = None):
        """
        著者のトピック情報から、上位3件のトピック ID を取得します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、各著者の上位3トピック ID のリストのリストを返す。
        :return: 全件の場合は各著者の上位3トピック ID のリスト、特定の場合はそのリスト（リスト）
        """
        topics_data = self.get_topics(author_id=author_id)
        if author_id is None:
            top3_ids_list = []
            for topics in topics_data:
                top3_ids = [topic.get("id") for topic in topics[:3]]
                top3_ids_list.append(top3_ids)
            return top3_ids_list
        else:
            return [topic.get("id") for topic in topics_data[:3]]

    def get_top3_topics(self, author_id: str = None):
        """
        著者のトピック情報から、上位3件のトピックの表示名を取得します。
        :param author_id: 特定の著者の ID を指定した場合、その著者のみ対象（URL形式も可）。
                          指定しなければ全件対象で、各著者の上位3トピック名のリストのリストを返す。
        :return: 全件の場合は各著者の上位3トピック名のリスト、特定の場合はそのリスト（リスト）
        """
        topics_data = self.get_topics(author_id=author_id)
        if author_id is None:
            top3_topics_list = []
            for topics in topics_data:
                top3_names = [topic.get("display_name") for topic in topics[:3]]
                top3_topics_list.append(top3_names)
            return top3_topics_list
        else:
            return [topic.get("display_name") for topic in topics_data[:3]]

    def get_h_index(self, author_id=None):
        """
        指定された著者（または全著者）のh-indexを取得して返す。
        APIレスポンス内の各著者の"summary_stats"フィールドに"h_index"が格納されている前提です。
        
        :param author_id: 単一の著者ID（URL形式でも可）を指定するとその著者のみ対象、Noneの場合は全著者を対象とする。
        :return: 単一の場合はh-index（整数または"N/A"）、全件の場合は {著者ID: h-index} の辞書
        """
        if author_id is None:
            h_index_dict = {}
            for author in self.data.get("results", []):
                std_id = extract_id_from_url(author.get("id"))
                h = author.get("summary_stats", {}).get("h_index", "N/A")
                h_index_dict[std_id] = h
            return h_index_dict
        else:
            author = self._find_author(author_id)
            if author:
                return author.get("summary_stats", {}).get("h_index", "N/A")
            return "N/A"
        
    def get_works_count(self, author_id=None):
        """
        指定された著者（または全著者）の論文数（works_count）を取得して返す。
        
        :param author_id: 単一の著者ID（URL形式でも可）を指定するとその著者のみ対象、Noneの場合は全著者を対象とする。
        :return: 単一の場合はworks_count（整数または"N/A"）、全件の場合は {著者ID: works_count} の辞書
        """
        if author_id is None:
            works_count_dict = {}
            for author in self.data.get("results", []):
                std_id = extract_id_from_url(author.get("id"))
                count = author.get("works_count", "N/A")
                works_count_dict[std_id] = count
            return works_count_dict
        else:
            author = self._find_author(author_id)
            if author:
                return author.get("works_count", "N/A")
            return "N/A"


    def get_cited_by_count(self, author_id=None):
        """
        指定された著者（または全著者）の被引用数（cited_by_count）を取得して返す。
        
        :param author_id: 単一の著者ID（URL形式でも可）を指定するとその著者のみ対象、Noneの場合は全著者を対象とする。
        :return: 単一の場合はcited_by_count（整数または"N/A"）、全件の場合は {著者ID: cited_by_count} の辞書
        """
        if author_id is None:
            cited_by_dict = {}
            for author in self.data.get("results", []):
                std_id = extract_id_from_url(author.get("id"))
                count = author.get("cited_by_count", "N/A")
                cited_by_dict[std_id] = count
            return cited_by_dict
        else:
            author = self._find_author(author_id)
            if author:
                return author.get("cited_by_count", "N/A")
            return "N/A"


    def get_two_year_mean_citedness(self, author_id=None):
        """
        指定された著者（または全著者）の2年間平均被引用数（2yr_mean_citedness）を取得して返す。
        この値は、APIレスポンス内のsummary_statsフィールドに格納されている前提です。
        
        :param author_id: 単一の著者ID（URL形式でも可）を指定するとその著者のみ対象、Noneの場合は全著者を対象とする。
        :return: 単一の場合は2yr_mean_citedness（数値または"N/A"）、全件の場合は {著者ID: 2yr_mean_citedness} の辞書
        """
        if author_id is None:
            result = {}
            for author in self.data.get("results", []):
                std_id = extract_id_from_url(author.get("id"))
                value = author.get("summary_stats", {}).get("2yr_mean_citedness", "N/A")
                result[std_id] = value
            return result
        else:
            author = self._find_author(author_id)
            if author:
                return author.get("summary_stats", {}).get("2yr_mean_citedness", "N/A")
            return "N/A"


    def get_i10_index(self, author_id=None):
        """
        指定された著者（または全著者）のi10-indexを取得して返す。
        この値は、APIレスポンス内のsummary_statsフィールドに格納されている前提です。
        
        :param author_id: 単一の著者ID（URL形式でも可）を指定するとその著者のみ対象、Noneの場合は全著者を対象とする。
        :return: 単一の場合はi10_index（整数または"N/A"）、全件の場合は {著者ID: i10_index} の辞書
        """
        if author_id is None:
            result = {}
            for author in self.data.get("results", []):
                std_id = extract_id_from_url(author.get("id"))
                value = author.get("summary_stats", {}).get("i10_index", "N/A")
                result[std_id] = value
            return result
        else:
            author = self._find_author(author_id)
            if author:
                return author.get("summary_stats", {}).get("i10_index", "N/A")
            return "N/A"
    
    
    def get_authorid_and_hindex_list(self):
        """
        全著者のIDとh-indexをまとめた辞書のリストを返します。
        例:
        [
            {"id": "A5100705073", "h_index": 25},
            {"id": "A5106315809", "h_index": 18},
            ...
        ]
        :return: 著者ごとのIDとh-indexをまとめた辞書のリスト
        """
        if not self.data:
            return []
        # 全著者のIDリストを取得（各IDは元の形式の場合もあるので標準化する）
        all_ids = self.get_author_id()
        # 全著者のh-indexの辞書を取得（キーは標準化済みID）
        h_index_dict = self.get_h_index()
        
        result = []
        for author_id in all_ids:
            # IDを標準化して取得
            std_id = extract_id_from_url(author_id)
            # 対応するh-indexを取得、存在しない場合は "N/A"
            h_index = h_index_dict.get(std_id, "N/A")
            result.append({"id": std_id, "h_index": h_index})
        
        return result
    
    
    
if __name__ == "__main__":
    
    # テスト用の著者IDリスト（URL形式やそのままの ID も可）
    test_author_ids = [
        "https://openalex.org/A5100705073",
        "A5106315809",
        "https://openalex.org/A5090933484"
    ]
    from data_class.lists import urls
    # API キーを使用する場合は use_api_key=True, api_key にキーを指定（例: "YOUR_API_KEY"）
    # ここでは使用しない例として use_api_key=False としています
    test_author_ids = urls[0:100]
    fetcher = NewFetchAuthorEntity(test_author_ids, use_api_key=True)


    print("\n【全著者のID】")
    print(fetcher.get_author_id("A5003851517"))
    print(len(fetcher.get_authorid_and_hindex_list()))

    # print("\n【全著者の表示名】")
    # print(fetcher.get_display_name())

    # print("\n【全著者のトピック一覧】")
    # print(fetcher.get_topics())

    # print("\n【全著者の上位3トピックID】")
    # print(fetcher.get_top3_topic_ids())

    # print("\n【全著者の上位3トピック名】")
    # print(fetcher.get_top3_topics())

    # # 特定の著者 ID でのテスト（例: "A5100705073"）
    # test_id = "A5100705073"
    # print(f"\n【{test_id} の国情報】")
    # print(fetcher.calculate_country_counts(author_id=test_id))

    # print(f"\n【{test_id} のタイプ情報】")
    # print(fetcher.calculate_type_counts(author_id=test_id))

    # print(f"\n【{test_id} の成長率】")
    # print(fetcher.calculate_growth_rates(author_id=test_id))

    # print(f"\n【{test_id} の ID】")
    # print(fetcher.get_author_id(author_id=test_id))

    # print(f"\n【{test_id} の表示名】")
    # print(fetcher.get_display_name(author_id=test_id))

    # print(f"\n【{test_id} のトピック一覧】")
    # print(fetcher.get_topics(author_id=test_id))

    # print(f"\n【{test_id} の上位3トピックID】")
    # print(fetcher.get_top3_topic_ids(author_id=test_id))

    # print(f"\n【{test_id} の上位3トピック名】")
    # print(fetcher.get_top3_topics(author_id=test_id))
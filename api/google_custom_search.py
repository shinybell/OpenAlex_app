import sys
import os
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

class JGlobalCustomSearch:
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, exact_terms=None, loose_terms=None):

        if not exact_terms and not loose_terms:
            raise Exception("少なくともどちらかのキーワードリストは指定してください。")

        self.exact_terms = exact_terms or []  # 完全一致キーワードのリスト
        self.loose_terms = loose_terms or []  # そうでないキーワードのリスト

        # 最終的な検索クエリ文字列を作成
        self.query = self.__build_query()

        # 環境変数から検索エンジンIDとAPIキーを取得
        self.search_engine_id = os.getenv("J_GLOBAL_SEARCH_ENGINE_ID")
        self.api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
        if not self.search_engine_id:
            raise Exception("環境変数 J_GLOBAL_SEARCH_ENGINE_ID が設定されていません。")
        if not self.api_key:
            raise Exception("環境変数 GOOGLE_CUSTOM_SEARCH_API_KEY が設定されていません。")

        # 検索結果のうち、最初の結果のリンク、タイトル、スニペットを格納するための変数
        self.first_result_link = None
        self.first_result_title = None
        self.first_result_snippet = None

        # フィルタリングされた全ての検索結果を保持するリスト
        self.filtered_items = []

        # フィルター条件をリストで管理（後から条件を追加できる）
        self.filter_terms = ["研究者情報", "Researcher Information"]

        # 検索を実施
        self.search()

    def __build_query(self):
        exact_query = " ".join(f'"{term}"' for term in self.exact_terms) if self.exact_terms else ""
        loose_query = " ".join(self.loose_terms) if self.loose_terms else ""
        # 両方の文字列をスペースで連結
        return f"{exact_query} {loose_query}".strip()

    def search(self):
        params = {
            "q": self.query,
            "key": self.api_key,
            "cx": self.search_engine_id,
            "start": 1  # 最初の結果のみを取得
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()  # HTTPエラーの場合は例外を発生させる
            data = response.json()
            items = data.get("items")
            if items:
                # タイトルに指定のフィルター条件が含まれるものだけをフィルタリング
                self.filtered_items = self.__filter_search_results(items)
                if self.filtered_items and len(self.filtered_items) > 0:
                    first_item = self.filtered_items[0]
                    self.first_result_link = first_item.get("link")
                    self.first_result_title = first_item.get("title")
                    self.first_result_snippet = first_item.get("snippet")
                else:
                    print("指定のフィルター条件に一致する検索結果が見つかりませんでした。クエリ:", self.query)
            else:
                print("検索結果が見つかりませんでした。クエリ:", self.query)
        except Exception as e:
            print("検索中にエラーが発生しました:", e)

    def __filter_search_results(self, items):  
        
        return [
            item for item in items
            if any(term in item.get("title", "") for term in self.filter_terms)
        ]

    def get_first_result_link(self):
      
        if self.first_result_link:
            print("記事のタイトル:", self.first_result_title)
            print("スニペット:", self.first_result_snippet)
        else:
            print("検索結果が存在しません。")
        return self.first_result_link

    def print_all_results(self):
        """
        フィルタリングされた全ての検索結果について、タイトルとリンクのみを出力します。
        """
        if not self.filtered_items:
            print("フィルタリングされた検索結果が存在しません。")
            return

        print("フィルタリングされた全ての検索結果:")
        for idx, item in enumerate(self.filtered_items, start=1):
            title = item.get("title", "No title")
            link = item.get("link", "No link")
            print(f"{idx}. タイトル: {title}")
            print(f"   リンク: {link}")

    def get_jglobal_researcher_link_from_first_result(self):
         # URL をパースしてクエリから "JGLOBAL_ID" のみを抽出
        parsed = urlparse(self.first_result_link)
        qs = parse_qs(parsed.query)
        new_qs = {}
        if "JGLOBAL_ID" in qs:
            new_qs["JGLOBAL_ID"] = qs["JGLOBAL_ID"]
        new_query = urlencode(new_qs, doseq=True)
        cleaned_link = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
        
        return cleaned_link
    


if __name__ == "__main__":
    # サンプル：完全一致キーワードとそうでないキーワードを両方使って検索する例
    #exact_terms = ["J-Global","Kawamura","Ren","Dokkyo Medical University"]         # 完全一致させたいキーワード
    exact_terms = ["Atsushi","Mizumoto","Kansai University"]

    jglobal_search = JGlobalCustomSearch(exact_terms=exact_terms)
    print(jglobal_search.get_jglobal_researcher_link_from_first_result())
    jglobal_search.print_all_results()
    
    if exact_terms[0] in jglobal_search.first_result_title and exact_terms[1] in jglobal_search.first_result_title:
        print("この人物です")

    
    
    

    # def search_jglobal_link(self):
    #     try:
    #         for result in self.results_list: 
    #             for paper in result["papers_info"][:10]:
    #                 try:
    #                     paper_title = paper["paper_title"]
    #                     if paper_title:
    #                         exact_terms = [result["name"]]+ [paper_title]
    #                         jglobal_search = JGlobalCustomSearch(exact_terms=exact_terms)
    #                         if jglobal_search.get_jglobal_researcher_link_from_first_result():
    #                             result["j_global_link"]  = jglobal_search.get_jglobal_researcher_link_from_first_result()
    #                             break
    #                 except Exception as e:
    #                     print(f"search_jglobal_link内でエラー:{e}")
        
    #             result["j_global_link"] = ""
    #         return
    #     except Exception as e:
    #         raise Exception(f"search_jglobal_linkの中でエラー:{e}")
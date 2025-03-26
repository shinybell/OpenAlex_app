import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from api.google_custom_search import JGlobalCustomSearch
from scraping.jglobal_selenium_search import JGlobalSeleniumSearch
from urllib.parse import urlparse, urlunparse

#####注意#####
#これは、研究者データが載っている、jglobal(https://jglobal.jst.go.jp/)というサイトから、研究者の特許情報を取得するための、スクレイピングコードです。
#しかし、現在のコードのままでは、EC2上では使えず、ローカル環境でのみ動作しますので、もしjglobalから特許情報を取得するロジックを追加したい場合は、下記の修正が必要です。
#・chromeがないEC2でも動作するように修正
#・現在のコードでは、OpenAlex上のデータとjglobal上のデータで研究者の最新の所属機関情報が異なると見つけられない。



class GetJGlobalData:
    def __init__(self, results_list, method="search"):
        self.results_list = results_list
        self.method = method
        if self.method == "search":
            #倫理的な問題を回避する方法だが、google custom search API を使用する。
            self.search_by_google_custom_search()
        else:
            #こちらは、robots.txtに違反し、倫理的な問題が伴う方法。
            self.search_in_research_map()
        
        self.selenium_search_for_patent()
            
    def search_by_google_custom_search(self):
        try:
            for result in self.results_list: 
                result["j_global_link"] = ""
                latest_affiliations = result.get("latest_affiliation", [])
                name = result.get("name", "").strip()
                name_splited = name.split(" ")
                if not name:
                    continue
                
                for aff in latest_affiliations:
                    aff.strip()
                    exact_terms = name_splited + [aff.strip()]
                    jglobal_search = JGlobalCustomSearch(exact_terms=exact_terms)
                    if jglobal_search.get_jglobal_researcher_link_from_first_result():
                        if exact_terms[0] in jglobal_search.first_result_title and exact_terms[0] in jglobal_search.first_result_title:  
                            result["j_global_link"] = self.remove_en_from_jglobal_url(jglobal_search.get_jglobal_researcher_link_from_first_result())
                        break
            return
        
        except Exception as e:
            raise Exception(f"search_jglobal_linkの中でエラー:{e}")
        

    def search_in_research_map(self):
        try:
            from scraping.research_map_search import JGlobalResearchMapSearch
        except ImportError as e:
            raise Exception("JGlobalResearchMapSearch モジュールの読み込みに失敗しました: " + str(e))
        print("search_in_research_map関数 (外部クラス利用)")
        jglobal_rm_search = JGlobalResearchMapSearch(data_set_list=self.results_list, max_work=3)
        jglobal_rm_search.get_research_map_links()
        
    def selenium_search_for_patent(self):
        print("selenium_search_for_patent関数")
       
        try:
            data_set_list = []
            for result in self.results_list: 
                data_set = {
                    "author_id": result["author_id"],
                    "j_global_link": result["j_global_link"]
                }
                data_set_list.append(data_set)
            
            print(len(data_set_list))
            jglobal_search = JGlobalSeleniumSearch(data_set_list, max_work=3)
            jglobal_search.get_patents_counts()
            patents_mapping = {
                data["author_id"]: data.get("patents_count", -200)
                for data in data_set_list
            }
            # self.results_list を走査して、同一の author_id があれば patents_count を更新
            for result in self.results_list:
                author_id = result.get("author_id")
                if author_id in patents_mapping:
                    result["patents_count"] = patents_mapping[author_id]
        except Exception as e:
            raise Exception(f"selenium_search_for_patent関数内でエラー:{e}")
        
    def remove_en_from_jglobal_url(self, url):
        """
        指定されたURLのパス部分に '/en/' が含まれていれば、最初の1箇所を '/' に置換して返す。
        
        例：
        https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=201101096882374533
        → https://jglobal.jst.go.jp/detail?JGLOBAL_ID=201101096882374533
        """
        parsed = urlparse(url)
        # パスが '/en/...' で始まっている場合、先頭の '/en/' を '/' に置換
        if parsed.path.startswith('/en/'):
            new_path = parsed.path.replace('/en/', '/', 1)
        else:
            new_path = parsed.path
        new_parsed = parsed._replace(path=new_path)
        return urlunparse(new_parsed)

    
# ----------------------------------------------------------------------------
# サンプル利用例
if __name__ == "__main__":
    # サンプルの results_list（各要素に "name" と "latest_affiliation" の情報が入っている）
    sample_results = [
        {
            "author_id": "A1",
            "name": "Yutaka Matsuo",
            "latest_affiliation": ["The University of Tokyo", "Dokkyo Medical University"],
            "j_global_link": ""
        }
    ]
    
    get_jglobal = GetJGlobalData(sample_results,method="selenium")
    
    # 結果の確認
    for res in sample_results:
        print("名前:", res.get("name"))
        print("j_global_link:", res.get("j_global_link"))
        print("-----")
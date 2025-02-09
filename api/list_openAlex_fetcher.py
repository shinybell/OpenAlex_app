import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import requests
from dotenv import load_dotenv
import math
from concurrent.futures import ThreadPoolExecutor
import time
from utils.common_method import extract_id_from_url
from collections import Counter

class OpenAlexPagenationDataFetcher:
    
    def __init__(self,endpoint_url, params,id,max_works,only_japanese=False,use_API_key=False,max_count_10000=True):
        load_dotenv()  # 追加
        self.output_log =True
        self.max_count_10000 = max_count_10000
        self.max_workers =  max_works
        self.endpoint_url = endpoint_url
        self.params = params
        id = extract_id_from_url(id)
        self.id=id.upper()
        if self.id in ["A9999999999"]:
            raise Exception(f"OpenAlexPagenationDataFetcherに不当なauthor_idが渡されました。{self.id}")
        
        self.only_japanese = only_japanese
        #self.correspondingR_results = []

        # APIキーの取得
        if use_API_key:
            self.api_key = os.getenv('API_KEY')  # 環境変数からAPIキーを取得
            if not self.api_key:
                raise ValueError("API_KEYが環境変数に設定されていません。")
            # APIキーをクエリパラメータに追加
            self.params["api_key"] = self.api_key  # クエリパラメータとして追加
            self.params["mailto"] = "t.ichikawa.bnv@gmail.com"
            self.print_log("APIキーを使っています。")
        else:
            self.print_log("APIキーを使っていません。")
            
        self.meta, self.all_results = self.meta_data_getter()
            
        if self.meta or self.all_results: 
            if params["per_page"] and self.meta.get('count') <= params["per_page"]:
                pass
                #print("１回目で終了")
            else:
                if self.max_count_10000 or self.meta.get('count')<=10000:
                    #print("オフセット")
                    self.all_results.extend(self.fetch_all_data_with_offset_pagination())
                else:
                    #print("カーソル")
                    print(f"カーソル:\nendpoint_url: {self.endpoint_url}\n" + "\n".join([f"{key}: {value}" for key, value in self.params.items()]))
                    self.all_results.extend(self.fetch_all_data_with_cursor_pagination())
            
    def meta_data_getter(self):
        
        retrial_num=0
        while True:
            try: 
                response = requests.get(self.endpoint_url, params=self.params,timeout=5)
                self.print_log(response.url)
                if response.status_code == 200:  
                    data = response.json()
                    # メタデータの表示
                    meta_data = "\n".join([f"{key}: {value}" for key, value in data.get("meta", {}).items()])
                    self.print_log(f"id:{self.id}\nMeta Data:\n{meta_data}")
                    if not self.only_japanese:
                        return data.get("meta", {}) ,data.get("results",[])
                    else:
                        return data.get("meta", {}),self.extract_japanese(data.get("results",[]))
                
                else:
                    retrial_num+=1
                    time.sleep(retrial_num) 
                    self.print_log(f"meta_data_getter retrial_num:{retrial_num},id:{self.id},Status Code:{response.status_code}")   
                    if retrial_num>20:
                        print("データなしと見なす")
                        return {},[]
                         
            except requests.exceptions.Timeout:
                print("リクエストがタイムアウトしました。再試行します。")
            except Exception as e:
                print(f"サーバーから遮断されたので1秒休憩します。:{self.endpoint_url}/{self.params}")
                time.sleep(1)
            
        # オフセットページネーションを使って並列処理をし、全ての結果を取得する関数　　#params['page']はこの関数の中で設定されている。
    def fetch_all_data_with_offset_pagination(self):
        all_results = []
        count = self.meta.get("count")
        if self.max_count_10000 == True:
            count = count if count<=10000 else 10000
        per_page = self.meta.get("per_page")
        total_pages = math.ceil(count / per_page) + 1
        
        # 各ページのデータを並列処理で取得
        def execute_for_page(page):
            retrial_num=0
            while True:
                try:
                    copied_params = self.params.copy()
                    copied_params["page"] = page
                    response = requests.get(self.endpoint_url, params=copied_params,timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        self.print_log(f"Fetched page {page} with {len(data['results'])} results.")
                        if not self.only_japanese:
                            return page, data.get("results", [])  # ページ番号とデータを返す
                        else:
                            return page,self.extract_japanese(data.get("results",[]))       
                    # else:
                    #   print(f"Failed to fetch data for page {page}. Status Code: {response.status_code}")
                        #return page, []  # ページ番号と空リストを返す
                    
                    retrial_num+=1
                    time.sleep(retrial_num)
                    self.print_log(f"fetch_all_data_with_offset_pagination retrial_num:{retrial_num},id:{self.id},Status Code: {response.status_code}")
                
                except requests.exceptions.Timeout:
                    print("リクエストがタイムアウトしました。再試行します。")
                
                except Exception as e:
                    print(f"サーバーから遮断されたので1秒休憩します。:{self.endpoint_url}/{self.params}")
                    print(e)
                    time.sleep(1)
                    
                
        with ThreadPoolExecutor(max_workers = self.max_workers) as executor:
            pages_data = list(executor.map(execute_for_page, range(2, total_pages)))

        # ページ番号順にソートしてall_resultsに追加
        for _, data in sorted(pages_data, key=lambda x: x[0]):  # ページ番号でソート
            all_results.extend(data)

        return all_results

    #カーソルページネーション
    def fetch_all_data_with_cursor_pagination(self):
        all_results = []
        page = 1
        params = self.params.copy()
        del params["page"]
        cursor = "*"
        
        retrial_num=0
        while cursor:
            # APIのパラメータでURL形式のトピックIDをそのまま使用し、カーソルページネーションを指定
            params["cursor"] = cursor
            
            while True:
                try:
                    response = requests.get(self.endpoint_url, params=params,timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        self.print_log(f"Fetched page {page} with {len(data['results'])} results.")
                        results = data.get("results", [])
                        # 結果をall_resultsに追加
                        all_results.extend(results)
                        break
                    
                    retrial_num+=1
                    time.sleep(retrial_num)
                    print(f"fetch_all_data_with_cursor_pagination retrial_num:{retrial_num},id:{self.id},Status Code:{response.status_code}")
                    
                except requests.exceptions.Timeout:
                    print("リクエストがタイムアウトしました。再試行します。")    
                
                except Exception as e:
                    print(f"サーバーから遮断されたので1秒休憩します。:{self.endpoint_url}/{self.params}")
                    time.sleep(1)
                
            #print(f"Failed to fetch data. Status Code: {response.status_code}")
            if len(data['results']) < params["per_page"]:
                break
            
            if len(all_results)>30000:
                print(f"30000個以上:\nendpoint_url: {self.endpoint_url}\n" + "\n".join([f"{key}: {value}" for key, value in self.params.items()])+"\n"+self.meta)
                break

            # 次のカーソルを取得してループを継続（最後のページでcursorがnullになる）
            cursor = data.get("meta", {}).get("next_cursor", None)
            page += 1

        if not self.only_japanese:
            return all_results
        else:
            return self.extract_japanese(all_results)
            
    
    def correspondingR_extracter(self):
        correspondingR_results = []
        for result in self.all_results:
            for author in result.get("authorships", []):
                if self.id.upper() in author.get("author", {}).get("id", "N/A"): 
                    if author.get("is_corresponding", False):
                        correspondingR_results.append(result)    
                    elif "last" in author.get('author_position', 'N/A'):
                        correspondingR_results.append(result)
                    break
                
        return correspondingR_results
            

    def extract_japanese(self,results_list):
        japanese_results_list =[]
        for result in results_list:
            if self.author_JP_checker(result):
                japanese_results_list.append(result)
        return japanese_results_list
                 
    def author_JP_checker(self,data):
        for authorship in data.get("authorships", []):
            for institution in authorship.get("institutions", []):
                if institution.get("country_code") == "JP":
                    return True
        return False
    
    def print_log(self,text):
        try:
            if self.output_log:
                print(text)
        except Exception as e:
            print(e)
        
if __name__ == "__main__":
    # author_id = "https://openalex.org/A5063724667"
    start_time = time.time()  # 実行開始時間を記録
    
    endpoint_url= "https://api.openalex.org/works"
    # params={
    #     "filter": f"author.id:{author_id},type_crossref:journal-article",
    #     "per_page":200
    # }
    params = {#type_crossref: "journal-article" #publication_date:"2018-02-13"#cited_by_count:>20#type_crossref:journal-article
        "filter": f'author.id:A9999999999', #publication_date:<{found_date}>,#type:article',publication_year:2006'
        "page": 1,
        "per_page": 200,
    }
    
    fetcher = OpenAlexPagenationDataFetcher(endpoint_url, params,id="aaaaaa",max_works=100,only_japanese=False,use_API_key=True)
    print(fetcher.meta)
    
    end_time = time.time()  # 実行終了時間を記録
    elapsed_time = end_time - start_time  # 実行時間を計算
    # 時間、分、秒に変換
    hours = int(elapsed_time // 3600)
    minutes = int((elapsed_time % 3600) // 60)
    seconds = int(elapsed_time % 60)
    # フォーマット済みの文字列を作成
    formatted_time = f"{hours}時間{minutes}分{seconds}秒"
    print(formatted_time)
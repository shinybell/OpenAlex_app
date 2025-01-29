import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import time
import threading
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor,as_completed
from utils.fetch_result_parser import OpenAlexResultParser, author_dict_list_to_author_work_data_list, author_dict_to_author_work_data
from api.list_openAlex_fetcher import OpenAlexPagenationDataFetcher
from utils.format_change import title_and_abstract_search_format
from utils.outputer import sort_dict_list_by_key

class CreateAuthorIdList:
    def __init__(self,topic_ids: List[str],primary:bool,threshold:Optional[int],year_threshold:Optional[int],title_and_abstract_search:str,max_works:int,use_API_key = False):
        self.use_API_key = use_API_key
        self.all_results =[]
        self.authors_id_list =[]
        if isinstance(topic_ids,list):
            self.topic_ids = topic_ids 
        else:
            raise Exception(f"topic_idsはリスト型を想定しています。{topic_ids}")
        self.max_works=max_works
        self.endpoint_url = "https://api.openalex.org/works"
        # しきい値などの条件を設定してデータを取得
        self.work_type = "article"
        self.per_page = 200  # 1ページあたりの取得数
        self.page = 1
        self.threshold = threshold if threshold else -1 #最低引用件数
        self.year_threshold = year_threshold if year_threshold else -1 #以降の年   
        self.title_and_abstract_search =""
        
        if title_and_abstract_search:
            #title_and_abstract_searchをフィルターで使えるようにフォーマットを変換
            self.title_and_abstract_search = title_and_abstract_search_format(title_and_abstract_search)

        self.primary = primary
        self.researcher_rows=[]
        self.lock = threading.Lock()  # ロックを初期化
        
        #「スレッド数が max_works を超えない上、できるだけ max_works に近い数になる」よう分割・制御する設計
        if len(self.topic_ids) <=1:
            self.max_workers=max_works
        elif len(self.topic_ids) ==2:
            self.max_workers=max_works//2
        elif len(self.topic_ids) ==3:
            self.max_workers=max_works//3
        else:
            self.max_workers=max_works//4
            

    def run_get_works(self)-> None:
        #topicがある場合
        if len(self.topic_ids)>0:
            with ThreadPoolExecutor(max_workers=4) as executor:
                results = executor.map(self.__process_by_topic, self.topic_ids)
                for result in results:
                    if result:  # 結果が存在する場合のみ追加
                        with self.lock:  # ロックを使って排他制御
                            self.all_results.extend(result)
        
        #topicがない場合
        else:
            try:
                filter_value = f"cited_by_count:>{self.threshold},publication_year:>{self.year_threshold},type:{self.work_type},title_and_abstract.search:{self.title_and_abstract_search}"#,authorships.institutions.country_code:JP"
                params = {
                    "filter":filter_value,
                    "page": self.page, 
                    "per_page": self.per_page
                }
                fetcher = OpenAlexPagenationDataFetcher(self.endpoint_url,params,self.title_and_abstract_search,max_works = self.max_works,only_japanese=False,use_API_key = self.use_API_key)
                self.all_results.extend(fetcher.all_results) 
            except Exception as e:
                raise Exception(f"Failed to fetch works without topics: {e}")
            
        _,self.article_dict_list=OpenAlexResultParser.works_dict_list_from_works_results(self.all_results)
        self.article_dict_list = sort_dict_list_by_key(self.article_dict_list,"Cited By Count")

    def __process_by_topic(self, topic_id: str)-> List[dict]:
        try: # 条件に応じてfilterの内容を分岐させる
            filter_value = self.__build_filter(topic_id)
            params = {
                "filter":filter_value,
                "page": self.page, 
                "per_page": self.per_page
            }
            fetcher = OpenAlexPagenationDataFetcher(self.endpoint_url,params,topic_id,max_works =self.max_workers,only_japanese=False,use_API_key=self.use_API_key)
            return fetcher.all_results  # 成功した場合は結果を返す
        except Exception as e:
            raise Exception(f"Failed to add results for topic_id {topic_id}: {e}")
    
    def __build_filter(self, topic_id: str) -> str:
        topic_key = "primary_topic.id" if self.primary else "topics.id"
        return f"{topic_key}:{topic_id},cited_by_count:>{self.threshold},publication_year:>{self.year_threshold},type:{self.work_type},title_and_abstract.search:{self.title_and_abstract_search}"#,authorships.institutions.country_code:JP"
    
    def extract_authors(self, only_japanese: bool = False) -> None:
        def is_japanese_author(author: dict) -> bool:
            institutions = author.get('institutions', [])
            return any(inst.get('country_code') == "JP" for inst in institutions)
        
        temp_authors_id_list = [
            author.get('author', {}).get('id', 'N/A')
            for result in self.all_results
            for author in result.get("authorships", [])
            if not only_japanese or is_japanese_author(author)
        ]
        self.authors_id_list = list(set(temp_authors_id_list))
    
    def convert_keywords_to_or_condition(self,keywords:List[str]) -> str:
        if not keywords:
            return ""
        # 各キーワードをクォートで囲み、ORで結合して括弧で囲む
        quoted_keywords = [f'"{keyword}"' for keyword in keywords]
        return f"({' OR '.join(quoted_keywords)})"
    
    def get_top_article(self,author_id):
        # 指定された著者IDに関連する論文を抽出
        author_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(self.article_dict_list, only_single_author_id=author_id)
        #author_dict_list = sort_dict_list_by_key(author_dict_list,"Cited By Count")
        if not author_dict_list:
            return -1, {}

        article = author_dict_list[0]
        article_dict = {
            "世界ランキング":article.get("ranking",-1),
            "総数":article.get("total_count",-1),
            "条件論文1:ID":article.get("Article ID",""),
            "条件論文1:タイトル":article.get("Title",""),
            "条件論文1:出版年月":article.get("Publication Date",""),
            "条件論文1:被引用数":article.get("Cited By Count",0)
        }
        
        return article_dict

if __name__ == "__main__":
  
    #開始時間を記録
    start_time = time.time()
    #'("novel target" OR "new target" OR "therapeutic target")'
    #["novel target","new target","therapeutic target"]                                                                                                                             
    creater = CreateAuthorIdList(topic_ids=["T10966"],primary=True,threshold=9,year_threshold=2009,title_and_abstract_search="" ,max_works=16,use_API_key=False)#("novel target" OR "new target" OR "therapeutic target")
    creater.run_get_works()
    print(len(creater.all_results))
    print(len(creater.authors_id_list))
    
    creater.extract_authors(only_japanese=True)
    print(f"日本研究者数:{len(creater.authors_id_list)}")
    
    # 終了時間を記録
    end_time = time.time()
    # 処理時間を計算
    elapsed_time = end_time - start_time
    print(f"処理時間:{elapsed_time:.2f}秒")


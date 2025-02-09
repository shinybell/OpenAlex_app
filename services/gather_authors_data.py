import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils.common_method import get_type_counts,extract_id_from_url
from utils.create_author_profile import create_author_profile
from utils.calculater import Calculater
from utils.fetch_result_parser import OpenAlexResultParser, author_dict_list_to_author_work_data_list
from api.list_openAlex_fetcher import OpenAlexPagenationDataFetcher
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import ThreadPoolExecutor, as_completed

class GatherAuthorData:
    def __init__(self,author_id,max_workers=1,found_date="",use_API_key=False):
        if author_id in ["A9999999999"]:
            raise ValueError(f"GatherAuthorDataに不当なauthor_idが渡されました。{self.id}")
        self.article_dict_list = []
        self.author_id = extract_id_from_url(author_id)
        self.author_id=self.author_id.upper()
        self.found_date = found_date
        self.max_workers = max_workers
        self.use_API_key =use_API_key
        self.profile = None
        
    def run_fetch_works(self):
        endpoint_url = "https://api.openalex.org/works" 
        if not self.found_date:
            params = {#type_crossref: "journal-article" #publication_date:"2018-02-13"#cited_by_count:>20#type_crossref:journal-article
                "filter": f'author.id:{self.author_id}', #publication_date:<{found_date}>,#type:article',publication_year:2006'
                "page": 1,
                "per_page": 200,
            }
        else:
            params = {
                "filter": f'author.id:{self.author_id},publication_date:<{self.found_date}',
                "page": 1,
                "per_page": 200,
            }
        fetcher = OpenAlexPagenationDataFetcher(endpoint_url, params, self.author_id, max_works=self.max_workers, only_japanese=False,use_API_key=self.use_API_key)
        if fetcher.all_results:
            _, self.article_dict_list = OpenAlexResultParser.works_dict_list_from_works_results(fetcher.all_results)
        else:
            self.article_dict_list = []
            
    def di_calculation(self):
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_article = {executor.submit(Calculater.calculate_disruption_index_for_article, article,self.found_date,use_API_key=self.use_API_key): article 
            for article in self.article_dict_list
            }
            for future in as_completed(future_to_article):
                article = future_to_article[future]
                try:
                    updated_article = future.result()
                    # 計算された disruption_index を元の article_dict_list に戻す
                    article.update(updated_article)
                except Exception as exc:
                    print(f"{article['ID']} の処理中にエラーが発生しました#D-indexとimpactの計算: {exc}")

    def gathering_author_data(self,get_type_counts_info=False):
        if self.article_dict_list:
            author_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(self.article_dict_list, only_single_author_id=self.author_id)
            authorWoorkData_list = author_dict_list_to_author_work_data_list(author_dict_list)
            profile = create_author_profile(authorWoorkData_list)
            
            if get_type_counts_info:
                type_crossref_dict = get_type_counts(self.author_id,type="type_crossref",found_date=self.found_date)
                type_dict = get_type_counts(self.author_id,type="type",found_date=self.found_date)
                profile.article_type_crossref_dict = type_crossref_dict
                profile.article_type_dict = type_dict
                
            self.profile = profile
            return self.profile
        else:
            raise Exception("article_dict_listがFalseの時は、gathering_author_dataを実行してはいけません。")
        
    def coauthors_coauthor_data(self,key_list):
        sum_dict = {key: 0 for key in key_list}  
        coauthor_keys_list = list(self.profile.each_coauthor_count_dict.keys())
        
        def process_coauthor(coauthor_id):
            coauthor = GatherAuthorData(coauthor_id, max_workers=1, found_date=self.found_date, use_API_key=self.use_API_key)
            coauthor.run_fetch_works()
            if not coauthor.article_dict_list:
                return {}
            profile = coauthor.gathering_author_data()
            profile_dict = profile.to_dict()

            return profile_dict

        # 並列処理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_coauthor = {executor.submit(process_coauthor, coauthor_id): coauthor_id for coauthor_id in coauthor_keys_list}

            for future in as_completed(future_to_coauthor):
                coauthor_id = future_to_coauthor[future]
                try:
                    profile_dict = future.result()
                    # key_list に基づいて profile_dict から値を取得して合計
                    for key in key_list:
                        value = profile_dict.get(key, 0)  # key が存在しない場合は 0 を返す
                        if isinstance(value, (int, float)):  # 数値型のみ合計
                            count = self.profile.each_coauthor_count_dict.get(coauthor_id, 0)
                            sum_dict[key] += value * count
                            
                except Exception as exc:
                    print(f"{coauthor_id} の処理中にエラーが発生しました: {exc}")
                    
        return sum_dict

    def get_top_three_article(self):
        
        # impact_indexが存在し、かつ0より大きい記事を収集
        articles_with_impact = []
        articles_without_impact = []

        for article in self.article_dict_list:
            impact = article.get("impact_index")
            try:
                impact_val = float(impact)
                if impact_val > 0:
                    articles_with_impact.append(article)
                else:
                    articles_without_impact.append(article)
            except (ValueError, TypeError):
                # impact_indexが""やNoneなど数値に変換できない場合
                articles_without_impact.append(article)

        # impact_indexがある記事をimpact_indexの降順でソート
        articles_with_impact_sorted = sorted(
            articles_with_impact,
            key=lambda x: float(x["impact_index"]),
            reverse=True
        )

        # impact_indexがない記事をCited By Countの降順でソート
        articles_without_impact_sorted = sorted(
            articles_without_impact,
            key=lambda x: int(x.get("Cited By Count", 0)),
            reverse=True
        )

        # 上位3つを抽出
        top_articles = articles_with_impact_sorted[:3]

        # impact_indexが0より大きい記事が3つ未満の場合、Cited By Countで埋める
        if len(top_articles) < 3:
            needed = 3 - len(top_articles)
            top_articles.extend(articles_without_impact_sorted[:needed])

        top_articles_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(top_articles,only_single_author_id=self.author_id)
        works_data = {}
        for i, article in enumerate(top_articles_dict_list[:3], start=1):  # 1から始める
            works_data[f"論文{i}:ID"] = article.get("Article ID", "N/A")
            works_data[f"論文{i}:タイトル"] = article.get("Title","N/A")
            works_data[f"論文{i}:Corresponding Authors"] = any(
                extract_id_from_url(art.get("id")) == self.author_id for art in article.get("Corresponding Authors", [])
            )
            works_data[f"論文{i}:Author Position"] = article.get("Author Position", "N/A")
            works_data[f"論文{i}:Corresponding Authors name"] = [
                author['name'] for author in article.get("Corresponding Authors", [])
            ]
            works_data[f"論文{i}:被引用数"] = article.get("Cited By Count", 0)
            works_data[f"論文{i}:D-Index"] = article.get("Disruption Index", -200)     
            works_data[f"論文{i}:Primary Topic"] = article.get("Primary Topic", "N/A")
            works_data[f"論文{i}:Topics"] = article.get("Topics", [])
            works_data[f"論文{i}:出版年月"] = article.get("Publication Date", "N/A")
            works_data[f"論文{i}:Landing Page URL"] = article.get("Landing Page URL", "N/A")
            works_data[f"論文{i}:Authors"] = article.get("Authors", "N/A")
            works_data[f"論文{i}:Keywords"] = article.get("Keywords", "N/A")
            works_data[f"論文{i}:Grants"] = article.get("Grants", [])
        
        return works_data
        
   
    

if __name__ == "__main__":
    
    # secret = SecretManager()
    # sheet_manager = SpreadsheetManager("ジャーナル一覧", "シート1")

    # 開始時間を記録
    start_time = time.time()

    author = GatherAuthorData(author_id="https://openalex.org/A5076725199",max_workers=12)
    author.run_fetch_works()
    print(len(author.article_dict_list))
    #author.di_calculation()
    profile_dict = author.gathering_author_data()
    
    coauthor_data_dict = author.coauthors_coauthor_data(["works_count","total_works_citations","h_index","last_5_year_h_index","coauthor_from_company_count","first_paper_count","corresponding_paper_count"])
    
    # 終了時間を記録
    end_time = time.time()
    # 処理時間を計算
    elapsed_time = end_time - start_time
    print(f"処理時間: {elapsed_time:.2f} 秒")
    
    #print(coauthor_data_dict)
    
    
    # row = [str(value) for value in profile_dict.values()]
    # rows = [row]  # `append_rows`はリストのリストを期待する
    # for row in rows:
    #     for i,each in enumerate(row):
    #         if len(each)>=50000:
    #             print("インデクス",i)
    #             row[i] = each[:50000]
            
    # sheet_manager.append_rows(rows)
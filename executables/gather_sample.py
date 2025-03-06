import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
import requests
from typing import List, Optional
from services.gather_authors_data import GatherAuthorData
from api.new_fetch_author_entity import NewFetchAuthorEntity
from utils.common_method import get_type_counts,extract_id_from_url
from api.list_openAlex_fetcher import DataNotFoundError, OpenAlexPagenationDataFetcher
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from services.get_global_data import GetJGlobalData
from utils.outputer import Outputer
import threading
from utils.aggregate_vectors_spacy import aggregate_vectors

class GatheringSampleAuthor:
    def __init__(self,focul_author_id: str,found_date = "",max_works = 80,use_API_key = True):
       
        self.focul_author_id = extract_id_from_url(focul_author_id) #このauhorのサンプルを調べる
        self.found_date = found_date #いつまでのデータが欲しいか
        self.max_works = max_works
        self.use_API_key = use_API_key
        self.filtered_authors_ids = [] #サンプル候補としてauthorエンティティから見つけたauthorIDリスト
        self.profile_list_befor_ranking= [] #author_id とGetAuthorDataのインスタンスを入れたリスト
        self.lock = threading.Lock()

    def search_focul_author(self) -> dict:
        #見つけるサンプルの元となるauthorの基本情報を収集する関数
        works_entity = GatherAuthorData(self.focul_author_id,max_workers=self.max_works,found_date=self.found_date,use_API_key=True)
        works_entity.run_fetch_works()
        if not works_entity.article_dict_list:
            raise DataNotFoundError("該当のデータは存在しません。")
        profile = works_entity.gathering_author_data()
        self.top3_topics = [extract_id_from_url(topic["Topic ID"]) for topic in profile.topics_detail[:3]]
        self.works_count = profile.works_count
        self.h_index = profile.h_index
        self.cited_by_count = profile.total_works_citations
        self.career_years = profile.career_years
        self.first_career_year = profile.first_career_year
        print(
            f"Top3 Topic IDs: {self.top3_topics}\n"
            f"Works Count: {self.works_count}\n"
            f"H-Index: {self.h_index}\n"
            f"Cited by Count: {self.cited_by_count}\n"
            f"career_years:{self.career_years}\n"
        )
                        
    def search_sample_authors_ids(self) -> List[str]:
        #search_focul_authorで調べて得たサンプルの基準となるデータをもとに、authorエンティティ候補となるauthorIDを取得する。
        
        # works_count と h_index に対して下限・上限を設定
        lower_works_count = int(self.works_count * 0.8)
        upper_works_count = int(self.works_count * 1.2)
        lower_h_index = int(self.h_index * 0.8) if not self.found_date else self.h_index
        upper_h_index = int(self.h_index * 1.2)
        
        # トピックフィルターの候補を作成
        # 例として self.top3_topics は ["Txxxx", "Tyyyy", "Tzzzz"] などのリストである前提
        filters = []
        if len(self.top3_topics) >= 3:
            filters.append(f"topics.id:{self.top3_topics[0]}+{self.top3_topics[1]}+{self.top3_topics[2]}")
        if len(self.top3_topics) >= 2:
            filters.append(f"topics.id:{self.top3_topics[0]}+{self.top3_topics[1]}")
            filters.append(f"topics.id:{self.top3_topics[0]}+{self.top3_topics[2]}")
            filters.append(f"topics.id:{self.top3_topics[1]}+{self.top3_topics[2]}")
        if len(self.top3_topics) >= 1:
            filters.append(f"topics.id:{self.top3_topics[0]}")
        
        filtered_authors_set = set()
        
        def search_filter(filt: str) -> List[str]:
            filter_str = (
                f"affiliations.institution.country_code:JP,"
                # f"works_count:<{upper_works_count},"
                # f"works_count:>{lower_works_count},"
                #f"summary_stats.h_index:<{upper_h_index},"
                f"summary_stats.h_index:>{lower_h_index},"
                f"{filt}"
            )

            endpoint_url= "https://api.openalex.org/authors"
            params = {
                "filter":filter_str, 
                "page": 1,
                "per_page": 200,
            }
            fetcher = OpenAlexPagenationDataFetcher(endpoint_url,params,filters,self.max_works,use_API_key=self.use_API_key,max_count_10000=True)
            author_id_list =[]
            for result in fetcher.all_results:
                author_id = extract_id_from_url(result["id"])
                author_id_list.append(author_id)
            return author_id_list
               
        # 並列処理で各フィルター条件ごとのリクエストを実行
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(search_filter, filt) for filt in filters]
            for future in concurrent.futures.as_completed(futures):
                try:
                    result_ids = future.result()
                    for author_id in result_ids:
                        if author_id not in filtered_authors_set:
                            filtered_authors_set.add(author_id)
                except Exception as e:
                    print("エラーが発生しました:", e)
        
        # self.focul_author_idが含まれていなければ追加する
        if self.focul_author_id not in filtered_authors_set:
            filtered_authors_set.add(self.focul_author_id)
        
        self.filtered_authors_ids = list(filtered_authors_set)
        return self.filtered_authors_ids

    def search_sample_authors_info(self):
        def process_author(author_id): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(author_id, "の調査")
                author = GatherAuthorData(author_id=author_id,max_workers=20,found_date=self.found_date,use_API_key=self.use_API_key)
                author.run_fetch_works()
                # if di_calculation:
                #     author.di_calculation()
                if not author.article_dict_list:
                    return {}
                profile = author.gathering_author_data()
                
                with self.lock:
                    temp_dict ={
                        "author_id":author_id,
                        "instance":author
                    }
                    self.profile_list_befor_ranking.append(temp_dict)
                
                profile_dict = profile.to_dict()
                 
                #profile_dict["h_index"]とself.h_index とのござが20%以上であれば、return {}をする
                if self.h_index != 0 and abs(profile_dict["h_index"] - self.h_index) / self.h_index >= 0.2:
                    return {}
                
                return profile_dict
            
            except ValueError as e:
                print(f"process_author内で想定内のエラー (author_id: {author_id}): {e}") 
            except Exception as e:
                print(f"process_authorのprocess_author内で想定外のエラーが発生 (author_id: {author_id}): {e}") 
                raise
            
        self.sample_dict_list = []
        max_workers = 16 if self.use_API_key else 8
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, author_id): author_id for author_id in self.filtered_authors_ids[:1500]}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    if result:
                        self.sample_dict_list.append(result)
                        print(f"{len(self.sample_dict_list)}人目の{author_id}の抽出が完了しました")
                    else:
                        print(f"{author_id}は条件を満たしていませんでした。")
                
                except Exception as e: 
                    print("エラーが発生",e)
                    
        return self.sample_dict_list
    
    def rank_samples_by_relevance(self):

        def compute_topic_score(sample):
            score = 0.0
            sample_topic_detail = sample["topics_detail"]  # 例: [{'Topic ID': 'Txxxx', 'Count': 10, ...}, ...]
            for forcal_topic_id in self.top3_topics:
                # topics_detail 内で self.top3_topics のトピックを探す
                for i, t in enumerate(sample_topic_detail):
                    if extract_id_from_url(t.get("Topic ID")) == forcal_topic_id:
                        score += 1.0 / (i + 1)
            return score

        def sample_sort_key(sample):
            topic_score = compute_topic_score(sample)
            sample["topic_score"] = round(topic_score, 4)
            career_diff = abs(sample["career_years"] - self.career_years)
            threshold = 0.15 * self.career_years  # self.career_yearsの15%を閾値として設定

            if career_diff <= threshold:
                # キャリア差が15%以下なら、まずflag 0（＝「許容範囲内」）とし、
                # topic_scoreは高いほうが良いため、降順にする（マイナス値）
                # 同値の場合、キャリア差が小さいほうが良いので、career_diffをそのまま採用
                return (0, -topic_score, career_diff)
            else:
                # キャリア差が15%を超える場合は、flag 1（＝「許容範囲外」）とし、
                # career_diffが小さいものを優先
                return (1, career_diff)

        # 並び替えを実行
        self.sample_dict_list.sort(key=sample_sort_key)
        
        # まず、self.profile_list_befor_ranking を author_id をキーにした辞書に変換しておくと高速に検索できます。
        profile_dict = { profile["author_id"]: profile for profile in self.profile_list_befor_ranking }

        # self.sample_dict_list の順番に合わせて、self.profile_list_after_ranking を作成
        self.profile_list_after_ranking = []
        for sample in self.sample_dict_list:
            author_id = extract_id_from_url(sample.get("author_id"))
            # 該当する author_id があれば、辞書から取り出して追加
            if author_id in profile_dict:
                profile_dict[author_id]["topic_score"]=sample["topic_score"]
                self.profile_list_after_ranking.append(profile_dict[author_id])
        
        print(f"self.profile_list_after_ranking{len(self.profile_list_after_ranking)}")
        return self.sample_dict_list

    def detail_sample_author_survey(self,need_sample_num=5):
        def process_author(entry): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                author = entry["instance"]
                author_id = entry["author_id"]
                topic_score = entry["topic_score"]
                
                print(author_id, "の調査")
                author.di_calculation()
                profile = author.gathering_author_data(get_type_counts_info=True,release=True)
                profile_dict = profile.to_dict()
                
                profile_dict["topic_score"] = topic_score
                
                coauthor_data_dict = author.coauthors_coauthor_data(["works_count","total_works_citations","h_index","last_5_year_h_index","coauthor_from_company_count","first_paper_count","corresponding_paper_count","keyword_count","coauthor_count"])
                coauthor_data_dict = {f"coauthors_total_{key}": value for key, value in coauthor_data_dict.items()}
                profile_dict.update(coauthor_data_dict)
                
                vectors_dict = aggregate_vectors(profile_dict["papers_info"],baseline_date=self.found_date)
                profile_dict.update(vectors_dict)
                
                return profile_dict
            
            except ValueError as e:
                print(f"process_author内で想定内のエラー (author_id: {author_id}): {e}") 
            except Exception as e:
                print(f"detail_sample_author_surveyのprocess_author内で想定外のエラーが発生 (author_id: {author_id}): {e}") 
                raise
            
        self.sample_dict_list_for_detail_surveyed = []
        max_workers = 5 if self.use_API_key else 1
        print(f"{len(self.profile_list_after_ranking[:need_sample_num])}個のサンプルを用意します。")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, entry): entry["author_id"] for entry in self.profile_list_after_ranking[:need_sample_num]}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    self.sample_dict_list_for_detail_surveyed.append(result)
                    print(f"{len(self.sample_dict_list_for_detail_surveyed)}人目の{author_id}の抽出が完了しました")
                except Exception as e: 
                    print("エラーが発生",e)
                    
        return self.sample_dict_list_for_detail_surveyed
        

    def ensure_focal_author_first(self, sample_dict_list: list) -> list:
        """
        サンプルの辞書リストから、focul_author_id と一致する author_id を持つ辞書を
        先頭に配置します。
        
        - 一致する辞書が存在する場合は、その辞書をリストの先頭に移動します。
        - 一致する辞書が存在しない場合は、既存の辞書のキー構成を参考にして、
        全ての値に "focul_author_idがありませんでした" を設定した辞書をリストの先頭に追加します。
        
        Parameters:
            sample_dict_list (list): 各エントリーが辞書となっているリスト
        
        Returns:
            list: focul_author_id のエントリーが先頭に配置された辞書リスト
        """
        focal_found = False
        # 各辞書を走査して、author_id が focul_author_id と一致するか確認する
        for i, entry in enumerate(sample_dict_list):
            if extract_id_from_url(entry.get("author_id")) == extract_id_from_url(self.focul_author_id):
                # 該当する辞書が見つかったら、その辞書をリストの先頭に移動
                focal_entry = sample_dict_list.pop(i)
                sample_dict_list.insert(0, focal_entry)
                focal_found = True
                break

        # focul_author_id に該当する辞書がなかった場合
        if not focal_found:
            print("ensure_focal_author_firstで、focal_authorを見つけられませんでした。")
           #raise ValueError("ensure_focal_author_firstで、focal_authorを見つけられませんでした。")
        
        return sample_dict_list

if __name__ == "__main__":
    from api.spreadsheet_manager import SpreadsheetManager
    # sheet_manager = SpreadsheetManager("OpenAlex_App_Core8_テスト用（使用できません）", "シート7")
    # sheet_manager.clear_rows_from_second()
    import asyncio
    
    search_datas = [#ソフトウェア/アプリ
        {"date": "2017/08/30", "author_id": "A5042410446"},
        {"date": "2022/07/30", "author_id": "A5034708867"},
        {"date": "2022/03/30", "author_id": "A5070315511"},
        {"date": "2013/11/30", "author_id": "A5063896943"},
        {"date": "2018/03/30", "author_id": "A5069794526"},
        {"date": "2014/09/30", "author_id": "A5037803109"},
        {"date": "2020/01/30", "author_id": "A5080895628"},
        {"date": "2018/07/30", "author_id": "A5037718511"},
        {"date": "2016/04/30", "author_id": "A5112292144"},
        {"date": "2001/04/30", "author_id": "A5110502296"},
        {"date": "2021/12/30", "author_id": "A5112653589"},
        {"date": "2005/11/30", "author_id": "A5001431702"},
        {"date": "2014/09/30", "author_id": "A5101584052"},
        {"date": "2018/11/30", "author_id": "A5052996420"},
        {"date": "2017/03/30", "author_id": "A5030484228"},
        {"date": "2004/04/30", "author_id": "A5074039834"},
        {"date": "2022/02/28", "author_id": "A5110784260"},
        {"date": "2020/10/30", "author_id": "A5037675237"},
        {"date": "2011/11/30", "author_id": "A5014835275"},
        {"date": "2020/01/30", "author_id": "A5043867612"},
        {"date": "2008/01/30", "author_id": "A5011588138"},
        {"date": "2023/05/30", "author_id": "A5111344876"},
        {"date": "2005/05/30", "author_id": "A5108639576"},
        {"date": "2008/09/30", "author_id": "A5050981333"},
        {"date": "2019/10/30", "author_id": "A5102327755"},
        {"date": "2017/03/30", "author_id": "A5103003713"},
        {"date": "2018/04/30", "author_id": "A5028226308"},
        {"date": "1994/12/30", "author_id": "A5111675992"},
        {"date": "2015/09/30", "author_id": "A5069123778"},
        {"date": "2013/11/30", "author_id": "A5108297324"},
        {"date": "2004/03/30", "author_id": "A5034359695"},
        {"date": "2016/04/30", "author_id": "A5103787030"},
        {"date": "2018/11/30", "author_id": "A5052996420"},
        {"date": "2022/09/30", "author_id": "A5057961231"},
        {"date": "2018/03/30", "author_id": "A5111677477"},
        {"date": "2018/11/30", "author_id": "A5039757363"},
        {"date": "2018/03/30", "author_id": "A5080053416"}
    ]


    for idx,search_data in enumerate(search_datas,start=1):
        try:
            async def main():
                print("スタート")
                focul_author_id =search_data["author_id"]
                sample_fetcher = GatheringSampleAuthor(
                    focul_author_id=focul_author_id,
                    found_date = search_data["date"],
                    max_works=20,
                    use_API_key=True
                )
                
                print(f"{idx}focul_authorの情報を検索")
                sample_fetcher.search_focul_author()
                print(f"{idx}候補となるauthor_idをauthorエンティティから取得")
                data1 = sample_fetcher.search_sample_authors_ids()
                print(f"{idx}見つかった候補数:",len(data1))
                data = sample_fetcher.search_sample_authors_info()
                print(f"{idx}見つかった情報のある候補数:{len(data)}/{len(data1)}")
                print(f"{idx}rank_samples_by_relevanceを実行します。")
                sample_fetcher.rank_samples_by_relevance()
                print(f"{idx}detail_sample_author_surveyを実行します。")
                sample_dict_list = sample_fetcher.detail_sample_author_survey(need_sample_num=10)
                # detail_sample_author_survey() の返り値に対して、focul_author_id を優先する処理を実行
                sample_dict_list = sample_fetcher.ensure_focal_author_first(sample_dict_list)
                print(f"{idx}用意できたサンプル数:",len(sample_dict_list))
                if sample_dict_list:
                    # print("GetJGlobalDataを実行します。")
                    # print(len(sample_dict_list))
                    # GetJGlobalData(sample_dict_list,method="selenium")
                    # print(len(sample_dict_list))
                    try:
                        print("アウトプットします。")
                        outputer = Outputer(results_list=sample_dict_list,file_name=focul_author_id)
                        await outputer.batch_execute_for_display(analysis="sample")
                    except Exception as e:
                        print(f"シートへの出力でエラーがおきました。:{e}")
                    
                else:
                    print("サンプルは見つかりませんでした。")
            asyncio.run(main())
            
        except DataNotFoundError as e:
            print(f"{e}")
            print(f'{search_data["author_id"]}は存在しませんでした。')
            
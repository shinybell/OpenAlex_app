import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from api.list_openAlex_fetcher import OpenAlexPagenationDataFetcher; 
from utils.fetch_result_parser import OpenAlexResultParser
import requests
import time
from utils.common_method import extract_id_from_url

class Calculater:
    
    def calculate_disruption_index_for_article(article,found_date="",use_API_key=False):
        # フォーカルペーパーのID
        focal_paper_id = extract_id_from_url(article["ID"])
        print(focal_paper_id,"のDIを計算します。")
        # フォーカルペーパーの引用先論文IDリスト
        referenced_works_list = list(map(extract_id_from_url, article["referenced_works"]))
        
        if not found_date:
            cited_by_api_url = article["cited_by_api_url"]+f",type:article"
        else:
            cited_by_api_url = article["cited_by_api_url"]+f",type:article,publication_date:<{found_date}"
            
        # OpenAlexPagenationDataFetcherのインスタンス生成
        fetcher = OpenAlexPagenationDataFetcher(   #引数にonly_japaneseを追加。 #"mailto":"ichiharabox@gmail.com"
            cited_by_api_url, params={"per_page": 200}, id=focal_paper_id, max_works=1 ,only_japanese=False,use_API_key=use_API_key,max_count_10000=True
        )
        #被引用数が15未満であれば、計算しない。
        if len(fetcher.all_results)<15:
            article["disruption_index"]=-200
            article["impact_index"]=-200
            return article
            
        _, cited_article_dict_list = OpenAlexResultParser.works_dict_list_from_works_results(fetcher.all_results)
        
        # フォーカルペーパーの被引用論文情報を入れるリスト（論文ID,その論文の引用先論文s）
        cited_works_info_list = [
            (extract_id_from_url(work["ID"]), list(map(extract_id_from_url, work["referenced_works"])))
            for work in cited_article_dict_list
        ]
        # ディスラプションインデックス インパクトインデックスの計算
        disruption_index = Calculater.cal_disruption_index(focal_paper_id, referenced_works_list, cited_works_info_list)
        article["disruption_index"] = round(disruption_index,2)
        article["impact_index"] = round(Calculater.calculate_article_impact(disruption_index,article["Cited By Count"]),2)
        article["cited_by_other_field"] = Calculater.count_citations_from_other_field(article,fetcher.all_results)
        return article

    
    def count_citations_from_other_field(focal_article,result_list):
        """
            被引用論文の中から、focal_articleと異なるtopicとsubfield,field,domainから引用された論文数を数える関数。
        Args:
            focal_article: works_dict_list_from_works_resultsで作成した辞書
            result_list: openalexから取得したresultsのリスト。
        """
        # カウント用の辞書を初期化
        citation_counts = {
            'topic': 0,
            'subfield': 0,
            'field': 0,
            'domain': 0
        }
        
        #関連トピック(topics)データを取得
        relative = focal_article.get("Topics",[])
        
        relative_topics_list = [extract_id_from_url(topic.get('id', None)) for topic in relative]
        relative_subfield_list = [extract_id_from_url(topic.get('subfield', {}).get('id', None)) for topic in relative]
        relative_field_list = [extract_id_from_url(topic.get('field', {}).get('id', None)) for topic in relative]
        relative_domain_list = [extract_id_from_url(topic.get('domain', {}).get('id', None)) for topic in relative]

        for result in result_list:
             # 各引用論文の主な分野情報を取得
            result_primary_topic = result.get("primary_topic",{})
            if not isinstance(result_primary_topic, dict):
                continue
            result_topic_id = extract_id_from_url(result_primary_topic.get("id",None))
            if not result_topic_id:
                continue
            result_subfield_id = extract_id_from_url(result_primary_topic.get("subfield", {}).get("id"))
            result_field_id = extract_id_from_url(result_primary_topic.get("field", {}).get("id"))
            result_domain_id = extract_id_from_url(result_primary_topic.get("domain", {}).get("id"))
            
            
           # 各カテゴリごとにリストに存在しない場合、カウントを増加
            if result_topic_id and result_topic_id not in relative_topics_list:
                citation_counts['topic'] += 1
            if result_subfield_id and result_subfield_id not in relative_subfield_list:
                citation_counts['subfield'] += 1
            if result_field_id and result_field_id not in relative_field_list:
                citation_counts['field'] += 1
            if result_domain_id and result_domain_id not in relative_domain_list:
                citation_counts['domain'] += 1

        return citation_counts
 
    def calculate_article_impact(di,cited):

        score = 0
        # cited_by_countが19以下の場合は何もしない
        if cited <= 19:
            return 0

        # disruption_indexが0より大きい場合にのみスコアを加算
        if di > 0:

            # cited_by_countに応じて乗数を決定（200以上もカバー）
            if  cited > 2000: 
                multiplier = 4.0
            elif  cited > 1000: 
                multiplier = 3.8
            elif  cited > 750: 
                multiplier = 3.6
            elif  cited > 500: 
                multiplier = 3.4
            elif  cited > 400: 
                multiplier = 3.2
            elif cited > 300:
                multiplier = 3.0
            elif cited > 200:
                multiplier = 2.8
            elif cited > 150:
                multiplier = 1.6
            elif cited > 100:
                multiplier = 1.4
            elif cited > 50:
                multiplier = 1.2
            else:  # 20 < cited_by_count <= 50
                multiplier = 1.0

            # スコアに加算
            score += di * multiplier

        return score
    
    def cal_disruption_index(focal_paper_id, referenced_works_list, cited_works_info_list):
        try:
            # Convert referenced_works_list to a set for faster lookups
            referenced_works_set = set(referenced_works_list)
            
            # Initialize counts for N_f, N_b, and N_r
            N_f = 0  # Citing papers that only cite the focal paper
            N_b = 0  # Citing papers that cite both the focal paper and its references
            N_r = 0  # Citing papers that cite only the references of the focal paper but not the focal paper itself

            # Loop through cited_works_info_list to count N_f, N_b, and N_r
            for citing_paper_id, citation_list in cited_works_info_list:
                # Check if the citing paper cites the focal paper
                cites_focal = focal_paper_id in citation_list
                # Check if the citing paper cites any of the references in the focal paper
                cites_references = any(citation_id in referenced_works_set for citation_id in citation_list)

                if cites_focal and not cites_references:
                    # Only cites the focal paper
                    N_f += 1
                elif cites_focal and cites_references:
                    # Cites both the focal paper and its references
                    N_b += 1
                elif not cites_focal and cites_references:
                    # Only cites the references, not the focal paper
                    N_r += 1

            # Calculate the Disruption Index using the formula
            disruption_index = (N_f - N_b) / (N_f + N_b + N_r) if (N_f + N_b + N_r) != 0 else 0

            return disruption_index
        
        except:
            return -300

if __name__ == "__main__":
    article_link = "https://openalex.org/W2041780387"
    link = "https://api.openalex.org/works/W2041780387"
    
    response = requests.get(link)
    result = response.json()
    print(result)
    # result_dict = OpenAlexResultParser.works_dict_list_from_works_results(result)
    
    # params = {
    # "filter":f"cites:{article_link}", 
    # "per_page": 200    
    # }
    
    # endpoint_url="https://api.openalex.org/works"
    # fetcher = OpenAlexPagenationDataFetcher(endpoint_url,params,article_link,max_workers = 10,only_japanese=False)
    # Calculater.count_citations_from_other_field()
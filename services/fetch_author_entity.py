import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from utils.common_method import get_type_counts,extract_id_from_url
import requests
from collections import Counter

#https://api.openalex.org/authors?filter=id:A5100705073|A5106315809
class FetchAuthorEntity:
    
    def __init__(self,author_id,use_API_key=False):
        self.use_API_key = use_API_key
        self.author_id = extract_id_from_url(author_id)
        self.data = self.fetch_author_json(self.author_id) 
        print(f"{self.author_id}の取得")
        
    def fetch_author_json(self,author_id):
        if  self.use_API_key:
            API_KEY = os.getenv('API_KEY') 
            if not API_KEY:
                raise ValueError("API_KEYが環境変数に設定されていません。")
            url = f"https://api.openalex.org/authors/{author_id}?api_key={API_KEY}&mailto=t.ichikawa.bnv@gmail.com"
        else:
            url = f"https://api.openalex.org/authors/{author_id}"
        retrial_num=1 #全てのリトライをカウント
        server_retrial=1 #予期せぬエラーのみカウント
        while True:
            try:
                response = requests.get(url,timeout=7)
                if response.status_code == 200:
                    # 全著者情報をJSON形式で取得
                    data = response.json()
                    return data
                else:
                    if retrial_num>30:
                        print(author_id,"の情報をauthorエンティティから収集できませんでした。")
                        return {}
                    print(author_id,"リクエストやり直し。retrial_num:",retrial_num)
                    if retrial_num<7:
                        time.sleep(retrial_num)
                    else:
                        time.sleep(2)
                    
            except requests.exceptions.Timeout:
                if retrial_num>8:
                    print(author_id,"の情報をauthorエンティティから収集できませんでした。")
                    return {}
                print("リクエストがタイムアウトしました。再試行します。retrial_num:",retrial_num)
                time.sleep(retrial_num)
            except:
                if server_retrial>8:
                    time.sleep(15)
                    return {}
                else:
                    print("予期せぬエラー（ネットワーク接続も含む）10秒後に再接続してみます。server_retrial:",server_retrial)
                    server_retrial+=1
                    time.sleep(10)
            retrial_num+=1
    
    def extract_researcher_info(self):
        if not self.data:
            return {}
        
        return {
            "id": self.data.get("id", "N/A"),
            "display_name": self.data.get("display_name", "N/A"),
            "display_name_alternatives": self.data.get("display_name_alternatives", []),
            "ORCID": self.data.get("orcid", "N/A"),
            "Works Count": self.data.get("works_count", "N/A"),
            "cited_by_count": self.data.get("cited_by_count", "N/A"),
            "2yr Mean Citedness": self.data.get("summary_stats", {}).get("2yr_mean_citedness", "N/A"),
            "H-Index": self.data.get("summary_stats", {}).get("h_index", "N/A"),
            "I10-Index": self.data.get("summary_stats", {}).get("i10_index", "N/A"),
            "Affiliations": [
                {
                    "Institution ID": affiliation.get("institution", {}).get("id", "N/A"),
                    "Institution Name": affiliation.get("institution", {}).get("display_name", "N/A"),
                    "Country Code": affiliation.get("institution", {}).get("country_code", "N/A"),
                    "type": affiliation.get("institution", {}).get("type", "N/A"),
                    "Years": affiliation.get("years", [])
                }
                for affiliation in self.data.get("affiliations", [])
            ],
            "Last Known Institutions": [
                {
                    "Institution ID": inst.get("id", "N/A"),
                    "Institution Name": inst.get("display_name", "N/A"),
                    "Country Code": inst.get("country_code", "N/A")
                }
                for inst in self.data.get("last_known_institutions", [])
            ],
            "topics": [
                {
                    "Topic ID": topic.get("id", "N/A"),
                    "Display Name": topic.get("display_name", "N/A"),
                    "Count": topic.get("count", "N/A"),
                    "Subfield": topic.get("subfield", {}).get("display_name", "N/A"),
                    "Field": topic.get("field", {}).get("display_name", "N/A"),
                    "Domain": topic.get("domain", {}).get("display_name", "N/A")
                }
                for topic in self.data.get("topics", [])
            ],
            "counts_by_year": self.data.get("counts_by_year", [])
        }

    def calculate_type_counts(self):
        researcher_info = self.extract_researcher_info()
        affiliations = researcher_info.get("Affiliations", [])
        if not affiliations:
            return {}
        type_list = [affiliation.get("type", "N/A") for affiliation in affiliations]
        type_counts = Counter(type_list)
        return dict(type_counts)

    def calculate_country_counts(self):
        researcher_info = self.extract_researcher_info()
        affiliations = researcher_info.get("Affiliations", [])
        if not affiliations:
            return {}
        country_list = [affiliation.get("Country Code", "N/A") for affiliation in affiliations]
        country_counts = Counter(country_list)
        return dict(country_counts)

    def calculate_growth_rates(self):
        researcher_info = self.extract_researcher_info()
        data = researcher_info.get("counts_by_year", [])
        growth_rates = []
        for i in range(min(3, len(data) - 1)):
            current = data[i]
            prev = data[i + 1]
            current_cited = current.get("cited_by_count", 0)
            prev_cited = prev.get("cited_by_count", 0)
            if prev_cited != 0:
                growth_rate = round((current_cited - prev_cited) / prev_cited * 100, 2)
            else:
                growth_rate = ""
            growth_rates.append({
                "year": current.get("year", "N/A"),
                "growth_rate": growth_rate
            })
        return growth_rates

    def get_author_id(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("id", "N/A")

    def get_display_name(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("display_name", "N/A")

    def get_alternative_names(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("display_name_alternatives", [])

    def get_orcid(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("ORCID", "N/A")

    def get_works_count(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("Works Count", "N/A")

    def get_cited_by_count(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("cited_by_count", "N/A")

    def get_two_year_mean_citedness(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("2yr Mean Citedness", "N/A")

    def get_h_index(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("H-Index", "N/A")

    def get_i10_index(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("I10-Index", "N/A")

    def get_affiliations(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("Affiliations", [])

    def get_affiliations_for_display(self):
        affiliations = self.get_affiliations()
        return "\n".join(
            f"{affiliation['Institution Name']}: {', '.join(map(str, affiliation['Years']))}"
            for affiliation in affiliations
        )

    def get_last_institution_names(self):
        researcher_info = self.extract_researcher_info()
        return [
            inst.get("Institution Name", "N/A") 
            for inst in researcher_info.get("Last Known Institutions", [])
        ]

    def get_country_codes(self):
        researcher_info = self.extract_researcher_info()
        return [
            inst.get("Country Code", "N/A") 
            for inst in researcher_info.get("Last Known Institutions", [])
        ]

    def get_type_counts(self):
        return self.calculate_type_counts()

    def get_country_counts(self):
        return self.calculate_country_counts()

    def get_growth_rates(self):
        return self.calculate_growth_rates()

    def get_career_years(self):
        return self.calculate_career_years()

    def get_topics(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("topics", [])

    def get_counts_by_year(self):
        researcher_info = self.extract_researcher_info()
        return researcher_info.get("counts_by_year", [])
    
    def get_top3_topic_ids(self) -> list:
        """
        extract_researcher_info() で取得した topics の中から上位3件の "Topic ID" をリストで返します。
        """
        researcher_info = self.extract_researcher_info()
        topics = researcher_info.get("topics", [])
        top3 = topics[:3]  # 先頭3件を取得
        return [extract_id_from_url(topic.get("Topic ID", "N/A")) for topic in top3]
        
    def get_top3_topics(self) -> list:
        """
        self.data 内の "topics" リストから、"count" キーに基づいて降順にソートし、
        上位3件のトピックのデータ（辞書）をそのままリストで返します。
        """
        topics = self.data.get("topics", [])
        if not topics:
            return []
        # "count" キーの値で降順にソート
        sorted_topics = sorted(topics, key=lambda t: t.get("count", 0), reverse=True)
        # 上位3件のトピックの辞書データを返す
        return sorted_topics[:3]
    


if __name__ == "__main__":
    # 使用例
    start_time = time.time()  # 実行開始時刻を記録
    author_id = "https://openalex.org/A5038138665"
    author_entity = FetchAuthorEntity(author_id,use_API_key=False)
    print("H-Index:", author_entity.get_top3_topics())

    end_time = time.time()  # 実行終了時刻を記録
    elapsed_time = end_time - start_time  # 経過時間を計算
    #print(f"プログラムの実行時間: {elapsed_time:.2f} 秒")
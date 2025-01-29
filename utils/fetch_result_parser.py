import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from data_class.researcher_data import AuthorWorkData
from utils.common_method import extract_id_from_url
class OpenAlexResultParser:
    
     #all_resultsから、authorIDなどの著者情報だけを抽出する関数を作る。
    
    
    def works_dict_list_from_works_results(all_results):
        try:
            article_dict_template = {
                "ID":"", 
                "Title":"", 
                "Publication Year":0, 
                "Publication Date":"",
                "Landing Page URL":"",
                "Authors":"",
                "Authors_info":[],
                "Primary Topic":{},
                "Topics":[], 
                #"topics_name_id":"",
                #"subfield_name_id":"",
                #"domain_name_id":"",
                "Keywords":[],
                "referenced_works_count":"",
                "Cited By Count":0,
                "Citation Normalized Percentile":"",
                "Cited By Percentile Year (Min)":"",
                "Cited By Percentile Year (Max)":"",
                "FWCI":"",
                "Corresponding Authors":"",
                "referenced_works":"",
                "grants":"",
                "source":"",
                "cited_by_api_url":"",
                "disruption_index":"",
                "cited_by_other_field":{},
                "impact_index":0.0,
            }
            article_dict_list = []
            
            for work in all_results:
                article_dict = article_dict_template.copy()
                # "authorships" 内の各研究者情報の取得
                authors_info = work.get("authorships", [])
                article_dict["Authors_info"] = authors_info
            
                
                authors_info = ", ".join(
                [
                    f"{author.get('author', {}).get('display_name', 'N/A')} ({author.get('author_position', 'N/A')}, ID: {author.get('author', {}).get('id', 'N/A')})"
                    for author in work.get("authorships", [])
                ]
                )
                
                # "is_corresponding" が True の著者のリストを取得し、名前とIDを取得
                corresponding_authors = [
                    {
                        "name": author.get("author", {}).get("display_name", "N/A"),
                        "id": author.get("author", {}).get("id", "N/A")
                    }
                    for author in work.get("authorships", [])
                    if author.get("is_corresponding", False) or "last" in author.get("author_position", "N/A")
                ]
                
                # 各フィールドを取得し、リストに格納
                # 各フィールドを article_dict のコピーに格納
                article_dict["ID"] = work.get("id", "N/A")
                article_dict["Title"] = work.get("title", "N/A")
                article_dict["Publication Year"] = work.get("publication_year", 0)
                article_dict["Publication Date"] = work.get("publication_date", "N/A")
                article_dict["Landing Page URL"] = work.get("primary_location", {}).get("landing_page_url", "N/A") if work.get("primary_location") else "N/A"
                article_dict["Authors"] = authors_info
                article_dict["Primary Topic"] = work.get("primary_topic", {})#.get("display_name", {}) if work.get("primary_topic") else {}
                article_dict["Topics"] = work.get("topics", [])# トピック情報を配列で取得
                article_dict["Keywords"] = work.get("keywords", [])
                article_dict["referenced_works_count"] = work.get("referenced_works_count", "N/A")
                article_dict["Cited By Count"] = work.get("cited_by_count", 0)
                article_dict["Citation Normalized Percentile"] = (
                    work.get("citation_normalized_percentile", {}).get("value", "N/A")
                    if work.get("citation_normalized_percentile") else "N/A"
                )
                article_dict["Cited By Percentile Year (Min)"] = work.get("cited_by_percentile_year", {}).get("min", "N/A") if work.get("cited_by_percentile_year") else "N/A"
                article_dict["Cited By Percentile Year (Max)"] = work.get("cited_by_percentile_year", {}).get("max", "N/A") if work.get("cited_by_percentile_year") else "N/A"
                article_dict["FWCI"] = work.get("fwci", "N/A")  # FWCI
                article_dict["Corresponding Authors"] = corresponding_authors  # "is_corresponding" 著者のリスト
                article_dict["referenced_works"] = work.get("referenced_works", [])
                article_dict["cited_by_api_url"] = work.get("cited_by_api_url", "N/A")
                if work.get("primary_location"):
                    article_dict["source"] = work.get("primary_location", {}).get('source',{}).get("id","N/A") if work.get("primary_location", {}).get('source',{}) else "N/A"
                article_dict["grants"] = work.get("grants", [])
                article_dict_list.append(article_dict)
                
            return article_dict_template,article_dict_list
        
        except Exception as e:
            print(e)
            return article_dict_template,article_dict_list
    
    
    def author_dict_list_from_article_dict_list(article_dict_list,only_single_author_id=""):
        author_dict_list = []
        
        for index,article in enumerate(article_dict_list,start=1):
            for author_info in article["Authors_info"]:
                if only_single_author_id and not extract_id_from_url(only_single_author_id)==extract_id_from_url(author_info.get("author", {}).get("id", "N/A")):
                    continue
                # 著者情報と記事に関するすべてのデータを格納
                author_data = {
                    "Author ID": author_info.get("author", {}).get("id", "N/A"),
                    "Author Name": author_info.get("author", {}).get("display_name", "N/A"),
                    "Author Position": author_info.get("author_position", "N/A"),
                    "Is Corresponding": author_info.get("is_corresponding", False),
                    "Affiliation": ", ".join([inst.get("display_name", "N/A") for inst in author_info.get("institutions", [])]),
                    "Institutions": author_info.get("institutions", []),
                    "Country Codes": ", ".join([
                        inst.get("country_code", "N/A") if inst.get("country_code", "N/A") is not None else "N/A"
                        for inst in author_info.get("institutions", [])
                    ]),
                    # 記事情報をすべて含める
                    "Authors_info": article.get("Authors_info", []),
                    "Article ID": article.get("ID", "N/A"),
                    "Title": article.get("Title", "N/A"),
                    "Publication Year": article.get("Publication Year", 0),
                    "Publication Date": article.get("Publication Date", "N/A"),
                    "Landing Page URL": article.get("Landing Page URL", "N/A"),
                    "Authors": article.get("Authors", "N/A"),
                    "Primary Topic": article.get("Primary Topic", {}),
                    "Topics": article.get("Topics", "N/A"),
                    "Keywords": article.get("Keywords",[]),
                    "Referenced Works Count": article.get("referenced_works_count", "N/A"),
                    "Cited By Count": article.get("Cited By Count", 0),
                    "Citation Normalized Percentile": article.get("Citation Normalized Percentile", "N/A"),
                    "Cited By Percentile Year (Min)": article.get("Cited By Percentile Year (Min)", "N/A"),
                    "Cited By Percentile Year (Max)": article.get("Cited By Percentile Year (Max)", "N/A"),
                    "FWCI": article.get("FWCI", "N/A"),
                    "Corresponding Authors": article.get("Corresponding Authors", []),
                    "Referenced Works": article.get("referenced_works", []),
                    #"Works Cited By": article.get("works_cited_by", []),
                    "Source" :article.get("source", "N/A"),
                    "Grants": article.get("grants", []),
                    "Cited By API URL": article.get("cited_by_api_url", "N/A"),
                    "Disruption Index": article.get("disruption_index", "N/A"),
                    "impact_index": article.get("impact_index", 0.0),
                    "cited_by_other_field":article.get("cited_by_other_field",{}),
                    "ranking":f"{index}",
                    "total_count": f"{len(article_dict_list)}"
                }
                author_dict_list.append(author_data)

        return author_dict_list
    
from typing import List, Dict, Any
def author_dict_list_to_author_work_data_list(author_dict_list: List[Dict[str, Any]]) -> List[AuthorWorkData]:
    author_work_data_list = []
    for author_dict in author_dict_list:
        work_data = author_dict_to_author_work_data(author_dict)
        author_work_data_list.append(work_data)
    return author_work_data_list
  
def author_dict_to_author_work_data(author_dict):
    work_data = AuthorWorkData(
        paper_id=author_dict.get("Article ID", ""),
        paper_title = author_dict.get("Title",""),
        author_id=author_dict.get("Author ID", ""),
        name=author_dict.get("Author Name", ""),
        affiliation=author_dict.get("Affiliation", ""),
        institutions=author_dict.get("Institutions", []),
        country_codes=author_dict.get("Country Codes", ""),
        corresponding_author=author_dict.get("Is Corresponding", False),
        position=author_dict.get("Author Position", ""),
        corresponding_author_name=[
            auth.get('name', '') for auth in author_dict.get("Corresponding Authors", [])
        ] if author_dict.get("Corresponding Authors") else [],
        citations=int(author_dict.get("Referenced Works Count", 0)) if author_dict.get("Referenced Works Count") else 0,
        total_citations=int(author_dict.get("Cited By Count", 0)) if author_dict.get("Cited By Count") else 0,
        cited_by_other_field=author_dict.get("cited_by_other_field",{}),
        d_index=float(author_dict.get("Disruption Index", -200)) if author_dict.get("Disruption Index") else -200.0,
        impact_index=float(author_dict.get("impact_index", -200.0)) if author_dict.get("impact_index") else -200.0,
        primary_topic=author_dict.get("Primary Topic", ""),
        topics=author_dict.get("Topics", []),
        publication_year=int(author_dict.get("Publication Year", 0)) if author_dict.get("Publication Year") else 0,
        publication_date=author_dict.get("Publication Date", ""),
        landing_page_url=author_dict.get("Landing Page URL", ""),
        authors=author_dict.get("Authors", ""),
        authors_info=author_dict.get("Authors_info",[]),
        keywords=author_dict.get("Keywords", []),
        grants=author_dict.get("Grants", []),
        source_id=author_dict.get("Source","")
    )
    return work_data

  
            
if __name__ == "__main__":
    import requests
    
    response = requests.get("https://api.openalex.org/works/W3134325890")
    
    all_results=[response.json()]
    article_dict_template,article_dict_list = OpenAlexResultParser.works_dict_list_from_works_results(all_results)
    author_dict_list = OpenAlexResultParser.author_dict_list_from_article_dict_list(article_dict_list)
    print(author_dict_list[4]["Source"])
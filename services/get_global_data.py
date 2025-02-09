import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from api.google_custom_search import JGlobalCustomSearch
from api.jglobal_selenium_search import JGlobalSeleniumSearch
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse, urlunparse

class GetJGlobalData:
    def __init__(self,results_list,method="search"):
        self.results_list = results_list
        self.method=method
        if self.method =="search":
            self.search_by_google_custom_search()
        else:
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
                            result["j_global_link"]  = self.remove_en_from_jglobal_url(jglobal_search.get_jglobal_researcher_link_from_first_result())
                        break
            return
        
        except Exception as e:
            raise Exception(f"search_jglobal_linkの中でエラー:{e}")
        

    def search_in_research_map(self):
        # Selenium ドライバーのセットアップ（ヘッドレスモード）
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(options=options)
        
        base_url = "https://researchmap.jp"
        for result in self.results_list:
            
            # result["name"]（検索する名前）を取得し、前後の空白を除去
            name = result.get("name", "").strip()
            if not name:
                result["j_global_link"] = ""
                continue

            # 名前中のスペースを "+" に置換して、ダブルクォーテーションで囲む
            # 例："Yutaka+Matsuo"
            query = f'"{name.replace(" ", "+")}"'
            search_url = f"{base_url}/researchers?q={query}&lang=en"
            print(f"検索URL: {search_url}")
            
            try:# 検索結果ページにアクセス後、ページ全体の読み込みが完了するまで待機
                driver.get(search_url)
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
            except TimeoutException:
                print("タイムアウトにより検索結果の ul 要素が取得できませんでした。")
                result["j_global_link"] = ""
                continue
            except Exception as e:
                print(f"検索ページ読み込みエラー: {e}")
                result["j_global_link"] = ""
                continue

            # ページソースを BeautifulSoup でパース
            soup = BeautifulSoup(driver.page_source, "html.parser")
            ul_element = soup.find("ul", class_="list-inline rm-cv-card")
            if not ul_element:
                print("検索結果の ul 要素が見つかりませんでした。")
                result["j_global_link"] = ""
                continue

            li_elements = ul_element.find_all("li")
            matching_link = ""
            latest_affiliations = result.get("latest_affiliation", [])
            
            # 各研究者カードをチェック
            for li in li_elements:
                affiliation_div = li.find("div", class_="rm-cv-card-name-affiliation")
                if not affiliation_div:
                    continue
                aff_text = affiliation_div.get_text(strip=True)
                # 最新所属リスト内のいずれかと完全一致するかチェック
                for aff in latest_affiliations:
                    if aff.strip() == aff_text:
                        # 一致するカードが見つかったら、リンクを取得
                        name_div = li.find("div", class_="rm-cv-card-name")
                        if not name_div:
                            continue
                        a_tag = name_div.find("a")
                        if not a_tag:
                            continue
                        researcher_link = a_tag.get("href")
                        if researcher_link and researcher_link.startswith("/"):
                            researcher_link = base_url + researcher_link
                        print(f"一致する所属の研究者カードリンク: {researcher_link}")
                        
                        # 詳細ページを Selenium で取得
                        try:
                            driver.get(researcher_link)
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "div.panel.panel-default.rm-cv-panel"))
                            )
                        except Exception as e:
                            print(f"詳細ページ読み込みエラー: {e}")
                            continue
                        
                        detail_soup = BeautifulSoup(driver.page_source, "html.parser")
                        panel_div = detail_soup.find("div", class_="panel panel-default rm-cv-panel")
                        if not panel_div:
                            print("詳細ページ内の対象パネルが見つかりませんでした。")
                            continue
                        
                        a_tags = panel_div.find_all("a")
                        for a in a_tags:
                            href = a.get("href", "")
                            if "https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=" in href:
                                matching_link = href
                                print(f"見つかった jGlobal リンク: {matching_link}")
                                break
                        if matching_link:
                            break  # 内側の for-loop終了
                if matching_link:
                    break  # li ループ終了
            
            # 一致するリンクが見つかったかどうかを結果に設定
            result["j_global_link"] = self.remove_en_from_jglobal_url(matching_link) if matching_link else ""
        
        # ドライバー終了
        driver.quit()
        
    def selenium_search_for_patent(self):
        print("selenium_search_for_patent関数")
       
        try:
            data_set_list = []
            for result in self.results_list: 
                data_set ={
                    "author_id":result["author_id"],
                    "j_global_link":result["j_global_link"]
                }
                data_set_list.append(data_set)
            
            print(len(data_set_list))
            jglobal_search = JGlobalSeleniumSearch(data_set_list,max_work=1)
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
        
    
    def remove_en_from_jglobal_url(self,url):
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
    
    get_jglobal = GetJGlobalData(sample_results)
    get_jglobal.search_in_research_map()
    
    # 結果の確認
    for res in sample_results:
        print("名前:", res.get("name"))
        print("j_global_link:", res.get("j_global_link"))
        print("-----")
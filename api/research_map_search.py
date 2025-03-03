import re
import time
import threading
from queue import Queue
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urlunparse

class JGlobalResearchMapSearch:
    def __init__(self, data_set_list, max_work=5):
        """
        コンストラクタ
        
        :param data_set_list: 検索対象のデータセット（各辞書に "name" や "latest_affiliation" が含まれる）
        :param max_work: 並列に実行するスレッド数（ChromeDriver インスタンス数）
        """
        print("JGlobalResearchMapSearchのコンストラクタ")
        self.data_set_list = data_set_list
        self.max_work = max_work
        
        # Chrome の基本オプション（ヘッドレスモード・ウィンドウサイズなど）
        self.base_options = Options()
        self.base_options.add_argument("--headless")
        self.base_options.add_argument("--disable-gpu")
        self.base_options.add_argument("--window-size=1920,1080")
    
    @staticmethod
    def remove_en_from_jglobal_url(url):
        """
        URL のパス部分に '/en/' が含まれていれば、最初の1箇所を '/' に置換して返す
        
        例:
        https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=201101096882374533
        → https://jglobal.jst.go.jp/detail?JGLOBAL_ID=201101096882374533
        """
        parsed = urlparse(url)
        if parsed.path.startswith('/en/'):
            new_path = parsed.path.replace('/en/', '/', 1)
        else:
            new_path = parsed.path
        new_parsed = parsed._replace(path=new_path)
        return urlunparse(new_parsed)
    
    def get_research_map_links(self):
        """
        並列処理で各データセットに対して Research Map 上の jGlobal リンクを取得する。
        結果は各辞書の "j_global_link" キーに格納される。
        """
        base_url = "https://researchmap.jp"
        
        # タスク用のキューに各データセットを投入
        task_queue = Queue()
        for result in self.data_set_list:
            task_queue.put(result)
        
        # webdriver_manager を使って ChromeDriver のサービスを作成
        service = Service(ChromeDriverManager().install())
        
        # 各スレッドで使用するため、各自専用の ChromeDriver インスタンスを作成
        drivers = []
        for _ in range(self.max_work):
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            driver = webdriver.Chrome(service=service, options=options)
            drivers.append(driver)
        
        def worker(driver):
            while not task_queue.empty():
                try:
                    result = task_queue.get_nowait()
                except Exception:
                    break

                # 検索対象の名前を取得
                name = result.get("name", "").strip()
                if not name:
                    result["j_global_link"] = ""
                    task_queue.task_done()
                    continue

                # 名前中のスペースを "+" に置換し、ダブルクォーテーションで囲んだ検索クエリを生成
                query = f'"{name.replace(" ", "+")}"'
                search_url = f"{base_url}/researchers?q={query}&lang=en"
                print(f"検索URL: {search_url}")
                
                # 検索結果ページにアクセス
                try:
                    driver.get(search_url)
                    WebDriverWait(driver, 10).until(
                        lambda d: d.execute_script("return document.readyState") == "complete"
                    )
                except TimeoutException:
                    print("タイムアウトにより検索結果の ul 要素が取得できませんでした。")
                    result["j_global_link"] = ""
                    task_queue.task_done()
                    continue
                
                except Exception as e:
                    print(f"検索ページ読み込みエラー: {e}")
                    result["j_global_link"] = ""
                    task_queue.task_done()
                    continue

                # 検索結果ページの解析
                soup = BeautifulSoup(driver.page_source, "html.parser")
                ul_element = soup.find("ul", class_="list-inline rm-cv-card")
                if not ul_element:
                    print("検索結果の ul 要素が見つかりませんでした。")
                    result["j_global_link"] = ""
                    task_queue.task_done()
                    continue

                li_elements = ul_element.find_all("li")
                matching_link = ""
                latest_affiliations = result.get("latest_affiliation", [])
                
                # 各研究者カードをチェックして、所属が一致するかを確認
                for li in li_elements:
                    affiliation_div = li.find("div", class_="rm-cv-card-name-affiliation")
                    if not affiliation_div:
                        continue
                    aff_text = affiliation_div.get_text(strip=True)
                    for aff in latest_affiliations:
                        if aff.strip() == aff_text:
                            # 一致するカードが見つかったので、リンクを取得
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
                            
                            # 詳細ページにアクセスして、jGlobal リンクを取得
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
                                break
                    if matching_link:
                        break
                
                # 結果のセット（/en/ 部分は置換）
                result["j_global_link"] = self.remove_en_from_jglobal_url(matching_link) if matching_link else ""
                task_queue.task_done()

        # 各ドライバーごとにワーカースレッドを作成
        threads = []
        for driver in drivers:
            t = threading.Thread(target=worker, args=(driver,))
            t.start()
            threads.append(t)
        
        # 全てのタスクが完了するまで待機
        task_queue.join()
        for t in threads:
            t.join()
        
        # 使用した各ドライバーを終了
        for driver in drivers:
            driver.quit()
        
        return self.data_set_list

if __name__ == "__main__":
    # サンプル利用例
    sample_results = [
        {
            "author_id": "A1",
            "name": "Yutaka Matsuo",
            "latest_affiliation": ["The University of Tokyo", "Dokkyo Medical University"],
            "j_global_link": ""
        }
    ]
    
    # 並列処理数（max_work）を 1 に設定して実行
    jglobal_rm_search = JGlobalResearchMapSearch(data_set_list=sample_results, max_work=1)
    jglobal_rm_search.get_research_map_links()
    
    # 結果の確認
    for res in sample_results:
        print("名前:", res.get("name"))
        print("j_global_link:", res.get("j_global_link"))
        print("-----")
        
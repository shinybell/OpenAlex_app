import re
import time
import threading
from queue import Queue

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

class JGlobalSeleniumSearch:
    def __init__(self, data_set_list, max_work=5):
        print("JGlobalSeleniumSearchのコンストラクタ")
        """
        コンストラクターでデータセットリストと同時起動数(max_work)を受け取る。
        セレニウムのオプションもここで設定しておく。
        """
        self.data_set_list = data_set_list
        self.max_work = max_work

        # Chromeをヘッドレスモードで起動するためのオプション設定
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # ヘッドレスモード
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--window-size=1920,1080")
        
    def get_patents_counts(self):
        print("get_patents_counts関数")
        """
        各データセットに含まれるj_global_linkに対して、"&e=REL0103EST"を付加したURLを
        Seleniumでアクセスし、特許件数を抽出してdata_set["patents_count"]に格納する。
        同時に起動するセレニウムのインスタンス数はself.max_workとなる。
        """
        # Seleniumドライバーのインスタンスをmax_work件分作成（使い回し）
        drivers = []
        # ChromeDriverManagerでサービスを作成（同一サービスを複数ドライバーで共有可能）
        service = Service(ChromeDriverManager().install())
        for _ in range(self.max_work):
            driver = webdriver.Chrome(service=service, options=self.chrome_options)
            drivers.append(driver)
        
        # タスクキューに、各データセットを投入する
        task_queue = Queue()
        for data_set in self.data_set_list:
            task_queue.put(data_set)
        
        def worker(driver):
            """
            各スレッドで実行するワーカー関数。
            driverを使い回して、タスクキューからデータセットを取り出し、リンク先のページから
            特許件数を抽出してdata_set["patents_count"]に格納する。
            """
            while not task_queue.empty():
                
                data_set = task_queue.get_nowait()
                link = data_set.get("j_global_link", "")
                if not link:
                    data_set["patents_count"] = -200
                    task_queue.task_done()
                    continue

                # リンクに指定パラメーターを付加
                final_link = link + "&e=REL0103EST"
                try:
                    # 既存のdriverを使い、リンク先のページにアクセス（driver.get()でリンクを入れ替える）
                    driver.get(final_link)
                    time.sleep(3)
                    # ページが完全にロードされるまで待機
                    WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
                    time.sleep(1.5)  # ページ内要素のレンダリング待ち
                    # 指定のCSSセレクターが現れるまで待機
                    wait = WebDriverWait(driver, 15)
                    detail_div = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.detail_list_title"))
                    )
                    text = detail_div.text.strip()
                    # 正規表現で「(数字件)」の数字部分を抽出
                    match = re.search(r'\((\d+)件\)', text)
                    if match:
                        count = int(match.group(1))
                    else:
                        count = -200
                except Exception as e:
                    # エラー発生時はエラーメッセージを出力し、特許件数に-1を設定
                    print(f"Error processing {final_link}: {e}")
                    count = -200
                
                # 抽出した件数をデータセットに格納
                data_set["patents_count"] = count
                task_queue.task_done()
        
        # 各ドライバーに対してワーカースレッドを作成してタスクを並列処理
        threads = []
        for driver in drivers:
            t = threading.Thread(target=worker, args=(driver,))
            t.start()
            threads.append(t)
        
        # 全てのタスクが完了するのを待機
        task_queue.join()
        for t in threads:
            t.join()
        
        # 全てのドライバーを終了
        for driver in drivers:
            driver.quit()

# サンプル利用例（実際の利用時は、data_set_listは各データセットのリストとなる）
if __name__ == "__main__":
    # サンプルデータセット：各辞書は、author_idとj_global_linkを含む
    sample_data_set_list = [
        {"author_id": "A1", "j_global_link": "https://jglobal.jst.go.jp/detail?JGLOBAL_ID=202301016710211380"},
        {"author_id": "A2", "j_global_link": "https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=202301006773797940"},
        # ... 他のデータセット
    ]
    jglobal_search = JGlobalSeleniumSearch(data_set_list=sample_data_set_list, max_work=1)
    jglobal_search.get_patents_counts()
    
    # 結果確認
    for data in sample_data_set_list:
        print(data)
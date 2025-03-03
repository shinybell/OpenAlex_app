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
        self.data_set_list = data_set_list
        self.max_work = max_work

    def get_patents_counts(self):
        print("get_patents_counts関数")
        drivers = []
        # webdriver_manager を使って ChromeDriver のサービスを作成
        service = Service(ChromeDriverManager().install())
        # max_work 件数分の ChromeDriver インスタンスを作成
        for _ in range(self.max_work):
            # シンプルなオプションを使用（ユーザーディレクトリ指定は不要）
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            #options.binary_location = "/opt/homebrew/bin/chromium"
            driver = webdriver.Chrome(service=service, options=options)
            drivers.append(driver)

        # タスクキューに各データセットを投入
        task_queue = Queue()
        for data_set in self.data_set_list:
            task_queue.put(data_set)

        def worker(driver):
            """
            各スレッドで実行するワーカー関数。
            driver を使って各 j_global_link ページにアクセスし、特許件数を抽出する。
            """
            while not task_queue.empty():
                try:
                    data_set = task_queue.get_nowait()
                except Exception:
                    break

                link = data_set.get("j_global_link", "")
                if not link:
                    data_set["patents_count"] = -200
                    task_queue.task_done()
                    continue

                final_link = link + "&e=REL0103EST"
                try:
                    driver.get(final_link)
                    # ページが完全に読み込まれるまで待機
                    WebDriverWait(driver, 30).until(lambda d: d.execute_script("return document.readyState") == "complete")
                    time.sleep(1.5)  # ページ内のレンダリング待ち
                    # 指定の要素が現れるまで待機
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
                    print(f"Error processing {final_link}: {e}")
                    count = -200

                data_set["patents_count"] = count
                task_queue.task_done()

        # 各ドライバーに対してワーカースレッドを作成
        threads = []
        for driver in drivers:
            t = threading.Thread(target=worker, args=(driver,))
            t.start()
            threads.append(t)

        # タスク完了を待機
        task_queue.join()
        for t in threads:
            t.join()

        # 全てのドライバーを終了
        for driver in drivers:
            driver.quit()


if __name__ == "__main__":
    # サンプルデータセット
    sample_data_set_list = [
        {"author_id": "A1", "j_global_link": "https://jglobal.jst.go.jp/detail?JGLOBAL_ID=202301016710211380"},
        {"author_id": "A2", "j_global_link": "https://jglobal.jst.go.jp/en/detail?JGLOBAL_ID=202301006773797940"},
    ]
    jglobal_search = JGlobalSeleniumSearch(data_set_list=sample_data_set_list, max_work=2)
    jglobal_search.get_patents_counts()

    # 結果確認
    for data in sample_data_set_list:
        print(data)
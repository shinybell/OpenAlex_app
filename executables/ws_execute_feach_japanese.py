import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from endpoint.connection_manager import ConnectionManager
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
import time
secret = SecretManager()

#条件を指定して研究者リスト作成する
async def ws_execute(manager: ConnectionManager,topic_ids,primary=True,threshold=15,year_threshold=2015,title_and_abstract_search='',max_works=16,di_calculation=False,output_sheet_name="API動作確認"):
    
    try:
        await manager.broadcast("SpreadsheetManagerの初期化を開始します。")
        sheet_manager = SpreadsheetManager("アプリケーション", output_sheet_name)
        
        await manager.broadcast("並列処理用のパラメータを設定中...")
        person_num = 4
        count_cores = count_logical_cores()
        max_works = count_cores*2
        creater = CreateAuthorIdList(topic_ids=topic_ids,primary=primary,threshold=threshold,year_threshold=year_threshold,title_and_abstract_search=title_and_abstract_search,max_works=max_works)
        
        await manager.broadcast("論文データの取得を開始します。")
        creater.run_get_works()
        await manager.broadcast(f"取得した論文数: {len(creater.all_results)}")
       
        creater.extract_authors(only_japanese=True)
        await manager.broadcast(f"抽出した日本人著者数: {len(creater.authors_id_list)}")
        
        max_workers=max_works//person_num
        
        def process_author(author_id): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(author_id, "の調査")
                author = GatherAuthorData(author_id=author_id,max_workers=max_workers)
                author.run_fetch_works()
                
                if di_calculation:
                    author.di_calculation()
                
                profile_dict = author.gathering_author_data()
                works_data_dict = author.get_top_three_article()
                
                #profile辞書＋top_three_article
                profile_dict.update(works_data_dict)
                
                return profile_dict
            
            except Exception as e: 
                logging.error(f"process_author内でエラー発生 (author_id: {author_id}): {e}", exc_info=True)
                raise  # エラーを再スローして上位で処理
            
        # 並列処理
        results_list = []
        length = 10 # 初期値を0に設定
        with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, author_id): author_id for author_id in creater.authors_id_list}
            for future in as_completed(futures):
                author_id = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    results_list.append(result)
                    #await manager.broadcast(f"著者{author_id}の処理が完了しました。")
                
                    if len(results_list) >= length:  # 次の10人に
                        print(f"著者{length}人の処理が完了しました。")
                        await manager.broadcast(f"著者{length}人の処理が完了しました。")
                        length+=10
                    
                except Exception as e: 
                    # メインスレッドでのエラーハンドリング
                    logging.error(f"処理中にエラーが発生しました。authorID:{author_id}。エラー: {e}")
                    await manager.broadcast(f"著者 {author_id} の処理中にエラーが発生しました: {e}")

        #print("研究者数:",len(results_list))
        rows =[]
        for result in results_list:
            row = [str(value) for value in result.values()]
            rows.append(row)
            
        for row in rows:
            for i,each in enumerate(row):
                if len(each)>=50000:
                    #print("インデクス",i)
                    row[i] = each[:50000]
        
        max_retries = 5
        attempt = 0  
        while attempt < max_retries:
            try:
                sheet_manager.append_rows(rows)
                await manager.broadcast("行の追加に成功しました。") 
                break
            except Exception as e:
                attempt += 1
                await manager.broadcast(f"エラーが発生しました (試行回数: {attempt}/{max_retries}): {e}")
               # print(f"エラーが発生しました (試行回数: {attempt}/{max_retries}): {e}")
                if attempt < max_retries:
                    print(f"再試行します...")
                else:
                    await manager.broadcast(f"最大リトライ回数に達しました。操作を終了します。エラー:{e}")
                    #print("最大リトライ回数に達しました。操作を終了します。")
                    raise ValueError(f"sheet_manager.append_rowsが最大リトライ回数に達しました: {e}")  # ValueError を再スロー
                
        return {"count_authors":len(results_list)}
    
    except ValueError as e:
        print(f"エラー: {e}")
        await manager.broadcast(f"ValueError: {e}")
        return {"error": f"ValueError: {e}"}
    except Exception as e:
        print(f"予期しないエラー: {e}")
        await manager.broadcast(f"ValueError: {e}")
        return {"error": f"予期しないエラー: {e}"}
    

# if __name__ == "__main__":
#     # 開始時間を記録
#     start_time = time.time()
    
#     topic_ids= ["T10966"]
#     ws_execute(topic_ids,primary=True,threshold=15,year_threshold=2015,title_and_abstract_search='',max_works=16)
    
#     # 終了時間を記録
#     end_time = time.time()
#     # 処理時間を計算
#     elapsed_time = end_time - start_time
#     print(f"処理時間: {elapsed_time:.2f} 秒")
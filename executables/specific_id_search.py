import os, sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from scraping.jglobal_selenium_search import JGlobalSeleniumSearch
from utils.outputer import Outputer
from utils.common_method import count_logical_cores
from services.create_author_id_list import CreateAuthorIdList
from services.gather_authors_data import GatherAuthorData
from concurrent.futures import ThreadPoolExecutor, as_completed
from api.spreadsheet_manager import SpreadsheetManager
from config.secret_manager import SecretManager
from utils.async_log_to_sheet import append_log_async
from utils.common_method import extract_id_from_url
from utils.predict_models import extract_keys_from_dict, get_education_value, get_jp_value, rui_predict_model
import asyncio
import time
secret = SecretManager()

#条件を指定して研究者リスト作成する
async def specific_id_execute(data,di_calculation=False,output_sheet_name="API動作確認",use_API_key = False,output_mode=""):
    
    start_time = time.time()  # 実行開始時間を記録
    try:
        await append_log_async(f"") 
        await append_log_async(f"処理を開始します。") 
        
        file_name = os.getenv('FIXED_SPREADSHEET_NAME')
        sheet_manager = SpreadsheetManager(file_name, output_sheet_name)
        sheet_manager.clear_rows_from_second()
        count_cores = count_logical_cores()
        if use_API_key:
            max_works = count_cores*20
        else:
            max_works = count_cores*10
        
 
        person_num = 8 if use_API_key else 4
        max_workers=max_works//person_num
        
        def process_author(item): 
            """
            個々のauthor_idに対して処理を実行する関数
            """
            try:
                print(item['id'], "の調査")
                author = GatherAuthorData(author_id=item['id'], max_workers=max_workers, use_API_key=use_API_key, found_date=item['date'])
                author.run_fetch_works()
                
                if not author.article_dict_list:
                    return {}
                 
                if di_calculation and output_mode!="simple":
                    author.di_calculation()
                
                profile = author.gathering_author_data()
                
    
                profile_dict = profile.to_dict()
                works_data_dict = author.get_top_three_article()
        
                profile_dict.update(works_data_dict)
                raw_keys = [
                    "total_works_citations",
                    "career_years",
                    "coauthor_count",
                    "first_paper_count",
                    "country_affiliation_count",
                    "affiliation_type",
                    "coauthor_type_counter",
                    "last_5_year_h_index"
                ]

                # raw な値だけの
                dict_for_rui_model = extract_keys_from_dict(profile_dict, raw_keys)
                if dict_for_rui_model is None:
                    predict_dict = {
                        "predict_model": -200,
                    }
                    print("extract_keys_from_dictが失敗")
                else:
                     # 各 raw 値を取得し、float 化（辞書型の値は必要に応じて get_jp_value, get_education_value を使用）
                    career_years = float(dict_for_rui_model["career_years"])
                    processed_last_5_year_h_index = float(dict_for_rui_model["last_5_year_h_index"])
                    processed_career_year_adjust_coauthor_count = float(dict_for_rui_model["coauthor_count"]) / career_years
                    processed_career_year_adjust_first_paper_count = float(dict_for_rui_model["first_paper_count"]) / career_years
                    processed_career_year_adjust_JP = get_jp_value(dict_for_rui_model["country_affiliation_count"]) / career_years
                    processed_career_year_adjust_education = get_education_value(dict_for_rui_model["affiliation_type"]) / career_years
                    processed_career_year_adjust_coauthor_education = get_education_value(dict_for_rui_model["coauthor_type_counter"])
                    processed_career_year_adjust_citations = float(dict_for_rui_model["total_works_citations"]) / career_years

                    args = [
                        processed_last_5_year_h_index,
                        processed_career_year_adjust_coauthor_count,
                        processed_career_year_adjust_education,
                        processed_career_year_adjust_coauthor_education,
                        processed_career_year_adjust_JP,
                        processed_career_year_adjust_first_paper_count,
                        processed_career_year_adjust_citations
                    ]
                    predict_dict = {
                        "predict_model": rui_predict_model(*args),
                    }
                    
                profile_dict.update(predict_dict)
                
                return profile_dict
            
            except Exception as e:
                raise Exception(f"process_author内でエラー発生 (author_id: {item['id']}): {e}") # エラーを再スローして上位で処理
            
        # 並列処理
        results_list = []
        length = 5
        with ThreadPoolExecutor(max_workers=person_num) as executor:  # max_workersは並列スレッド数
            futures = {executor.submit(process_author, item): item for item in data}
            for future in as_completed(futures):
                item = futures[future]
                try:
                    result = future.result()  # 処理結果を取得
                    results_list.append(result)
                    
                    if len(results_list) >= length:
                        await append_log_async(f"著者{length}人の処理が完了しました。")  #ログの追加
                        length+=5
                        
                    # イベントループに制御を戻す
                    await asyncio.sleep(0)
                
                except Exception as e: 
                    # メインスレッドでのエラーハンドリング
                    await append_log_async(f"{item['id']} の処理中にエラーが発生しました: {e}") #ログの追加
                    # イベントループに制御を戻す
                    await asyncio.sleep(0)


        #GoogleCustomSearchとSeleniumをつかて、特許件数とJ-GLOBALでのresearcherリンクを取得
        #EC2では動作しないのでコメントアウツ中。必要に応じて追加開発して下さい。
        #if need_J_Global:
            # await append_log_async(f"J-GLOBALからデータを取得します。") #ログの追加
            # GetJGlobalData(results_list,method="selenium")#selenium or search
        
        end_time = time.time()  # 実行終了時間を記録
        elapsed_time = end_time - start_time  # 実行時間を計算
        # 時間、分、秒に変換
        hours = int(elapsed_time // 3600)
        minutes = int((elapsed_time % 3600) // 60)
        seconds = int(elapsed_time % 60)
        
        # フォーマット済みの文字列を作成
        formatted_time = f"{hours}時間{minutes}分{seconds}秒"
        await append_log_async(f"処理が終了しました。処理にかかった時間:{formatted_time}")  # ログの追加
        await append_log_async(f"スプレットシートに追加します。") 
        outputer = Outputer(sheet_manager,results_list)
        await outputer.batch_execute_for_display(output_mode=output_mode)

        return {"count_authors":len(results_list)}
    
    except ValueError as e:
        await append_log_async(f"エラーにより処理が中断しました。:{e}") 
        return e
    except Exception as e:
        await append_log_async(f"予期しないエラーにより処理が中断しました。:{e}") 
        return e


if __name__ == "__main__":
    
    # 各辞書のキーは "date" と "id" です
    # 各辞書のキーは "date" と "id" です。dateはすべて空文字に設定しています。
    data = [
        {"date": "", "id": "A5088470421"},
        {"date": "", "id": "A5046929921"},
        {"date": "", "id": "A5069381472"},
        {"date": "", "id": "A5078708083"},
        {"date": "", "id": "A5103729537"},
        {"date": "", "id": "A5103758018"},
        {"date": "", "id": "A5008853188"},
        {"date": "", "id": "A5001703580"},
        {"date": "", "id": "A5101864668"},
        {"date": "", "id": "A5025502033"},
        {"date": "", "id": "A5030416341"},
        {"date": "", "id": "A5047575077"},
        {"date": "", "id": "A5027781657"},
        {"date": "", "id": "A5009927733"},
        {"date": "", "id": "A5022077244"},
        {"date": "", "id": "A5056590036"},
        {"date": "", "id": "A5054416068"},
        {"date": "", "id": "A5048103459"},
        {"date": "", "id": "A5023389902"},
        {"date": "", "id": "A5020461673"},
        {"date": "", "id": "A5083163427"},
        {"date": "", "id": "A5107483313"},
        {"date": "", "id": "A5086543319"},
        {"date": "", "id": "A5101653342"},
        {"date": "", "id": "A5019961334"},
        {"date": "", "id": "A5037383580"},
        {"date": "", "id": "A5036467430"},
        {"date": "", "id": "A5078242198"},
        {"date": "", "id": "A5090517305"},
        {"date": "", "id": "A5007645582"},
        {"date": "", "id": "A5082304775"},
        {"date": "", "id": "A5101904235"},
        {"date": "", "id": "A5056964526"},
        {"date": "", "id": "A5039088371"},
        {"date": "", "id": "A5108690521"},
        {"date": "", "id": "A5101494445"}
    ]

    import asyncio
    asyncio.run(specific_id_execute(data, di_calculation=True, output_sheet_name="API動作確認", use_API_key=True, output_mode=""))
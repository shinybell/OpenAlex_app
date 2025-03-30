#uvicorn endpoint.api_endpoint:app --reload
#uvicorn endpoint.api_endpoint:app --host 0.0.0.0 --port 8000 --reload --ws-ping-interval 20 --ws-ping-timeout 500
#ngrok http 8000
import os, sys; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from fastapi import FastAPI,HTTPException,Request
from typing import List
from pydantic import BaseModel
import asyncio
import time
import boto3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo  # Python 3.9以降で利用可能

from executables.execute_feach_japanese import execute
from services.create_author_id_list import CreateAuthorIdList
from utils.common_method import count_logical_cores
from utils.async_log_to_sheet import append_log_async
from endpoint.connection_manager import ConnectionManager  # 修正後のインポート
from config.get_env import get_instance_id,stop_this_instance
from config.secret_manager import SecretManager

secret = SecretManager()

# グローバルロックを定義
processing_lock = asyncio.Lock()

# タイムゾーンをAsia/Tokyoに設定
JST = ZoneInfo("Asia/Tokyo")

# グローバル変数の初期化
last_access_time = datetime.now(JST)  # 現在の日本時間を記録
last_active_time = last_access_time  # 処理終了時に更新
start_activate_time = last_access_time

# 処理中かどうかを示すフラグ
is_processing = False

# WebSocket 接続を管理するクラス
manager = ConnectionManager()

def stop_ec2_instance(instance_id: str):
    #現在使っていない。テストもしていない。
    try:
        ec2 = boto3.client('ec2', region_name="ap-northeast-1")  # リージョンを設定
        response = ec2.stop_instances(InstanceIds=[instance_id])
        print(f"インスタンス {instance_id} を停止しました。")
    except Exception as e:
        print(f"インスタンスの停止中にエラーが発生しました: {e}")

async def monitor_activity(instance_id: str):
    try:
        global last_access_time, last_active_time, is_processing
        while True:
            now = datetime.now(JST)  # 日本時間を取得
            time_diff = now - last_access_time
            active_time_diff = now - last_active_time

            if time_diff > timedelta(hours=5):
                await append_log_async(f"最後にアクセスがあってから、5時間経過しました。無限ループの可能性を考え処理を自動停止します。 起動時:{start_activate_time}\n最後のアクセス:{last_access_time}")
                stop_this_instance(instance_id)
                await asyncio.sleep(15)
                await append_log_async(f"直ぐにエンジニアの確認が必要です。モニターによる自動停止に失敗しました。 起動時:{start_activate_time}\n最後のアクセス:{last_access_time}")
                #ここにslackに通知する機能を追加する。

            elif not is_processing and active_time_diff > timedelta(minutes=15):
                await append_log_async(f"最後の処理終了から15分以上経過しました。インスタンスを停止します。 起動時:{start_activate_time}\n最後の処理終了:{last_active_time}")
                stop_this_instance(instance_id)
                await asyncio.sleep(15)
                await append_log_async(f"直ぐにエンジニアの確認が必要です。モニターによる自動停止に失敗しました。 起動時:{start_activate_time}\n最後のアクセス:{last_access_time}")

            # ログ出力部分の修正
            if is_processing:
                await append_log_async(
                    f"起動時刻:{start_activate_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"処理中:{is_processing}\n"
                    f"最後のアクセス時刻:{last_access_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                await append_log_async(
                    f"起動時刻:{start_activate_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"処理中:{is_processing}\n"
                    f"最後の終了時刻:{last_active_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            await asyncio.sleep(120)#2分ごとモニタリングする。

    except Exception as e:
        try:
            print(e)
            await append_log_async(f"エンジニアの確認が必要です。モニタリングに予期せぬエラーが発生しました。インスタンスを停止します。エラー:{e}")
            stop_this_instance(instance_id)
        except:
            await append_log_async(f"直ぐにエンジニアに確認して下さい。stop_this_instance関数に問題があります。インスタンスの停止に失敗しました。")
 
app = FastAPI(title="Author Information API")  # ここでライフサイクルを統合)

@app.on_event("startup")
async def start_monitoring():
    """
    モニタリングタスクを開始し、APIのライフサイクル中に実行を維持する。
    """
    # 起動時のログ出力
    await append_log_async("インスタンスが起動しました。")
    
    # インスタンスIDの取得
    instance_id = get_instance_id()  # 環境変数やメタデータからインスタンスIDを取得

    # バックグラウンドでモニタリングタスクを開始
    app.state.monitor_task = asyncio.create_task(monitor_activity(instance_id))
    
    await append_log_async("モニタリングが開始されました。リクエストを受け付けます。")

@app.middleware("http") #すべてのリクエストを受け取る
async def endpoint_of_all(request: Request, call_next):
    global last_access_time, last_active_time, is_processing
    if is_processing:
        raise HTTPException(status_code=408, detail="リクエストがタイムアウトしました。現在実行中のプログラムがあります。")
    
    try:
        # ロックを取得し、タイムアウトを設定
        try:
            await asyncio.wait_for(processing_lock.acquire(), timeout=10)  # 最大10秒待機
        except asyncio.TimeoutError:
            raise HTTPException(status_code=408, detail="リクエストがタイムアウトしました。現在実行中のプログラムがあるか、ネット環境に問題があります。")
        
        # ロック取得成功
        try:
            await append_log_async(f"リクエストを受け付けました。")
            is_processing = True  # 処理中フラグを有効化
            last_access_time = datetime.now(JST)  # 現在の日本時間を記録
            response = await call_next(request)
            return response
        except Exception as e:
            await append_log_async(f"ミドルウェアでエラーが発生しました。: {e}")
            raise HTTPException(status_code=500, detail="処理に失敗しました")
        finally:
            is_processing = False  # 処理終了
            last_active_time = datetime.now(JST)  # 処理終了時に更新
            processing_lock.release()  # ロックを解放
            
   
    except HTTPException as he:
        # タイムアウトや他のHTTP例外をそのまま返す
        raise he
    except Exception as e:
        # その他の例外をキャッチ
        await append_log_async(f"ミドルウェアで未処理のエラーが発生しました: {e}")
        raise HTTPException(status_code=500, detail="サーバー内部エラーが発生しました")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the Author Information API"}  
    
# WebSocket 接続を管理するクラス
manager = ConnectionManager()

# リクエストデータのモデル
class RequestData(BaseModel):
    topic_id: List[str] =[] # トピックID（リスト）
    primary: bool =True
    citation_count: int =-1 # 引用数（整数）
    publication_year: int =-1 # 出版年（整数）
    title_and_abstract_search: str =""
    di_calculation: bool =False # DI計算（真偽値）
    output_sheet_name: str =""  # 出力シート名
    stop_control:bool=False #実行後に自動でインスタンスを閉じる。
    use_API_key:bool=True
    output_mode:str=""

# エンドポイント: データを受け取って処理
@app.post("/feach_japanese/")
async def process_feach_japanese(request_data: RequestData):
    try:

        result= await execute(
                topic_ids=request_data.topic_id,
                primary=request_data.primary,  # 固定値
                threshold=request_data.citation_count,
                year_threshold=request_data.publication_year,
                title_and_abstract_search=request_data.title_and_abstract_search,
                di_calculation=request_data.di_calculation,
                output_sheet_name=request_data.output_sheet_name,
                use_API_key = request_data.use_API_key,
                output_mode = request_data.output_mode
                )
        
        this_instance_id = get_instance_id()
        if request_data.stop_control:
            await append_log_async(f"インスタンスを停止します。インスタンスID:{this_instance_id}")     
            stop_this_instance(this_instance_id)

    except Exception as e:
        try:
            await append_log_async(f"エラーが発生したため、処理が中断されました。{e}")  # ログの追加
        
            this_instance_id = get_instance_id()
            if request_data.stop_control:
                await append_log_async(f"インスタンスの停止処理をします。インスタンスID:{this_instance_id}")
                stop_this_instance(this_instance_id)
            else:
                await append_log_async(f"インスタンスを停止していません。停止忘れに注意してください。インスタンスID:{this_instance_id}")
        except:
            if request_data.stop_control:
                await append_log_async(f"インスタンスの停止処理に失敗しました。手動で停止させてください。:{this_instance_id}") 
            else:
                await append_log_async(f"インスタンスを停止していません。停止忘れに注意してください。インスタンスID:{this_instance_id}")


if __name__ == "__main__":
    # 非同期関数を呼び出すためにイベントループを使用
    request_data = {
        "topic_id": [],
        "primary": True,
        "citation_count": 50,
        "publication_year": 2015,
        "title_and_abstract_search": "AI,machine",
        "di_calculation": False,
        "output_sheet_name": "テスト2",
        "use_API_key":True,
        "output_mode":"detail"
    }

    async def main():
        # 非同期関数を直接実行
        #process_count_japanese
        #process_feach_japanese
        await process_feach_japanese(RequestData(**request_data))
    
    # イベントループで実行
    asyncio.run(main())

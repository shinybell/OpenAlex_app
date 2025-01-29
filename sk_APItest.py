import asyncio
import httpx
import json
import time
import traceback  # 追加

# 基本となるURLを設定（必要に応じて変更してください）
BASE_URL = "http://127.0.0.1:8000"

# POSTエンドポイントのURL
POST_URL = f"{BASE_URL}/sk_fech_japanese/"

# GETエンドポイントのURL
GET_LOGS_URL = f"{BASE_URL}/sk_get_logs/"

# リクエストデータのサンプル（必要に応じて調整してください）
request_data = {
    "author_info_source": "Example Source",
    "topic_id": ["T10966"],
    "primary": True,
    "citation_count": 15,
    "publication_year": 2015,
    "title_and_abstract_search": "(\"novel target\" OR \"new target\" OR \"therapeutic target\")",
    "di_calculation": False,
    "output_sheet_name": "API動作確認"
}

async def send_post_request(client: httpx.AsyncClient):
    """
    /sk_fech_japanese/ エンドポイントにPOSTリクエストを送信します。
    """
    try:
        print("POSTリクエストを送信中...")
        response = await client.post(POST_URL, json=request_data)
        response.raise_for_status()
        result = response.json()
        print("POSTリクエストの結果:", json.dumps(result, ensure_ascii=False, indent=2))
    except httpx.HTTPStatusError as exc:
        print(f"HTTPエラーが発生しました: {exc.response.status_code} - {exc.response.text}")
    except Exception as e:
        print("予期せぬエラーが発生しました:")
        traceback.print_exc()  # トレースバックを表示

async def poll_logs(client: httpx.AsyncClient, interval: int, stop_event: asyncio.Event):
    """
    /sk_get_logs/ エンドポイントに定期的にGETリクエストを送信してログを取得します。
    """
    while not stop_event.is_set():
        try:
            response = await client.get(GET_LOGS_URL)
            response.raise_for_status()
            logs = response.json()
            print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] 現在のログ ({logs.get('total_logs', 0)} 件):")
            for log in logs.get("logs", []):
                print(log)
        except httpx.HTTPStatusError as exc:
            print(f"ログ取得時にHTTPエラーが発生しました: {exc.response.status_code} - {exc.response.text}")
        except Exception as e:
            print("ログ取得時に予期せぬエラーが発生しました:")
            traceback.print_exc()  # トレースバックを表示
        
        await asyncio.sleep(interval)

async def main():
    """
    メインの非同期関数。POSTリクエストを送信し、並行してログをポーリングします。
    """
    async with httpx.AsyncClient() as client:
        # 停止用のイベントを作成
        stop_event = asyncio.Event()
        
        # POSTリクエストを送信するタスク
        post_task = asyncio.create_task(send_post_request(client))
        
        # ログをポーリングするタスク（例: 5秒ごと）
        poll_task = asyncio.create_task(poll_logs(client, interval=5, stop_event=stop_event))
        
        # POSTリクエストが完了するのを待つ
        await post_task
        
        # POSTリクエストが完了したら、ポーリングを停止
        stop_event.set()
        
        # ポーリングタスクが停止するのを待つ
        await poll_task

if __name__ == "__main__":
    asyncio.run(main())
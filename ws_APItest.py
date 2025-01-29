# ws_APItest.py

import asyncio
import json
import websockets
import aiohttp

# サーバーのURL設定
WS_URI = "ws://127.0.0.1:8000/ws_feach_japanese/ws/"  # 修正後のWebSocketエンドポイント
PROCESS_URI = "http://127.0.0.1:8000/ws_feach_japanese/"  # WebSocket対応の処理エンドポイント

# 送信するデータ
data = {
    "author_info_source": "Example Source",
    "topic_id": ["T10966"],  # リストとして修正
    "primary": True,  # フィールドを追加
    "citation_count": 15,  # 整数に修正
    "publication_year": 2010,  # 整数に修正
    "title_and_abstract_search": '("novel target" OR "new target" OR "therapeutic target")',  # フィールドを追加
    "di_calculation": False,  # ブール値に修正
    "output_sheet_name": "API動作確認"
}

async def listen_progress():
    async with websockets.connect(WS_URI,ping_interval=20, ping_timeout=600) as websocket:
        print("WebSocket接続が確立しました。")
        try:
            while True:
                message = await websocket.recv()
                print(f"進捗メッセージ: {message}")
                if message == "ping":
                    # サーバーからのpingに対してpongを返す
                    await websocket.send("pong")
                    print("サーバーからのpingに対してpongを送信しました。")
                
                if message == "!*処理が完了しました*!": 
                    print("処理完了通知を受け取りました。接続を終了します。")
                    break  # 接続を閉じる
                    
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket接続が閉じられました。処理開始から10分でWebSocket接続が切断されるように設計されています。良好なネットワーク環境で10分も経たずに接続が切れた場合は、システムの不具合の可能性があります。")

async def send_process_request():
    async with aiohttp.ClientSession() as session:
        async with session.post(PROCESS_URI, json=data) as resp:
            if resp.status == 200:
                response_data = await resp.json()
                print(f"処理が正常に終了しました: {response_data}")
            else:
                error_text = await resp.text()
                print(f"処理に失敗しました。ステータスコード: {resp.status}, エラー内容: {error_text}")

async def main():
    # 進捗メッセージを受信するタスク
    listener = asyncio.create_task(listen_progress())

    # 少し待ってからPOSTリクエストを送信
    await asyncio.sleep(1)  # WebSocket接続の安定を待つ
    await send_process_request()

    # 処理が完了するまで待機（必要に応じて調整）
    await listener

if __name__ == "__main__":
    asyncio.run(main())
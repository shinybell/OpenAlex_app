import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

import asyncio
from api.spreadsheet_manager import SpreadsheetManager
from datetime import datetime
from pytz import timezone
from config.secret_manager import SecretManager

secret =SecretManager()

# 固定のスプレッドシート名とシート名
FIXED_SPREADSHEET_NAME = os.getenv('FIXED_SPREADSHEET_NAME')
FIXED_WORKSHEET_NAME = os.getenv('FIXED_WORKSHEET_NAME')


# 固定のSpreadsheetManagerインスタンスを作成
fixed_sheet_manager = SpreadsheetManager(FIXED_SPREADSHEET_NAME, FIXED_WORKSHEET_NAME)


async def append_log_async(text):
    """
    非同期でappend_logを実行する
    """
    try:
        print(text)
        # 日本時間のタイムゾーンを指定
        jst = timezone('Asia/Tokyo')
        current_time = datetime.now(jst)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, fixed_sheet_manager.append_row, [current_time.strftime("%Y-%m-%d %H:%M:%S"),text])
    except Exception as e:
        print(f"append_log_asyncの処理中にエラーが発生しました。{e}")

if __name__ == "__main__":
    # 使用例
    secret =SecretManager()
    asyncio.run(append_log_async("非同期処理のログテスト"))
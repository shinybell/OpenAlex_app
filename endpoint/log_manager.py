# log_manager.py

from typing import List
import threading

# ログスタックとロックの初期化
log_stack: List[str] = []
log_lock = threading.Lock()

def add_log(message: str):
    """ログスタックにメッセージを追加する"""
    with log_lock:
        log_stack.append(message)

def get_logs() -> List[str]:
    """ログスタックの内容を取得する"""
    with log_lock:
        return list(log_stack)

def clear_logs():
    """ログスタックをクリアする"""
    with log_lock:
        log_stack.clear()
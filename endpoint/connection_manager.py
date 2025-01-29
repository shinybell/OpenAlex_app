# connection_manager.py

from fastapi import WebSocket
from typing import List
import logging

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"新しい接続: {websocket.client}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logging.info(f"接続が切断されました: {websocket.client}")

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logging.error(f"クライアントへのメッセージ送信エラー: {e}")
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)
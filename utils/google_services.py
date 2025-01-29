import os
import sys
import uuid
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload


PARENT_FOLDER_ID ="1ydsJKCIHTet5d-A59tadTG3PXFye3t3E"

class GoogleServices:
    """
    Google Drive API と Google Slides API のサービスオブジェクトを保持し、関連する操作を提供するクラス。
    """
    def __init__(self, service_account_file):
        """
        GoogleServices クラスのコンストラクタ。サービスアカウントの認証情報を使用して
        Google Drive API と Google Slides API のサービスオブジェクトを初期化する。

        Args:
            service_account_file (str): サービスアカウントキーのJSONファイルのパス（相対パスまたは絶対パス）。
        """
    
        self.drive = None
        self.slides = None

        # ファイルパスが相対パスか絶対パスかを判断
        if not os.path.isabs(service_account_file):
            # 相対パスの場合、絶対パスに変換
            service_account_file = os.path.abspath(service_account_file)
            print(f"サービスアカウントファイルの絶対パスに変換しました: {service_account_file}")
        else:
            print(f"サービスアカウントファイルのパス: {service_account_file}")

        # スコープの定義（Google Drive APIとGoogle Slides APIへのフルアクセス）
        scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/presentations'
        ]

        try:
            # サービスアカウントの認証情報を取得
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file,
                scopes=scopes
            )
            print("認証情報を正常に取得しました。")
        except Exception as e:
            print(f"認証情報の取得に失敗しました: {e}")
            sys.exit(1)

        try:
            # Drive APIのサービスオブジェクトを構築
            self.drive = build('drive', 'v3', credentials=credentials)
            print("Google Drive APIのサービスオブジェクトを作成しました。")
        except Exception as e:
            print(f"Drive APIのサービスオブジェクトの作成に失敗しました: {e}")
            sys.exit(1)


    def upload_files_to_folder(self, folder_id, local_file_paths):
        """
        local_file_pathsに含まれるローカルファイルを指定フォルダにアップロードするメソッド。

        Args:
            folder_id (str): アップロード先フォルダID。
            local_file_paths (list): アップロードするローカルファイルパスのリスト。
        """
        for local_file_path in local_file_paths:
            if not os.path.isabs(local_file_path):
                local_file_path = os.path.join(os.getcwd(), local_file_path)

            if os.path.exists(local_file_path) and os.path.isfile(local_file_path):
                file_metadata = {
                    'name': os.path.basename(local_file_path),
                    'parents': [folder_id]
                }

                media = MediaFileUpload(local_file_path, resumable=True)

                try:
                    uploaded_file = self.drive.files().create(
                        body=file_metadata,
                        media_body=media,
                        fields='id'
                    ).execute()

                    print(f"ローカルファイル '{local_file_path}' をアップロードしました。ID: {uploaded_file.get('id')}")
                except Exception as e:
                    print(f"ローカルファイル '{local_file_path}' のアップロード中にエラーが発生しました: {e}")
            else:
                print(f"ローカルファイルが見つかりません: {local_file_path}")

# フォルダーIDが正しいかを確認するための簡単なチェック
def check_folder_exists(drive_service, folder_id):
    try:
        folder = drive_service.files().get(fileId=folder_id, fields='id, name').execute()
        print(f"フォルダーが存在します。名前: {folder.get('name')}, ID: {folder.get('id')}")
        return True
    except Exception as e:
        print(f"フォルダーの確認中にエラーが発生しました: {e}")
        return False
    
# メイン実行部分に追加

# メインの実行部分
if __name__ == "__main__":
    # 必要なライブラリをインポート
    import sys
    import os

    # 現在のスクリプトのディレクトリの親ディレクトリを取得
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    SERVICE_ACCOUNT_FILE = "config/uplifted-env-435001-p3-36f18da76d83.json"
    # GoogleServices クラスのインスタンスを生成
    google_service = GoogleServices(service_account_file=SERVICE_ACCOUNT_FILE)
    google_service.upload_files_to_folder("1KcgyL-IkA6At7OdGdbByKdp2MYdJgauT",["test.txt"])
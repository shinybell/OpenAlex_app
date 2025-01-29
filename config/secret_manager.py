import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import NoCredentialsError
#from botocore.exceptions import ClientError



class SecretManager:
    def __init__(self):
        # 環境を判定 ('local' か 'lambda')
        #self.environment = os.getenv('ENVIRONMENT', 'local')
        # ローカル環境では.envファイルをロード
        #if self.environment == 'local':
        load_dotenv()  # .envファイルから環境変数を読み込む

    def get_secret(self, key):
        """
        環境変数やAWS Secrets Managerから秘密情報を取得する関数
        :param key: 秘密情報のキー名
        :return: 秘密情報の値
        """
        if self.environment == 'local':
            # ローカル環境 (.envから取得)
            return os.getenv(key)
        elif self.environment == 'lambda':
            # Lambda環境 (Secrets ManagerまたはSSMから取得)
            return self._get_secret_from_aws(key)
        else:
            raise ValueError(f"不明な環境: {self.environment}")

    def _get_secret_from_aws(self, key):
        """
        Secrets ManagerまたはSSMから秘密情報を取得する内部メソッド
        """
        try:
            # AWS Secrets Managerを使用して秘密情報を取得
            client = boto3.client('secretsmanager')
            response = client.get_secret_value(SecretId=key)
            return response['SecretString']
        except NoCredentialsError:
            print("AWS認証情報がありません")
        except Exception as e:
            print(f"秘密情報の取得中にエラーが発生しました: {e}")
            return None


# if __name__ == "__main__":
#     secret_manager = SecretManager()

#     # ローカル環境からAPIキーを取得する例
#     # 環境変数をos.getenvで直接取得
#     google_api_key = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
#     openai_api_key = os.getenv('OPENAI_API_KEY')

#     # 値を表示して確認
#     print("Google Spreadsheet API Key:", google_api_key)
#     print("OpenAI API Key:", openai_api_key)
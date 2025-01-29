
import requests
import os


def get_instance_id():
    try:
        # メタデータサービスのトークン取得エンドポイント
        token_url = "http://169.254.169.254/latest/api/token"
        metadata_url = "http://169.254.169.254/latest/meta-data/instance-id"

        # トークンを取得
        token_response = requests.put(
            token_url, 
            headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"}, 
            timeout=5
        )
        token_response.raise_for_status()
        token = token_response.text

        # メタデータを取得
        response = requests.get(
            metadata_url, 
            headers={"X-aws-ec2-metadata-token": token}, 
            timeout=5
        )
        response.raise_for_status()
        return response.text  # インスタンスIDを返す

    except requests.RequestException:
        # EC2メタデータにアクセスできない場合、ローカル環境と判断
        return "local"
    
    except Exception as e:
        raise



import subprocess
from fastapi import HTTPException


def stop_this_instance(instance_id):
    # 現在のファイルのパスを取得してディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    if instance_id=="i-00263e90d849af505":
        CORE8_SCRIPT_PATH = os.path.join(current_dir, "ec2_core8_inst2_control.sh")
    elif instance_id=="i-06a99ec8dab83f67a":
        CORE8_SCRIPT_PATH = os.path.join(current_dir, "ec2_core8_inst3_control.sh")
    elif instance_id=="i-0411b476934cc16a5":
        CORE8_SCRIPT_PATH = os.path.join(current_dir, "ec2_core8_inst1_control.sh")   
    elif instance_id=="i-00c9116fa53632f53":
        CORE8_SCRIPT_PATH = os.path.join(current_dir, "ec2_test_instance_control.sh") 
    elif instance_id=="local":
        print("ローカル環境で実行しているのでインスタンスを止める処理はしません。")
        return
    else:
        raise Exception(f"Unexpected value in stop_this_instance method: {instance_id}")
        
    try:
        # シェルスクリプトを実行
        result = subprocess.run(
            [CORE8_SCRIPT_PATH, "stop"],  # コマンドと引数
            capture_output=True,          # 標準出力と標準エラーをキャプチャ
            text=True                     # 出力を文字列として取得
        )

        # 実行結果を返却
        if result.returncode == 0:
            print(result.stdout)
            return {"status": "success", "output": result.stdout}
        else:
            raise HTTPException(status_code=500, detail=result.stderr)

    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Script not found: {CORE8_SCRIPT_PATH}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
if __name__ == "__main__":
    # instance_id = get_instance_id()
    # print(f"Instance ID: {instance_id}")
    stop_this_instance("i-00c9116fa53632f53")
    
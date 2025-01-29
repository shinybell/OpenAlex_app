import time
import requests

# APIのエンドポイントURL
#http://127.0.0.1:8000/

#url ="  http://44.211.68.239:8000/count_japanese/"

#18.183.149.240
#ec2-18-183-149-240.ap-northeast-1.compute.amazonaws.com
#url = "http://127.0.0.1:8000/feach_japanese/"

def request_to_OpenAlex_instance(instance:str,data):

    if instance =="core8_2":
        url = "http://18.179.125.203:8000/feach_japanese/"
       # url = f"http://127.0.0.1:8000/feach_japanese"
    else:
        print(f"入力されたインスタンスはありますん。:{instance}")
        return "faild"
    
    try:   
        # POSTリクエストを送信して結果を確認
        response = requests.post(url, json=data)

        # レスポンスを表示
        print("Status Code:", response.status_code)
        print("Response Body:", response.json())

        return {"status":response.status_code,"body":response.json()}
    
    except requests.exceptions.RequestException as e:
        print("接続エラー:", e)
        return {"status": "error", "error": str(e)}
    
def control_ec2_instance(instance:str,action:str):

    try:
        url = "http://13.113.21.96:8000/control-ec2/"

        data = {
            "action":action,
            "instance":instance #core8
        }
        response = requests.post(url, json=data,timeout=25)
        # レスポンスを表示
        print("Status Code:", response.status_code)
        if response.status_code==500:           
            try:
                error_detail = response.json().get("detail", "詳細なエラー情報はありません")
                print("現在処理を受け付けていません。しばらく待ってからやり直してください。")
                print("エラー詳細:", error_detail)
            except ValueError:
                print("エラー情報を解析できません。")
        
        else:
            data = response.json()
            print("Response Body:",data)
            print(data.get("status",""))
            print(data.get("output",""))
            
    except Exception as e:
        print(e)
        
        
if __name__ == "__main__":

    #スプレットシートをクリアにしてからアップ。
   control_ec2_instance("core8_1","start")

    # #time.sleep(15)
    # # # # 送信するデータ
    # data = {
    #     "author_info_source": "Example Source",
    #     "topic_id": ["T10966"],  # リストとして修正
    #     "primary": True,  # フィールドを追加
    #     "citation_count": 20,  # 整数に修正
    #     "publication_year": 2020,  # 整数に修正
    #     "title_and_abstract_search":"novel target,new target,therapeutic target" ,  # フィールドを追加'("novel target" OR "new target" OR "therapeutic target")'
    #     "di_calculation": False,  # ブール値に修正
    #     "output_sheet_name": "API動作確認",
    #     "stop_control":True
    # }
    
    # request_to_OpenAlex_instance("core8_2",data)

    
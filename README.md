t2.micro
--------設計のメモ---------

あるエンドポイントで、ws_APItestのようなものを作り、

messageをリストで管理して、このエンドポイントにリクエストしたら、
現状のログをreturnするようのエンドポイントを用意する。

#curl -X GET "http://127.0.0.1:8000/sk_get_logs/"
curl -X POST "http://127.0.0.1:8000/sk_fech_japanese/" \
     -H "Content-Type: application/json" \
     -d '{
           "author_info_source": "Example Source",
           "topic_id": ["T10966"],
           "primary": true,
           "citation_count": 15,
           "publication_year": 2010,
           "title_and_abstract_search": "(\"novel target\" OR \"new target\" OR \"therapeutic target\")",
           "di_calculation": false,
           "output_sheet_name": "API動作確認"
         }'



スプレットシートにログをそのまま送信する。
--------------------------
1.以下のコマンドでGitをインストールします
sudo yum update -y
sudo yum install git -y

1. Gitリポジトリを初期化する
git init

2. リモートリポジトリを追加する
git remote add origin git@github.com:ichiharahiroroki/OpenAlex_app.git

3. 必要なファイルをコミットする
git add .
git commit -m "Initial commit"


4. リモートリポジトリにPushする
git branch -M main  # 現在のブランチの名前を「main」に変更する
git push -u origin main



########EC2での作業Amazon Linuxの場合########

1.以下のコマンドでGitをインストールします
sudo yum update -y
sudo yum install git -y

2. リモートリポジトリをHTTPSでクローン
git clone https://github.com/ichiharahiroroki/OpenAlex_app.git

3. クローンされたリポジトリに移動
cd OpenAlex_app

4. リポジトリの内容を確認
ls

5. 最新の状態をPull（すでにリモートリポジトリとローカルは同期しているはずですが、以下のコマンドで最新状態を確認できます）
git pull origin main
変更があるが、pullを強制したい場合は、変更を破棄
git reset --hard HEAD


-----------------#初期設定#-----------------
仮想環境を作成：
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

公開
uvicorn api_endpoint:app --host 0.0.0.0 --port 8000

2. セキュリティグループの設定（AWS特有の手順）
EC2インスタンス上で動作させる場合、AWSセキュリティグループでポートを開放する必要があります。
	1.	AWS管理コンソールで設定を確認：
	•	EC2ダッシュボードを開く。
	•	対象インスタンスのセキュリティグループを開く。
	•	インバウンドルールを編集し、以下を追加：
	•	タイプ: カスタムTCPルール
	•	ポート範囲: 8000
	•	ソース: 0.0.0.0/0（全世界からアクセス可能）または特定のIP。
	2.	設定を保存。

3. 外部からアクセス
	1.	EC2インスタンスのパブリックIPアドレスを確認。
	•	AWS管理コンソールのインスタンス情報に「パブリックIPv4アドレス」が記載されています（例: 44.211.68.239）。
	2.	ブラウザまたはHTTPクライアントでアクセス：
	•	例: Swagger UI (APIドキュメント) にアクセス：
        http://44.211.68.239:8000/docs
    3.	エンドポイントに直接リクエスト：
        http://44.211.68.239:8000/count_japanese/





------Start Stop Control OpenAlex Server------------
[ec2-user@ip-172-31-7-197 ~]$ --query 'Reservations[*].Instances[*].[InstanceId, State.Name, Tags]'
bash: --query: command not found
[ec2-user@ip-172-31-7-197 ~]$ aws configure
AWS Access Key ID [None]: 
AWS Secret Access Key [None]: 
Default region name [ap-northeast-1]: ap-northeast-1
Default output format [json]: json
[ec2-user@ip-172-31-7-197 ~]$ aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId, State.Name]' --output table
------------------------------------
|         DescribeInstances        |
+----------------------+-----------+
|  i-0745aeb1f80000a88 |  running  |
|  i-00c9116fa53632f53 |  running  |
+----------------------+-----------+
[ec2-user@ip-172-31-7-197 ~]$ 




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


① ソースから Python 3.11 をインストールする方法
1. システムの更新と依存パッケージのインストール

sudo yum update -y
sudo yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make -y

2. Python 3.11 のソースコードをダウンロード

wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz

3. アーカイブを解凍する

tar xzf Python-3.11.4.tgz
cd Python-3.11.4


4. コンパイル前の設定

./configure --enable-optimizations

※ --enable-optimizations オプションは最適化を有効にし、実行速度を向上させますが、コンパイルに時間がかかる場合があります。

5. Python のビルドとインストール
CPU コア数に応じて -j オプションで並列ビルドすると速くなります。
make -j 8
sudo make altinstall

※ make altinstall を使うことで、既存のシステム Python と競合しないように python3.11 としてインストールされます。

6. インストール確認

/usr/local/bin/python3.11 --version

もしくは、パスが通っていれば

python3.11 --version

7. 仮想環境の作成
Python 3.11 がインストールできたら、仮想環境を作成できます。

python3.11 -m venv scispacy_env
source scispacy_env/bin/activate



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


# ======================================================
# ① Python 3.11 をソースからインストールする手順
# ======================================================
#ベクトル評価する場合は、：spaCyのen_core_sci_lgを使用するために、Python 3.11のバージョンを使用する必要がある。


# 1. システムの更新と依存パッケージのインストール
sudo yum update -y
sudo yum install gcc openssl-devel bzip2-devel libffi-devel zlib-devel wget make -y

# 2. Python 3.11.4 のソースコードをダウンロード
wget https://www.python.org/ftp/python/3.11.4/Python-3.11.4.tgz

# 3. アーカイブを解凍してディレクトリに移動
tar xzf Python-3.11.4.tgz
cd Python-3.11.4

# 4. コンパイル前の設定（最適化有効化）
./configure --enable-optimizations

# 5. Python のビルドとインストール（CPU コア数に合わせ -j オプションを使用）
make -j 8
sudo make altinstall
# ※ 'altinstall' を使用することで、既存のシステム Python と競合せず python3.11 としてインストールされます。

# 6. インストール確認（バージョン確認）
python3.11 --version

# ======================================================
# ② 仮想環境の作成と requirements.txt からのパッケージインストール
# ======================================================

# ※ ここからはプロジェクトディレクトリ（例: /home/ec2-user/OpenAlex_app）で作業してください
cd /home/ec2-user/OpenAlex_app

# 7. Python 3.11 を使って仮想環境 "venv_py311" を作成
python3.11 -m venv venv_py311

# 8. 仮想環境の有効化
source venv_py311/bin/activate

# 9. 仮想環境内の pip を最新にアップグレード
python -m pip install --upgrade pip

# 10. ※重要: requirements.txt から en_core_sci_lg の行を削除またはコメントアウトする
# 例: エディタで requirements.txt を開き、以下の行をコメントアウトしてください
# en_core_sci_lg @ https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz#sha256=...

# 11. requirements.txt に記載されたその他の依存パッケージを一括インストール
python -m pip install -r requirements.txt

# 12. en_core_sci_lg を依存関係チェックなし (--no-deps) で個別にインストール
python -m pip install --no-deps "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.1/en_core_sci_lg-0.5.1.tar.gz"

# ======================================================
# これで、Python 3.11 のインストール、仮想環境の構築、及び
# 必要なパッケージのインストールが完了し、既存環境と同じ組み合わせで動作します。
# ======================================================
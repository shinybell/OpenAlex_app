# OpenAlex_app

## 動作要件

python 3.11.11

## 環境構築

- python のバージョンを pyenv などで固定
  pyenv 以外のバージョン管理ツールを使っている場合は適宜置き換えてください。

```bash
pyenv local 3.11.11
python --version
```

3.11.11 とでたら反映できてます。

- venv の仮想環境を構築

```bash
python -m venv .venv

# 仮想環境に入る
#  WIndowsの場合
./.venv/Scripts/activate
# MacOSの場合
source .venv/bin/activate
```

- 依存関係インストール

```bash
pip install -r venv_py311_requirements.txt
```

## サンプルの json データを用いた動作方法

sample_request_data.json に検索条件を記入して以下のコマンドを実行すると、csv ファイルが作成される。
json において、`output_mode = "sample"`とすること

```bash
python test_with_json.py sample_request_data.json
```

`sample_output.csv`というファイルが新しくできているはず。

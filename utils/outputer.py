from datetime import datetime
from utils.async_log_to_sheet import append_log_async
from urllib.parse import quote

async def output_to_sheet(sheet_manager,header,rows):
    attempt = 1
    max_retries = 6
    while attempt < max_retries:
        try:
            sheet_manager.sheet.update('A1',[header])
            break
        except Exception as e:
            await append_log_async(f"headerの追加をやり直す。エラー:{e}") 
    
    
    for i in range(0, len(rows), 1000):
        attempt = 1
        max_retries = 6
        while attempt < max_retries:
            try:
                sheet_manager.append_rows(rows[i:i+1000])
                await append_log_async(f"[{i}:{i+1000}]を追加しました。") 
                break
            except Exception as e:
                await append_log_async(f"[{i}:{i+1000}]をやり直す。エラー:{e}") 
            attempt+=1
            
        if attempt < max_retries:
            continue
        else:
            raise ValueError(f"スプレットシートに追加できませんでした。エラー:{e}")
            

def truncate_and_report_long_cells(data, limit=50000):
    try:
        for i, row in enumerate(data):
            for j, cell in enumerate(row):
                if len(cell) > limit:
                    data[i][j] = cell[:limit]  # セルの内容をlimit文字に切り捨て
    except Exception as e:
        raise ValueError(f"truncate_and_report_long_cells関数の使い方に問題があります。エラー:{e}")

    return data


#スプレットシートにアップするために、各要素はstr型の２次元リストに変換。
def dict_list_to_string_rows(dict_list):
    rows =[]
    for result in dict_list:
        row = [str(value) for value in result.values()]
        rows.append(row)
    return rows


def adjust_indicators(dict_list,add_key_list=[]):
    # 新しい辞書リストを格納するリスト
    new_list = []
    header = [ "Google検索","研究の質","h-index世界ランク","若さ","起業意欲","革新性","研究者ID", "名前", "最新の所属", "キャリア年数", "出版数", "全ての出版の被引用数","h-indexランキング","研究者検索結果総数","H-Index", "過去5年H-index", "企業との共著数", "first論文数", "対応(last)論文数", "DI0.8以上のworks数","STP.論文ID", "STP.論文タイトル", "STP.論文出版年月", "STP.論文被引用数","引用数ランキング","論文検索結果総数","CTP.論文ID", "CTP.論文タイトル", "CTP.論文出版年月", "CTP.論文被引用数"]

    # 必要なキー
    need_keys = [
        "researcher_id", "name", "latest_affiliation",
        "career_years", "works_count", "total_works_citations","h_index_ranking","all_author_count",
        "h_index", "last_5_year_h_index", "coauthor_from_company_count", "first_paper_count",
        "corresponding_paper_count", "disruption_index_above_08",
        "条件論文1:ID","条件論文1:タイトル","条件論文1:出版年月","条件論文1:被引用数","引用数ランキング","総数",
        "論文1:ID","論文1:タイトル","論文1:出版年月","論文1:被引用数"
        # "論文2:ID","論文2:タイトル","論文2:出版年月","論文2:被引用数",
        # "論文3:ID","論文3:タイトル","論文3:出版年月","論文3:被引用数",
    ]
    
    #add_key_list に含まれるキーを need_keys に追加（重複を避ける）
    need_keys.extend([key for key in add_key_list if key not in need_keys])
    
    # 入力リスト内の各辞書について処理
    for original_dict in dict_list:
        # 新しい辞書を作成して、必要なキーとその値だけをコピー
        new_dict = {key: original_dict[key] for key in need_keys if key in original_dict}
        new_list.append(new_dict)
    
    new_list = reorder_dict_keys(new_list)
    return header ,new_list

def reorder_dict_keys(dict_list):
    new_list = []
    
    for item in dict_list:
        # Google検索用URLの作成
        name = item.get("name", "")
        latest_affiliation = item.get("latest_affiliation", [""])
        
        # 空白や特殊文字をエンコード
        encoded_name = quote(name)
        encoded_affiliation = quote(latest_affiliation[0]) if latest_affiliation else ""
        
        search_query = f"https://www.google.com/search?q={encoded_name}+{encoded_affiliation}" if latest_affiliation else ""
        
        # 若さ（キャリア年数の逆数）
        career_years = item.get("career_years", 0)
        youth_index = round(1 / career_years, 4) if career_years > 0 else 0  # 0除算を回避し、少数第4位に丸める
                
        # 新しいキーとその値
        new_data = {
            "Google検索": search_query,
            "研究の質（h-index）": item.get("h_index", ""),
            "h-index世界ランク": item.get("h_index_ranking", ""),
            "若さ（逆数）": youth_index,
            "起業意欲": "",  # 一旦空白
            "革新性（DI0.8以上のworks数）": item.get("disruption_index_above_08", "")
        }
        
        # 既存のデータを新しいデータの後に追加
        combined_data = {**new_data, **item}
        
        new_list.append(combined_data)
    
    return new_list
    




def sort_dict_list_by_key(dict_list, sort_key):
    """
    辞書リストを指定したキーの値で降順にソートする関数。

    :param dict_list: 辞書リスト (List[dict])
    :param sort_key: ソートの基準となるキー名 (str)
    :return: ソートされた辞書リスト (List[dict])
    """
    try:
        sorted_list = sorted(dict_list, key=lambda x: x.get(sort_key, 0), reverse=True)
        return sorted_list
    except Exception as e:
        raise Exception(f"ソートに失敗しました。エラー: {e}")
import requests
import time
import os

def extract_id_from_url(url):
    if not isinstance(url, str):
        return url  # 文字列以外ならそのまま返す
    
    return url.split('/')[-1].upper() # スラッシュで分割して最後の部分を取得

def count_logical_cores():
    logical_cores = os.cpu_count()
    print(f"論理コア数: {logical_cores}")
    return logical_cores


#type type_crossref
def get_type_counts(author_id,type,found_date=""):
    url = f"https://api.openalex.org/works?group_by={type}"
    if found_date:
        params = {
            "filter": f"author.id:{author_id},publication_date:<{found_date}",
            "per_page": 200,
        }
    else:
        params = {
            "filter": f"author.id:{author_id}",
            "per_page": 200,
        }
    retry_num = 0
    while True:
        try:
            response = requests.get(url, params=params,timeout=5)
            if response.status_code == 200:  
                break
            else:
                if retry_num>8:
                    print("get_type_counts関数リクエストやり直し。断念する")
                    return {}
                print("get_type_counts関数リクエストやり直し。:",retry_num)
                retry_num +=1
                
                time.sleep(retry_num)
        except requests.exceptions.Timeout:
            if retry_num>8:
                print("get_type_counts関数タイムアウトしました。断念する")
                return {}
            print("get_type_counts関数タイムアウトしました。:",retry_num)
            retry_num +=1
            time.sleep(retry_num)
        except:
            if retry_num>8:
                print("get_type_counts関数。サーバーの遮断。断煙する")
                return {}
            print("get_type_counts関数。サーバーの遮断。:",retry_num)
            time.sleep(retry_num)
            
            
    json_data = response.json()
    result = {}
    # 'group_by' キーが JSON に含まれているか確認
    if 'group_by' in json_data:
        for group in json_data['group_by']:
            # 'key_display_name' と 'count' を取得
            display_name = group.get('key_display_name', '')
            count = group.get('count', 0)
            result[display_name] = count
    return result


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

if __name__ == "__main__":
    print(extract_id_from_url(None))
import re

def title_and_abstract_search_format(title_and_abstract_search):
    # 引数が空文字列や空リストの場合はエラーを発生させる
    if not title_and_abstract_search:
        raise ValueError("title_and_abstract_search cannot be empty")
    
    # 引数が文字列の場合、英字または日本語を含むかをチェック
    if isinstance(title_and_abstract_search, str):
        if not re.search(r'[a-zA-Zぁ-んァ-ン一-龥]', title_and_abstract_search):
            raise ValueError("title_and_abstract_search must contain at least one alphabetic or Japanese character")
    
    if isinstance(title_and_abstract_search, list):
        title_and_abstract_search = convert_keywords_to_or_condition(title_and_abstract_search)
    elif isinstance(title_and_abstract_search, str):
        if "," in title_and_abstract_search:
            array = title_and_abstract_search.split(",")
            title_and_abstract_search = convert_keywords_to_or_condition(array)
        elif title_and_abstract_search.startswith("(") and title_and_abstract_search.endswith(")"):
            title_and_abstract_search = title_and_abstract_search
        else:
            title_and_abstract_search = title_and_abstract_search
            # print(f"CreateAuthorIdListコンストラクタのtitle_and_abstract_searchに予期せぬ値:{title_and_abstract_search}")
            # raise Exception(f"CreateAuthorIdListコンストラクタのtitle_and_abstract_searchに予期せぬ値:{title_and_abstract_search}")

    else:
        print(f"CreateAuthorIdListコンストラクタのtitle_and_abstract_searchに予期せぬ値:{title_and_abstract_search}")
        raise Exception(f"CreateAuthorIdListコンストラクタのtitle_and_abstract_searchに予期せぬ値:{title_and_abstract_search}")

    return title_and_abstract_search


def convert_keywords_to_or_condition(keywords):
    if not keywords:
        return ""
    # 各キーワードをクォートで囲み、ORで結合して括弧で囲む
    quoted_keywords = [f'"{keyword}"' for keyword in keywords]
    return f"({'OR'.join(quoted_keywords)})"
    
    
if __name__ == "__main__":
    text = 'novel target,new target,therapeutic target'
    try:
        text = title_and_abstract_search_format(text)
        print(text)
    except ValueError as e:
        print(f"Error: {e}")
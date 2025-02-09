from collections import defaultdict, Counter
from typing import List, Dict, Any
from data_class.researcher_data import ResearcherData,AuthorProfileData,AuthorWorkData
from utils.common_method import extract_id_from_url
from datetime import datetime
from dateutil.relativedelta import relativedelta

def create_author_profile(author_work_data_list: List[AuthorWorkData]) -> AuthorProfileData:
    if not author_work_data_list:
        print("提供された author_work_data_list が空です。")
        return AuthorProfileData()

    # すべてのエントリが同じ Author ID であることを確認
    researcher_ids = set(work.author_id for work in author_work_data_list)
    if len(researcher_ids) != 1:
        print("author_work_data_list には複数の異なる Author ID が含まれています。")
        return AuthorProfileData()

    author_id = researcher_ids.pop()
    profile = AuthorProfileData(author_id=author_id)

    # 名前のカウント用
    name_counter = count_names(author_work_data_list)

    
    profile.latest_affiliation, profile.latest_country = get_latest_affiliation_and_country(author_work_data_list)

    profile.career_first_affiliation = get_first_affiliation_and_country(author_work_data_list)
    
    # Works数のカウント
    profile.works_count = len(author_work_data_list)

    # 所属機関と国コードの集計
    detail_of_affiliation = {}  # キー: (Institution ID), 値: {'Institution Name', 'Country Code', 'Years': set()}

    # 所属タイプの集計を初期化
    institution_types = defaultdict(int)
    
    # 共著者の集計用
    coauthor_counter = Counter()
    
    # ソースIDの集計用
    source_id_counter = Counter()

    # 共著者の所属タイプをカウントする Counter
    coauthor_type_counter = Counter()
    
    # 全ての論文からデータを集約
    for work in author_work_data_list:
        # ここで各論文の情報をpapers_infoに追加する
        paper_dict = {
            "paper_id": work.paper_id,
            "paper_title": work.paper_title,
            "position": work.position,
            "total_citations": work.total_citations,
            "d_index": work.d_index,
            "publication_date": work.publication_date
        }
        profile.papers_info.append(paper_dict)
        
        publication_year = work.publication_year if work.publication_year else None
        for inst in work.institutions:
            inst_id = inst.get('id', 'N/A')
            inst_name = inst.get('display_name', 'N/A')
            country_code = inst.get('country_code', 'N/A')

            if inst_id == "N/A":
                continue
            
            # 新たに取得する inst_type (空文字の場合は "N/A" とする)
            new_inst_type = inst.get("type", "").strip().lower() if inst.get("type", "").strip() else "N/A"
        
            # 一意な所属機関に追加
            if inst_id not in detail_of_affiliation:
                detail_of_affiliation[inst_id] = {
                    'Institution ID': inst_id,
                    'Institution Name': inst_name,
                    'Country Code': country_code,
                    'inst_type': new_inst_type,
                    'Years': set()
                }
                # 所属タイプの集計
                if new_inst_type != "N/A" and new_inst_type:
                    institution_types[new_inst_type] += 1
                    if new_inst_type != "education":
                        profile.non_education_affiliation_count += 1

            else:
                # エントリが既に存在する場合、inst_type の更新のみを検討
                current_inst_type = detail_of_affiliation[inst_id].get("inst_type", "N/A")
                if current_inst_type == "N/A" and new_inst_type != "N/A":
                    # 以前は N/A だったものを、新しい有効な値で上書き
                    detail_of_affiliation[inst_id]["inst_type"] = new_inst_type


            # 論文の出版年を使用して Years を更新
            if isinstance(publication_year, int):
                detail_of_affiliation[inst_id]['Years'].add(publication_year)

        # 被引用数の集計
        profile.total_works_citations += work.total_citations
        
        # 対応論文数の集計
        if work.corresponding_author or work.position=="last":
            profile.corresponding_paper_count += 1

        # ソースIDの集計
        if work.source_id:
            source_id_counter[work.source_id] += 1
                
        #ポジションがfirstの数
        if work.position=="first":
            profile.first_paper_count += 1

        #DIのカウント
        if work.d_index >= 0.9:
            profile.disruption_index_above_09 += 1
        if work.d_index >= 0.8:
            profile.disruption_index_above_08 += 1
        if work.d_index >= 0.7:
            profile.disruption_index_above_07 += 1
        if work.d_index >= 0.6:
            profile.disruption_index_above_06 += 1
        if work.d_index >= 0.5:
            profile.disruption_index_above_05 += 1
        if work.d_index >= 0.4:
            profile.disruption_index_above_04 += 1
        if work.d_index >= 0.3:
            profile.disruption_index_above_03 += 1
            
        # インパクト指数の合計
        try:
            if float(work.impact_index) > 0:  # impact_indexが0より大きいかをチェック
                profile.total_impact_index += float(work.impact_index)
        except (ValueError, TypeError):
            pass  # 無効な値の場合はスキップ

        # Topics の詳細の集計
        if work.topics:
            profile.topics_detail.extend(work.topics)
            
        # 共著者のカウント
        for author_info in work.authors_info:
            coauthor_id = author_info.get("author", {}).get("id", "N/A")
            if coauthor_id != author_id and coauthor_id != "N/A":
                coauthor_counter[extract_id_from_url(coauthor_id)] += 1
                
            # 共著者の所属機関タイプをチェック
            institutions = author_info.get("institutions", [])
            if isinstance(institutions, list):
                for inst in institutions:
                    type_value = inst.get("type", "")
                    if isinstance(type_value, str):
                        coauthor_type = type_value.lower()
                    if coauthor_type:
                        coauthor_type_counter[coauthor_type] += 1
            else:
                print(f"Unexpected type for institutions: {type(institutions)}")

    #論文リストのソート
    profile.papers_info.sort(key=lambda paper: paper["publication_date"], reverse=True)
    # 所属タイプをプロファイルに設定
    profile.affiliation_type = dict(institution_types)

    # detail_of_affiliation の作成
    profile.detail_of_affiliation = []
    for inst_id, inst in detail_of_affiliation.items():
        affiliation_entry = inst.copy()
        affiliation_entry['Years'] = sorted(affiliation_entry['Years'], reverse=True)
        profile.detail_of_affiliation.append(affiliation_entry)

    # 国別所属数の計算
    profile.country_affiliation_count = calculate_country_affiliation_count(profile.detail_of_affiliation)
    
    # past_affiliations の作成
    past_affiliations_list = []
    for aff in profile.detail_of_affiliation:
        inst_name = aff['Institution Name']
        years = ', '.join(map(str, aff['Years']))
        past_affiliations_list.append(f"{inst_name}: {years}")

    profile.past_affiliations = '\n'.join(past_affiliations_list)

    # 異なるフィールドからの被引用数を集計
    citation_counter = Counter()
    for work in author_work_data_list:
        citation_counter.update(work.cited_by_other_field)
    
    profile.total_cited_by_other_field = dict(citation_counter)

    # 名前の設定: 最も頻繁に出現する名前を 'name' に設定し、その他を 'alternate_name' に追加
    if name_counter:
        most_common_name, _ = name_counter.most_common(1)[0]
        profile.name = most_common_name
        # 重複を排除してリスト化
        profile.alternate_name = list(set(name_counter.keys()))

    # トピックの集計を関数に分割して実行
    aggregated_topics = aggregate_topics(profile.topics_detail)
    profile.topics_detail = aggregated_topics
    # overseas_period の計算を関数に分割して実行
    profile.overseas_period = calculate_overseas_period(profile.detail_of_affiliation)
    # career_years の計算を関数に分割して実行
    profile.career_years = calculate_career_years(profile.detail_of_affiliation)
     #キャリア最初の年
    profile.first_career_year = get_career_earliest_year(profile.detail_of_affiliation)
    # h_index の計算を関数に分割して実行
    profile.h_index = calculate_h_index(author_work_data_list)
    # 過去5年のh_index の計算を関数に分割して実行
    filtered_works = filter_works_within_years(author_work_data_list, 5)
    profile.last_5_year_h_index = calculate_h_index(filtered_works)
    # 過去10年のh_index の計算を関数に分割して実行
    filtered_works = filter_works_within_years(author_work_data_list, 10)
    profile.last_10_year_h_index = calculate_h_index(author_work_data_list)
    # I10 Index の計算を関数に分割して実行
    profile.i10_index = calculate_i10_index(author_work_data_list)
    # キーワードの集計処理を count_keywords 関数に委譲
    profile.each_keywords_count_dict = count_keywords(author_work_data_list)
    profile.keyword_count = sum(profile.each_keywords_count_dict.values())
    # 共著者の集計結果をプロファイルに設定
    profile.each_coauthor_count_dict = dict(coauthor_counter)
    #共著回数
    profile.co_authorship_count = sum(profile.each_coauthor_count_dict.values())
    # 辞書を値の大きい順にソート
    sorted_coauthor_dict = dict(sorted(profile.each_coauthor_count_dict.items(), key=lambda item: item[1], reverse=True))
    # ソートされた辞書を profile に再設定
    profile.each_coauthor_count_dict = sorted_coauthor_dict
    
    profile.coauthor_count = len(coauthor_counter)
    
    # 共著者の所属機関タイプのカウントをプロファイルに設定
    profile.coauthor_type_counter = dict(coauthor_type_counter)
    profile.coauthor_from_company_count = profile.coauthor_type_counter["company"] if "company" in profile.coauthor_type_counter else 0
    
    # ソースIDのカウント結果を、値が大きい順に並び替えてから辞書に変換する
    profile.each_source_id_count_dict = dict(sorted(source_id_counter.items(), key=lambda item: item[1], reverse=True))
    profile.source_id_count = len(source_id_counter)
    return profile

def calculate_country_affiliation_count(detail_of_affiliation: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    国別所属数を計算します。

    Args:
        detail_of_affiliation (List[Dict[str, Any]]): 所属機関の詳細情報リスト。

    Returns:
        Dict[str, int]: 国コードごとの所属機関数。
    """
    country_affiliation_count = {}
    for affiliation in detail_of_affiliation:
        country_code = affiliation.get("Country Code", "N/A")
        if country_code:  # 空でない場合のみ処理
            country_affiliation_count[country_code] = country_affiliation_count.get(country_code, 0) + 1

    return country_affiliation_count

def aggregate_topics(topics_detail: List[Any]) -> List[Dict[str, Any]]:
    """
    トピックの詳細リストを集計します。
    """
    topic_counter = defaultdict(int)
    topic_info = {}

    for topic in topics_detail:
        if isinstance(topic, dict):
            topic_id = topic.get('id')
            if topic_id:
                topic_counter[topic_id] += 1
                if topic_id not in topic_info:
                    topic_info[topic_id] = {
                        'Topic ID': topic_id,
                        'Display Name': topic.get('display_name', 'N/A'),
                        'Subfield': topic.get('subfield', {}).get('display_name', 'N/A'),
                        'Field': topic.get('field', {}).get('display_name', 'N/A'),
                        'Domain': topic.get('domain', {}).get('display_name', 'N/A')
                    }
        elif isinstance(topic, str):
            topic_counter[topic] += 1
            if topic not in topic_info:
                topic_info[topic] = {
                    'Topic ID': topic,
                    'Display Name': topic,
                    'Subfield': 'N/A',
                    'Field': 'N/A',
                    'Domain': 'N/A'
                }

    aggregated_topics = []
    for topic_id, count in topic_counter.items():
        info = topic_info[topic_id]
        aggregated_topic = {
            'Topic ID': info['Topic ID'],
            'Display Name': info['Display Name'],
            'Count': count,
            'Subfield': info['Subfield'],
            'Field': info['Field'],
            'Domain': info['Domain']
        }
        aggregated_topics.append(aggregated_topic)

    aggregated_topics.sort(key=lambda x: x['Count'], reverse=True)

    return aggregated_topics

def calculate_overseas_period(detail_of_affiliation: List[Dict[str, Any]]) -> int:
    """
    detail_of_affiliationから海外在籍年数を計算します。
    
    Args:
        detail_of_affiliation (List[Dict[str, Any]]): 所属機関の詳細情報リスト。
    
    Returns:
        int: 海外在籍年数の合計。
    """
    overseas_years = 0
    for affiliation in detail_of_affiliation:
        country_code = affiliation.get('Country Code', 'N/A')
        if country_code != 'JP':
            years = affiliation.get('Years', set())
            overseas_years += len(years)
    return overseas_years

def calculate_career_years(detail_of_affiliation: List[Dict[str, Any]]) -> int:
    """
    detail_of_affiliationからキャリア年数を計算します。
    
    Args:
        detail_of_affiliation (List[Dict[str, Any]]): 所属機関の詳細情報リスト。
    
    Returns:
        int: キャリア年数の合計。
    """
    all_years = set()
    for affiliation in detail_of_affiliation:
        years = affiliation.get('Years', set())
        all_years.update(years)
    
    if not all_years:
        return 0  # 年データがない場合は0年
    
    earliest_year = min(all_years)
    latest_year = max(all_years)
    
    career_years = latest_year - earliest_year + 1  # 包括的にカウント
    
    return career_years

def calculate_h_index(author_work_data_list: List[AuthorWorkData]) -> int:
    """
    H-Index を計算します。
    """
    if not author_work_data_list:
        return 0

    sorted_works = sorted(
        author_work_data_list,
        key=lambda x: x.total_citations if x.total_citations else 0,
        reverse=True
    )

    h_index = 0
    for rank, work in enumerate(sorted_works, start=1):
        citations = work.total_citations if work.total_citations else 0
        if rank <= citations:
            h_index = rank
        else:
            break

    return h_index

def calculate_i10_index(author_work_data_list: List[AuthorWorkData], citation_threshold: int = 10) -> int:
    """
    I10 Index を計算します。
    """
    if not author_work_data_list:
        return 0

    i10_count = sum(
        1 for work in author_work_data_list if (work.total_citations if work.total_citations else 0) >= citation_threshold
    )

    return i10_count

def count_names(author_work_data_list: List[AuthorWorkData]) -> Counter:
    """
    著者名の出現回数をカウントします。
    """
    name_counter = Counter()
    for work in author_work_data_list:
        author_name = work.name.strip()
        if author_name:
            name_counter[author_name] += 1
    return name_counter

def count_keywords(author_work_data_list: List[AuthorWorkData]) -> Dict[str, int]:
    """
    author_work_data_list から各キーワードの出現回数をカウントし、
    出現回数が多い順にソートされた辞書を生成します。
    
    Args:
        author_work_data_list (List[AuthorWorkData]): 著者の論文情報リスト。
        
    Returns:
        Dict[str, int]: 出現回数が多い順にソートされた各キーワードとその出現回数の辞書。
    """
    keywords_list = []
    
    for work in author_work_data_list:
        keywords = work.keywords  # AuthorWorkData の keywords 属性にアクセス
        
        if isinstance(keywords, list):
            for kw in keywords:
                if isinstance(kw, str):
                    keywords_list.append(kw.lower())  # 小文字化して追加
                elif isinstance(kw, dict):
                    # 辞書からキーワード文字列を抽出
                    keyword_str = kw.get('display_name') or kw.get('keyword')
                    if keyword_str and isinstance(keyword_str, str):
                        keywords_list.append(keyword_str.lower())  # 小文字化して追加
                    else:
                        print(f"Unexpected keyword format in author ID {work.author_id}: {kw}")
                else:
                    print(f"Unexpected keyword type in author ID {work.author_id}: {kw}")
        elif isinstance(keywords, str):
            keywords_list.append(keywords.lower())  # 小文字化して追加
        else:
            print(f"Unexpected format for Keywords in author ID {work.author_id}: {keywords}")
    
    # キーワードのカウント
    keyword_counter = Counter(keywords_list)
    
    # 出現回数が多い順にソートされたリストを取得
    sorted_keywords = keyword_counter.most_common()
    
    # ソートされたリストを辞書に変換
    sorted_keyword_dict = dict(sorted_keywords)
    
    return sorted_keyword_dict

def parse_publication_date(pub_date_str: str) -> datetime:
    """
    publication_dateの文字列をdatetimeオブジェクトに変換します。
    複数のフォーマットを試みます。
    """
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(pub_date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"未対応の日時形式: {pub_date_str}")

def filter_works_within_years(author_work_data_list: List[AuthorWorkData], years: int = 5) -> List[AuthorWorkData]:
    """
    最新の論文から指定された年数以内の論文のみを抽出します。
    月単位での精度を持ちます。

    Args:
        author_work_data_list (List[AuthorWorkData]): 著者の論文情報リスト。
        years (int, optional): フィルタリングする年数。デフォルトは5年。

    Returns:
        List[AuthorWorkData]: フィルタリングされた論文リスト。
    """
    if not author_work_data_list:
        return []

    # publication_dateが有効な論文のみを対象とする
    valid_works = [work for work in author_work_data_list if work.publication_date]
    
    if not valid_works:
        return []

    # publication_dateをdatetimeオブジェクトに変換し、最新の日付を取得
    try:
        latest_date = max(
            parse_publication_date(work.publication_date)
            for work in valid_works
        )
    except ValueError as ve:
        print(f"日付の解析中にエラーが発生しました: {ve}")
        return []

    # カットオフ日付を計算（指定年数を正確に遡る）
    cutoff_date = latest_date - relativedelta(years=years)

    # 指定年数以内の論文をフィルタリング
    filtered_works = []
    for work in author_work_data_list:
        pub_date_str = work.publication_date
        if not pub_date_str or not isinstance(pub_date_str, str):
            continue  # 無効な日付形式はスキップ

        try:
            pub_date = parse_publication_date(pub_date_str)
        except ValueError:
            print(f"無効な日付形式: {pub_date_str}（論文ID: {work.paper_id}）")
            continue  # 無効な日付形式はスキップ

        if pub_date >= cutoff_date:
            filtered_works.append(work)

    return filtered_works

# 最新の論文から所属機関と国コードを取得する関数を定義
def get_latest_affiliation_and_country(author_work_data_list: List[AuthorWorkData]):
    sorted_works = sorted(
        author_work_data_list,
        key=lambda x: (
            x.publication_year if x.publication_year else 0,
            x.publication_date if x.publication_date else ""
        ),
        reverse=True
    )
    
    latest_affiliation = latest_country = []
    for work in sorted_works:
        if work.affiliation:
            latest_affiliation = work.affiliation
            latest_country = work.country_codes
            break
    return latest_affiliation, latest_country


def get_first_affiliation_and_country(author_work_data_list: List[AuthorWorkData]):
    # 出版年および出版日の昇順（古い順）にソートする
    sorted_works = sorted(
        author_work_data_list,
        key=lambda x: (
            x.publication_year if x.publication_year else 0,
            x.publication_date if x.publication_date else ""
        )
    )
    
    institutions = []
    # ソートされたリストの先頭から所属機関情報がある論文を探す
    for work in sorted_works:
        if work.affiliation:
            institutions = work.institutions
            break
    
    return institutions

def get_career_earliest_year(detail_of_affiliation: List[Dict[str, Any]]) -> int:
        """
        institutions: 各辞書は 'Years' キーに年のリストを持つ
        すべての 'Years' の中で最も古い年を返す
        """
        earliest = float('inf')
        for inst in detail_of_affiliation:
            years = inst.get("Years", [])
            if years:
                # 現在の辞書内の最小の年を取得
                min_year = min(years)
                if min_year < earliest:
                    earliest = min_year
        # 該当する年がない場合は None を返す（ここでは int を返すことを前提）
        return earliest if earliest != float('inf') else None

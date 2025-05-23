from dataclasses import dataclass, field, asdict
from typing import Any, List, Dict, Optional, Union

@dataclass
class AuthorProfileData:
    # 研究者ID
    author_id: str = ""  # 研究者の一意の識別子
    # 研究者名
    name: str = ""  # メインの名前
    # 研究者名（別名）
    alternate_name: List[str] = field(default_factory=list)  # 別名のリスト
    # 最新の国
    latest_country: List[str] = field(default_factory=list)  # 所属が確認された最新の国のリスト
    # 最新の所属機関
    latest_affiliation: List[str] = field(default_factory=list)  # 所属が確認された最新の機関のリスト
    # 過去の所属機関
    past_affiliations: str = ""  # 過去に所属していた機関の詳細
    # 所属機関の詳細
    detail_of_affiliation: List[Dict[str, Any]] = field(default_factory=list)  # 所属機関に関する詳細情報のリスト
    #最初の所属機関
    career_first_affiliation: List[Dict[str, Any]] = field(default_factory=list)  
    #キャリア最初の年
    first_career_year:int=0
    # 所属タイプ
    affiliation_type: Dict[str, int] = field(default_factory=dict)  # 所属のタイプとその説明
    # 教育以外の所属機関数
    non_education_affiliation_count: int = 0  # 教育機関以外の所属機関の数
    # 国別所属数
    country_affiliation_count: Dict[str, int] = field(default_factory=dict)  # 国ごとの所属機関数
    # 海外にいる期間
    overseas_period: int = 0  # 研究者が海外にいた年数
    # キャリア年数
    career_years: int = 0  # 研究者としてのキャリア年数
    # Works数
    works_count: int = 0  # 発表した研究成果（Works）の総数
    # 全てのWorksの被引用数
    total_works_citations: int = 0  # 全Worksの被引用数の合計
    #H-Index-global-ranking
    h_index_ranking: int =0
    #（ランキングの）研究者数の総数
    all_author_count:int=0
    # H-Index
    h_index: int = 0 # H-Index（被引用数と論文数のバランスを示す指標）
    #過去５年のH-Index
    last_5_year_h_index: int = 0
    #過去10年のH-Index
    last_10_year_h_index: int = 0
    # I10 Index
    i10_index: int = 0  # 10回以上引用された論文の数
    # Topicsの詳細
    topics_detail: List[Dict[str, Any]] = field(default_factory=list)  # 研究テーマの詳細リスト
    #キーワード数
    keyword_count: int = 0  # キーワードの総数
    #キーワードの詳細
    each_keywords_count_dict: Dict[str, int] = field(default_factory=dict)  # 各キーワードの出現回数
    #共著者数
    coauthor_count:int = 0
    #共著回数
    co_authorship_count:int = 0
    #共著者の詳細
    each_coauthor_count_dict: Dict[str, int] = field(default_factory=dict)
    # 共著者の所属機関タイプのカウント
    coauthor_type_counter: Dict[str, int] = field(default_factory=dict)  # 共著者の所属タイプごとのカウント
    #企業との共著の数
    coauthor_from_company_count:int = 0
    #fastの論文数
    first_paper_count: int = 0
    #対応論文数
    corresponding_paper_count: int = 0  # 対応論文数
    #DIが0.9以上のworks数
    disruption_index_above_09: int = 0
    #DIが0.8以上のworks数
    disruption_index_above_08: int = 0
    #DIが0.7以上のworks数
    disruption_index_above_07: int = 0
    #DIが0.6以上のworks数
    disruption_index_above_06: int = 0
    #DIが0.5以上のworks数
    disruption_index_above_05: int = 0
    #DIが0.4以上のworks数
    disruption_index_above_04: int = 0
    #DIが0.3以上のworks数
    disruption_index_above_03: int = 0
    
    #異なるフィールドからの被引用数
    total_cited_by_other_field: Dict[str, int] = field(default_factory=dict)
    #インパクト指数
    total_impact_index: float = -0.0  # impact指数の合計
    #type_crossref
    article_type_crossref_dict: Dict[str, int] = field(default_factory=dict)  # CrossRefタイプごとのデータ
    #type
    article_type_dict: Dict[str, int] = field(default_factory=dict)  # 論文typeのデータ
    # ソースIDの集計
    each_source_id_count_dict: Dict[str, int] = field(default_factory=dict)  # ソースIDごとの出現回数
    # ユニークなソースIDの数
    source_id_count: int = 0 
    #論文情報を入れる
    papers_info: List[Dict[str, Any]] = field(default_factory=list)


    def to_dict(self) -> Dict:
        """Convert the data class to a dictionary."""
        return asdict(self)
    
    def to_flat_dict(self) -> Dict[str, Any]:
        """
        このクラスを辞書に変換し、辞書型のフィールドを再帰的にフラット化します。
        フラット化は辞書型フィールドに対してのみ行い、その場で展開します。
        順序を変更せず、フィールドの元の順序を保ちながらフラット化します。
        """
        def flatten_dict(d: Dict[str, Any], parent_key: str = '') -> Dict[str, Any]:
            items = []
            for k, v in d.items():
                new_key = f"{parent_key}_{k}" if parent_key else k
                if isinstance(v, dict):
                    # 再帰的に辞書をフラット化
                    items.extend(flatten_dict(v, new_key).items())
                else:
                    items.append((new_key, v))
            return dict(items)
        
        original_dict = asdict(self)
        flat_dict = {}
        
        for key, value in original_dict.items():
            if isinstance(value, dict):
                # 辞書型の場合、フラット化してその場で展開
                flat_dict.update(flatten_dict(value, key))
            else:
                # その他の型の場合、そのまま追加
                flat_dict[key] = value
        
        return flat_dict

    
@dataclass
class AuthorWorkData:
    # 論文ID
    paper_id: str = ""  # 論文の一意の識別子
    #論文タイトル
    paper_title:str =""
    # 著者名ID
    author_id: str = ""
    # 著者名
    name: str = ""  # 著者名
    # 所属
    affiliation: str = ""  # 論文の所属機関
    # 所属機関の詳細情報
    institutions: List[Dict[str, Any]] = field(default_factory=list)  # 所属機関の詳細情報
    # 国コード
    country_codes: str = ""  # 論文の国コード
    # 責任著者
    corresponding_author: bool = False  # 責任著者であるかどうか
    # ポジション
    position: str = ""  # 著者のポジション
    # 責任著者名
    corresponding_author_name: List[str] = field(default_factory=list)  # 責任著者の名前リスト
    # 引用数
    citations: int = 0  # 引用数
    # 被引用数
    total_citations: int = 0  # 被引用数
    #各fieldの被引用数
    cited_by_other_field: Dict[str, int] = field(default_factory=dict)
    # D-index
    d_index: float = -200.0  # D-index
    # Impact指数
    impact_index: float = -200.0  # Impact指数
    # 主題
    primary_topic: str = ""  # 主な研究テーマ
    # トピック
    topics: List[Dict[str, Any]] = field(default_factory=list)  # トピックリスト
    # 出版年
    publication_year: int = 0  # 出版年
    # 出版日
    publication_date: str = ""  # 出版日
    # Landing Page URL
    landing_page_url: str = ""  # ランディングページのURL
    # 著者リスト
    authors: str = ""  # 著者リスト
    #共著者情報の詳細
    authors_info: List[Dict[str, Any]] = field(default_factory=list)
    # キーワード
    keywords: List[Dict[str, Any]] = field(default_factory=list)  # キーワードリスト
    # 助成金
    grants: List[Dict[str, Any]] = field(default_factory=list)  # 助成金情報
    # ソースID
    source_id: str = ""  # ジャーナルの一意の識別子
    
    # 共著者情報
    #coauthors_info: List['AuthorWorkData'] = field(default_factory=list)  # 空のリストを初期値に設定

    def to_dict(self) -> Dict:
        """Convert the data class to a dictionary."""
        return asdict(self)


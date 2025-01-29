from dataclasses import dataclass, field, asdict
from typing import Any, List, Dict, Optional, Union

@dataclass
class AuthorProfileData:
    # 研究者ID
    researcher_id: str = ""  # 研究者の一意の識別子
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
    # H-Index
    h_index: int = 0 # H-Index（被引用数と論文数のバランスを示す指標）
    #過去５年のH-Index
    last_5_year_h_index: int = 0
    #過去10年のH-Index
    last_10_year_h_index: int = 0
    # 過去2年間の平均被引用数
    two_year_mean_citedness: float = 0.0  # 過去2年間の平均被引用数
    # I10 Index
    i10_index: int = 0  # 10回以上引用された論文の数
    # 年次の被引用数
    annual_citation_count: List[int] = field(default_factory=list)  # 各年ごとの被引用数
    # 年次の被引用数の伸び率
    annual_citation_growth_rate: Dict[str, int] = field(default_factory=dict)
    # Topicsの詳細
    topics_detail: List[Dict[str, Any]] = field(default_factory=list)  # 研究テーマの詳細リスト
    #キーワード数
    keyword_count: int = 0  # キーワードの総数
    #キーワードの詳細
    each_keywords_count_dict: Dict[str, int] = field(default_factory=dict)  # 各キーワードの出現回数
    #共著者数
    coauthor_count:int = 0
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
    source_id_count: int = 0  # ユニークなソースIDの数

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
class WorkData:
    # 論文ID: 論文の一意の識別子
    paper_id: str = ''
    # タイトル: 論文のタイトル
    title: str = ''
    # 出版年: 論文の出版年
    publication_year: str = ''
    # 出版日: 論文の出版日（YYYY-MM-DD形式）
    publication_date: str = ''
    # ランディングページURL: 論文のランディングページのURL
    landing_page_url: str = ''
    # 著者: 論文の著者情報（名前のリスト形式）
    authors: str = ''
    # 著者情報: 著者に関する詳細情報のリスト
    authors_info: List[Dict] = field(default_factory=list)
    # 主題: 論文の主な研究テーマ
    primary_topic: str = ''
    # トピック: 論文に関連するトピックのリスト
    topics: List[Dict] = field(default_factory=list)
    # キーワード: 論文に関連するキーワードのリスト
    keywords: List[Dict] = field(default_factory=list)
    # 引用数: 論文が他の文献で引用された回数
    referenced_citation_count: int = 0
    # 被引用数: 論文に関連して他の文献で引用された総数
    cited_by_count: int = 0
    #fwci
    fwci = int = 0

    # 所属: 著者の所属機関
    affiliation: str = ''
    # 国コード: 所属機関の国コード
    country_codes: str = ''
    # 責任著者: 責任著者であるかどうか（True/False）
    corresponding_author: bool = False
    # ポジション: 著者の論文内でのポジション（例: First, Last, Middle）
    position: str = ''
    # 責任著者名: 責任著者の名前リスト
    corresponding_author_names: List[str] = field(default_factory=list)
    

    # D-index: Disruption Index（論文の影響の新規性を評価する指標）
    d_index: float = 0.0
    # Impact指数: 論文のインパクトを示す指標
    impact_index: float = 0.0


    # 助成金: 論文に関連する助成金情報のリスト
    grants: List[Dict] = field(default_factory=list)
    
    
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

    
@dataclass
class ResearcherData:
    # 研究者ID
    researcher_id: str = ""  # 研究者の一意の識別子
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
    # 所属タイプ
    affiliation_type: Dict[str, str] = field(default_factory=dict) # 所属のタイプとその説明  
    
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
    # H-Index
    h_index: int = 0  # H-Index（被引用数と論文数のバランスを示す指標）
    # 過去2年間の平均被引用数
    two_year_mean_citedness: float = 0.0  # 過去2年間の平均被引用数
    # I10 Index
    i10_index: int = 0  # 10回以上引用された論文の数
    # 年次の被引用数
    annual_citation_count: List[int] = field(default_factory=list)  # 各年ごとの被引用数
    # 年次の被引用数の伸び率
    annual_citation_growth_rate: str = ""  # 被引用数の年次ごとの成長率（例：+10%、-5%）
    # Topicsの詳細
    topics_detail: List[str] = field(default_factory=list)  # 研究テーマの詳細リスト
    # キーワードの数（非引用数が20以上）
    keyword_count_above_20_citations: int = 0  # 非引用数が20以上のキーワード数
    # 指定条件で見つかった論文のキーワード
    specified_keywords: str = ""  # 指定条件で見つかった論文のキーワード
    # 指定条件で見つかった論文数
    specified_paper_count: int = 0  # 指定条件で該当する論文の数
    # 論文ID
    no1_paper_id: str = ""  # 論文1のID
    # 論文名
    no1_paper_name: str = ""  # 論文1の名前
    # 所属
    no1_affiliation: str = ""  # 論文1の所属機関
    # 国コード
    no1_country_codes: str = ""  # 論文1の国コード
    # 責任著者
    no1_corresponding_author: bool = False  # 論文1で責任著者であるか
    # 責任著者の名前
    no1_corresponding_author_name: List[str] = field(default_factory=list)  # 責任著者の名前リスト
    # 引用数
    no1_citations: int = 0  # 論文1の引用数
    # 被引用数
    no1_total_citations: int = 0  # 論文1の被引用数
    # D-index
    no1_d_index: int = 0  # 論文1のD-index
    # Impact指数
    no1_impact_index: float = 0.0  # 論文1のImpact指数
    # 主題
    no1_primary_topic: str = ""  # 論文1の主題
    # トピック
    no1_topics: List[str] = field(default_factory=list)  # 論文1のトピックリスト
    # 出版年
    no1_publication_year: int = 0  # 論文1の出版年
    # 出版日
    no1_publication_date: str = ""  # 論文1の出版日
    # Landing Page URL
    no1_landing_page_url: str = ""  # 論文1のURL
    # 著者リスト
    no1_authors: str = ""  # 論文1の著者リスト
    # キーワード
    no1_keywords: str = ""  # 論文1のキーワード
    # Grants
    no1_grants: List[str] = field(default_factory=list)  # 論文1の助成金情報

    def to_dict(self) -> Dict:
        """Convert the data class to a dictionary."""
        return asdict(self)

    # 他の論文情報（no2, no3）も同様に定義可能

if __name__ == "__main__":
    # テスト用インスタンス作成
    researcher = ResearcherData(
        researcher_id="R12345",
        name="John Doe",
        latest_country=["USA"],
        career_years=10,
        total_works_citations=500
    )
    print(researcher)
import sys
import os
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))
from utils.common_method import extract_id_from_url
from services.gather_authors_data import GatherAuthorData

class GetAuthorJsonData:
    
    def __init__(self,author_id,found_date,use_api_key=False):
        if extract_id_from_url(author_id) in ["A9999999999"]:
            raise ValueError(f"GatherAuthorDataに不当なauthor_idが渡されました。{self.id}")
        self.author_id = extract_id_from_url(author_id)
        self.found_date = found_date
        self.use_api_key = use_api_key
        
        
    
    def run():
        GatherAuthorData()
        
        
        
        
        """
        
        必要なデータ
        ・author_id
        ・name
        
        
        論文リスト
        ・alternate_name
        ・
        
        
        """
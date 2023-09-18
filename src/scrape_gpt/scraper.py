import requests
from scrape_gpt.parser import SelectolaxParser
from typing import List, Dict, Tuple, Union, Optional
from transformers import BertTokenizerFast, BertModel
import torch


class LlmScraper():
    
    def __init__(self, 
                 url: str, 
                 parser: str="selectolax", 
                 load_retrieval_model: bool=True, 
                 model_name: str="BAAI/bge-large-en-v1.5",
                 hf_cache_dir: Optional[str]=None,
                 device_map: Optional[Union[int, str, torch.device, Dict[str, Union[int, str, torch.device]]]]=None,
                 model: Optional[BertModel]=None,
                 tokenizer: Optional[BertTokenizerFast]=None,
                 ):
        self.url = url
        self.html = self.fetch_html(self.url)
        self.parser = self.get_parser(parser)
        self.model = model
        self.tokenizer = tokenizer
        self.hf_cache_dir = hf_cache_dir

        if device_map and (isinstance(device_map, int) or isinstance(device_map, torch.device)):
            device_map = {"": device_map}

        if load_retrieval_model:
            self.init_retrieval_model(model_name, 
                                      device_map,
                                      init_tokenizer=self.tokenizer is None, 
                                      init_model=self.model is None)
        elif model is not None:
            self.device = model.device
        else:
            self.device = None
        
                
                


    def fetch_html(self, url: str) -> str:
        return requests.get(url).text
    

    def init_retrieval_model(self, 
                             model_name: str, 
                             device_map: Optional[Union[int, str, torch.device, Dict[str, Union[int, str, torch.device]]]]=None, 
                             hf_cache_dir: Optional[str]=None,
                             init_tokenizer: bool=True, 
                             init_model: bool=True) -> None:
        if init_tokenizer:
            self.tokenizer = BertTokenizerFast.from_pretrained(model_name, cache_dir=hf_cache_dir)
        if init_model:
            self.model = BertModel.from_pretrained(model_name, cache_dir=hf_cache_dir, device_map=device_map)
        self.device = self.model.device
        
    

    def get_parser(self, parser: str = "selectolax"):
        if parser == "selectolax":
            return SelectolaxParser(self.url)
        else:
            raise NotImplementedError(f"Parser {parser} not implemented yet.")

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
        
    def _retrieval_format(self, instruction: str, texts: List[str]) -> List[str]:
        return [f"{instruction} {text}" for text in texts]
    
    def text_retrieval(self,
                        queries: List[str], 
                        corpus: List[str], 
                        top_k: Optional[int]=None,
                        query_instruction: str="retrieve similar", 
    
                        only_cosine: bool=False) -> List[List[Tuple[str, float]]]:
        formatted_queries = self._retrieval_format(query_instruction, queries)

        tok_inputs = self.tokenizer(formatted_queries + corpus, padding=True, truncation=True, return_tensors="pt")
        with torch.no_grad():
            all_vecs = self.model(**tok_inputs.to(self.device))


        sentence_embeddings = all_vecs[0][:, 0]
        sentence_embeddings = torch.nn.functional.normalize(sentence_embeddings, p=2, dim=-1)

        query_vecs = sentence_embeddings[:len(formatted_queries)]
        corpus_vecs = sentence_embeddings[len(formatted_queries):]

        cosine_scores = query_vecs @ corpus_vecs.T



        if top_k is not None:
            cosine_scores = cosine_scores.topk(top_k, dim=-1)

        if only_cosine:
            return cosine_scores
        

        final_results = []
        for i, query in enumerate(queries):
            if top_k is None:
                results = list(zip(corpus, cosine_scores[i]))
            else:
                results = []
                for j, idx in enumerate(cosine_scores.indices[i]):
                    results.append((corpus[idx], cosine_scores.values[i][j]))


            final_results.append((query, results))


        return final_results



    def get_parser(self, parser: str = "selectolax"):
        if parser == "selectolax":
            return SelectolaxParser(self.html)
        else:
            raise NotImplementedError(f"Parser {parser} not implemented yet.")

from dataclasses import dataclass
import yaml
import tldextract
from urllib.parse import urlparse


def iter_llm_info(llm_info):
    for info in llm_info:
        if isinstance(info, list):
            yield from iter_llm_info(info)
        elif isinstance(info, tuple):
            yield info

def get_llm_keys(llm_info):
    key_names = set()
    
    for info in llm_info:
        key_names.update(list(info[1].keys()))

    return key_names

def to_key_string(llm_info):
    key_string = ""
    key_names = get_llm_keys(llm_info)
    key_string = ",".join(key_names)
    return key_string


def to_llm_string(llm_info):
    llm_string = ""
    key_string = to_key_string(llm_info)
    llm_string += key_string + "\n"
    for path, info in llm_info:
        row = path
        values_string = ",".join(list(info.values()))
        row += f": {values_string}"
        llm_string += row + "\n"
    return llm_string

def format_path(paths):
    return ".".join(paths)






def get_yaml_from_dict(d):
    return yaml.dump(d)


class DictIterableMixin:
    def as_dict(self):
        return self.__dict__

    def __iter__(self):
        return iter(self.as_dict().items())

class LlmDictMixin(DictIterableMixin):
    def get_llm_dict(self, ignored_info = []):
        return {k:v for k,v in self.__iter__() if k not in ignored_info and v}
    

@dataclass
class EntryInfo(LlmDictMixin):
    content_label: str
    target: str
    target_method: str # maybe enum
    description: str = None
    # steps is optional
    steps: list = None
    note: str = None

    def __str__(self):
        return f'{self.content_label}'

    def __repr__(self):
        return f'{self.content_label}'

    
    
    def get_llm_view(self, ignored_info = []):
        
        # return llm self.info with ignored_info removed
        return get_yaml_from_dict(self.get_llm_dict(ignored_info))

class SiteMapEntry(DictIterableMixin):
    # not sure if it is worth inherting here or just use 1 class LlmDictMixin for EntryInfo and SiteMap.
    # SiteMapEntry not inherit from anything
    def __init__(self, entry_info, parent = None, parent_path = "", main_method = None, entry_methods=[], sub_target_info = []):
        self.info = entry_info
        self.parent = parent
        self.parent_path = parent_path
        self.sub_target_info = sub_target_info
        self.main_method = main_method
        self.entry_methods = entry_methods
        self.children = []


    def __str__(self):
        return f'{self.info}'

    def __repr__(self):
        return f'{self.info}'
    

    def add_child(self, child):
        self.children.append(child)

    def add_parent(self, parent, parent_path):
        self.parent = parent
        self.parent_path = parent_path

    def create_child(self, child_info, main_method = None, entry_methods = [], sub_target_info = []):
        child = SiteMapEntry(child_info, self, self.parent_path, main_method, entry_methods, sub_target_info)
        self.add_child(child)
        return child
    
    def get_llm_dict(self, ignored_info = []):
        pass

    def get_llm_internal(self, ignored_info = [],  include_children = False, include_sub_targets = False):
        final_data = []
        main_llm_dict = self.info.get_llm_dict(ignored_info)
        label_path = format_path([self.parent_path, self.info.content_label])
        final_data.append((label_path, main_llm_dict))

        if include_sub_targets:
            sub_llm_dicts = []
            for sub_info in self.sub_target_info:
                sub_label_path = format_path([label_path, sub_info.content_label])
                sub_llm_dicts.append((sub_label_path, sub_info.get_llm_dict(ignored_info)))

            final_data.extend(sub_llm_dicts)
        
        if include_children:
            child_llm_dicts = []
            for child in self.children:
                child_llm_dicts.extend(child.get_llm_internal(ignored_info, include_children, include_sub_targets))
            
            final_data.extend(child_llm_dicts)

        return final_data
    
    def get_llm_view(self, ignored_info = [],  include_children = False, include_sub_targets = False):
        
        # return llm self.info with ignored_info removed

        llm_info = self.get_llm_internal(ignored_info, include_children, include_sub_targets)
        print(llm_info)
        llm_string = to_llm_string(llm_info)

        return llm_string



class SiteMap(LlmDictMixin):
    def __init__(self, url, domain_url = None, subdomain_url = None, page_url_template = None, description=None,  path = "root", auto_url_info = True):
        self.url = url
        self.path = path
        self.description = description

        if auto_url_info:
            url_info = tldextract.extract(url)
            parsed_url = urlparse(url)
            if not domain_url:
                domain_url = f'{url_info.domain}.{url_info.suffix}'
            if not subdomain_url:
                subdomain_url = parsed_url.netloc
            if not page_url_template:
                parsed_path = parsed_url.path
                if parsed_path:
                    if parsed_path[-1] == "/":
                        parsed_path = parsed_path[:-1]

                    split_path = parsed_path.split("/")
                    split_path = [path for path in split_path if path]
                    if not split_path:
                        page_url_template = parsed_url.netloc
                    if len(split_path) > 1:
                        page_url_template = f'{parsed_url.netloc}/{split_path[:-1]}'
                    else:
                        page_url_template = f'{parsed_url.netloc}/{split_path[0]}'
                else:
                    page_url_template = parsed_url.netloc

        self.domain_url = domain_url
        self.subdomain_url = subdomain_url
        self.page_url_template = page_url_template
        self.entries = []

    
    def add_entry(self, entry):
        self.entries.append(entry)

    
    def create_entry(self, entry_info = None, label = None, target = None, method = None, description = None, steps = None):
        if entry_info:
            new_entry = SiteMapEntry(entry_info, parent=self, parent_path=self.path)
        else:
            info = EntryInfo(label, target, method, description, steps)
            new_entry = SiteMapEntry(info, parent=self, parent_path=self.path)
        self.add_entry(new_entry)
        return new_entry
    

    def get_llm_view(self,  ignored_site_info = [], ignore_url_info = False, include_children = False, include_sub_targets = False, ignored_info = []):
        llm_info = []
        llm_string = ""
        if ignore_url_info:
            ignored_site_info.extend(["url", "domain_url", "subdomain_url", "page_url_template"])

        site_info = ""
        site_info_dict = self.get_llm_dict(ignored_site_info)
        if site_info_dict:
            site_info = get_yaml_from_dict(site_info_dict)
        
        llm_string += site_info
        
        for entry in self.entries:
            llm_info.extend(entry.get_llm_internal(ignored_info, include_children, include_sub_targets))
        
        if llm_info:
            llm_string += to_llm_string(llm_info)
        return llm_string


    def __str__(self):
        return f"SiteMap for {self.url} with {len(self.entries)} entries"
    
    def __repr__(self):
        return f"SiteMap({self.url})"
    


class EntryMethod():
    def __init__(self, method_name, method, code = None):
        self.method_name = method_name
        self.method = method
        self.code = code

    def __str__(self):
        return f'{self.method_name}'

    def __repr__(self):
        return f'{self.method_name}'
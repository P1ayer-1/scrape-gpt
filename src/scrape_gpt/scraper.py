import requests
from selectolax.parser import HTMLParser

header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

class LlmScraper():
    def __init__(self, url):
        self.url = url
        self.html = self.fetch_html(self.url)
        self.tree = HTMLParser(self.html)
        self.remove_unwanted_nodes()

        
    
    def fetch_html(self, url):
        return requests.get(url).text
    
    def remove_unwanted_nodes(self):
        tags = ["script", "style"]
        self.parser.strip_tags(tags, recursive=True)

        nodes_to_remove = []
        for node in self.tree.root.traverse(include_text=True):
            tag = node.tag
            if tag == '-text' and not node.text_content.strip():
                nodes_to_remove.append(node)

            if tag == '_comment':
                nodes_to_remove.append(node)
        
        for node in nodes_to_remove:
            node.decompose(recursive=False)

    
    def get_media_paths(self, node, path="", return_text=True, return_images=True):
        texts = []
        images = []
        for child in node.iter(include_text=True):
            tag = child.tag
            new_path = f"{path}.{tag}" if child.tag else path
            if child.text_content:
                texts.append((new_path, len(child.text_content.strip())))
            if tag == "img":
                images.append((new_path, child.attributes["src"]))
            if tag == "svg":
                path_tags = child.css("path")
                svg_data = []
                for path_tag in path_tags:
                    svg_data.append(path_tag.attributes["d"])
                
                images.append((new_path, svg_data))

            new_results, imgs = self.get_media_paths(child, new_path, return_text, return_images)
            if new_results and return_text:
                texts.extend(new_results)
            if imgs and return_images:
                images.extend(imgs)
        return texts, images
    

    def count_all_nodes(self):
        node_count = 0
        text_count = 0
        for node in self.tree.root.traverse(include_text=True):
            node_count += 1
            if node.tag == '-text':
                text_count += 1
        return node_count, text_count
    


    def traverse_partial_tree(self, start_node, end_node = None, include_text=True, include_self=True):
        if include_self:
            yield start_node
        
        for node in start_node.traverse(include_text=include_text):
            if end_node and node == end_node:
                break
            yield node


    def count_child_nodes(self, start_node):
        node_count = 0
        text_count = 0
        for node in start_node.traverse_children(include_text=True):
            node_count += 1
            if node.tag == '-text':
                text_count += 1
        return node_count, text_count
    

    def get_headings(self, start_node):
        heading_nodes = []
        heading_text = []
        for node in start_node.traverse_children(include_text=True):
            if node.tag in header_tags:
                text = node.text().strip()
                heading_text.append(text)
                heading_nodes.append(node)
        return heading_nodes, heading_text
    

    def get_links(self, start_node, end_node = None, include_self=True, ignore_fragments=True):
        link_nodes = []
        links = []
        for node in self.traverse_partial_tree(start_node, end_node=end_node, include_text=False, include_self=include_self):
            if node.tag == "a":
                link = node.attributes["href"]
                if ignore_fragments and link.startswith('#'):
                    continue
                links.append(link)
                link_nodes.append(node)

                
        return links
    
    def traverse_text_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        for node in self.traverse_partial_tree(start_node, end_node=end_node, include_text=True, include_self=include_self):
            if node.tag == '-text':
                if node in ignore_nodes:
                    continue
                yield node
        
    def get_text_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        return [node for node in self.traverse_text_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes)]
    

    def get_text_lens(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        text_lens = []
        for node in self.traverse_text_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes):
            text_lens.append(len(node.text().strip()))
        return text_lens
    

    def handle_text_len(self, texts, max_len = 75, trancute=False): # should be in tokens eventually
        new_texts = []
        for text in texts:
            text_len = len(text)

            if text_len > max_len:
                if trancute:
                    text = text[:max_len]
                else:
                    text = text_len
            

            new_texts.append(text)
        return new_texts

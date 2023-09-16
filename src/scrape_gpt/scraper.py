import requests
from selectolax.parser import HTMLParser

class LlmScraper():
    def __init__(self, url):
        self.url = url
        self.html = self.fetch_html()
        self.parser = HTMLParser(self.html)
        self.remove_unwanted_nodes()

        
    
    def fetch_html(self):
        return requests.get(self.url).text
    
    def remove_unwanted_nodes(self):
        tags = ["script", "style"]
        self.parser.strip_tags(tags, recursive=True)

        nodes_to_remove = []
        for node in self.parser.root.traverse(include_text=True):
            tag = node.tag
            if tag == '-text' and not node.text_content.strip():
                nodes_to_remove.append(node)

            if tag == '_comment':
                nodes_to_remove.append(node)
        
        for node in nodes_to_remove:
            node.decompose(recursive=False)

    
    def traverse_nodes(self, node, path="", return_text=True, return_images=True):
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

            new_results, imgs = self.traverse_nodes(child, new_path, return_text, return_images)
            if new_results and return_text:
                texts.extend(new_results)
            if imgs and return_images:
                images.extend(imgs)
        return texts, images
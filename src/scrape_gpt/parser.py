import requests
from selectolax.parser import HTMLParser

header_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

class SelectolaxParser():
    def __init__(self, html):
        self.tree = HTMLParser(html)
        self.remove_unwanted_nodes()

        
    

    
    def remove_unwanted_nodes(self):
        tags = ["script", "style"]
        self.tree.strip_tags(tags, recursive=True)

        nodes_to_remove = []
        for node in self.tree.root.traverse(include_text=True):
            tag = node.tag
            if tag == '-text' and not node.text_content.strip():
                nodes_to_remove.append(node)

            if tag == '_comment':
                nodes_to_remove.append(node)
        
        for node in nodes_to_remove:
            node.decompose(recursive=False)
    

    def count_all_nodes(self):
        node_count = 0
        text_count = 0
        for node in self.tree.root.traverse(include_text=True):
            node_count += 1
            if node.tag == '-text':
                text_count += 1
        return node_count, text_count
    

    def conditional_traverse(self, start_node, end_node=None, include_text=False, include_self=True, tag_conditions=[], ignore_tags=[], ignore_nodes=[], children_only=False):
        if children_only:
            traverse_func = start_node.traverse_children
        else:
            traverse_func = start_node.traverse
        if include_self and start_node.tag in ignore_tags and start_node not in ignore_nodes:
            yield start_node
        for node in traverse_func(include_text):
            if end_node and node == end_node:
                break
            tag = node.tag
            if node not in ignore_nodes and tag not in ignore_tags:
                if not tag_conditions:
                    yield node
                    continue
                if tag_conditions and tag in tag_conditions:
                    yield node
    
    def filtered_traverse(self, start_node, filter_func, end_node=None, include_self=True, tag_conditions=[], ignore_tags=[], ignore_nodes=[], children_only=False):

        for node in self.conditional_traverse(start_node, end_node=end_node, include_text=True,
                                              include_self=include_self, tag_conditions=tag_conditions, 
                                              ignore_nodes=ignore_nodes, children_only=children_only):
            if filter_func(node):
                yield node
    

    def traverse_partial_tree(self, start_node, end_node = None, include_text=True, include_self=True):
        # keeping the function because I am unsure if llm will find it easier to use purpose made functions 
        # or the more generic ones and pass args
        yield from self.conditional_traverse(start_node, end_node=end_node, include_text=include_text, include_self=include_self,tag_conditions=[],  ignore_tags=[], ignore_nodes=[])

    def traverse_partial_child_tree(self, start_node, end_node = None, include_text=True, include_self=True):
        yield from self.conditional_traverse(start_node, end_node=end_node, include_text=include_text, include_self=include_self, tag_conditions=[], ignore_tags=[], ignore_nodes=[], children_only=True)


    def traverse_text_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        tag_conditions = ["-text"]
        yield from self.conditional_traverse(start_node, 
                                             end_node=end_node, 
                                             include_text=True, 
                                             include_self=include_self, 
                                             tag_conditions=tag_conditions, 
                                             ignore_tags=[], 
                                             ignore_nodes=ignore_nodes)

    def traverse_text_child_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        tag_conditions = ["-text"]
        yield from self.conditional_traverse(start_node, 
                                        end_node=end_node, 
                                        include_text=True, 
                                        include_self=include_self, 
                                        tag_conditions=tag_conditions, 
                                        ignore_tags=[], 
                                        ignore_nodes=ignore_nodes,
                                        children_only=True)

    
    def _media_filter(self, node, ignore_nodes, headings_as_text):
        if node in ignore_nodes:
            return False
        if not headings_as_text and node.tag in header_tags:
            return True  # assuming that the subsequent next_node handling logic will be handled elsewhere
        return node.tag in ["img", "svg", "-text"]
    
    def check_parent(self, node, check_nodes = [], tags = [], ignore_tags = True):
        while node.parent:
            parent = node.parent
            if parent in check_nodes:
                return True
            if ignore_tags ^ (parent.tag in tags):
                return True
            node = parent
        return False

    def traverse_media_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[], headings_as_text=False, children_only=False):
            tag_conditions = ["img", "svg", "-text"]
            if not headings_as_text:
                tag_conditions.extend(header_tags)

            def filter_function(node):
                return not self.check_parent(node, tags=header_tags, ignore_tags=False)  # Check if node doesn't have a parent with a header tag
            
            yield from self.filtered_traverse(start_node,
                                                filter_function,
                                                end_node=end_node, 
                                                include_self=include_self, 
                                                tag_conditions=tag_conditions, 
                                                ignore_tags=[], 
                                                ignore_nodes=ignore_nodes,
                                                children_only=children_only)



    def count_child_nodes(self, start_node):
        node_count = 0
        text_count = 0
        for node in start_node.traverse_children(include_text=True):
            node_count += 1
            if node.tag == '-text':
                text_count += 1
        return node_count, text_count
    

    def get_headings(self, start_node, end_node=None, include_self=True, children_only=False):
        heading_nodes = []
        heading_text = []
        gen = self.conditional_traverse(start_node,end_node, include_text=False, include_self=include_self, tag_conditions=header_tags, children_only=children_only)
        for node in gen(include_text=True):
            text = node.text().strip()
            heading_text.append(text)
            heading_nodes.append(node)
        return heading_nodes, heading_text
    

    def extract_link(self, node, ignore_fragments=True):
        link = node.attributes["href"]
        if ignore_fragments and link.startswith('#'):
            return None
        return link

    def get_links(self, start_node, end_node = None, include_self=True, children_only=False, ignore_fragments=True):
        link_nodes = []
        links = []
        gen = self.conditional_traverse(start_node, include_text=False, include_self=include_self, tag_conditions=["a"], children_only=children_only)
        for node in gen(start_node, end_node=end_node, include_text=False, include_self=include_self):
            link = self.extract_link(node, ignore_fragments=ignore_fragments)
            if link is not None:
                links.append(link)
                link_nodes.append(node)
        return link_nodes, links
    
    def get_media_paths(self, node, path="", return_text=True, return_images=True):
        texts = []
        images = []
        for child in node.iter(include_text=True):
            tag = child.tag
            if child.tag:
                if path:
                    new_path = f"{path}.{tag}"
                else:
                    new_path = tag
            if return_text and child.text_content:
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
    


    def parse_media_children(self, start_node, end_node = None, include_self=True, ignore_fragments=True, headings_as_text=False):
        

        pass


    

        
    def get_text_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        # might be better to have a get_x_nodes func instead of separate funcs for each type of node
        return [node for node in self.traverse_text_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes)]
    
    def get_text_child_nodes(self, start_node, end_node = None, include_self=True, ignore_nodes=[]):
        return [node for node in self.traverse_text_child_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes)]
    

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

import requests
from selectolax.parser import HTMLParser, Node
from typing import List, Tuple, Dict, Union, Optional, Generator, Iterator

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
    


    

    def conditional_traverse(self, start_node: Node, end_node: Optional[Node] = None, include_text: bool = True,
                             include_self: bool = True, ignore_nodes: List[Node] = [], 
                             children_only: bool = False, tags: List[str] = [], match_excluded_tags: bool = True) -> Iterator[Node]:
        """
        Traverse through the nodes starting from `start_node` based on the provided conditions.

        This method provides a customizable way to traverse through nodes starting 
        from `start_node` and ending at `end_node` (if provided) based on conditions 
        like whether to include text nodes, whether to include the `start_node` itself, 
        which nodes to ignore, and which tags to match or exclude.

        Parameters:
            start_node (Node): The starting node for the traversal.
            end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
            include_text (bool, default=True): If True, text nodes are included in the traversal.
            include_self (bool, default=True): If True, the `start_node` itself is yielded.
            ignore_nodes (List[Node], default=[]): List of nodes to be ignored during traversal.
            children_only (bool, default=False): If True, only traverse the direct children of `start_node`.
            tags (List[str], default=[]): List of tags to either match or exclude based on `match_excluded_tags`.
            match_excluded_tags (bool, default=True): Determines behavior of the `tags` list.
                                                    If True, tags in the list are excluded. If False, only tags in the list are included.

        Yields:
            Node: Nodes that match the provided conditions.

        Example:
            Given a node tree and starting from a <div> node, if `tags` is ['span'] 
            and `match_excluded_tags` is True, the traversal will yield nodes excluding any <span> nodes.
        """
        if children_only:
            traverse_func = start_node.traverse_children
        else:
            traverse_func = start_node.traverse
        
        if include_self and start_node not in ignore_nodes and match_excluded_tags ^ (start_node.tag in tags):
            yield start_node

        for node in traverse_func(include_text):
            if end_node and node == end_node:
                break
            tag = node.tag
            if node not in ignore_nodes and match_excluded_tags ^ (tag in tags):
                yield node
    
    def filtered_traverse(self, start_node: Node, filter_func: callable, end_node: Optional[Node] = None, include_text: bool = True,
                                include_self: bool = True, ignore_nodes: List[Node] = [],
                                children_only: bool = False, tags: List[str] = [], match_excluded_tags: bool = True) -> Iterator[Node]:
        """
        Traverse through the nodes starting from `start_node` based on the provided conditions and apply a filtering function.

        This method uses the `conditional_traverse` method to traverse through nodes based 
        on the given conditions. It then applies the `filter_func` to each node and yields only 
        the nodes for which the filter function returns `True`.

        Parameters:
            start_node (Node): The starting node for the traversal.
            filter_func (callable): The filtering function to be applied on each node. Returns `True` for nodes that should be included.
            end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
            include_text (bool, default=True): If True, text nodes are included in the traversal.
            include_self (bool, default=True): If True, the `start_node` itself is yielded.
            ignore_nodes (List[Node], default=[]): List of nodes to be ignored during traversal.
            children_only (bool, default=False): If True, only traverse the direct children of `start_node`.
            tags (List[str], default=[]): List of tags to either match or exclude based on `match_excluded_tags`.
            match_excluded_tags (bool, default=True): Determines behavior of the `tags` list.
                                                    If True, tags in the list are excluded. If False, only tags in the list are included.

        Yields:
            Node: Nodes that match the provided conditions and for which the `filter_func` returns `True`.

        Example:
            Given a node tree and starting from a <div> node, if `tags` is ['span'] 
            and `match_excluded_tags` is True, the traversal will yield nodes excluding any <span> nodes. 
            If the filter_func returns `True` only for nodes containing certain attributes, only those nodes will be yielded.
        """

        for node in self.conditional_traverse(start_node, end_node=end_node, include_text=include_text,
                                              include_self=include_self, ignore_nodes=ignore_nodes,
                                            children_only=children_only, tags=tags, match_excluded_tags=match_excluded_tags):
            if filter_func(node):
                yield node
    

    def traverse_text_nodes(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, ignore_nodes: List[Node] = [], children_only: bool = False) -> Iterator[Node]:
        """
        Traverse through text nodes starting from `start_node` based on the provided conditions.

        This method is designed to specifically traverse through text nodes in a node structure, starting 
        from `start_node` and ending at `end_node` (if provided). The traversal can be customized based 
        on conditions like whether to include the `start_node` itself, which nodes to ignore, and if only 
        direct children of the `start_node` should be considered.

        Parameters:
            start_node (Node): The starting node for the traversal.
            end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
            include_self (bool, default=True): If True, the `start_node` itself is yielded, provided it's a text node.
            ignore_nodes (List[Node], default=[]): List of nodes to be ignored during traversal.
            children_only (bool, default=False): If True, only traverse the direct children of `start_node`.

        Yields:
            Node: Text nodes that match the provided conditions.

        Example:
            Given a node tree and starting from a <div> node, the traversal will yield any direct or nested 
            text nodes, depending on the conditions set by the parameters.
        """       
        tag_conditions = ["-text"]
        yield from self.conditional_traverse(start_node, 
                                             end_node=end_node, 
                                             include_text=True, 
                                             include_self=include_self, 
                                             tag_conditions=tag_conditions, 
                                             ignore_tags=[], 
                                             ignore_nodes=ignore_nodes,
                                             children_only=children_only)



    
    def check_parents(self, node, check_nodes = [], tags = [], match_excluded_tags=True):
        while node.parent:
            parent = node.parent
            if parent in check_nodes:
                return True
            if match_excluded_tags ^ (parent.tag in tags):
                return True
            node = parent
        return False

    def traverse_media_nodes(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, 
                            ignore_nodes: List[Node] = [], extract_text_within_headers: bool = False, children_only: bool = False) -> Iterator[Node]:
        """
        Traverse and yield media-related nodes from the tree, optionally including/excluding text nodes inside header tags.

        This method focuses on traversing nodes related to media elements such as images and SVGs. It allows 
        specific behaviors for header tags, either extracting text nodes from within the header tags or 
        yielding the header nodes themselves and skipping over their children.

        Parameters:
            start_node (Node): The starting node for the traversal.
            end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
            include_self (bool, default=True): If True, the `start_node` itself is yielded.
            ignore_nodes (List[Node], default=[]): List of nodes to be ignored during traversal.
            extract_text_within_headers (bool, default=False): Determines how header nodes are treated.
                                                            If True, it yields only the text nodes inside headers
                                                            If False, it yields the header nodes and skips over their children.
            children_only (bool, default=False): If True, only traverse the direct children of `start_node`.

        Yields:
            Node: Nodes related to media elements and, based on conditions, nodes related to headers or their content.

        Example:
            If the tree has a structure like <div><h1><img></h1></div>, with `extract_text_within_headers` set to True, 
            the traversal will yield only the <img> node. If set to False, it yields the <h1> node and skips its children.
        """
        

        tag_conditions = ["img", "svg", "-text"]


        if extract_text_within_headers:
            filter_func = lambda _: True
        else:
            filter_func = lambda node: not self.check_parents(node, tags=header_tags, match_excluded_tags=False)
            tag_conditions.extend(header_tags)
        yield from self.filtered_traverse(start_node,
                                            filter_func,
                                            end_node=end_node, 
                                            include_self=include_self, 
                                            tag_conditions=tag_conditions, 
                                            ignore_tags=[], 
                                            ignore_nodes=ignore_nodes,
                                            children_only=children_only)




    

    def get_headings(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, children_only: bool = False) -> Tuple[List[Node], List[str]]:

        """
        Retrieve the heading nodes and their corresponding text starting from `start_node` up to `end_node`.

        This method utilizes the `conditional_traverse` to fetch heading nodes based on the provided conditions.
        It collects heading nodes and their respective text content between the `start_node` and the `end_node`.

        Parameters:
            start_node (Node): The starting node to begin retrieval of heading nodes.
            end_node (Optional[Node], default=None): The end node to stop retrieval. If encountered, the traversal stops.
            include_self (bool, default=True): If True, considers the `start_node` itself for heading check.
            children_only (bool, default=False): If True, only checks the direct children of `start_node` for headings.

        Returns:
            Tuple[List[Node], List[str]]: A tuple containing a list of heading nodes and a list of their corresponding text content.

        Example:
            Given a node tree and starting from a <div> node, this method would retrieve all heading nodes (like <h1>, <h2>, etc.)
            between the <div> and `end_node` (if provided) along with their text content.
        """

        heading_nodes = []
        heading_text = []
        gen = self.conditional_traverse(start_node,end_node, include_text=False, include_self=include_self, tags=header_tags, 
                                        match_excluded_tags=False, children_only=children_only)
        for node in gen(include_text=True):
            text = node.text().strip()
            heading_text.append(text)
            heading_nodes.append(node)
        return heading_nodes, heading_text
    

    def extract_link(self, node: Node, ignore_fragments: bool = True) -> Optional[str]:
        """
        Extracts the "href" attribute from the provided node.

        This method is designed to extract the link from a node, typically used to parse anchor
        (<a>) tags in an HTML document. If the ignore_fragments flag is set to True (default),
        it will exclude links that are only fragments (i.e., links that point to a section within
        the same page).

        Parameters:
        node (Node): The node from which the "href" attribute is to be extracted.
        ignore_fragments (bool, default=True): If True, fragment links are excluded.

        Returns:
        Optional[str]: The extracted link or None if the link is a fragment and ignore_fragments is True.

        Example:
        If the node represents the HTML <a href="#section2">Section 2</a> and ignore_fragments
        is True, this method will return None. However, if ignore_fragments is False, it will return '#section2'.
        """

        link = node.attributes["href"]
        if ignore_fragments and link.startswith('#'):
            return None
        return link

    def get_links(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, ignore_fragments: bool = True, children_only: bool = False) -> Tuple[List[Node], List[str]]:
        """
        Extracts and returns link nodes and their corresponding "href" attributes starting from start_node.

        This method uses the conditional_traverse to fetch all anchor (<a>) nodes starting
        from start_node and ending at end_node (if provided) based on specified conditions.
        For each anchor node, it fetches the "href" attribute using the extract_link method.

        Parameters:
        start_node (Node): The starting node for the traversal.
        end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
        include_self (bool, default=True): If True, the start_node itself is included, provided it's an anchor node.
        ignore_fragments (bool, default=True): If True, links that are fragments (i.e., links pointing to a section within the same page) are excluded.
        children_only (bool, default=False): If True, only direct children of start_node are considered.

        Returns:
        Tuple[List[Node], List[str]]: A tuple where the first element is a list of link nodes and the second element is a list of corresponding "href" attributes.

        Example:
        If the node tree has three <a> tags with the links "/home", "#section1", and "/about" and both ignore_fragments
        and include_self are True, this method, when called with the parent of these nodes, will return:
        ([node1, node3], ["/home", "/about"]). If ignore_fragments is False, it will return:
        ([node1, node2, node3], ["/home", "#section1", "/about"]).
        """
        link_nodes = []
        links = []
        gen = self.conditional_traverse(start_node, include_text=False, include_self=include_self, tags=["a"], match_excluded_tags=False, children_only=children_only)
        for node in gen(start_node, end_node=end_node, include_text=False, include_self=include_self):
            link = self.extract_link(node, ignore_fragments=ignore_fragments)
            if link is not None:
                links.append(link)
                link_nodes.append(node)
        return link_nodes, links
    
    def get_media_paths(self, node: Node, path: str = "", return_text: bool = True, return_images: bool = True) -> Tuple[List[Tuple[str, int]], List[Tuple[str, str]]]: # should I return a dict instead?
        # think i should rewrite this if it proves useful to inlcude params like ignore_nodes, tags, etc.
        """
        Retrieves media paths and their associated metadata from a given node.

        This method is designed to recursively traverse the node and its children, collecting media-related 
        details, specifically text and image paths. It provides a structured way to extract textual content 
        lengths and image descriptions (via the "alt" attribute or SVG text) from an HTML document.

        Parameters:
        node (Node): The starting node from which media details are to be extracted.
        path (str, default=""): The initial path representing the node hierarchy, which is updated as the recursion progresses.
        return_text (bool, default=True): If True, returns textual content paths and their corresponding lengths.
        return_images (bool, default=True): If True, returns image paths and their associated descriptions or SVG text.

        Returns:
        Tuple[List[Tuple[str, int]], List[Tuple[str, str]]]:
            The first list in the tuple contains pairs of text paths and their lengths.
            The second list contains pairs of image paths and their descriptions or SVG text.

        Example:
        Given an HTML structure with a <div> containing a paragraph of text and an <img> with an alt text,
        invoking this method with the <div> node might produce:
        ([
            ('div.p', 50)  # Assuming the paragraph contains 50 characters.
        ], 
        [
            ('div.img', 'Sample Image Description')
        ])
        """

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
            if return_images:
                if tag == "img":
                    images.append((new_path, child.attributes.get("alt", "")))
                if tag == "svg":
                    text = "" # TODO: get svg text
                    
                    images.append((new_path, text))

            new_results, imgs = self.get_media_paths(child, new_path, return_text, return_images)
            if new_results:
                texts.extend(new_results)
            if imgs:
                images.extend(imgs)
        return texts, images
    


    def parse_media_node(self, node: Node) -> Optional[Dict[str, Union[str, List[str]]]]:

        tag = node.tag
        if tag == "img":
            return {"type": "img", "tag": tag, "alt": node.attributes.get("alt", ""), "src": node.attributes["src"]}
        if tag == "svg":
            data = []
            path_nodes = node.css("path")
            for path_node in path_nodes:
                data.append(path_node.attributes["d"])
            return {"type": "svg", "tag": tag, "data": data}
        if tag == "-text":
            return {"type": "text", "tag": tag, "text": node.text().strip()}
        if tag in header_tags:
            return {"type": "header", "tag": tag, "text": node.text().strip()}
        return None

    


    def parse_media_nodes(self, start_node: Node, end_node: Optional[Node] = None, 
                             include_self: bool = True, extract_text_within_headers: bool = False, children_only: bool = False) -> Iterator[Dict[str, Union[str, List[str]]]]:
        
        """    
        Traverse and parse media-related nodes, returning their properties.

        This method leverages the traversal functionality provided by `traverse_media_nodes` to navigate through media elements
        such as images, SVGs, text, and headers. Each traversed node is subsequently parsed to extract its relevant attributes 
        and characteristics using the `parse_media_node` method.

        Parameters:
            start_node (Node): The starting node for the traversal.
            end_node (Optional[Node], default=None): The end node for traversal. If encountered, the traversal stops.
            include_self (bool, default=True): If True, the `start_node` itself is parsed and included in the results.
            extract_text_within_headers (bool, default=False): Determines how header nodes are treated.
                                                            If True, it parses only the text nodes inside headers.
                                                            If False, it parses the header nodes and skips over their children.
            children_only (bool, default=False): If True, only parse the direct children of `start_node`.
        Yields:
            Dict[str, Union[str, List[str]]]: Dictionary containing metadata about the node. For example:
                - For an <img> node, yields {"type": "img", "tag": "img", "alt": "alternative text", "src": "source_link"}
                - For an <svg> node, yields {"type": "svg", "tag": "svg", "data": ["path_data1", "path_data2"]}
                - For a text node or header node (when `headings_as_text` is True), yields {"type": "text", "tag": "-text", "text": "actual text content"}
                - For a header node (when `headings_as_text` is False), yields {"type": "header", "tag": "h1", "text": "header text content"}
        Example:
            If the tree has a structure like <div><h1>fish</h1></div> and `extract_text_within_headers` is set to True, 
            it will only yield a dictionary for the text node ("fish"). If `headings_as_text` is set to False, it will 
            yield a dictionary for the <h1> node treated as a header.
        """
        
        gen = self.traverse_media_nodes(start_node, end_node=end_node, include_self=include_self, extract_text_within_headers=extract_text_within_headers, children_only=children_only)

        for node in gen:
            yield self.parse_media_node(node)


    def count_nodes(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, ignore_nodes: List[Node] = [], children_only: bool = False) -> Tuple[int, int]:

        """
        Count the number of nodes and text nodes starting from `start_node` based on the provided conditions.

        This method uses `conditional_traverse` to yield nodes starting from `start_node` and ending at 
        `end_node` (if provided). It then counts the total number of nodes and text nodes based on the conditions 
        provided such as whether to include the `start_node` itself, which nodes to ignore, and if only the 
        direct children of `start_node` should be considered.

        Parameters:
            start_node (Node): The starting node for counting.
            end_node (Optional[Node], default=None): The end node for counting. If encountered, the counting stops.
            include_self (bool, default=True): If True, the `start_node` itself is considered in the count.
            ignore_nodes (List[Node], default=[]): List of nodes to be ignored during counting.
            children_only (bool, default=False): If True, only consider the direct children of `start_node`.

        Returns:
            Tuple[int, int]: A tuple where the first element is the total number of nodes and the second 
                            element is the number of text nodes.

        Example:
            Given a node tree and starting from a <div> node, calling this function would return the total count 
            of nodes and text nodes starting from the <div> node based on the conditions provided.
        """

        node_count = 0
        text_count = 0
        gen = self.conditional_traverse(start_node, end_node=end_node, include_text=True, include_self=include_self, ignore_nodes=ignore_nodes, children_only=children_only)
        for node in gen:
            node_count += 1
            if node.tag == '-text':
                text_count += 1
        return node_count, text_count

        
    def get_text_nodes(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, ignore_nodes: List[Node] = [], children_only: bool = False) -> List[Node]:
        # might be better to have a get_x_nodes func instead of separate funcs for each type of node
        """
        Retrieve a list of text nodes starting from `start_node` based on the provided conditions.

        This method fetches text nodes from a node structure, starting from `start_node` and
        optionally ending at `end_node`. The retrieval can be tailored based on conditions 
        like whether to include the `start_node` itself, which nodes to disregard, and whether
        to only consider the direct children of the `start_node`.

        Parameters:
            start_node (Node): The starting node for the retrieval.
            end_node (Optional[Node], default=None): The end node for retrieval. If encountered, the retrieval stops.
            include_self (bool, default=True): If True, the `start_node` itself is included in the list, provided it's a text node.
            ignore_nodes (List[Node], default=[]): List of nodes to be excluded during the retrieval.
            children_only (bool, default=False): If True, only considers the direct children of `start_node` for retrieval.

        Returns:
            List[Node]: A list of text nodes that match the provided conditions.

        Example:
            Given a node tree <div><h1>fish</h1><p>fish are cool</p></div> and starting from the <div> node,
            this method would return a list containing the text nodes "fish" and "fish are cool".
        """

        return [node for node in self.traverse_text_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes, children_only=children_only)]
    
    

    def get_text_lens(self, start_node: Node, end_node: Optional[Node] = None, include_self: bool = True, ignore_nodes: List[Node] = []) -> List[int]:

        """
        Retrieve a list of text lengths starting from `start_node` based on the provided conditions.

        This method fetches text nodes from a node structure, starting from `start_node` and
        optionally ending at `end_node`. The retrieval can be tailored based on conditions
        like whether to include the `start_node` itself and which nodes to disregard.
        to only consider the direct children of the `start_node`.

        Parameters:
            start_node (Node): The starting node for the retrieval.
            end_node (Optional[Node], default=None): The end node for retrieval. If encountered, the retrieval stops.
            include_self (bool, default=True): If True, the `start_node` itself is included in the list, provided it's a text node.
            ignore_nodes (List[Node], default=[]): List of nodes to be excluded during the retrieval.
            children_only (bool, default=False): If True, only considers the direct children of `start_node` for retrieval.

        Returns:
            List[int]: A list of text lengths for nodes that match the provided conditions.

        Example:
            Given a node tree <div><h1>fish</h1><p>fish are cool</p></div> and starting from the <div> node,
            this method would return a list containing the text lengths 4 and 13.
        """

        text_lens = []
        for node in self.traverse_text_nodes(start_node, end_node=end_node, include_self=include_self, ignore_nodes=ignore_nodes):
            text_lens.append(len(node.text().strip()))
        return text_lens
    

    def handle_text_len(self, texts: List[str], max_len: int, trancute: bool = True) -> List[str]:
        """
        Handles and modifies a list of text nodes based on their lengths.

        This method processes a list of text nodes to ensure they conform to a specified maximum length. It's particularly 
        useful for preparing text nodes before passing them to an LLM (Large Language Model) when parsing an HTML tree.
        If a text node exceeds the maximum length, this function provides two choices:
        1. Truncate the text node to fit the maximum length.
        2. Replace the text node with its length.

        By default, texts will be truncated if they exceed the specified length. However, if the `trancute` flag is set to
        False, the function will replace over-length text nodes with their corresponding lengths.

        Parameters:
        texts (List[str]): A list of text nodes to be processed.
        max_len (int): The maximum allowable length for each text node.
        trancute (bool, default=True): If True, text nodes exceeding max_len will be truncated. If False, they will be
                                    replaced by their respective lengths.

        Returns:
        List[str]: A processed list of text nodes, either truncated or replaced by their lengths based on the `trancute`
                flag and the `max_len` value.

        Example:
        If texts = ["Hello, world!", "This is a very long text node that needs to be handled."], max_len = 20, and 
        trancute is True, the returned list will be ["Hello, world!", "This is a very long t"]. If trancute is False, 
        the second text node will be replaced by its length, resulting in ["Hello, world!", 52].
        """

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

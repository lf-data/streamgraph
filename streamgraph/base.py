import logging
import json
import os
import multiprocessing.pool
import base64
from typing import Any, Optional, Union
from functools import lru_cache
from copy import deepcopy
import requests
from .utils import (_input_args, _is_positional_or_keyword,
                    _get_args, _get_docs, _id_counter, _deprecated_method)
from .utils import Callable, List, Dict, Tuple, CSS_MERMAID

logger = logging.getLogger(__name__)

counter = _id_counter()

lru_cache(maxsize=2)
def _reset_id(nodes: Union[List, Dict, Tuple]) -> Union[List, Dict, Tuple]:
    """
    Resets the IDs of nodes and their nested structures to new unique values.

    This function takes a collection of nodes, either a list, dictionary, 
    or tuple, and generates a new unique ID for
    each node within the collection. It also recursively processes nested 
    nodes, including `IfNode`, `Chain`, and `Layer`,
    ensuring that all nested nodes receive new IDs and that the internal 
    structures are correctly updated.

    Args:
        nodes (Union[List, Dict, Tuple]): A collection of nodes to be processed. 
                                          Nodes must be instances of `Base`.

    Returns:
        Union[List, Dict, Tuple]: The collection of nodes with updated IDs.

    Raises:
        AssertionError: If any item in the collection is not an instance of `Base`.

    Notes:
        - Uses LRU caching with a maximum size of 2 to optimize performance for repeated inputs.
        - Recursively processes nested nodes, including those within 
          `IfNode`, `LoopNode`, `Chain`, and `Layer`.
        - Ensures that each node and its nested structures receive a unique ID.

    Examples:
        >>> _reset_id([node1, node2])
        [Node1 with new ID, Node2 with new ID]

        >>> _reset_id({'key1': node1, 'key2': node2})
        {'key1': Node1 with new ID, 'key2': Node2 with new ID}
        
        >>> _reset_id((node1, node2))
        (Node1 with new ID, Node2 with new ID)
    """
    if isinstance(nodes, dict):
        nodes = {node: deepcopy(nodes[node]) for node in nodes}
    else:
        nodes = [deepcopy(node) for node in nodes]
    for nodeid in nodes:
        if isinstance(nodes, dict):
            node_to_reset = nodes[nodeid]
        else:
            node_to_reset = nodeid

        assert isinstance(node_to_reset, Base), "The items in 'nodes' must be Base instances"
        node_to_reset.id = node_to_reset.name + str(next(counter))
        if isinstance(node_to_reset, IfNode):
            node_to_reset.true_node = deepcopy(node_to_reset.true_node)
            node_to_reset.true_node.id = node_to_reset.true_node.name + str(next(counter))
            if hasattr(node_to_reset.true_node, "_nodes"):
                node_to_reset.true_node._nodes = _reset_id(node_to_reset.true_node._nodes)

            node_to_reset.false_node = deepcopy(node_to_reset.false_node)
            node_to_reset.false_node.id = node_to_reset.false_node.name + str(next(counter))
            if hasattr(node_to_reset.false_node, "_nodes"):
                node_to_reset.false_node._nodes = _reset_id(node_to_reset.false_node._nodes)
        elif isinstance(node_to_reset, LoopNode):
            node_to_reset.loop_node = deepcopy(node_to_reset.loop_node)
            node_to_reset.loop_node.id = node_to_reset.loop_node.name + str(next(counter))
            if hasattr(node_to_reset.loop_node, "_nodes"):
                node_to_reset.loop_node._nodes = _reset_id(node_to_reset.loop_node._nodes)
        elif isinstance(node_to_reset, (Chain, Layer)):
            node_to_reset._nodes = _reset_id(node_to_reset._nodes)

        if isinstance(nodes, dict):
            nodes[nodeid] = node_to_reset
        else:
            nodeid = node_to_reset
    return nodes

lru_cache(maxsize=2)
def _create_mermaid(nodes: Union[List, Tuple, Dict]) -> Tuple:
    """
    Converts a collection of nodes into a Mermaid diagram representation.

    This function processes a list, tuple, or dictionary of nodes to generate a 
    Mermaid diagram syntax, 
    which can be used to visualize the flow of a chain of nodes. Nodes can be of type 
    `Node`, `IfNode`, `LoopNode`, `Layer`, or `Chain`. 
    The function handles various node types and their relationships, including conditional branching
    and nested layers.

    Args:
        nodes (Union[List, Tuple, Dict]): A collection of nodes or a dictionary of 
                                          nodes to be converted. Nodes must be instances of `Base`.

    Returns:
        Tuple: A tuple containing:
            - `first_node` (List): A list of the first nodes in the diagram.
            - `lines` (List): The lines of Mermaid syntax representing the diagram.
            - `last_node` (List): A list of the last nodes in the diagram.

    Raises:
        AssertionError: If any node in the collection is not an instance of `Base`.

    Notes:
        - Uses LRU caching with a maximum size of 2 to optimize performance for repeated inputs.
        - Handles nodes of type `Node`, `IfNode`, `LoopNode`, `Layer`, and `Chain`.
        - Converts conditional nodes into diamond-shaped Mermaid nodes and 
          other nodes into rectangle-shaped nodes.
        - Processes nested layers and chains, including generating subgraphs for chains.

    Examples:
        >>> _create_mermaid([node1, node2, conditional_node])
        (first_node_list, ['node1[Node 1]:::rectangle;', 'node2[Node 2]:::rectangle;', 
        'conditional_node{{If Node}}:::diamond;'], last_node_list)
        
        >>> _create_mermaid({'key1': node1, 'key2': [node2, node3]})
        (first_node_list, ['node1[Node 1]:::rectangle;', 'node2[Node 2]:::rectangle;', 
        'node3[Node 3]:::rectangle;'], last_node_list)
    """
    lines = []
    first_node = None
    last_node = None
    if isinstance(nodes, dict):
        nodes = [nodes[node] for node in nodes]
    for node_mermaid in nodes:
        assert isinstance(node_mermaid, Base), "The items in 'nodes' must be Base instances"
        if isinstance(node_mermaid, Node):
            if isinstance(node_mermaid, IfNode):
                lines.append(f"{node_mermaid.id}{{{node_mermaid.name}}}:::diamond;")

                if hasattr(node_mermaid.true_node ,"_nodes"):
                    true_nodes = node_mermaid.true_node._nodes
                else:
                    true_nodes = [node_mermaid.true_node]

                if hasattr(node_mermaid.false_node ,"_nodes"):
                    false_nodes = node_mermaid.false_node._nodes
                else:
                    false_nodes = [node_mermaid.false_node]

                first_node_true, lines_true, last_node_true = _create_mermaid(true_nodes)
                first_node_false, lines_false, last_node_false = _create_mermaid(false_nodes)

                for x in first_node_true:
                    lines.append(f"{node_mermaid.id} -- True --> {x.id};")
                for y in first_node_false:
                    lines.append(f"{node_mermaid.id} -- False --> {y.id};")

                if isinstance(node_mermaid.true_node, Chain):
                    lines.append("subgraph \" \";")
                    lines += lines_true
                    lines.append("end;")
                else:
                    lines += lines_true

                if isinstance(node_mermaid.false_node, Chain):
                    lines.append("subgraph \" \";")
                    lines += lines_false
                    lines.append("end;")
                else:
                    lines += lines_false

                if last_node is not None:
                    for x in last_node:
                        lines.append(f"{x.id} --> {node_mermaid.id};")

                if first_node is None:
                    first_node = [node_mermaid]

                last_node = last_node_false + last_node_true
            elif isinstance(node_mermaid, LoopNode):
                if hasattr(node_mermaid.loop_node ,"_nodes"):
                    true_nodes = node_mermaid.loop_node._nodes
                else:
                    true_nodes = [node_mermaid.loop_node]

                first_node_loop, lines_loop, last_node_loop = _create_mermaid(true_nodes)

                if isinstance(node_mermaid.loop_node, Chain):
                    lines.append("subgraph \" \";")
                    lines += lines_loop
                    lines.append("end;")
                else:
                    lines += lines_loop

                if last_node is not None:
                    for x in last_node:
                        for y in first_node_loop:
                            lines.append(f"{x.id} --> {y.id};")

                lines.append(f"{node_mermaid.id}{{{node_mermaid.name}}}:::diamond_loop;")

                for x in last_node_loop:
                    lines.append(f"{x.id} --> {node_mermaid.id};")

                for x in first_node_loop:
                    lines.append(f"{node_mermaid.id} -. New Iteration .-> {x.id};")

                if first_node is None:
                    first_node = first_node_loop

                last_node = [node_mermaid]
            else:
                lines.append(f"{node_mermaid.id}[{node_mermaid.name}]:::rectangle;")

                if first_node is None:
                    first_node = [node_mermaid]

                if last_node is not None:
                    for x in last_node:
                        lines.append(f"{x.id} --> {node_mermaid.id};")
                last_node = [node_mermaid]
        elif isinstance(node_mermaid, Layer):
            list_layer = []
            for x in node_mermaid._nodes:
                if hasattr(x ,"_nodes"):
                    list_layer.append(_create_mermaid(x._nodes))
                else:
                    list_layer.append(_create_mermaid([x]))

            for i, x in enumerate(node_mermaid._nodes):
                if isinstance(x, Chain):
                    lines.append("subgraph \" \";")
                    lines += list_layer[i][1]
                    lines.append("end;")
                else:
                    lines += list_layer[i][1]

            if first_node is None:
                first_node = [y for x in list_layer for y in x[0]]

            if last_node is not None:
                for x in last_node:
                    for j in [y for f in list_layer for y in f[0]]:
                        lines.append(f"{x.id} --> {j.id};")

            last_node = [y for f in list_layer for y in f[2]]

        elif isinstance(node_mermaid, Chain):
            chain_first_node, chain_line, chain_last_node = _create_mermaid(node_mermaid._nodes)

            lines.append("subgraph \" \";")
            lines += chain_line
            lines.append("end;")

            if first_node is None:
                first_node = chain_first_node

            if last_node is not None:
                for x in last_node:
                    for y in chain_first_node:
                        lines.append(f"{x.id} --> {y.id};")

            last_node = chain_last_node

    return first_node, lines, last_node


lru_cache(maxsize=2)
def _check_input_node(inputs: Union[List, Tuple, Dict, "Base"]) ->None:
    """
    Validates that the input consists solely of `Base` instances or 
    nested collections of `Base` instances.

    This function checks whether the provided input is either a single 
    instance of `Base`, or a list, tuple, or dictionary
    containing `Base` instances or nested collections thereof. 
    If the input contains any non-`Base` elements, a `TypeError` is raised.

    Args:
        inputs (Union[List, Tuple, Dict, "Base"]): The input to be checked, 
        which can be a single `Base` instance or a nested structure.

    Raises:
        TypeError: If any element in the input is not an instance of `Base` 
        or a collection containing only `Base` instances.

    Notes:
        - Uses LRU caching with a maximum size of 2 to optimize performance for repeated inputs.
        - The function assumes that all elements in the nested structures 
          must be instances of `Base`.

    Examples:
        >>> _check_input_node([node1, [node2, node3]])
        # No exception raised, as all elements are `Base` instances or nested collections of `Base`.

        >>> _check_input_node({'key1': node1, 'key2': [node2, node3]})
        # No exception raised, as all elements are `Base` instances or nested collections of `Base`.

        >>> _check_input_node(node1)
        # No exception raised, as the input is a single `Base` instance.

        >>> _check_input_node([node1, "invalid"])
        Traceback (most recent call last):
            ...
        TypeError: Only "Base", or lists of this class can be used as inputs
    """
    if isinstance(inputs, (list, tuple, dict)):
        for inp in inputs:
            if isinstance(inputs, dict):
                _check_input_node(inputs[inp])
            else:
                _check_input_node(inp)
    else:
        if not isinstance(inputs, Base):
            raise TypeError('Only "Base", or lists of this class can be used as inputs')

lru_cache(maxsize=2)
def _convert_parallel_node(inputs: Union[List, Tuple, Dict, "Base"]) ->Any:
    """
    Recursively converts inputs into a `Layer` if they are nested lists, tuples, or dictionaries.

    This function traverses through the provided input, which can be a 
    list, tuple, dictionary, or a single `Base` instance. 
    If the input contains nested lists, tuples, or dictionaries, 
    these are recursively converted into `Layer` instances. 
    If the input is already an instance of `Base`, it is returned as-is.

    Args:
        inputs (Union[List, Tuple, Dict, "Base"]): The input to 
        be converted, which can be a nested structure or a `Base` instance.

    Returns:
        Any: A `Layer` containing the converted nodes if 
        the input was a nested structure; otherwise, returns the `Base` instance.

    Notes:
        - Uses LRU caching with a maximum size of 2 to optimize performance for repeated inputs.
        - The function assumes that the `Layer` class is 
        capable of handling lists, tuples, and dictionaries as input.

    Examples:
        >>> _convert_parallel_node([node1, [node2, node3]])
        Layer([node1, Layer([node2, node3])])
        
        >>> _convert_parallel_node({'key1': node1, 'key2': [node2, node3]})
        Layer({'key1': node1, 'key2': Layer([node2, node3])})
        
        >>> _convert_parallel_node(node1)
        node1
    """
    if isinstance(inputs, Base):
        return inputs

    if isinstance(inputs, dict):
        for key in inputs:
            if isinstance(inputs[key], (list, tuple, dict)):
                inputs[key] = _convert_parallel_node(inputs[key])
    else:
        for x in inputs:
            if isinstance(x, (list, tuple, dict)):
                x = _convert_parallel_node(x)
    return Layer(inputs)


def node() -> "Node":
    """
    Factory function for creating a `Node` instance.

    This function wraps a callable function into a `Node`.

    Returns:
        Callable: A function that takes a callable `func` and returns a `Node` instance.

    Notes:
        - This function only creates a simple `Node`.
    """
    def run_node(func: Callable) -> Node:
        return Node(func)

    return run_node

def ifnode(true_node: "Base", false_node: "Base") -> "IfNode":
    """
    Factory function for creating a `IfNode` instance.

    This function wraps a callable function into a `IfNode`.

    Returns:
        Callable: A function that takes a callable `func` and returns a `IfNode` instance.

    Notes:
        - This function only creates a simple `IfNode`.
    """
    def run_node(func: Callable, true_node = true_node, false_node = false_node) -> IfNode:
        return IfNode(func, true_node=true_node, false_node=false_node)

    return run_node

def loopnode(loop_node: "Base") -> "LoopNode":
    """
    Factory function for creating a `LoopNode` instance.

    This function wraps a callable function into a `LoopNode`.

    Returns:
        Callable: A function that takes a callable `func` and returns a `LoopNode` instance.

    Notes:
        - This function only creates a simple `LoopNode`.
    """
    def run_node(func: Callable, loop_node = loop_node) -> LoopNode:
        return LoopNode(func, loop_node = loop_node)

    return run_node

class Base:
    """
    Base class for creating nodes in the chain.
    
    This class serves as an abstract base for nodes that can be added to a chain.
    It provides methods for adding nodes to the chain in different positions, 
    but the actual implementation of adding a node must be provided by subclasses.
    """

    def add_node(self, other: Any, before: bool) ->"Base":
        """
        Add a node to the chain.

        This method should be implemented by subclasses to define how nodes are added to the chain.

        Args:
            *args: Positional arguments for adding the node.
            **kwargs: Keyword arguments for adding the node.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.

        Returns:
            Base: The new chain with the added node.
        """
        raise NotImplementedError("This method should be implemented by subclasses")

    def __rshift__(self, other) ->"Base":
        """
        Adds a node to the chain after the current node using the '>>' operator.

        Args:
            other (Base): The node to be added to the chain.

        Returns:
            Base: A new chain with the node added after the current node.
        """
        return self.add_node(other, before=False)

    def __rlshift__(self, other) ->"Base":
        """
        Adds a node to the chain after the current node using the '<<' operator on the right side.

        Args:
            other (Base): The node to be added to the chain.

        Returns:
            Base: A new chain with the node added after the current node.
        """
        return self.add_node(other, before=False)

    def __lshift__(self, other) ->"Base":
        """
        Adds a node to the chain before the current node using the '<<' operator.

        Args:
            other (Base): The node to be added to the chain.

        Returns:
            Base: A new chain with the node added before the current node.
        """
        return self.add_node(other, before=True)

    def __rrshift__(self, other) ->"Base":
        """
        Adds a node to the chain before the current node using the '>>' operator on the right side.

        Args:
            other (Base): The node to be added to the chain.

        Returns:
            Base: A new chain with the node added before the current node.
        """
        return self.add_node(other, before=True)


class Chain(Base):
    """
    A class representing a chain of nodes, which are instances of the `Base` class.
    
    This class allows for the creation and manipulation of a sequence of nodes, 
    facilitating operations like adding new nodes, chaining the nodes together, and
    generating visual representations of the chain.

    Attributes:
        _nodes (List[Base]): A list of nodes in the chain.
        name (str): The name of the chain. Automatically generated if not provided.
        id (str): A unique identifier for the chain.

    Methods:
        __init__(nodes, name=None):
            Initializes a Chain instance with a list of nodes and an optional name.
        
        __or__(other):
            Sets the name of the chain using a string and returns a copy of the chain.
        
        add_node(other, before):
            Adds a node to the chain, either before or after the existing nodes.
        
        __call__(*args, **kwargs):
            Executes the chain by sequentially calling each node with the provided arguments.
        
        view(direction='TB', path=None):
            Generates a visual representation of the chain using Mermaid and 
            saves it as a PNG image.

        __getitem__(index):
            Retrieves the node at the specified index.

        get_node_data():
            Extracts the data of each node in the chain.
        
        __setitem__(index, node):
            Replaces the node at the specified index with a new node.
        
        __repr__():
            Returns a string representation of the chain, including its ID and name.
    """
    def __init__(self, nodes: List[Base], name: Optional[str] = None) -> None:
        """
        Initializes a Chain instance with a list of nodes and an optional name.

        Args:
            nodes (List[Base]): A list of nodes to be included in the chain. 
            Must contain at least two nodes.
            name (Optional[str]): An optional name for the chain. 
            If not provided, a name will be generated.

        Raises:
            AssertionError: If the number of nodes is less than two.
        """
        assert len(nodes) > 1, "There must be at least two nodes"
        _check_input_node(nodes)
        nodes = _reset_id(nodes)
        self._nodes = nodes
        if name is not None:
            self.name = name
        else:
            self.name = "Chain"
        self.id = self.name + str(next(counter))

    def __or__(self, other):
        """
        Sets the name of the chain using a string and returns a copy of the chain.

        Args:
            other (str): The new name for the chain.

        Returns:
            Chain: A deep copy of the chain with the updated name.

        Raises:
            ValueError: If the provided name is not a string.
        """
        if isinstance(other, str):
            cself = deepcopy(self)
            cself.name = other
            cself.id = cself.name + str(next(counter))
            return cself
        else:
            raise ValueError("The name be 'str'")

    def add_node(self, other: Any, before: bool) -> 'Chain':
        """
        Adds a node to the chain, either before or after the existing nodes.

        Args:
            other (Base): The node to be added to the chain.
            before (bool): If True, the node is added before the existing nodes. 
            Otherwise, it is added after.

        Returns:
            Base: A new chain instance with the added node.
        """
        _check_input_node(other)
        other = _convert_parallel_node(other)
        if before:
            chain = Chain(nodes=[other] + self._nodes)
        else:
            chain = Chain(nodes=self._nodes + [other])
        chain._nodes = _reset_id(chain._nodes)
        return chain

    def __call__(self, *args, **kwargs) -> Any:
        """
        Executes the chain by sequentially calling each node with the provided arguments.

        Args:
            *args: Positional arguments to pass to the first node.
            **kwargs: Keyword arguments to pass to the first node.

        Returns:
            Any: The output of the last node in the chain.

        Raises:
            Exception: If an error occurs during the execution of any node in the chain.
        """
        try:
            logger.info("Start Chain", extra={"id": self.id, "name_class": self.name})
            x = None
            for i, node_run in enumerate(self._nodes):
                if i == 0:
                    x = node_run(*args, **kwargs)
                else:
                    if isinstance(x, (list, tuple)):
                        x = node_run(*x)
                    elif isinstance(x, dict):
                        x = node_run(**x)
                    else:
                        x = node_run(x)
            logger.info("End Chain", extra={"id": self.id, "name_class": self.name})
            return x
        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

    @_deprecated_method(msg="This method is replace by 'save' method.")
    def view(self, path: str, direction: str = "TB") -> None:
        """
        Generates a visual representation of the chain using Mermaid and saves it as a PNG image.

        Args:
            path (str): The file path where the PNG image will be saved.
            direction (str): The direction of the flowchart 
            ('TB' for top-bottom, 'LR' for left-right).
        
        Raises:
            Exception: If the image generation fails.
        """
        mg = "\n".join(_create_mermaid(self._nodes)[1])
        mg = f"flowchart {direction};\n" + mg + CSS_MERMAID
        graphbytes = mg.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        response = requests.get("https://mermaid.ink/img/" + base64_string, timeout=10)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to generate PNG image. Status code: {response.status_code}")

    def save(self, path: str, direction: str = "TB") -> None:
        """
        Generates a visual representation of the chain using Mermaid and saves it as a PNG image.

        Args:
            path (str): The file path where the PNG image will be saved.
            direction (str): The direction of the flowchart 
            ('TB' for top-bottom, 'LR' for left-right).
        
        Raises:
            Exception: If the image generation fails.
        """
        mg = "\n".join(_create_mermaid(self._nodes)[1])
        mg = f"flowchart {direction};\n{mg}{CSS_MERMAID}"
        graphbytes = mg.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        response = requests.get("https://mermaid.ink/img/" + base64_string, timeout=10)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to generate PNG image. Status code: {response.status_code}")

    def show(self, direction: str = "TB") -> str:
        """
        Generates a visual representation of the chain using Mermaid.

        Args:
            direction (str): The direction of the flowchart 
            ('TB' for top-bottom, 'LR' for left-right).
        """
        mg = "\n".join(_create_mermaid(self._nodes)[1])
        mg = f"flowchart {direction};\n{mg}{CSS_MERMAID}"
        return mg

    def get_node_data(self) -> List[Dict[str, Any]]:
        """
        Extracts the data of each node in the chain.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing details of each node.
            Each dictionary includes the node's name, function, ID, and class type.
        """
        node_data_list = []
        for node_get in self._nodes:
            node_data = {
                "name": getattr(node_get, 'name', None),
                "function": getattr(node_get, '__call__', None).__name__ \
                    if isinstance(node_get, (Node, IfNode)) else None,
                "id": getattr(node_get, 'id', None),
                "class_type": type(node_get).__name__
            }
            node_data_list.append(node_data)
        return node_data_list

    def __getitem__(self, index: int) -> Base:
        """
        Retrieves the node at the specified index.

        Args:
            index (int): The index of the node to retrieve.

        Returns:
            Base: The node at the specified index.
        """
        return self._nodes[index]

    def __setitem__(self, index: int, new_node: Base) -> None:
        """
        Replaces the node at the specified index with a new node.

        Args:
            index (int): The index of the node to replace.
            node (Base): The new node to set at the specified index.

        Raises:
            ValueError: If the provided node is not an instance of Base.
        """
        _check_input_node(new_node)
        self._nodes[index] = _convert_parallel_node(new_node)
        self._nodes = _reset_id(self._nodes)

    def __repr__(self) -> str:
        """
        Returns a string representation of the chain, including its ID and name.

        Returns:
            str: A JSON string representing the chain's ID and name.
        """
        json_repr = json.dumps({
            "id": self.id,
            "name": self.name
        })
        return f"Chain({json_repr})"


class Layer(Base):
    """
    A class representing a layer of nodes, which can be either a 
    list, tuple, or dictionary of `Base` instances.
    
    This class allows for grouping multiple nodes into a single layer that can be added to a chain.
    It supports parallel execution of its nodes and can be added to other chains or layers.

    Attributes:
        _nodes (Union[List[Base], Tuple[Base], Dict[str, Base]]): The nodes within the layer.
        name (str): The name of the layer. Automatically generated if not provided.
        _is_dict (bool): Indicates if the nodes are stored in a dictionary.
        id (str): A unique identifier for the layer.

    Methods:
        __init__(nodes, name=None):
            Initializes a Layer instance with a list, tuple, 
            or dictionary of nodes and an optional name.
        
        add_node(other, before):
            Adds a node to the chain either before or after the current layer.
        
        __call__(*args, **kwargs):
            Executes the layer by running its nodes in parallel with the provided arguments.
        
        __repr__():
            Returns a string representation of the layer, including its ID and name.
    """

    def __init__(self, nodes: Union[List[Base], Tuple[Base], Dict[str, Base]],
                 name: Optional[str] = None) -> None:
        """
        Initializes a Layer instance with a list, tuple, or 
        dictionary of nodes and an optional name.

        Args:
            nodes (Union[List[Base], Tuple[Base], Dict[str, Base]]): The nodes to be included 
            in the layer. Must not contain other `Layer` instances.
            name (Optional[str]): An optional name for the layer. 
            If not provided, a name will be generated.

        Raises:
            AssertionError: If any of the nodes are instances of `Layer`.
        """
        assert len([node for node in nodes if isinstance(node, Layer)]) == 0, \
            "Layers cannot contain other Layers"
        assert len(nodes) > 1, "There must be at least two nodes"
        _check_input_node(nodes)
        nodes = _reset_id(nodes)
        self._nodes = nodes
        if name is not None:
            self.name = name
        else:
            self.name = "Layer"
        self._is_dict = isinstance(nodes, dict)
        self.id = self.name + str(next(counter))

    def add_node(self, other, before: bool) ->'Chain':
        """
        Adds a node to the chain, either before or after the current layer.

        Args:
            other (Base): The node to be added to the chain.
            before (bool): If True, the node is added before the current layer. 
            Otherwise, it is added after.

        Returns:
            Base: A new chain instance with the added node.
        """
        _check_input_node(other)
        other = _convert_parallel_node(other)
        if before:
            chain = Chain(nodes=[other, self])
        else:
            chain = Chain(nodes=[self, other])
        chain._nodes = _reset_id(chain._nodes)
        return chain

    def __call__(self, *args, **kwargs)->Any:
        """
        Executes the layer by running its nodes in parallel with the provided arguments.

        Args:
            *args: Positional arguments to pass to each node.
            **kwargs: Keyword arguments to pass to each node.

        Returns:
            Any: A dictionary or list of the outputs from each node in the layer, 
            depending on how nodes are stored.

        Raises:
            Exception: If an error occurs during the execution of any node in the layer.
        """
        try:
            logger.info("Start Layer", extra={"id": self.id, "name_class": self.name})
            res = {} if self._is_dict else []
            cpus = max([int(os.cpu_count()/2), 1])

            def run_node(node_input, args, kwargs):
                return node_input(*args, **kwargs)

            with multiprocessing.pool.ThreadPool(cpus) as pool:
                if self._is_dict:
                    keys = list(self._nodes.keys())
                    nodes = list(self._nodes.values())
                    input_map = [(node, args, kwargs) for node in nodes]
                    output = pool.starmap(run_node, input_map)
                    res = dict(zip(keys, output))
                else:
                    input_map = [(node, args, kwargs) for node in self._nodes]
                    res = pool.starmap(run_node, input_map)
            logger.info("End Layer", extra={"id": self.id, "name_class": self.name})
            return res
        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

    def __repr__(self) -> str:
        """
        Returns a string representation of the layer, including its ID and name.

        Returns:
            str: A JSON string representing the layer's ID and name.
        """
        json_repr = json.dumps({
            "id": self.id,
            "name": self.name
        })
        return f"Layer({json_repr})"


class Node(Base):
    """
    A class representing a node in a chain, which is associated with a callable function.

    This class wraps a function into a node, allowing it to be used in a chain of operations.
    It stores information about the function, including its arguments, name, and description.
    
    Attributes:
        positional_or_keyword (bool): Indicates whether the function 
        accepts positional or keyword arguments.
        name (str): The name of the function.
        description (str): The documentation string of the function.
        args (List[str]): A list of argument names required by the function.
        func (Callable): The callable function associated with the node.
        id (str): A unique identifier for the node.

    Methods:
        __init__(func):
            Initializes a Node instance with a callable function.
        
        add_node(other, before):
            Adds a node to the chain either before or after the current node.
        
        __call__(*args, **kwargs):
            Executes the function associated with the node with the provided arguments.
        
        __repr__():
            Returns a string representation of the node, including its 
            ID, arguments, name, and description.
    """
    def __init__(self, func: Callable) -> None:
        """
        Initializes a Node instance with a callable function.

        Args:
            func (Callable): The function to be wrapped into a node.

        Attributes:
            positional_or_keyword (bool): Whether the function 
            accepts positional or keyword arguments.
            name (str): The name of the function.
            description (str): The documentation string of the function.
            args (List[str]): The list of argument names required by the function.
            func (Callable): The callable function associated with the node.
            id (str): A unique identifier for the node.
        """
        self.positional_or_keyword = _is_positional_or_keyword(func)
        self.name = func.__name__.replace(">","").replace("<","")
        self.description = _get_docs(func)
        self.args = _get_args(func)
        self.func = func
        self.id = self.name + str(next(counter))

    def add_node(self, other, before: bool) ->'Chain':
        """
        Adds a node to the chain, either before or after the current node.

        Args:
            other (Base): The node to be added to the chain.
            before (bool): If True, the node is added before the current node. 
            Otherwise, it is added after.

        Returns:
            Base: A new chain instance with the added node.
        """
        _check_input_node(other)
        other = _convert_parallel_node(other)
        if before:
            chain = Chain(nodes=[other, self])
        else:
            chain = Chain(nodes=[self, other])
        chain._nodes = _reset_id(chain._nodes)
        return chain

    def __call__(self, *args, **kwargs)-> Any:
        """
        Executes the function associated with the node with the provided arguments.

        Args:
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.

        Returns:
            Any: The result of the function execution.

        Raises:
            Exception: If an error occurs during the function execution.
        """
        try:
            logger.info("Start Node", extra={"id": self.id, "name_class": self.name})

            if not self.positional_or_keyword:
                logger.info("Select input args", extra={"id": self.id, "name_class": self.name})
                inp_args = _input_args(args, kwargs, node_args=self.args)
                logger.info("End Node", extra={"id": self.id, "name_class": self.name})
                return self.func(**inp_args)

            logger.info("End Node", extra={"id": self.id, "name_class": self.name})
            return self.func(*args, **kwargs)
        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

    def __repr__(self) ->str:
        """
        Returns a string representation of the node, including its 
        ID, arguments, name, and description.

        Returns:
            str: A JSON string representing the node's ID, arguments, name, and description.
        """
        json_repr = json.dumps({
            "id": self.id,
            "args": self.args,
            "name": self.name,
            "description": self.description 
        })
        return f"Node({json_repr})"


class IfNode(Node):
    """
    A class representing a if node in a chain, which executes one of 
    two nodes based on a boolean condition.

    This class extends the `Node` class to include conditional logic. 
    It allows for branching in a chain by 
    executing either a `true_node` or a `false_node` depending on 
    the boolean result of the function.

    Attributes:
        true_node (Base): The node to execute if the condition evaluates to True.
        false_node (Base): The node to execute if the condition evaluates to False.

    Methods:
        __init__(func, true_node, false_node):
            Initializes a IfNode instance with a callable function 
            and two possible nodes for execution.
        
        __call__(*args, **kwargs):
            Executes the conditional logic by evaluating the function 
            and executing the appropriate node.
        
        __repr__():
            Returns a string representation of the if node, including 
            its ID, arguments, name, and description.
    """
    def __init__(self, func: Callable,
                 true_node: Base,
                 false_node: Base):
        """
        Initializes a IfNode instance with a callable function and two possible nodes for execution.

        Args:
            func (Callable): The function that determines the condition for branching.
            true_node (Union[Base]): The node to execute if the function's result is True.
            false_node (Union[Base]): The node to execute if the function's result is False.

        Attributes:
            true_node (Base): A deep copy of the true_node with a new unique ID.
            false_node (Base): A deep copy of the false_node with a new unique ID.
        """
        super().__init__(func)
        _check_input_node([true_node, false_node])
        true_node = deepcopy(true_node)
        true_node.id = true_node.name + str(next(counter))
        if hasattr(true_node, "_nodes"):
            true_node._nodes = _reset_id(true_node._nodes)

        false_node = deepcopy(false_node)
        false_node.id = false_node.name + str(next(counter))
        if hasattr(false_node, "_nodes"):
            false_node._nodes = _reset_id(false_node._nodes)

        self.true_node = true_node
        self.false_node = false_node

    def __call__(self, *args, **kwargs)-> Any:
        """
        Executes the conditional logic by evaluating the function 
        and executing the appropriate node.

        Args:
            *args: Positional arguments to pass to the function and nodes.
            **kwargs: Keyword arguments to pass to the function and nodes.

        Returns:
            Any: The result of executing either the true_node or the false_node 
            based on the function's boolean result.

        Raises:
            AssertionError: If the function's output is not a boolean.
            Exception: If an error occurs during the execution of the function or nodes.
        """
        try:
            logger.info("Start IfNode", extra={"id": self.id, "name_class": self.name})
            logger.info("Get bool value", extra={"id": self.id, "name_class": self.name})
            if not self.positional_or_keyword:
                logger.info("Select input args", extra={"id": self.id, "name_class": self.name})
                inp_args = _input_args(args, kwargs, node_args=self.args)
                res = self.func(**inp_args)
                assert isinstance(res, bool), "The output of IfNode's function must be boolean"
            else:
                res = self.func(*args, **kwargs)
                assert isinstance(res, bool), "The output of IfNode's function must be boolean"

            logger.info("Execute %s Node", str(res), extra={"id": self.id, "name_class": self.name})
            logger.info("End IfNode", extra={"id": self.id, "name_class": self.name})
            return  self.true_node(*args, **kwargs) if res else self.false_node(*args, **kwargs)
        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

    def __repr__(self) ->str:
        """
        Returns a string representation of the if node, including its 
        ID, arguments, name, and description.

        Returns:
            str: A JSON string representing the node's ID, arguments, name, and description.
        """
        json_repr = json.dumps({
            "id": self.id,
            "args": self.args,
            "name": self.name
        })
        return f"IfNode({json_repr})"


class LoopNode(Node):
    """
    A class representing a loop node in a chain that executes a specified 
    node repeatedly until a condition is met.

    This class extends the `Node` class to include looping logic. 
    It executes a `loop_node` in each iteration until 
    the `condition_func` returns True. The loop continues 
    to execute `loop_node` with the result of the previous 
    execution until the condition is satisfied.

    Attributes:
        loop_node (Base): The node to execute in each iteration of the loop.
        condition_func (Callable): A function that determines when to stop the loop. 
        It is called with the result of 
            the `loop_node` execution and should return a boolean value.

    Methods:
        __init__(condition_func, loop_node):
            Initializes a LoopNode instance with a callable function
            and a node to execute in the loop.

        __call__(*args, **kwargs):
            Executes the loop node repeatedly until the condition function returns True.

        __repr__():
            Returns a string representation of the loop node, including its ID and name.
    """

    def __init__(self, condition_func: Callable, loop_node: Base) ->None:
        """
        Initializes a LoopNode instance with a callable function and a node to execute in the loop.

        Args:
            condition_func (Callable): A function that receives the result of the 
            `loop_node` and returns a boolean 
                indicating whether the loop should continue or stop.
            loop_node (Base): The node to execute in each iteration of the loop. 
            This node is executed repeatedly until `condition_func` returns True.

        Attributes:
            loop_node (Base): A deep copy of the `loop_node` with a new unique ID. 
            The node's `_nodes` attribute, 
                if present, is reset with new IDs.
        """
        super().__init__(condition_func)
        _check_input_node([loop_node])
        loop_node = deepcopy(loop_node)
        loop_node.id = loop_node.name + str(next(counter))
        if hasattr(loop_node, "_nodes"):
            loop_node._nodes = _reset_id(loop_node._nodes)

        self.loop_node = loop_node

    def __call__(self, *args, **kwargs) -> Any:
        """
        Executes the loop node repeatedly until the condition function returns True.

        Args:
            *args: Positional arguments to pass to the loop node.
            **kwargs: Keyword arguments to pass to the loop node.

        Returns:
            Any: The result of the last execution of `loop_node` when the condition is met.

        Raises:
            AssertionError: If the result of `condition_func` is not a boolean.
            Exception: If an error occurs during the execution 
            of the loop node or the condition function.
        """
        try:
            logger.info("Start LoopNode", extra={"id": self.id, "name_class": self.name})
            iteration = 0
            condition_met = False

            while not condition_met:
                logger.info("Iteration %s", str(iteration),
                            extra={"id": self.id, "name_class": self.name})
                if iteration == 0:
                    result = self.loop_node(*args, **kwargs)
                else:
                    if isinstance(result, (list, tuple)):
                        result = self.loop_node(*result)
                    elif isinstance(result, dict):
                        result = self.loop_node(**result)
                    else:
                        result = self.loop_node(result)

                if isinstance(result, (list, tuple)):
                    condition_met = self.func(*result)
                elif isinstance(result, dict):
                    condition_met = self.func(**result)
                else:
                    condition_met = self.func(result)
                iteration += 1

            logger.info("End LoopNode", extra={"id": self.id, "name_class": self.name})
            return result

        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

    def __repr__(self) -> str:
        """
        Returns a string representation of the loop node, including its ID and name.

        Returns:
            str: A JSON string representing the node's ID and name.
        """
        json_repr = json.dumps({
            "id": self.id,
            "name": self.name
        })
        return f"LoopNode({json_repr})"

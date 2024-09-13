from .utils import _input_args, _is_positional_or_keyword, _get_args, CSS_MERMAID
from typing import Any, Optional, Callable, Union, List, Dict, Tuple
from functools import lru_cache
from copy import deepcopy
import inspect
import logging
import json
import os
import multiprocessing.pool
import requests
import base64
import uuid

logger = logging.getLogger(__name__)

lru_cache(maxsize=2)
def _reset_id(nodes: list):
    nodes = [deepcopy(node) for node in nodes]
    for node in nodes:
        node.id = str(uuid.uuid4())
        if isinstance(node, ConditionalNode):
            node.true_node = deepcopy(node.true_node)
            node.true_node.id = str(uuid.uuid4())
            if hasattr(node.true_node, "_nodes"):
                node.true_node._nodes = _reset_id(node.true_node._nodes) 

            node.false_node = deepcopy(node.false_node)
            node.false_node.id = str(uuid.uuid4())
            if hasattr(node.false_node, "_nodes"):
                node.false_node._nodes = _reset_id(node.false_node._nodes)
        elif isinstance(node, (Chain, Layer)):
            node._nodes = _reset_id(node._nodes)
    return nodes

lru_cache(maxsize=2)
def _create_mermaid(nodes: list):
    lines = []
    first_node = None
    last_node = None
    for node in nodes:
        if isinstance(node, Node):
            if isinstance(node, ConditionalNode):
                # If the shape is diamond, use the appropriate Mermaid syntax
                lines.append(f"{node.id}{{{node.name}}}:::diamond;")

                if hasattr(node.true_node ,"_nodes"):
                    true_nodes = node.true_node._nodes
                else:
                    true_nodes = [node.true_node]

                if hasattr(node.false_node ,"_nodes"):
                    false_nodes = node.false_node._nodes
                else:
                    false_nodes = [node.false_node]

                first_node_true, lines_true, last_node_true = _create_mermaid(true_nodes)
                first_node_false, lines_false, last_node_false = _create_mermaid(false_nodes)

                for x in first_node_true:
                    lines.append(f"{node.id} -- True --> {x.id};")
                for y in first_node_false:
                    lines.append(f"{node.id} -- False --> {y.id};")
                
                if isinstance(node.true_node, Chain):
                    lines.append("subgraph \" \";")
                    lines += lines_true
                    lines.append("end;")
                else:
                    lines += lines_true
                
                if isinstance(node.false_node, Chain):
                    lines.append("subgraph \" \";")
                    lines += lines_false
                    lines.append("end;")
                else:
                    lines += lines_false
                
                if last_node is not None:
                    for x in last_node:
                        lines.append(f"{x.id} --> {node.id};")
                
                if first_node is None:
                    first_node = [node]
                
                last_node = last_node_false + last_node_true
            else:
                lines.append(f"{node.id}[{node.name}]:::rectangle;")

                if first_node is None:
                    first_node = [node]
                
                if last_node is not None:
                    for x in last_node:
                        lines.append(f"{x.id} --> {node.id};")
                last_node = [node]
        elif isinstance(node, Layer):
            list_layer = []
            for x in node._nodes:
                if hasattr(x ,"_nodes"):
                    list_layer.append(_create_mermaid(x._nodes))
                else:
                    list_layer.append(_create_mermaid([x]))

            for i in range(len(node._nodes)):
                if isinstance(node._nodes[i], Chain):
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
        elif isinstance(node, Chain):
            chain_first_node, chain_line, chain_last_node = _create_mermaid(node._nodes)

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
def _check_input_node(inputs) ->None:
    # If inputs is a list, tuple, or dict, iterate through each element
    if isinstance(inputs, (list, tuple, dict)):
        for inp in inputs:
            # If inputs is a dict, check each value
            if isinstance(inputs, dict):
                _check_input_node(inputs[inp])
            else:
                # Otherwise, check each item in the list or tuple
                _check_input_node(inp)
    else:
        # If input is not a Chain, Node, or Layer, raise a TypeError
        if not isinstance(inputs, Base):
            raise TypeError('Only "BaseChain", or lists of this class can be used as inputs')

lru_cache(maxsize=2)
def _convert_parallel_node(inputs) ->Any:
    # If inputs is a Chain, Node, or Layer, return it as is
    if isinstance(inputs, Base):
        return inputs
    else:
        if isinstance(inputs, dict):
            # If inputs is a dict, convert each value
            for key in inputs:
                if isinstance(inputs[key], (list, tuple, dict)):
                    inputs[key] = _convert_parallel_node(inputs[key])
        else:
            # If inputs is a list or tuple, convert each element
            for i in range(len(inputs)):
                if isinstance(inputs[i], (list, tuple, dict)):
                    inputs[i] = _convert_parallel_node(inputs[i])
        return Layer(inputs)

# Decorator function to create a node or conditional_node
def node(description: Optional[str] = None,  
         name: Optional[str] = None, 
         conditional: bool = False, 
         true_node: Optional[Union["Base"]] = None, 
         false_node: Optional[Union["Base"]] = None):
    def run_node(func: Callable):
        if conditional and true_node is not None and false_node is not None:
            return ConditionalNode(func, true_node=true_node, 
                                   false_node=false_node, 
                                   description=description, 
                                   name=name)
        else:
            return Node(func, description=description, name=name)
    
    return run_node

class Base:
    # Method to add a node to the chain

    def add_node(self, *args, **kwargs) ->"Base":
        raise NotImplementedError("This method should be implemented by subclasses")
    
    # Overloading the >> operator to add a node after the current chain
    def __rshift__(self, other) ->"Base":
        return self.add_node(other, before=False)
    
    # Overloading the << operator to add a node before the current chain
    def __rlshift__(self, other) ->"Base":
        return self.add_node(other, before=False)
    
    # Overloading the << operator to add a node before the current chain
    def __lshift__(self, other) ->"Base":
        return self.add_node(other, before=True)
    
    # Overloading the >> operator to add a node after the current chain
    def __rrshift__(self, other) ->"Base":
        return self.add_node(other, before=True)

class Chain(Base):
    def __init__(self, nodes: List[Base], name: str = "Chain", description: Optional[str] = None):
        # Ensure there are at least two nodes in the chain
        assert len(nodes) > 1, "There must be at least two nodes"
        _check_input_node(nodes)
        nodes = _reset_id(nodes)
        self._nodes = nodes
        self.name = name
        self.description = description
        self.id = str(uuid.uuid4())

    def add_node(self, other, before: bool) ->Base:
        # Create a deep copy of the current instance to avoid modifying the original
        _check_input_node(other)
        # Convert the input node into layer if one is a list, tuple or dict
        other = _convert_parallel_node(other)
        if before:
            chain = Chain(nodes=[other] + self._nodes)
        else:
            chain = Chain(nodes=self._nodes + [other])
        chain._nodes = _reset_id(chain._nodes)
        return chain
        
    
    def __call__(self, *args, **kwargs):
        try:
            # Initialize a variable to store the output of the nodes
            x = None
            # Iterate over the nodes in the chain
            for i, node in enumerate(self._nodes):
                # For the first node, pass the arguments directly
                if i == 0:
                    x = node(*args, **kwargs)
                else:
                    # For subsequent nodes, process the output from the previous node
                    if isinstance(x, (list, tuple)):
                        # If the output is a list or tuple, unpack it as positional arguments
                        x = node(*x)
                    elif isinstance(x, dict):
                        # If the output is a dictionary, unpack it as keyword arguments
                        x = node(**x)
                    else:
                        # Otherwise, pass the output as a single argument
                        x = node(x)
            return x
        except Exception as e:
            logger.error(e, exc_info=True, extra={"id": self.name})

    def view(self, direction: str = "TB", path: Optional[str] = None):
        mg = "\n".join(_create_mermaid(self._nodes)[1])
        mg = f"flowchart {direction};\n" + mg + CSS_MERMAID
        graphbytes = mg.encode("utf8")
        base64_bytes = base64.urlsafe_b64encode(graphbytes)
        base64_string = base64_bytes.decode("ascii")
        response = requests.get("https://mermaid.ink/img/" + base64_string)
        if response.status_code == 200:
            path_img = f'{self.name}.png' if path is None else path
            with open(path_img, 'wb') as file:
                file.write(response.content)
        else:
            print(f"Failed to generate PNG image. Status code: {response.status_code}")
    
    def __repr__(self) -> str:
        json_repr = json.dumps({
            "id": self.id,
            "name": self.name,
            "description": self.description 
        })
        return f"Chain({json_repr})"
    

class Layer(Base):
    def __init__(self, nodes: Union[List[Base], Tuple[Base], Dict[str, Base]], 
                 name: str = "Layer", 
                 description: Optional[str] = None):
        # Ensure that there are no nested layers within this layer
        assert len([node for node in nodes if isinstance(node, Layer)]) == 0, "Layers cannot contain other Layers"
        # Check if the input nodes are valid
        _check_input_node(nodes)
        # Store the nodes in the layer
        nodes = _reset_id(nodes)
        self._nodes = nodes
        self.name = name
        self.description = description
        # Determine if the nodes are stored in a dictionary
        self._is_dict = True if isinstance(nodes, dict) else False
        self.id = str(uuid.uuid4())

    def add_node(self, other, before: bool) ->Base:
        # Check if the input node is valid
        _check_input_node(other)
        # Convert the input node into layer if one is a list, tuple or dict
        other = _convert_parallel_node(other)
        # Insert the node before or after the current layer based on the 'before' flag and create a Chain
        if before:
            chain = Chain(nodes=[other, self])
        else:
            chain = Chain(nodes=[self, other])
        chain._nodes = _reset_id(chain._nodes)
        return chain
    
    def __call__(self, *args, **kwargs)->Any:
        try:
        # Initialize the result container as a dictionary if nodes are stored in a dictionary, otherwise as a list
            res = {} if self._is_dict else []
            # Determine the number of CPU cores to use, at least 1 and at most half of the available cores
            cpus = max([int(os.cpu_count()/2), 1])
            # Function to run a node with given arguments, used into Thread Pool
            run_node = lambda node, args, kwargs: node(*args, **kwargs)
            # Use a thread pool to parallelize the execution of nodes
            with multiprocessing.pool.ThreadPool(cpus) as pool:
                if self._is_dict:
                    # If nodes are stored in a dictionary, create a mapping of nodes to their arguments
                    keys = list(self._nodes.keys())
                    nodes = list(self._nodes.values())
                    input_map = [(node, args, kwargs) for node in nodes]
                    # Execute the nodes in parallel and store the results in a dictionary
                    output = pool.starmap(run_node, input_map)
                    res = {y: x for y, x in zip(keys, output)}
                else:
                    # If nodes are stored in a list or tuple, create a mapping of nodes to their arguments
                    input_map = [(node, args, kwargs) for node in self._nodes]
                    # Execute the nodes in parallel and store the results in a list
                    res = pool.starmap(run_node, input_map)
            return res
        except Exception as e:
            logger.error(e, exc_info=True, extra={"id": self.name})
    
    def __repr__(self) -> str:
        json_repr = json.dumps({
            "id": self.id,
            "name": self.name,
            "description": self.description 
        })
        return f"Layer({json_repr})"


class Node(Base):
    def __init__(self, 
                 func: Callable,
                 description: Optional[str] = None,
                 name: Optional[str] = None):
        # Determine if the function accepts positional or keyword arguments
        self.positional_or_keyword = _is_positional_or_keyword(func)
        # Set the name of the node to the function's name
        self.name = func.__name__
        # Get the function's docstring as its description
        self.description = inspect.getdoc(func)
        # Retrieve the function's argument names
        self.args = _get_args(func)
        # If a custom description is provided, use it
        if description is not None:
            self.description = description
        # If a custom name is provided, use it
        if name is not None:
            self.name = name
        # Store the function to be executed by the node
        self.func = func
        self.id = str(uuid.uuid4())

    def add_node(self, other, before: bool) ->Base:
        # Check if the input node is valid
        _check_input_node(other)
        # Convert the input node into layer if one is a list, tuple or dict
        other = _convert_parallel_node(other)
        # Create a deep copy of the input node to avoid modifying the original
        if before:
            chain = Chain(nodes=[other, self])
        else:
            chain = Chain(nodes=[self, other])
        chain._nodes = _reset_id(chain._nodes)
        return chain
    
    def __call__(self, *args, **kwargs)-> Any:
        try:
        # If the function does not accept positional arguments
            logger.info("Start Node", extra={"id": self.name})
            if not self.positional_or_keyword:
                # Map the input arguments to the function's parameters
                logger.info("Select input args", extra={"id": self.name})
                inp_args = _input_args(args, kwargs, node_args=self.args)
                # Call the function with keyword arguments
                logger.info("End Node", extra={"id": self.name})
                return self.func(**inp_args)
            else:
                # Call the function with positional arguments
                logger.info("End Node", extra={"id": self.name})
                return self.func(*args, **kwargs)
        except Exception as e:
            logger.error(e, exc_info=True, extra={"id": self.name})
    
    def __repr__(self) ->str:
        json_repr = json.dumps({
            "id": self.id,
            "args": self.args,
            "name": self.name,
            "description": self.description 
        })
        return f"Node({json_repr})"
    

class ConditionalNode(Node):
    def __init__(self, func: Callable, 
                 true_node: Union[Base],
                 false_node: Union[Base],
                 description: Optional[str] = None, 
                 name: Optional[str] = None):
        super().__init__(func, description, name)
        true_node = deepcopy(true_node)
        true_node.id = str(uuid.uuid4())
        if hasattr(true_node, "_nodes"):
            true_node._nodes = _reset_id(true_node._nodes)
        
        false_node = deepcopy(false_node)
        false_node.id = str(uuid.uuid4())
        if hasattr(false_node, "_nodes"):
            false_node._nodes = _reset_id(false_node._nodes)
        
        self.true_node = true_node
        self.false_node = false_node
    
    def __call__(self, *args, **kwargs)-> Any:
        # If the function does not accept positional arguments
        try:
            logger.info("Start ConditionlNode", extra={"id": self.name})
            logger.info("Get bool value", extra={"id": self.name})
            if not self.positional_or_keyword:
                # Map the input arguments to the function's parameters
                logger.info("Select input args", extra={"id": self.name})
                inp_args = _input_args(args, kwargs, node_args=self.args)
                # Call the function with keyword arguments
                res = self.func(**inp_args)
                assert isinstance(res, bool), "The output of ConditionalNode's function must be boolean"
            else:
                # Call the function with positional arguments
                res = self.func(*args, **kwargs)
                assert isinstance(res, bool), "The output of ConditionalNode's function must be boolean"

            logger.info(f"Execute {str(res)} Node", extra={"id": self.name})
            logger.info("End conditionalNode", extra={"id": self.name})
            # if the output is true the true_node will be executed, otherwise the false_node
            return  self.true_node(*args, **kwargs) if res else self.false_node(*args, **kwargs)
        except Exception as e:
            logger.error(e, exc_info=True, extra={"id": self.name})
        
    def __repr__(self) ->str:
        json_repr = json.dumps({
            "id": self.id,
            "args": self.args,
            "name": self.name,
            "description": self.description 
        })
        return f"ConditionalNode({json_repr})"
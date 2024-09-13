import inspect
import random
import string
from typing import Callable, Tuple, List, Dict, Optional


CSS_MERMAID = """

classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
"""

# Function to map input arguments to the node's parameters
def _input_args(args: Tuple, kwargs: Dict, node_args: List) ->Dict:
    # Create a dictionary of keyword arguments that match the node's parameters
    output_args = {node_args[node_args.index(kw)]: kwargs[kw] for kw in kwargs if kw in node_args}
    # If there are no positional arguments, return the keyword arguments
    if len(args) == 0:
        return output_args
    
    # Determine the missing node arguments that need to be filled by positional arguments
    loss_node_arg = [x for x in node_args if x not in output_args]
    if len(loss_node_arg) > 0:
        # Adjust the length of positional arguments if necessary
        if len(args) > len(loss_node_arg):
            args = args[:len(loss_node_arg)]
        elif len(args) < len(loss_node_arg):
            loss_node_arg = loss_node_arg[:len(args)]
        
        # Add the positional arguments to the output dictionary
        output_args |= {y:x for x, y in zip(args, loss_node_arg)}
    return output_args

# Function to check if a function accepts positional or keyword arguments
def _is_positional_or_keyword(func: Callable) ->bool:
    # Get the function's signature
    sig = inspect.signature(func)
    # Iterate through the function's parameters
    for param in sig.parameters.values():
        # Check if the parameter kind is either VAR_POSITIONAL or VAR_KEYWORD
        if param.kind == param.VAR_POSITIONAL or param.kind == param.VAR_KEYWORD:
            return True
    return False

# Function to get the list of argument names of a function
def _get_args(func: Callable) ->bool:
    # Get the function's signature
    sig = inspect.signature(func)
    # Return a list of parameter names
    return [name for name in sig.parameters.keys()]
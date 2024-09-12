import inspect
import random
import string
from typing import Callable, Tuple, List, Dict, Optional

class MermaidGraph:
    def __init__(self, direction: str ="TB"):
        # Initializes the graph with a direction (default is Top-Bottom)
        self.direction = direction
        self.nodes = {}  # Dictionary to store nodes with their labels and shapes
        self.edges = []  # List to store edges between nodes
    
    def add_node(self, node_id: str, label: Optional[str] = None, shape: Optional[str] = None):
        # Adds a node to the graph with an optional label and shape (e.g., rectangle, diamond)
        self.nodes[node_id] = {"label": label, "shape": shape}
    
    def add_edge(self, from_node: str, to_node: str, label: Optional[str] = None):
        # Adds an edge between two nodes with an optional label
        # Raises an error if one or both of the nodes have not been added
        if from_node not in self.nodes or to_node not in self.nodes:
            raise ValueError("Both nodes must be added before adding an edge.")
        self.edges.append((from_node, to_node, label))
    
    def generate_mermaid_code(self):
        # Generates the Mermaid diagram code based on the nodes and edges
        lines = [f"graph {self.direction};"]
        
        # Add nodes with their labels and shapes
        for node_id, properties in self.nodes.items():
            label = properties["label"]
            shape = properties["shape"]
    
            if shape == "diamond":
                # If the shape is diamond, use the appropriate Mermaid syntax
                lines.append(f"    {node_id}{{{label}}};")
            else:
                # Default shape is rectangle
                lines.append(f"    {node_id}[{label}];")
        
        # Add edges between nodes with optional labels
        for from_node, to_node, label in self.edges:
            if label:
                # If the edge has a label, include it
                lines.append(f"    {from_node} -- {label} --> {to_node};")
            else:
                # If the edge doesn't have a label, just connect the nodes
                lines.append(f"    {from_node} --> {to_node};")

        # Define CSS-like styles for rectangles and diamonds in the Mermaid diagram
        lines.append("""
        classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
        classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
        """)

        # Apply the styles to the nodes based on their shape
        for node_id, properties in self.nodes.items():
            if properties["shape"] == "diamond":
                lines.append(f"class {node_id} diamond;")
            else:
                lines.append(f"class {node_id} rectangle;")

        # Return the final Mermaid code as a string
        return "\n".join(lines)

def _create_mermaid(edges: list, nodes: list, name: str):
    # Helper function to create a Mermaid graph dynamically using nodes and edges
    mg = MermaidGraph(direction="LR")  # Set the graph direction (e.g., Left-Right)
    
    # Add nodes with optional shape properties
    for x in nodes:
        if len(x) == 3:
            mg.add_node(x[0], x[1], shape=x[2]["shape"])
        else:
            mg.add_node(x[0], x[1])
    
    # Add edges with optional labels
    for x in edges:
        if len(x) == 3:
            mg.add_edge(x[0], x[1], label=x[2]["label"])
        else:
            mg.add_edge(x[0], x[1])
    
    # Generate and return the Mermaid diagram code
    return mg.generate_mermaid_code()

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
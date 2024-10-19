"""This module contains utility functions.

Functions:
    - _deprecated_method(msg): A decorator that marks methods
                               as deprecated with a custom warning message.
    - _id_counter(): A generator function for
                     sequential integer IDs starting from 1.
    - _input_args(args, kwargs, node_args): Maps input arguments to
        the expected parameter names of a node function.
    - _is_positional_or_keyword(func): Determines if a callable object
        accepts variadic positional or keyword arguments.
    - _get_args(func): Extracts and returns a list of argument names
        (including variadic args) from a callable function's signature.
    - _get_docs(func): Retrieves the docstring of a callable object.

Variables:
    - CSS_MERMAID: A string containing CSS styles for visualizing
                   chains in Mermaid diagrams. It defines different
                   styles for representing nodes
                   (e.g., rectangle, diamond, loop) in visual flows.

Usage:
    These utility functions are primarily used for
    inspecting and manipulating callable objects, handling
    input arguments for nodes, and providing support
    for deprecated methods and custom ID generation.
"""

from typing import Callable, Tuple, List, Dict
import warnings
from functools import wraps
import inspect

R_CSS = "fill:#89CFF0,stroke:#003366,stroke-width:2px"
D_CSS = "fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray:5"
D_LOOP_CSS = "fill:#DDA0DD,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray:5"

CSS_MERMAID = F"""

classDef rectangle {R_CSS};
classDef diamond {D_CSS};
classDef diamond_loop {D_LOOP_CSS};
"""


def _deprecated_method(msg):
    """Mark methods as deprecated with a custom warning message.

    Args:
        msg (str): The custom message to display with the deprecation warning.

    Returns:
        Callable: A decorator that wraps the original method.
    """

    def decorator(func):
        """Actual decorator function that wraps the method."""

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Wrap function that issues a `DeprecationWarning`.

            Args:
                *args: Positional arguments passed to the decorated method.
                **kwargs: Keyword arguments passed to the decorated method.

            Returns:
                The result of calling the decorated method.
            """
            warnings.warn(
                f"{func.__name__} is deprecated and will be removed "
                f"in a future version: {msg}",
                category=DeprecationWarning,
                stacklevel=2,
            )
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _id_counter():
    """Generate sequential integer IDs.

    This functions provides a mechanism to generate unique integer IDs
    starting from 1.

    Returns:
        int: Return the integer IDs.

    Notes:
        - The function use "yield" instead of "return" in order
        to remember the previous value of counter variable.
    """
    counter = 1
    while True:
        yield counter
        counter += 1


def _input_args(args: Tuple, kwargs: Dict, node_args: List) -> Dict:
    """Map input arguments and keyword arguments.

    This function creates a dictionary that maps the positional
    and keyword arguments to the expected parameter names
    of a node function. It takes into account the order and
    availability of arguments to ensure that all required
    parameters are properly assigned.

    Args:
        args (Tuple): A tuple of positional arguments provided
        to the node function.
        kwargs (Dict): A dictionary of keyword arguments provided
        to the node function.
        node_args (List): A list of parameter names expected
        by the node function, in the order they are defined.

    Returns:
        Dict: A dictionary mapping parameter names to their corresponding
              values from `args` and `kwargs`. The dictionary
              includes both positional and keyword arguments
              as required by the node function.
    """
    output_args = {
        node_args[node_args.index(kw)]: kwargs[kw]
        for kw in kwargs
        if kw in node_args
    }
    if len(args) == 0:
        return output_args

    loss_node_arg = [x for x in node_args if x not in output_args]
    if len(loss_node_arg) > 0:
        if len(args) > len(loss_node_arg):
            args = args[: len(loss_node_arg)]
        elif len(args) < len(loss_node_arg):
            loss_node_arg = loss_node_arg[: len(args)]

        output_args |= {y: x for x, y in zip(args, loss_node_arg)}
    return output_args


def _is_positional_or_keyword(func: Callable) -> bool:
    """Determine variadic positional or keyword arguments.

    This function inspects the signature of the provided
    callable object and checks if it includes parameters
    that are variadic positional (`*args`) or variadic
    keyword arguments (`**kwargs`). If such parameters are found,
    the function returns `True`; otherwise, it returns `False`.

    Args:
        func (Callable): The callable object (function) to be inspected.

    Returns:
        bool: `True` if the callable accepts variadic
        positional or keyword arguments; otherwise, `False`.
    """
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            return True
    return False


def _get_args(func: Callable) -> List:
    """Extract and returns a list of argument.

    This function inspects the signature of a given callable
    object (such as a function) and generates a list
    of argument names in the order they appear.
    It includes special markers for variadic positional (`*args`) and
    keyword arguments (`**kwargs`).

    Args:
        func (Callable): The callable object (function) from which
        to extract argument information.

    Returns:
        List[str]: A list of argument names, including special markers
                   for variadic arguments.
                   For example, `["arg1", "arg2*", "arg3**"]` indicates
                   `arg1`, `arg2` (as variadic positional),
                   and `arg3` (as variadic keyword) arguments.
    """
    sig = inspect.signature(func)
    list_args = []
    for name, param in sig.parameters.items():
        if param.kind == param.VAR_POSITIONAL:
            list_args.append(name + "*")
        elif param.kind == param.VAR_KEYWORD:
            list_args.append(name + "**")
        else:
            list_args.append(name)
    return list_args


def _get_docs(func: Callable) -> str:
    """Retrieve the docstring of a callable object as a string.

    This function uses the `inspect` module to obtain
    the documentation string (docstring) associated with the
    provided callable object. The docstring
    provides a description of the callable's purpose and usage, if present.

    Args:
        func (Callable): The callable object (function)
        from which to retrieve the docstring.

    Returns:
        str: The docstring of the callable object.
        Returns `None` if no docstring is present.
    """
    return inspect.getdoc(func)

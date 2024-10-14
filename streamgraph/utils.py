import inspect
from typing import Callable, Tuple, List, Dict


CSS_MERMAID = """

classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
classDef diamond_loop fill:#DDA0DD,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray: 5;
"""
    
def _id_counter():
    """A simple generation function to generate sequential integer IDs.
    
    This functions provides a mechanism to generate unique integer IDs
    starting from 1.

    Returns:
        int: Return the integer IDs.

    Example:
        >>> _id_counter()
        1
        >>> _id_counter()
        2

    Notes:
        - The function use "yield" instead of "return" in order to remember the previous value of counter variable.
    """
    counter = 1
    while True:
        yield counter
        counter += 1

def _input_args(args: Tuple, kwargs: Dict, node_args: List) ->Dict:
    """
    Maps input arguments and keyword arguments to the expected parameter names of a node function.

    This function creates a dictionary that maps the positional and keyword arguments to the expected parameter names
    of a node function. It takes into account the order and availability of arguments to ensure that all required
    parameters are properly assigned.

    Args:
        args (Tuple): A tuple of positional arguments provided to the node function.
        kwargs (Dict): A dictionary of keyword arguments provided to the node function.
        node_args (List): A list of parameter names expected by the node function, in the order they are defined.

    Returns:
        Dict: A dictionary mapping parameter names to their corresponding values from `args` and `kwargs`. The dictionary
              includes both positional and keyword arguments as required by the node function.

    Example:
        >>> def example_func(a, b, c):
        ...     pass
        >>> _input_args((1, 2), {'c': 3}, ['a', 'b', 'c'])
        {'a': 1, 'b': 2, 'c': 3}

        >>> _input_args((), {'a': 1, 'b': 2}, ['a', 'b'])
        {'a': 1, 'b': 2}

    Notes:
        - The function first maps keyword arguments to their corresponding parameter names.
        - If there are positional arguments left after mapping keyword arguments, they are assigned to the remaining parameter names.
        - The function ensures that the number of positional arguments does not exceed the number of remaining parameter names.
        - If there are fewer positional arguments than remaining parameter names, only the available positional arguments are used.
    """
    output_args = {node_args[node_args.index(kw)]: kwargs[kw] for kw in kwargs if kw in node_args}
    if len(args) == 0:
        return output_args
    
    loss_node_arg = [x for x in node_args if x not in output_args]
    if len(loss_node_arg) > 0:
        if len(args) > len(loss_node_arg):
            args = args[:len(loss_node_arg)]
        elif len(args) < len(loss_node_arg):
            loss_node_arg = loss_node_arg[:len(args)]
        
        output_args |= {y:x for x, y in zip(args, loss_node_arg)}
    return output_args

def _is_positional_or_keyword(func: Callable) ->bool:
    """
    Determines whether a callable object (e.g., function) accepts variadic positional or keyword arguments.

    This function inspects the signature of the provided callable object and checks if it includes parameters
    that are variadic positional (`*args`) or variadic keyword arguments (`**kwargs`). If such parameters are found,
    the function returns `True`; otherwise, it returns `False`.

    Args:
        func (Callable): The callable object (function) to be inspected.

    Returns:
        bool: `True` if the callable accepts variadic positional or keyword arguments; otherwise, `False`.

    Example:
        >>> def func_with_args(a, b, *args, **kwargs):
        ...     pass
        >>> _is_positional_or_keyword(func_with_args)
        True

        >>> def func_without_args(a, b):
        ...     pass
        >>> _is_positional_or_keyword(func_without_args)
        False

    Notes:
        - The function uses the `inspect` module to retrieve and analyze the function's signature.
        - Variadic positional arguments are indicated by `param.VAR_POSITIONAL`.
        - Variadic keyword arguments are indicated by `param.VAR_KEYWORD`.
    """
    sig = inspect.signature(func)
    for param in sig.parameters.values():
        if param.kind == param.VAR_POSITIONAL or param.kind == param.VAR_KEYWORD:
            return True
    return False

def _get_args(func: Callable) ->List:
    """
    Extracts and returns a list of argument names and their types from the signature of a callable function.

    This function inspects the signature of a given callable object (such as a function) and generates a list
    of argument names in the order they appear. It includes special markers for variadic positional (`*args`) and 
    keyword arguments (`**kwargs`).

    Args:
        func (Callable): The callable object (function) from which to extract argument information.

    Returns:
        List[str]: A list of argument names, including special markers for variadic arguments. 
                   For example, `["arg1", "arg2*", "arg3**"]` indicates `arg1`, `arg2` (as variadic positional), 
                   and `arg3` (as variadic keyword) arguments.

    Example:
        >>> def example_func(a, b, *args, **kwargs):
        ...     pass
        >>> _get_args(example_func)
        ['a', 'b', '*args', '**kwargs']

        >>> def another_func(x, y, z=3, *varargs, **kwargs):
        ...     pass
        >>> _get_args(another_func)
        ['x', 'y', 'z', '*varargs', '**kwargs']

    Notes:
        - The function uses the `inspect` module to retrieve and process the function signature.
        - Variadic positional arguments (`*args`) are denoted with a trailing '*'.
        - Variadic keyword arguments (`**kwargs`) are denoted with a trailing '**'.
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
    """
    Retrieves the docstring of a callable object (e.g., function) as a string.

    This function uses the `inspect` module to obtain the documentation string (docstring) associated with the 
    provided callable object. The docstring provides a description of the callable's purpose and usage, if present.

    Args:
        func (Callable): The callable object (function) from which to retrieve the docstring.

    Returns:
        str: The docstring of the callable object. Returns `None` if no docstring is present.

    Example:
        >>> def sample_function(param1, param2):
        ...     \"\"\"This is a sample function that does something.\"\"\"
        ...     pass
        >>> _get_docs(sample_function)
        'This is a sample function that does something.'

        >>> def another_function():
        ...     pass
        >>> _get_docs(another_function)
        None

    Notes:
        - The function uses `inspect.getdoc()` to access the docstring.
        - If the callable object does not have a docstring, `None` is returned.
    """
    return inspect.getdoc(func)
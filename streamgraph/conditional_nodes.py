"""This module defines specialized conditional node classes.

the computational pipeline. These classes extend the base
`Node` class from the base module.

Classes:
    IfNode: A specialized type of Node that adds conditional logic.
            It evaluates a condition, and based on the
            result, it executes either the `true_node` or the `false_node`.

    LoopNode: A specialized type of Node that represents looping logic.
              It iterates over the `loop_node` for
              a specified number of times or until a condition is met.

Decorators:
    @ifnode: A decorator that allows a function to be wrapped in an IfNode.
             It accepts a condition, a `true_node`,
             and a `false_node` for conditional execution within a chain.

    @loopnode: A decorator that allows a function to be wrapped in a LoopNode.
               It accepts a `loop_node` for
               repeated execution and loop iteration logic.

This module is designed to extend the basic pipeline
structure with conditional and looping nodes, making
it possible to create dynamic, branching, and iterative processes.
"""

from .components import counter, logger, Any
from .components import Callable, Base, Node
from .components import deepcopy, _input_args, _check_input_node, _reset_id


def ifnode(true_node: "Base", false_node: "Base") -> "IfNode":
    """Create a `IfNode` instance.

    This function wraps a callable function into a `IfNode`.

    Returns:
        Callable: A function that takes a callable `func` and
        returns a `IfNode` instance.
    """

    def run_node(
        func: Callable, true_node=true_node, false_node=false_node
    ) -> "IfNode":
        return IfNode(func, true_node=true_node, false_node=false_node)

    return run_node


def loopnode(loop_node: "Base") -> "LoopNode":
    """Create a `LoopNode` instance.

    This function wraps a callable function into a `LoopNode`.

    Returns:
        Callable: A function that takes a callable `func` and
        returns a `LoopNode` instance.
    """

    def run_node(func: Callable, loop_node=loop_node) -> "LoopNode":
        return LoopNode(func, loop_node=loop_node)

    return run_node


class IfNode(Node):
    """A class representing a ifnode in a chain.

    This class extends the `Node` class to include conditional logic.
    It allows for branching in a chain by
    executing either a `true_node` or a `false_node` depending on
    the boolean result of the function.

    Attributes:
        true_node (Base): The node to execute if
        the condition evaluates to True.
        false_node (Base): The node to execute if
        the condition evaluates to False.

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

    def __init__(self, func: Callable, true_node: Base, false_node: Base):
        """Initialize a IfNode instance.

        Args:
            func (Callable): The function that determines
            the condition for branching.
            true_node (Union[Base]): The node to execute if
            the function's result is True.
            false_node (Union[Base]): The node to execute
            if the function's result is False.

        Attributes:
            true_node (Base): A deep copy of the true_node
            with a new unique ID.
            false_node (Base): A deep copy of the false_node
            with a new unique ID.
        """
        super().__init__(func)
        self._node_type = "IfNode"
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

    def __call__(self, *args, **kwargs) -> Any:
        """Execute the conditional logic.

        Args:
            *args: Positional arguments to pass to the function and nodes.
            **kwargs: Keyword arguments to pass to the function and nodes.

        Returns:
            Any: The result of executing either the true_node or the false_node
            based on the function's boolean result.

        Raises:
            AssertionError: If the function's output is not a boolean.
            Exception: If an error occurs during the execution.
        """
        try:
            logger.info(
                "Start IfNode", extra={"id": self.id, "name_class": self.name}
            )
            logger.info(
                "Get bool value",
                extra={"id": self.id, "name_class": self.name},
            )
            if not self.positional_or_keyword:
                logger.info(
                    "Select input args",
                    extra={"id": self.id, "name_class": self.name},
                )
                inp_args = _input_args(args, kwargs, node_args=self.args)
                res = self.func(**inp_args)
                assert isinstance(
                    res, bool
                ), "The output of IfNode's function must be boolean"
            else:
                res = self.func(*args, **kwargs)
                assert isinstance(
                    res, bool
                ), "The output of IfNode's function must be boolean"

            logger.info(
                "Execute %s Node",
                str(res),
                extra={"id": self.id, "name_class": self.name},
            )
            logger.info(
                "End IfNode", extra={"id": self.id, "name_class": self.name}
            )
            return (
                self.true_node(*args, **kwargs)
                if res
                else self.false_node(*args, **kwargs)
            )
        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise


class LoopNode(Node):
    """A class representing a loop node.

    This class extends the `Node` class to include looping logic.
    It executes a `loop_node` in each iteration until
    the `condition_func` returns True. The loop continues
    to execute `loop_node` with the result of the previous
    execution until the condition is satisfied.

    Attributes:
        loop_node (Base): The node to execute in each iteration of the loop.
        condition_func (Callable): A function that determines when
        to stop the loop.
        It is called with the result of
            the `loop_node` execution and should return a boolean value.

    Methods:
        __init__(condition_func, loop_node):
            Initializes a LoopNode instance with a callable function
            and a node to execute in the loop.

        __call__(*args, **kwargs):
            Executes the loop node repeatedly until the condition
            function returns True.

        __repr__():
            Returns a string representation of the loop node,
            including its ID and name.
    """

    def __init__(self, condition_func: Callable, loop_node: Base) -> None:
        """Initialize a LoopNode instance.

        Args:
            condition_func (Callable): A function that receives the result of
            the `loop_node` and returns a boolean
            indicating whether the loop should continue or stop.
            loop_node (Base): The node to execute in each iteration
            of the loop. This node is executed repeatedly
            until `condition_func` returns True.

        Attributes:
            loop_node (Base): A deep copy of the `loop_node`
            with a new unique ID.
            The node's `_nodes` attribute,
                if present, is reset with new IDs.
        """
        super().__init__(condition_func)
        self._node_type = "LoopNode"
        _check_input_node([loop_node])
        loop_node = deepcopy(loop_node)
        loop_node.id = loop_node.name + str(next(counter))
        if hasattr(loop_node, "_nodes"):
            loop_node._nodes = _reset_id(loop_node._nodes)

        self.loop_node = loop_node

    def __call__(self, *args, **kwargs) -> Any:
        """Execute the loop node.

        Args:
            *args: Positional arguments to pass to the loop node.
            **kwargs: Keyword arguments to pass to the loop node.

        Returns:
            Any: The result of the last execution of `loop_node`
            when the condition is met.

        Raises:
            AssertionError: If the result of `condition_func` is not a boolean.
            Exception: If an error occurs during the execution
            of the loop node or the condition function.
        """
        try:
            logger.info(
                "Start LoopNode",
                extra={"id": self.id, "name_class": self.name},
            )
            iteration = 0
            condition_met = False

            while not condition_met:
                logger.info(
                    "Iteration %s",
                    str(iteration),
                    extra={"id": self.id, "name_class": self.name},
                )
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

            logger.info(
                "End LoopNode", extra={"id": self.id, "name_class": self.name}
            )
            return result

        except Exception as e:
            logger.error(e, extra={"id": self.id, "name_class": self.name})
            raise

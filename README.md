# StreamGraph

StreamGraph is a Python library designed for creating and managing chains of function nodes. This library provides an easy-to-use framework for chaining together functions, layers, and complex processing chains, enabling parallel processing and modular code organization.

## Features

- **Node Decorator**: Convert functions into nodes that can be added to chains.
- **Chain**: Create sequential chains of nodes for step-by-step processing.
- **Layer**: Parallel processing of nodes, either as a list or a dictionary.
- **Automatic Argument Handling**: Automatically manage and pass arguments between nodes.
- **Parallel Processing**: Utilize multiple CPU cores for parallel node execution.
- **Flexible Chain Operations**: Use `>>` and `<<` operators to create complex chains and systems.

## Installation

Install StreamGraph directly from GitHub using pip:

```bash
pip install git+https://github.com/lf-data/streamgraph.git
```

## Examples

### 1. Basic Example with Math Operations

```python
from streamgraph import node

@node(description="Add two numbers")
def add(a, b):
    return a + b

@node(description="Divide two numbers")
def divide(a, b):
    return a/b

@node(description="Multiply two numbers")
def multiply(a, b):
    return a * b

chain = [add, divide] >> multiply
print(chain(2, 3))  # Output: 3.333
chain.view()
```

![chain1](https://raw.githubusercontent.com/lf-data/streamgraph/main/images/chain1.png)

### 11. ConditionalNode to check prime number

```python
from streamgraph import node

@node(description="This node checks if a number is prime", name="PrimeCheckNode")
def give_prime_num(n):
    if n <= 3:
        return n > 1
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i ** 2 <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

@node(description="Output if number is prime", name="PrimeNumber")
def is_prime():
    return "This number is prime"

@node(description="Output if number is not prime", name="NotPrimeNumber")
def is_not_prime():
    return "This number is not prime"

@node(conditional=True, true_node=is_prime, false_node=is_not_prime, description="check if is prime", name="CheckPrime")
def check_prime(prime):
    return prime

chain = give_prime_num >> check_prime
print(chain(4)) # This number is not prime
chain.view()
```

![chain2](https://raw.githubusercontent.com/lf-data/streamgraph/main/images/chain2.png)


### 12. Complex chain with nodes repeated several times

```python
from streamgraph import node

@node(description="This node adds one to the input number", name="PlusOneNode")
def plus_one(num: int):
    return num + 1

@node(description="This node adds two to the input number", name="PlusTwoNode")
def plus_two(num: int):
    return num + 2

@node(description="This node sums all input numbers", name="SumAllNode")
def sum_all(*args):
    print("Ciao")
    return sum(args)

base_chain = plus_one >> plus_two >> [plus_one, plus_one] >> sum_all
intermediate_chain = base_chain << plus_one << plus_two << sum_all
chain = plus_one >> [base_chain, plus_two] >> intermediate_chain
print(chain(1)) # Output: 46
chain.view()
```

![chain3](https://raw.githubusercontent.com/lf-data/streamgraph/main/images/chain3.png)



## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

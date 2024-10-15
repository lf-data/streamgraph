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

@node()
def add(a, b):
    return a + b

@node()
def divide(a, b):
    return a/b

@node()
def multiply(a, b):
    return a * b

chain = [add, divide] >> multiply
chain.show()
```

```mermaid
flowchart TB;
add13[add]:::rectangle;
divide14[divide]:::rectangle;
multiply15[multiply]:::rectangle;
add13 --> multiply15;
divide14 --> multiply15;

classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
classDef diamond_loop fill:#DDA0DD,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray: 5;
```

### 2. ConditionalNode to check prime number

```python
from streamgraph import node, ifnode

@node()
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

@node()
def is_prime():
    return "This number is prime"

@node()
def is_not_prime():
    return "This number is not prime"

@ifnode(true_node=is_prime, false_node=is_not_prime)
def check_prime_node(x):
    return x


chain = give_prime_num >> check_prime_node
chain.show()
```

```mermaid
flowchart TB;
give_prime_num12[give_prime_num]:::rectangle;
check_prime_node13{check_prime_node}:::diamond;
check_prime_node13 -- True --> is_prime14;
check_prime_node13 -- False --> is_not_prime15;
is_prime14[is_prime]:::rectangle;
is_not_prime15[is_not_prime]:::rectangle;
give_prime_num12 --> check_prime_node13;

classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
classDef diamond_loop fill:#DDA0DD,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray: 5;
```


### 3. Complex chain with nodes repeated several times

```python
from streamgraph import node, ifnode, loopnode

@node()
def plus_one(num: int):
    return num + 1

@node()
def plus_two(num: int):
    return num + 2

@node()
def sum_all(*args):
    return sum(args)

@node()
def give_prime_num(n):
    print(n)
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

@node()
def is_prime():
    return "This number is prime"

@node()
def is_not_prime():
    return "This number is not prime"

@ifnode(true_node=is_prime, false_node=is_not_prime)
def check_prime_node(x):
    return x

base_chain = plus_one >> plus_two >> [plus_one, plus_one] >> sum_all
intermediate_chain = base_chain << plus_one << plus_two << sum_all

@loopnode(loop_node=intermediate_chain)
def loop_node(x):
    return x >=100

chain = plus_one >> [base_chain, plus_two] >> loop_node >> give_prime_num >> check_prime_node
chain.show()
```

```mermaid
flowchart TB;
plus_one248[plus_one]:::rectangle;
subgraph " ";
plus_one251[plus_one]:::rectangle;
plus_two252[plus_two]:::rectangle;
plus_one251 --> plus_two252;
plus_one254[plus_one]:::rectangle;
plus_one255[plus_one]:::rectangle;
plus_two252 --> plus_one254;
plus_two252 --> plus_one255;
sum_all256[sum_all]:::rectangle;
plus_one254 --> sum_all256;
plus_one255 --> sum_all256;
end;
plus_two257[plus_two]:::rectangle;
plus_one248 --> plus_one251;
plus_one248 --> plus_two257;
subgraph " ";
sum_all260[sum_all]:::rectangle;
plus_two261[plus_two]:::rectangle;
sum_all260 --> plus_two261;
plus_one262[plus_one]:::rectangle;
plus_two261 --> plus_one262;
plus_one263[plus_one]:::rectangle;
plus_one262 --> plus_one263;
plus_two264[plus_two]:::rectangle;
plus_one263 --> plus_two264;
plus_one266[plus_one]:::rectangle;
plus_one267[plus_one]:::rectangle;
plus_two264 --> plus_one266;
plus_two264 --> plus_one267;
sum_all268[sum_all]:::rectangle;
plus_one266 --> sum_all268;
plus_one267 --> sum_all268;
end;
sum_all256 --> sum_all260;
plus_two257 --> sum_all260;
loop_node258{loop_node}:::diamond_loop;
sum_all268 --> loop_node258;
loop_node258 -. New Iteration .-> sum_all260;
give_prime_num269[give_prime_num]:::rectangle;
loop_node258 --> give_prime_num269;
check_prime_node270{check_prime_node}:::diamond;
check_prime_node270 -- True --> is_prime271;
check_prime_node270 -- False --> is_not_prime272;
is_prime271[is_prime]:::rectangle;
is_not_prime272[is_not_prime]:::rectangle;
give_prime_num269 --> check_prime_node270;

classDef rectangle fill:#89CFF0,stroke:#003366,stroke-width:2px;
classDef diamond fill:#98FB98,stroke:#2E8B57,stroke-width:2px,stroke-dasharray: 5;
classDef diamond_loop fill:#DDA0DD,stroke:#8A2BE2,stroke-width:2px,stroke-dasharray: 5;
```



## Contributing

Contributions are welcome! Please submit a pull request or open an issue to discuss your changes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

# `earley.py`, an implementation of an Earley parser variant

This code is based on the OCaml implementation
https://github.com/tomjridge/tjr_simple_earley but adapted to
Python. Documentation for the algorithm itself (not this
implementation in Python) can be found at that link.

The OCaml code is much faster (as should be expected).

Even so, the Python code is not slow. For example, for an input
"1"*100, and a grammar `E -> E E E | "1" | eps`, parsing takes about
.75 of a second. This is notable because most other Earley parsers
tend to fall over when given a grammar like this.

This is my first piece of Python code, and I was pleasantly surprised:

- pycharm is a nice environment for programming Python
- the checks that pycharm does ("inspect code") are useful
- I didn't miss types too much (of course, I am only translating from
  OCaml, rather than developing the algorithm from scratch... types
  would likely be much more useful when developing the algorithm).
- Python has nice support for sets, maps, and algebraic datatypes
  (namedtuples).
- Imperative/mutable programming actually makes the code nicer
  compared to the state-passing style used for the OCaml
  implementation
  
TODO:
- compare performance with other Python Earley parsers, such as
  https://github.com/lark-parser/lark

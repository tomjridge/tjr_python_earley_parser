# Earley parser variant, based on tjr_simple_earley, translated to Python

import collections
from typing import List
from typing import Set


# util --------------------------------------------------------

def empty_map():
    return dict()


# NOTE be sure to create new defaults if they are mutable
def lookup_with_default(m, k, default):
    r = m.get(k, None)
    if r is None:
        m[k] = default # remember to insert back into map
        r = default
    return r


# nonterminals, terminals and symbols ------------------------------------

# nt, tm and sym are all int

def is_nt(sym: int) -> bool:
    return sym % 2 == 0


# items -----------------------------------

Item = collections.namedtuple("Item", ["nt", "i", "as_", "k", "bs"])


# example_item = Item(nt=2,i=0,as_=(),k=0,bs=())  # NOTE to hash items, we need to use tuples not lists for as,bs


def cut(itm: Item, k: int):
    itm = Item(nt=itm.nt, i=itm.i, as_=itm.as_ + (itm.bs[0],), k=k, bs=itm.bs[1:])
    # print("cut:"+str(itm))
    return itm


# parsing state ------------------------------

State = collections.namedtuple("State",
                               ["k", "todo", "todo_done", "todo_gt_k", "bitms_lt_k", "bitms_at_k", "ixk_done", "ktjs"])


# types:
#
# k: int
# todo: item list
# todo_done: item set
# todo_gt_k: map, int -> item set
# bitms_lt_k: map, int * nt -> item set
# bitms_at_k: map, nt -> item set
# ixk_done: (int * nt) set  (FIXME prefer int -> nt set?)
# ktjs: map, tm -> item set option (item set or None)


# FIXME a lot of the following could be inlined - defining separate functions isn't buying much
def get_bitms(s: State, k: int, x: int) -> Set[Item]:
    if k == s.k:
        return lookup_with_default(s.bitms_at_k, x, set())
    else:
        m = lookup_with_default(s.bitms_lt_k, k, empty_map())
        bitms = lookup_with_default(m, x, set())
        return bitms


def add_bitm_at_k(s: State, nitm, nt):
    lookup_with_default(s.bitms_at_k, nt, set()).add(nitm)  # use mutable sets
    return None


# FIXME inline
def pop_todo(s: State) -> Item:
    todo: List[Item] = s.todo
    itm = todo.pop(0)
    return itm


def add_todo(s: State, nitm: Item):
    k = s.k
    nitm_k = nitm.k
    if nitm_k > k:
        lookup_with_default(s.todo_gt_k, nitm_k, set()).add(nitm)
        # print("add_todo"+str(s.todo_gt_k.get(nitm_k)))
        return None
    else:
        if nitm in s.todo_done:
            return None
        else:
            s.todo.insert(0, nitm)  # list
            s.todo_done.add(nitm)
            return None


# FIXME inline
def add_ixk_done(s: State, i: int, x):
    s.ixk_done.add((i, x))
    return None


# FIXME inline
def mem_ixk_done(s: State, i, x):
    return (i, x) in s.ixk_done


# FIXME inline
def find_ktjs(s: State, tm):
    return s.ktjs.get(tm, None)


# example grammar ---------------------------------------------

# Example grammar: E -> E E E | "1" | eps

# NOTE nonterms are even, terms are odd
_E = 0
_1 = 1
_eps = 3


# grammar represented as a function which produces items at a given stage
def mk_items(k: int):
    return [
        Item(_E, k, (), k, (_E, _E, _E)),
        Item(_E, k, (), k, (_1,)),
        Item(_E, k, (), k, (_eps,))
    ]


# dependent on grammar
def new_items(nt, input: str, k: int):
    return mk_items(k)


# dependent on grammar
def parse_tm(tm, input, k, input_length):
    if tm == _1:
        if k <= input_length - 1:
            return [k + 1]  # assume input is a string of 1s
        else:
            return []
    elif tm == _eps:
        return [k]
    else:
        print("Unknown terminal: " + tm)
        return None


def step(s: State, input: str, input_length: int):
    k = s.k
    nitm = pop_todo(s)
    # print(nitm)
    nitm_complete = len(nitm.bs) == 0
    if nitm_complete:
        (i, x) = (nitm.i, nitm.nt)
        already_done = mem_ixk_done(s, i, x)
        if already_done:
            return s
        else:
            add_ixk_done(s, i, x)
            for bitm in get_bitms(s, i, x):  # get((i,x),set()):
                add_todo(s, cut(bitm, k))
            return s
    else:
        bitm = nitm
        sym = bitm.bs[0]
        if is_nt(sym):
            _Y = sym
            bitms = get_bitms(s, k, _Y)  # .get((k,_Y),set())
            bitms_empty = len(bitms) == 0
            add_bitm_at_k(s, bitm, _Y)
            if bitms_empty:
                # NOTE different order to OCaml code
                # here we need to expand Y at k
                for nitm in new_items(_Y, input, k):
                    add_todo(s, nitm)
                return s
            else:
                if mem_ixk_done(s, k, _Y):
                    add_todo(s, cut(bitm, k))
                    return s
                else:
                    return s
        else:
            # is tm
            t = sym
            js = find_ktjs(s, t)
            if js is None:
                js = parse_tm(t, input, k, input_length)
                s.ktjs[t] = js
            for j in js:
                add_todo(s, cut(bitm, j))
            return s


def loop_k(s: State, input, input_length):
    while len(s.todo) > 0:
        s = step(s, input, input_length)
    return s


def loop(s: State, input: str, input_length: int):
    # we want to "reset" s every time we increase k, except at the end
    while s.k <= input_length:
        s = loop_k(s, input, input_length)
        old_k = s.k
        k = old_k + 1
        # if we are finished, then don't discard ixk_done info (and other info)
        if k > input_length:
            break
        todo = lookup_with_default(s.todo_gt_k, k, set())
        todo_done = todo  # as a set
        todo = list(todo)
        todo_gt_k = s.todo_gt_k
        todo_gt_k[old_k] = set()  # drop old info
        ixk_done = set()
        ktjs = empty_map()
        bitms_lt_k = s.bitms_lt_k
        bitms_lt_k[old_k] = s.bitms_at_k
        bitms_at_k = empty_map()
        new_s = State(k, todo, todo_done, todo_gt_k, bitms_lt_k, bitms_at_k, ixk_done, ktjs)
        s = new_s
    return s


# initial state ------------------------------------------------------------

# initial state consists of nonterminal to start parsing, the input, and the input length (in case input is not a
# string)
Init = collections.namedtuple("Init", ["nt", "input", "input_length"])


def init_state(init: Init):
    k = 0
    init_items = new_items(init.nt, init.input, 0)
    todo = init_items
    todo_done = set()
    todo_gt_k = empty_map()
    ixk_done = set()
    ktjs = empty_map()
    bitms_lt_k = empty_map()
    bitms_at_k = empty_map()
    s0 = State(k, todo, todo_done, todo_gt_k, bitms_lt_k, bitms_at_k, ixk_done, ktjs)
    return s0


# testing ----------------------------------------------------------------

# use the example grammar, and an input of length ...
init0 = Init(_E, "1" * 100, 100)

# https://stackoverflow.com/questions/7370801/measure-time-elapsed-in-python
from timeit import default_timer as timer

start = timer()
from pprint import pprint

# https://stackoverflow.com/questions/30062384/pretty-print-namedtuple
result = loop(init_state(init0), init0.input, init0.input_length)
end = timer()
print(end - start)

pprint(dict(result._asdict()))

# Example execution time:
# Grammar: E -> EEE | "1" | eps; input "1"*100; time: 0.7861349396407604

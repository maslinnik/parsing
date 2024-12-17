from .core import Grammar, Parser
from typing import Self, Iterable
from copy import deepcopy
from dataclasses import dataclass


class Item:
    # Assumes lhs and rhs are provided from grammar.rules and therefore correct.
    def __init__(self, lhs: str, rhs: str, lookahead: str | None):
        self.lhs = lhs
        self.rhs = rhs
        self.position = 0
        self.lookahead = lookahead

    def peek(self) -> str | None:
        if self.ended():
            return None
        return self.rhs[self.position]

    def next(self) -> Self:
        item = Item(self.lhs, self.rhs, self.lookahead)
        item.position = self.position + 1
        return item

    def ended(self) -> bool:
        return self.position == len(self.rhs)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.position, self.lookahead))

    def __eq__(self, other: Self):
        return ((self.lhs, self.rhs, self.position, self.lookahead)
                == (other.lhs, other.rhs, other.position, self.lookahead))

    def __ne__(self, other: Self):
        return not self.__eq__(other)

    def __str__(self):
        return ("(" + self.lhs + " -> " + self.rhs[:self.position] + '.'
                + self.rhs[self.position:] + ", " + str(self.lookahead) + ")")


class State:
    def first_from_string(self, string: str) -> set[str]:
        result = {None}
        for c in string:
            result = result | self.first[c]
            if None not in self.first[c]:
                result.remove(None)
                break
        return result

    def run_closure_dfs(self, item: Item, new_items: set[Item]):
        if item.peek() not in self.grammar.nonterminal:
            return
        for rhs in self.grammar.rules[item.peek()]:
            for c in self.first_from_string(item.rhs[item.position + 1:] + (item.lookahead if item.lookahead else '')):
                new_item = Item(item.peek(), rhs, c)
                if new_item in new_items:
                    continue
                new_items.add(new_item)
                self.run_closure_dfs(new_item, new_items)

    def __init__(self, grammar: Grammar, first: dict[str, set[str | None]], items: Iterable[Item]):
        self.grammar = grammar
        self.first = first
        new_items = set()
        for item in items:
            new_items.add(item)
            self.run_closure_dfs(item, new_items)
        self.items = frozenset(new_items)

    def goto(self, symbol: str) -> Self:
        result_items = set()
        for item in self.items:
            if item.peek() == symbol:
                result_items.add(item.next())
        return State(self.grammar, self.first, result_items)

    def __hash__(self) -> int:
        return hash(self.items)

    def __eq__(self, other: Self) -> bool:
        return self.items == other.items

    def __ne__(self, other: Self) -> bool:
        return not self.__eq__(other)


@dataclass(unsafe_hash=True)
class Shift:
    next_state: int


@dataclass(unsafe_hash=True)
class Reduce:
    rule_lhs: str
    rule_rhs: str


class Accept:
    pass


class Reject:
    pass


Action = Shift | Reduce | Accept | Reject


class LR(Parser):
    _first: dict[str, set[str | None]]
    _states: list[State]
    _goto: list[dict[str, int]]
    _action: list[dict[str, Action]]

    def _run_first_dfs(self, current: str, initial: str, visited: set[str]):
        visited.add(current)
        for rhs in self._grammar.rules[current]:
            if len(rhs) == 0:
                self._first[initial].add(None)
            elif rhs[0] in self._grammar.terminal:
                self._first[initial].add(rhs[0])
            elif rhs[0] not in visited:
                self._run_first_dfs(rhs[0], initial, visited)

    def _calculate_first(self):
        # Just run DFS multiple times here, since it's not the bottleneck anyway.
        self._first = dict()
        for c in self._grammar.terminal:
            self._first[c] = {c}
        for n in self._grammar.nonterminal:
            self._first[n] = set()
            self._run_first_dfs(n, n, set())

    def _traverse_states(self, index: int, state_hashes: dict[int, int]):
        for c in self._grammar.nonterminal | self._grammar.terminal:
            next_state = self._states[index].goto(c)
            current_hash = hash(next_state)
            if current_hash not in state_hashes:
                self._states.append(next_state)
                self._goto.append(dict())
                state_hashes[current_hash] = len(self._states) - 1
                self._traverse_states(len(self._states) - 1, state_hashes)
            self._goto[index][c] = state_hashes[current_hash]

    def _calculate_states(self):
        assert len(self._grammar.rules['&']) == 1
        starting_item = Item('&', self._grammar.rules['&'][0], None)
        self._states = [State(self._grammar, self._first, [starting_item])]
        self._goto = [dict()]
        state_hashes = {hash(self._states[0]): 0}
        self._traverse_states(0, state_hashes)

    def _calculate_actions(self) -> bool:
        self._action = [dict() for _ in range(len(self._states))]
        for index in range(len(self._states)):
            actions = dict([c, set()] for c in self._grammar.terminal | {None})
            for item in self._states[index].items:
                if item.peek() is None:
                    if item.lhs == '&':
                        actions[None].add(Accept())
                    else:
                        actions[item.lookahead].add(Reduce(item.lhs, item.rhs))
                elif item.peek() in self._grammar.terminal:
                    actions[item.peek()].add(Shift(self._goto[index][item.peek()]))
            for c in self._grammar.terminal | {None}:
                if len(actions[c]) == 0:
                    actions[c].add(Reject())
                if len(actions[c]) > 1:
                    return False
                self._action[index][c] = actions[c].pop()
        return True

    def _build(self) -> bool:
        self._calculate_first()
        self._calculate_states()
        ok = self._calculate_actions()
        return ok

    def __init__(self, grammar: Grammar):
        self._grammar = deepcopy(grammar)
        # todo: fix starting symbol ambiguity
        assert '&' not in self._grammar.nonterminal
        self._grammar.nonterminal.add('&')
        self._grammar.rules['&'] = []
        self._grammar.add_rule('&', self._grammar.starting)
        self._grammar.starting = '&'
        if not self._build():
            raise ValueError("grammar is not LR(1)")

    def predict(self, word: str) -> bool:
        if not all(word[i] in self._grammar.terminal for i in range(len(word))):
            raise ValueError("word must consist of terminal symbols")
        state_stack = [0]
        for c in list(word) + [None]:
            while True:
                current_state = state_stack[-1]
                current_action = self._action[current_state][c]
                if isinstance(current_action, Shift):
                    state_stack.append(self._goto[current_state][c])
                    break
                if isinstance(current_action, Reduce):
                    for i in range(len(current_action.rule_rhs)):
                        state_stack.pop()
                    n = current_action.rule_lhs
                    state_stack.append(self._goto[state_stack[-1]][n])
                if isinstance(current_action, Accept):
                    return len(state_stack) == 2 and state_stack[0] == 0
                if isinstance(current_action, Reject):
                    return False
        raise NotImplementedError("something went wrong")

from .core import Grammar, Parser
from typing import Self
from copy import deepcopy


class State:
    # Assumes lhs and rhs are provided from grammar.rules and therefore correct.
    def __init__(self, lhs: str, rhs: str, start: int):
        self.start = start
        self.lhs = lhs
        self.rhs = rhs
        self.position = 0

    def peek(self) -> str | None:
        if self.ended():
            return None
        return self.rhs[self.position]

    def next(self) -> Self:
        state = State(self.lhs, self.rhs, self.start)
        state.position = self.position + 1
        return state

    def ended(self) -> bool:
        return self.position == len(self.rhs)

    def __hash__(self):
        return hash((self.lhs, self.rhs, self.start, self.position))

    def __eq__(self, other: Self):
        return (self.lhs, self.rhs, self.start, self.position) == (other.lhs, other.rhs, other.start, other.position)

    def __ne__(self, other: Self):
        return not self.__eq__(other)


class StateSet:
    sets: dict[str, dict[str | None, set[State]]]

    def __init__(self, grammar: Grammar):
        self.sets = dict([n, dict([c, set()] for c in grammar.nonterminal | grammar.terminal | {None})]
                         for n in grammar.nonterminal)

    def get_states(self, lhs: str, next: str | None) -> set[State]:
        return self.sets[lhs][next]

    def add_state(self, state: State):
        self.sets[state.lhs][state.peek()].add(state)

    def has_state(self, state: State) -> bool:
        return state in self.sets[state.lhs][state.peek()]


class Earley(Parser):
    def __init__(self, grammar: Grammar):
        self._grammar = deepcopy(grammar)
        # todo: fix starting symbol ambiguity
        assert '&' not in self._grammar.nonterminal
        self._grammar.nonterminal.add('&')
        self._grammar.rules['&'] = []
        self._grammar.add_rule('&', self._grammar.starting)
        self._grammar.starting = '&'

    def _scan_and_run_dfs(self, next_symbol: str, index: int, state_sets: list[StateSet]):
        for n in self._grammar.nonterminal:
            for state in state_sets[index - 1].get_states(n, next_symbol):
                new_state = state.next()
                if state_sets[index].has_state(new_state):
                    continue
                state_sets[index].add_state(new_state)
                self._predict_complete_from(index, new_state, state_sets)

    def _predict_complete_from(self, index: int, state: State, state_sets: list[StateSet]):
        new_states = []
        if state.peek() is None:
            # complete from exhausted state
            for parent_n in self._grammar.nonterminal:
                for parent_state in state_sets[state.start].get_states(parent_n, state.lhs):
                    new_states.append(parent_state.next())
        elif state.peek() in self._grammar.nonterminal:
            # predict
            for rhs in self._grammar.rules[state.peek()]:
                new_states.append(State(state.peek(), rhs, index))
            # complete with epsilon-producing state
            if state_sets[index].get_states(state.peek(), None):
                new_states.append(state.next())
        for new_state in new_states:
            if state_sets[index].has_state(new_state):
                continue
            state_sets[index].add_state(new_state)
            self._predict_complete_from(index, new_state, state_sets)

    def predict(self, word: str) -> bool:
        if not all(word[i] in self._grammar.terminal for i in range(len(word))):
            raise ValueError("word must consist of terminal symbols")
        state_sets = [StateSet(self._grammar) for _ in range(len(word) + 1)]
        assert len(self._grammar.rules['&']) == 1
        starting_state = State('&', self._grammar.rules['&'][0], 0)
        state_sets[0].add_state(starting_state)
        self._predict_complete_from(0, starting_state, state_sets)
        for i, c in enumerate(list(word)):
            self._scan_and_run_dfs(c, i + 1, state_sets)
        return len(state_sets[len(word)].get_states('&', None)) > 0

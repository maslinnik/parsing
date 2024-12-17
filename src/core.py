from abc import ABC, abstractmethod
from typing import Iterable


class Grammar:
    def __init__(self, nonterminal: Iterable[str], terminal: Iterable[str], starting: str):
        self.nonterminal = set(nonterminal)
        self.terminal = set(terminal)
        self.starting = starting
        for n in self.nonterminal | self.terminal:
            if len(n) != 1:
                raise ValueError("symbols of variable length are disallowed")
        if starting not in self.nonterminal:
            raise ValueError("starting symbol is not nonterminal")
        self.rules: dict[str, list[str]] = dict([x, []] for x in self.nonterminal)

    def add_rule(self, lhs: str, rhs: str):
        if len(lhs) != 1 or lhs not in self.nonterminal:
            raise ValueError("left hand side of rule must be a single nonterminal symbol")
        if not all(rhs[i] in self.nonterminal or rhs[i] in self.terminal for i in range(len(rhs))):
            raise ValueError("right hand side of rule must consist of nonterminal and terminal symbols")
        self.rules[lhs].append(rhs)


class Parser(ABC):
    @abstractmethod
    def __init__(self, grammar: Grammar):
        pass

    @abstractmethod
    def predict(self, word: str) -> bool:
        pass

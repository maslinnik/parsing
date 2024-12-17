import sys
from src import *

if len(sys.argv) != 2 or sys.argv[1] not in ['earley', 'lr']:
    print("usage: python main.py [earley|lr]", file=sys.stderr)
    exit(1)

parser_type = sys.argv[1]

n, s, p = map(int, input().split())
nonterminal = list(input())
terminal = list(input())
rules = []
for _ in range(p):
    lhs, rhs = input().split("->")
    rules.append([lhs.strip(), rhs.strip()])
starting = input()

grammar = Grammar(nonterminal, terminal, starting)
for lhs, rhs in rules:
    grammar.add_rule(lhs, rhs)

match parser_type:
    case 'earley':
        parser = Earley(grammar)
    case 'lr':
        parser = LR(grammar)
    case _:
        raise NotImplementedError

m = int(input())
for _ in range(m):
    print('Yes' if parser.predict(input()) else 'No')

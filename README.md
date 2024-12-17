# parsing

Практикум курса "Формальные языки и трансляции", ФПМИ МФТИ, 2 курс

Роман Первутинский, Б05-328

## Описание

Библиотека для парсинга с реализациями алгоритма Эрли и LR(1).

### `Grammar`

Класс контекстно-свободной грамматики.

#### `Grammar(nonterminal, terminal, starting)`

Инициализирует грамматику. `nonterminal`, `terminal` и `starting` доступны как поля класса.

#### `Grammar.add_rule(lhs: str, rhs: str)`

Добавляет в грамматику правило вывода `lhs` $\rightarrow$ `rhs`.

### `Parser`

Абстрактный класс парсера.

#### `Parser(grammar: Grammar)`

Инициализирует парсер КС-грамматикой `grammar`.

#### `Parser.predict(word: str) -> bool`

Возвращает `True`, если `word` лежит в языке, заданном грамматикой, и `False` иначе.

### `Earley`

Реализация `Parser`, использующая алгоритм Эрли.

Время работы `Earley.predict` &mdash; не более чем кубическое от длины слова.

### `LR`

Реализация `Parser`, использующая LR(1). `Parser(grammar)` возвращает `ValueError`, если `grammar` не задаёт LR(1)-грамматику.

Время работы `LR.predict` &mdash; линейное от длины слова.

## Запуск

Запуск unit-тестов:

```shell
python -m unittest discover -stests
```

В `main.py` реализована возможность проверки парсеров на тестах в текстовом формате. Запуск:

```shell
python main.py earley   # для алгоритма Эрли
python main.py lr       # для LR(1)
```

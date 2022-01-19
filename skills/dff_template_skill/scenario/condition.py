import logging
import re

from dff.core import Context, Actor
import nltk
from nltk import word_tokenize
from nltk.util import ngrams
nltk.download('punkt')

import common.dialogflow_framework.utils.state as state_utils
from common.utils import is_yes

# from deeppavlov.models.spelling_correction.levenshtein.searcher_component import LevenshteinSearcher
# from deeppavlov.models.spelling_correction.levenshtein.searcher_component import LevenshteinSearcherComponent
import string
# from common.dialogflow_framework.extensions import custom_functions
# import Levenshtein

#
# def small_levenshtein(desired_item: str):
#     flag = False
#     desired_item = [str(x).replace(' ', '') for x in desired_item]
#     user_uttr = [str(x).replace(' ', '') for x in ctx.last_request]
#     lev_dist = Levenshtein.distance(desired_item, user_uttr)
#     if lev_dist < 4:
#         flag = True
#
#     return flag


logger = logging.getLogger(__name__)
# ....


# диппавловский левенштейн
import copy
import itertools

import numpy as np
from sortedcontainers import SortedListWithKey

from collections import defaultdict
class Trie:
    """
    Реализация префиксного бора (точнее, корневого направленного ациклического графа)
    Атрибуты
    --------
    alphabet: list, алфавит
    alphabet_codes: dict, словарь символ:код
    compressed: bool, индикатор сжатия
    cashed: bool, индикатор кэширования запросов к функции descend
    root: int, индекс корня
    graph: array, type=int, shape=(число вершин, размер алфавита), матрица потомков
    graph[i][j] = k <-> вершина k --- потомок вершины i по ребру, помеченному символом alphabet[j]
    data: array, type=object, shape=(число вершин), массив с данными, хранящямися в вершинах
    final: array, type=bool, shape=(число вершин), массив индикаторов
    final[i] = True <-> i --- финальная вершина
    """
    NO_NODE = -1
    SPACE_CODE = -1

    ATTRS = ['is_numpied', 'precompute_symbols', 'allow_spaces',
             'is_terminated', 'to_make_cashed']

    def __init__(self, alphabet, make_sorted=True, make_alphabet_codes=True,
                 is_numpied=False, to_make_cashed=False,
                 precompute_symbols=None, allow_spaces=False, dict_storage=False):
        self.alphabet = sorted(alphabet) if make_sorted else alphabet
        self.alphabet_codes = ({a: i for i, a in enumerate(self.alphabet)}
                               if make_alphabet_codes else self.alphabet)
        self.alphabet_codes[" "] = Trie.SPACE_CODE
        self.is_numpied = is_numpied
        self.to_make_cashed = to_make_cashed
        self.dict_storage = dict_storage
        self.precompute_symbols = precompute_symbols
        self.allow_spaces = allow_spaces
        self.initialize()

    def initialize(self):
        self.root = 0
        self.graph = [self._make_default_node()]
        self.data, self.final = [None], [False]
        self.nodes_number = 1
        self.descend = self._descend_simple
        self.is_terminated = False

    def _make_default_node(self):
        if self.dict_storage:
            return defaultdict(lambda: -1)
        elif self.is_numpied:
            return np.full(shape=(len(self.alphabet),),
                           fill_value=Trie.NO_NODE, dtype=int)
        else:
            return [Trie.NO_NODE] * len(self.alphabet)

    def save(self, outfile):
        """
        Сохраняет дерево для дальнейшего использования
        """
        with open(outfile, "w", encoding="utf8") as fout:
            attr_values = [getattr(self, attr) for attr in Trie.ATTRS]
            attr_values.append(any(x is not None for x in self.data))
            fout.write("{}\n{}\t{}\n".format(
                " ".join("T" if x else "F" for x in attr_values),
                self.nodes_number, self.root))
            fout.write(" ".join(str(a) for a in self.alphabet) + "\n")
            for index, label in enumerate(self.final):
                letters = self._get_letters(index, return_indexes=True)
                children = self._get_children(index)
                fout.write("{}\t{}\n".format(
                    "T" if label else "F", " ".join("{}:{}".format(*elem)
                                                    for elem in zip(letters, children))))
            if self.precompute_symbols is not None:
                for elem in self.data:
                    fout.write(":".join(",".join(
                        map(str, symbols)) for symbols in elem) + "\n")
        return

    def make_cashed(self):
        """
        Включает кэширование запросов к descend
        """
        self._descendance_cash = [dict() for _ in self.graph]
        self.descend = self._descend_cashed

    def make_numpied(self):
        self.graph = np.array(self.graph)
        self.final = np.asarray(self.final, dtype=bool)
        self.is_numpied = True

    def add(self, s):
        """
        Добавление строки s в префиксный бор
        """
        if self.is_terminated:
            raise TypeError("Impossible to add string to fitted trie")
        if s == "":
            self._set_final(self.root)
            return
        curr = self.root
        for i, a in enumerate(s):
            code = self.alphabet_codes[a]
            next = self.graph[curr][code]
            if next == Trie.NO_NODE:
                curr = self._add_descendant(curr, s[i:])
                break
            else:
                curr = next
        self._set_final(curr)
        return self

    def fit(self, words):
        for s in words:
            self.add(s)
        self.terminate()

    def terminate(self):
        if self.is_numpied:
            self.make_numpied()
        self.terminated = True
        if self.precompute_symbols is not None:
            precompute_future_symbols(self, self.precompute_symbols,
                                      allow_spaces=self.allow_spaces)
        if self.to_make_cashed:
            self.make_cashed()

    def __contains__(self, s):
        if any(a not in self.alphabet for a in s):
            return False
        # word = tuple(self.alphabet_codes[a] for a in s)
        node = self.descend(self.root, s)
        return (node != Trie.NO_NODE) and self.is_final(node)

    def words(self):
        """
        Возвращает итератор по словам, содержащимся в боре
        """
        branch, word, indexes = [self.root], [], [0]
        letters_with_children = [self._get_children_and_letters(self.root)]
        while len(branch) > 0:
            if self.is_final(branch[-1]):
                yield "".join(word)
            while indexes[-1] == len(letters_with_children[-1]):
                indexes.pop()
                letters_with_children.pop()
                branch.pop()
                if len(indexes) == 0:
                    raise StopIteration()
                word.pop()
            next_letter, next_child = letters_with_children[-1][indexes[-1]]
            indexes[-1] += 1
            indexes.append(0)
            word.append(next_letter)
            branch.append(next_child)
            letters_with_children.append(self._get_children_and_letters(branch[-1]))

    def is_final(self, index):
        """
        Аргументы
        ---------
        index: int, номер вершины
        Возвращает
        ----------
        True: если index --- номер финальной вершины
        """
        return self.final[index]

    def find_partitions(self, s, max_count=1):
        """
        Находит все разбиения s = s_1 ... s_m на словарные слова s_1, ..., s_m
        для m <= max_count
        """
        curr_agenda = [(self.root, [], 0)]
        for i, a in enumerate(s):
            next_agenda = []
            for curr, borders, cost in curr_agenda:
                if cost >= max_count:
                    continue
                child = self.graph[curr][self.alphabet_codes[a]]
                # child = self.graph[curr][a]
                if child == Trie.NO_NODE:
                    continue
                next_agenda.append((child, borders, cost))
                if self.is_final(child):
                    next_agenda.append((self.root, borders + [i + 1], cost + 1))
            curr_agenda = next_agenda
        answer = []
        for curr, borders, cost in curr_agenda:
            if curr == self.root:
                borders = [0] + borders
                answer.append([s[left:borders[i + 1]] for i, left in enumerate(borders[:-1])])
        return answer

    def __len__(self):
        return self.nodes_number

    def __repr__(self):
        answer = ""
        for i, (final, data) in enumerate(zip(self.final, self.data)):
            letters, children = self._get_letters(i), self._get_children(i)
            answer += "{0}".format(i)
            if final:
                answer += "F"
            for a, index in zip(letters, children):
                answer += " {0}:{1}".format(a, index)
            answer += "\n"
            if data is not None:
                answer += "data:{0} {1}\n".format(len(data), " ".join(str(elem) for elem in data))
        return answer

    def _add_descendant(self, parent, s, final=False):
        for a in s:
            code = self.alphabet_codes[a]
            parent = self._add_empty_child(parent, code, final)
        return parent

    def _add_empty_child(self, parent, code, final=False):
        """
        Добавление ребёнка к вершине parent по символу с кодом code
        """
        self.graph[parent][code] = self.nodes_number
        self.graph.append(self._make_default_node())
        self.data.append(None)
        self.final.append(final)
        self.nodes_number += 1
        return (self.nodes_number - 1)

    def _descend_simple(self, curr, s):
        """
        Спуск из вершины curr по строке s
        """
        for a in s:
            curr = self.graph[curr][self.alphabet_codes[a]]
            if curr == Trie.NO_NODE:
                break
        return curr

    def _descend_cashed(self, curr, s):
        """
        Спуск из вершины curr по строке s с кэшированием
        """
        if s == "":
            return curr
        curr_cash = self._descendance_cash[curr]
        answer = curr_cash.get(s, None)
        if answer is not None:
            return answer
        # для оптимизации дублируем код
        res = curr
        for a in s:
            res = self.graph[res][self.alphabet_codes[a]]
            # res = self.graph[res][a]
            if res == Trie.NO_NODE:
                break
        curr_cash[s] = res
        return res

    def _set_final(self, curr):
        """
        Делает состояние curr завершающим
        """
        self.final[curr] = True

    def _get_letters(self, index, return_indexes=False):
        """
        Извлекает все метки выходных рёбер вершины с номером index
        """
        if self.dict_storage:
            answer = list(self.graph[index].keys())
        else:
            answer = [i for i, elem in enumerate(self.graph[index])
                      if elem != Trie.NO_NODE]
        if not return_indexes:
            answer = [(self.alphabet[i] if i >= 0 else " ") for i in answer]
        return answer

    def _get_children_and_letters(self, index, return_indexes=False):
        if self.dict_storage:
            answer = list(self.graph[index].items())
        else:
            answer = [elem for elem in enumerate(self.graph[index])
                      if elem[1] != Trie.NO_NODE]
        if not return_indexes:
            for i, (letter_index, child) in enumerate(answer):
                answer[i] = (self.alphabet[letter_index], child)
        return answer

    def _get_children(self, index):
        """
        Извлекает всех потомков вершины с номером index
        """
        if self.dict_storage:
            return list(self.graph[index].values())
        else:
            return [elem for elem in self.graph[index] if elem != Trie.NO_NODE]


class TrieMinimizer:
    def __init__(self):
        pass

    def minimize(self, trie, dict_storage=False, make_cashed=False, make_numpied=False,
                 precompute_symbols=None, allow_spaces=False, return_groups=False):
        N = len(trie)
        if N == 0:
            raise ValueError("Trie should be non-empty")
        node_classes = np.full(shape=(N,), fill_value=-1, dtype=int)
        order = self.generate_postorder(trie)
        # processing the first node
        index = order[0]
        node_classes[index] = 0
        class_representatives = [index]
        node_key = ((), (), trie.is_final(index))
        classes, class_keys = {node_key: 0}, [node_key]
        curr_index = 1
        for index in order[1:]:
            letter_indexes = tuple(trie._get_letters(index, return_indexes=True))
            children = trie._get_children(index)
            children_classes = tuple(node_classes[i] for i in children)
            key = (letter_indexes, children_classes, trie.is_final(index))
            key_class = classes.get(key, None)
            if key_class is not None:
                node_classes[index] = key_class
            else:
                # появился новый класс
                class_keys.append(key)
                classes[key] = node_classes[index] = curr_index
                class_representatives.append(curr_index)
                curr_index += 1
        # построение нового дерева
        compressed = Trie(trie.alphabet, is_numpied=make_numpied,
                          dict_storage=dict_storage, allow_spaces=allow_spaces,
                          precompute_symbols=precompute_symbols)
        L = len(classes)
        new_final = [elem[2] for elem in class_keys[::-1]]
        if dict_storage:
            new_graph = [defaultdict(int) for _ in range(L)]
        elif make_numpied:
            new_graph = np.full(shape=(L, len(trie.alphabet)),
                                fill_value=Trie.NO_NODE, dtype=int)
            new_final = np.array(new_final, dtype=bool)
        else:
            new_graph = [[Trie.NO_NODE for a in trie.alphabet] for i in range(L)]
        for (indexes, children, final), class_index in \
                sorted(classes.items(), key=(lambda x: x[1])):
            row = new_graph[L - class_index - 1]
            for i, child_index in zip(indexes, children):
                row[i] = L - child_index - 1
        compressed.graph = new_graph
        compressed.root = L - node_classes[trie.root] - 1
        compressed.final = new_final
        compressed.nodes_number = L
        compressed.data = [None] * L
        if make_cashed:
            compressed.make_cashed()
        if precompute_symbols is not None:
            if (trie.is_terminated and trie.precompute_symbols
                    and trie.allow_spaces == allow_spaces):
                # копируем будущие символы из исходного дерева
                # нужно, чтобы возврат из финальных состояний в начальное был одинаковым в обоих деревьях
                for i, node_index in enumerate(class_representatives[::-1]):
                    # будущие символы для представителя i-го класса
                    compressed.data[i] = copy.copy(trie.data[node_index])
            else:
                precompute_future_symbols(compressed, precompute_symbols, allow_spaces)
        if return_groups:
            node_classes = [L - i - 1 for i in node_classes]
            return compressed, node_classes
        else:
            return compressed

    def generate_postorder(self, trie):
        """
        Обратная топологическая сортировка
        """
        order, stack = [], []
        stack.append(trie.root)
        colors = ['white'] * len(trie)
        while len(stack) > 0:
            index = stack[-1]
            color = colors[index]
            if color == 'white':  # вершина ещё не обрабатывалась
                colors[index] = 'grey'
                for child in trie._get_children(index):
                    # проверяем, посещали ли мы ребёнка раньше
                    if child != Trie.NO_NODE and colors[child] == 'white':
                        stack.append(child)
            else:
                if color == 'grey':
                    colors[index] = 'black'
                    order.append(index)
                stack = stack[:-1]
        return order


def load_trie(infile):
    with open(infile, "r", encoding="utf8") as fin:
        line = fin.readline().strip()
        flags = [x == 'T' for x in line.split()]
        if len(flags) != len(Trie.ATTRS) + 1:
            raise ValueError("Wrong file format")
        nodes_number, root = map(int, fin.readline().strip().split())
        alphabet = fin.readline().strip().split()
        trie = Trie(alphabet)
        for i, attr in enumerate(Trie.ATTRS):
            setattr(trie, attr, flags[i])
        read_data = flags[-1]
        final = [False] * nodes_number
        # print(len(alphabet), nodes_number)
        if trie.dict_storage:
            graph = [defaultdict(lambda: -1) for _ in range(nodes_number)]
        elif trie.is_numpied:
            final = np.array(final)
            graph = np.full(shape=(nodes_number, len(alphabet)),
                            fill_value=Trie.NO_NODE, dtype=int)
        else:
            graph = [[Trie.NO_NODE for a in alphabet] for i in range(nodes_number)]
        for i in range(nodes_number):
            line = fin.readline().strip()
            if "\t" in line:
                label, transitions = line.split("\t")
                final[i] = (label == "T")
            else:
                label = line
                final[i] = (label == "T")
                continue
            transitions = [x.split(":") for x in transitions.split()]
            for code, value in transitions:
                graph[i][int(code)] = int(value)
        trie.graph = graph
        trie.root = root
        trie.final = final
        trie.nodes_number = nodes_number
        trie.data = [None] * nodes_number
        if read_data:
            for i in range(nodes_number):
                line = fin.readline().strip("\n")
                trie.data[i] = [set(elem.split(",")) for elem in line.split(":")]
        if trie.to_make_cashed:
            trie.make_cashed()
        return trie


def make_trie(alphabet, words, compressed=True, is_numpied=False,
              make_cashed=False, precompute_symbols=False,
              allow_spaces=False, dict_storage=False):
    trie = Trie(alphabet, is_numpied=is_numpied, to_make_cashed=make_cashed,
                precompute_symbols=precompute_symbols, dict_storage=dict_storage)
    trie.fit(words)
    if compressed:
        tm = TrieMinimizer()
        trie = tm.minimize(trie, dict_storage=dict_storage, make_cashed=make_cashed,
                           make_numpied=is_numpied, precompute_symbols=precompute_symbols,
                           allow_spaces=allow_spaces)
    return trie


def precompute_future_symbols(trie, n, allow_spaces=False):
    """
    Collecting possible continuations of length <= n for every node
    """
    if n == 0:
        return
    if trie.is_terminated and trie.precompute_symbols:
        # символы уже предпосчитаны
        return
    for index, final in enumerate(trie.final):
        trie.data[index] = [set() for i in range(n)]
    for index, (node_data, final) in enumerate(zip(trie.data, trie.final)):
        node_data[0] = set(trie._get_letters(index))
        if allow_spaces and final:
            node_data[0].add(" ")
    for d in range(1, n):
        for index, (node_data, final) in enumerate(zip(trie.data, trie.final)):
            children = set(trie._get_children(index))
            for child in children:
                node_data[d] |= trie.data[child][d - 1]
            # в случае, если разрешён возврат по пробелу в стартовое состояние
            if allow_spaces and final:
                node_data[d] |= trie.data[trie.root][d - 1]
    trie.terminated = True


class LevenshteinSearcher:
    """
    Класс для поиска близких слов
    в соответствии с расстоянием Левенштейна
    """

    def __init__(self, alphabet, dictionary, operation_costs=None,
                 allow_spaces=False, euristics='none'):
        self.alphabet = alphabet
        self.allow_spaces = allow_spaces
        if isinstance(euristics, int):
            if euristics < 0:
                raise ValueError("Euristics should be non-negative integer or None")
            else:
                self.euristics = euristics if euristics != 0 else None
        elif euristics in ["none", "None", None]:
            self.euristics = None
        else:
            raise ValueError("Euristics should be non-negative integer or None")
        if isinstance(dictionary, Trie):
            # словарь передан уже в виде бора
            self.dictionary = dictionary
        else:
            self.dictionary = make_trie(alphabet, dictionary, make_cashed=True,
                                        precompute_symbols=self.euristics,
                                        allow_spaces=self.allow_spaces)
        self.transducer = SegmentTransducer(
            alphabet, operation_costs=operation_costs, allow_spaces=allow_spaces)
        self._precompute_euristics()
        self._define_h_function()

    def __contains__(self, word):
        return word in self.dictionary

    def search(self, word, d, allow_spaces=True, return_cost=True):
        """
        Finds all dictionary words in d-window from word
        """
        if not all((c in self.alphabet
                    or (c == " " and self.allow_spaces)) for c in word):
            return []
            # raise ValueError("{0} contains an incorrect symbol".format(word))
        return self._trie_search(
            word, d, allow_spaces=allow_spaces, return_cost=return_cost)

    def _trie_search(self, word, d, transducer=None,
                     allow_spaces=True, return_cost=True):
        """
        Находит все слова в префиксном боре, расстояние до которых
        в соответствии с заданным преобразователем не превышает d
        """
        if transducer is None:
            # разобраться с пробелами
            transducer = self.transducer.inverse()
        allow_spaces &= self.allow_spaces
        trie = self.dictionary
        #  инициализация переменных
        used_agenda_keys = set()
        agenda = SortedListWithKey(key=(lambda x: x[1]))
        h = self.h_func(word, trie.root)
        # agenda[self.agenda_key("", 0, trie.root)] = (0.0, 0.0, h)
        key, value = ("", 0, trie.root), (0.0, 0.0, h)
        agenda.add((key, value))
        answer = dict()
        k = 0
        # очередь с приоритетом с промежуточными результатами
        while len(agenda) > 0:
            key, value = agenda.pop(0)
            if key in used_agenda_keys:
                continue
            used_agenda_keys.add(key)
            low, pos, index = key
            cost, g, h = value
            # g --- текущая стоимость, h --- нижняя оценка будущей стоимости
            # cost = g + h --- нижняя оценка суммарной стоимости
            k += 1
            max_upperside_length = min(len(word) - pos, transducer.max_up_length)
            for upperside_length in range(max_upperside_length + 1):
                new_pos = pos + upperside_length
                curr_up = word[pos: new_pos]
                if curr_up not in transducer.operation_costs:
                    continue
                for curr_low, curr_cost in transducer.operation_costs[curr_up].items():
                    new_g = g + curr_cost
                    if new_g > d:  # если g > d, то h можно не вычислять
                        continue
                    if curr_low == " ":
                        if allow_spaces and trie.is_final(index):
                            new_index = trie.root
                        else:
                            new_index = Trie.NO_NODE
                    else:
                        new_index = trie.descend(index, curr_low)
                    if new_index is Trie.NO_NODE:
                        continue
                    new_low = low + curr_low
                    new_h = self.h_func(word[new_pos:], new_index)
                    new_cost = new_g + new_h
                    if new_cost > d:
                        continue
                    new_key = (new_low, new_pos, new_index)
                    new_value = (new_cost, new_g, new_h)
                    if new_pos == len(word) and trie.is_final(new_index):
                        old_g = answer.get(new_low, None)
                        if old_g is None or new_g < old_g:
                            answer[new_low] = new_g
                    agenda.add((new_key, new_value))
        answer = sorted(answer.items(), key=(lambda x: x[1]))
        if return_cost:
            return answer
        else:
            return [elem[0] for elem in answer]

    def _precompute_euristics(self):
        """
        Предвычисляет будущие символы и стоимости операций с ними
        для h-эвристики
        """
        if self.euristics is None:
            return
        # вычисление минимальной стоимости операции,
        # приводящей к появлению ('+') или исчезновению ('-') данного символа
        removal_costs = {a: np.inf for a in self.alphabet}
        insertion_costs = {a: np.inf for a in self.alphabet}
        if self.allow_spaces:
            removal_costs[' '] = np.inf
            insertion_costs[' '] = np.inf
        for up, costs in self.transducer.operation_costs.items():
            for low, cost in costs.items():
                if up == low:
                    continue
                if up != '':
                    removal_cost = cost / len(up)
                    for a in up:
                        removal_costs[a] = min(removal_costs[a], removal_cost)
                if low != '':
                    insertion_cost = cost / len(low)
                    for a in low:
                        insertion_costs[a] = min(insertion_costs[a], insertion_cost)
        # предвычисление возможных будущих символов в узлах дерева
        # precompute_future_symbols(self.dictionary, self.euristics, self.allow_spaces)
        # предвычисление стоимостей потери символа в узлах дерева
        self._absense_costs_by_node = _precompute_absense_costs(
            self.dictionary, removal_costs, insertion_costs,
            self.euristics, self.allow_spaces)
        # массив для сохранения эвристик
        self._temporary_euristics = [dict() for i in range(len(self.dictionary))]

    def _define_h_function(self):
        if self.euristics in [None, 0]:
            self.h_func = (lambda *x: 0.0)
        else:
            self.h_func = self._euristic_h_function

    def _euristic_h_function(self, suffix, index):
        """
        Вычисление h-эвристики из работы Hulden,2009 для текущей вершины словаря
        Аргументы:
        ----------
        suffix : string
            непрочитанный суффикс входного слова
        index : int
            индекс текущего узла в словаре
        Возвращает:
        -----------
        cost : float
            оценка снизу для стоимости замены,
            приводящей к входному слову с суффиксом suffix,
            если прочитанный префикс слова без опечатки
            привёл в вершину с номером index
        """
        if self.euristics > 0:
            suffix = suffix[:self.euristics]
        # кэширование результатов
        index_temporary_euristics = self._temporary_euristics[index]
        cost = index_temporary_euristics.get(suffix, None)
        if cost is not None:
            return cost
        # извлечение нужных данных из массивов
        absense_costs = self._absense_costs_by_node[index]
        data = self.dictionary.data[index]
        costs = np.zeros(dtype=np.float64, shape=(self.euristics,))
        # costs[j] --- оценка штрафа при предпросмотре вперёд на j символов
        for i, a in enumerate(suffix):
            costs[i:] += absense_costs[a][i:]
        cost = max(costs)
        index_temporary_euristics[suffix] = cost
        return cost

    def _minimal_replacement_cost(self, first, second):
        first_symbols, second_symbols = set(), set()
        removal_cost, insertion_cost = 0, 0
        for a, b in itertools.zip_longest(first, second, fillvalue=None):
            if a is not None:
                first_symbols.add(a)
            if b is not None:
                second_symbols.add(b)
            removal_cost = max(removal_cost, len(first_symbols - second_symbols))
            insertion_cost = max(insertion_cost, len(second_symbols - first_symbols))
        return min(removal_cost, insertion_cost)


def _precompute_absense_costs(dictionary, removal_costs, insertion_costs, n,
                              allow_spaces=False):
    """
    Вычисляет минимальную стоимость появления нового символа в узлах словаря
    в соответствии со штрафами из costs
    Аргументы:
    ---------------
    dictionary : Trie
        словарь, хранящийся в виде ациклического автомата
    removal_costs : dict
        штрафы за удаление символов
    insertion_costs : dict
        штрафы за вставку символов
    n : int
        глубина ``заглядывания вперёд'' в словаре
    Возвращает
    ---------------
    answer : list of dicts, len(answer)=len(dictionary)
        answer[i][a][j] равно минимальному штрафу за появление символа a
        в j-ой позиции в вершине с номером i
    """
    answer = [dict() for node in dictionary.data]
    if n == 0:
        return answer
    curr_alphabet = copy.copy(dictionary.alphabet)
    if allow_spaces:
        curr_alphabet += [' ']
    for l, (costs_in_node, node) in enumerate(zip(answer, dictionary.data)):
        # определение минимальной стоимости удаления символов
        curr_node_removal_costs = np.empty(dtype=np.float64, shape=(n,))
        if len(node[0]) > 0:
            curr_node_removal_costs[0] = min(removal_costs[symbol] for symbol in node[0])
            for j, symbols in enumerate(node[1:], 1):
                if len(symbols) == 0:
                    curr_node_removal_costs[j:] = curr_node_removal_costs[j - 1]
                    break
                curr_cost = min(removal_costs[symbol] for symbol in symbols)
                curr_node_removal_costs[j] = min(curr_node_removal_costs[j - 1], curr_cost)
        else:
            curr_node_removal_costs[:] = np.inf
        # определение минимальной стоимости вставки
        for a in curr_alphabet:
            curr_symbol_costs = np.empty(dtype=np.float64, shape=(n,))
            curr_symbol_costs.fill(insertion_costs[a])
            for j, symbols in enumerate(node):
                if a in symbols:
                    curr_symbol_costs[j:] = 0.0
                    break
                curr_symbol_costs[j] = min(curr_symbol_costs[j], curr_node_removal_costs[j])
            costs_in_node[a] = curr_symbol_costs
    return answer


class SegmentTransducer:
    """
    Класс, реализующий взвешенный конечный преобразователь,
    осуществляющий замены из заданного списка операций
    Аргументы:
    ----------
    alphabet : list
        алфавит
    operation_costs : dict or None(optional, default=None)
        словарь вида {(up,low) : cost}
    allow_spaces : bool(optional, default=False)
        разрешены ли элементы трансдукции, содержащие пробел
        (используется только если явно не заданы operation costs
        и они равны значению по умолчанию)
    """

    def __init__(self, alphabet, operation_costs=None, allow_spaces=False):
        self.alphabet = alphabet
        if operation_costs is None:
            self._make_default_operation_costs(allow_spaces=allow_spaces)
        elif not isinstance(operation_costs, dict):
            raise TypeError("Operation costs must be a dictionary")
        else:
            self.operation_costs = operation_costs
        self._make_reversed_operation_costs()
        self._make_maximal_key_lengths()
        # self.maximal_value_lengths = {}
        # for up, probs in self.operation_costs.items():
        # СЛИШКОМ МНОГО ВЫЗОВОВ, НАДО КАК-ТО ЗАПОМНИТЬ
        # МАКСИМАЛЬНЫЕ ДЛИНЫ КЛЮЧЕЙ ПРИ ОБРАЩЕНИИ
        # max_low_length = max(len(low) for low in probs) if (len(probs) > 0) else -1
        # self.maximal_value_lengths[up] = self.maximal_key_length

    def get_operation_cost(self, up, low):
        """
        Возвращает стоимость элементарной трансдукции up->low
        или np.inf, если такой элементарной трансдукции нет
        Аргументы:
        ----------
        up, low : string
            элементы элементарной трансдукции
        Возвращает:
        -----------
        cost : float
            стоимость элементарной трансдукции up->low
            (np.inf, если такая трансдукция отсутствует)
        """
        up_costs = self.operation_costs.get(up, None)
        if up_costs is None:
            return np.inf
        cost = up_costs.get(low, np.inf)
        return cost

    def inverse(self):
        """
        Строит пробразователь, задающий обратное конечное преобразование
        """
        # УПРОСТИТЬ ОБРАЩЕНИЕ!!!
        inversed_transducer = SegmentTransducer(self.alphabet, operation_costs=dict())
        inversed_transducer.operation_costs = self._reversed_operation_costs
        inversed_transducer._reversed_operation_costs = self.operation_costs
        inversed_transducer.max_low_length = self.max_up_length
        inversed_transducer.max_up_length = self.max_low_length
        inversed_transducer.max_low_lengths_by_up = self.max_up_lengths_by_low
        inversed_transducer.max_up_lengths_by_low = self.max_low_lengths_by_up
        return inversed_transducer

    def distance(self, first, second, return_transduction=False):
        """
        Вычисляет трансдукцию минимальной стоимости,
        отображающую first в second
        Аргументы:
        -----------
        first : string
        second : string
            Верхний и нижний элементы трансдукции
        return_transduction : bool (optional, default=False)
            следует ли возвращать трансдукцию минимального веса
            (см. возвращаемое значение)
        Возвращает:
        -----------
        (final_cost, transductions) : tuple(float, list)
            если return_transduction=True, то возвращает
            минимальную стоимость трансдукции, переводящей first в second
            и список трансдукций с данной стоимостью
        final_cost : float
            если return_transduction=False, то возвращает
            минимальную стоимость трансдукции, переводящей first в second
        """
        if return_transduction:
            add_pred = (lambda x, y: (y == np.inf or x < y))
        else:
            add_pred = (lambda x, y: (y == np.inf or x <= y))
        clear_pred = (lambda x, y: x < y < np.inf)
        update_func = lambda x, y: min(x, y)
        costs, backtraces = self._fill_levenshtein_table(first, second,
                                                         update_func, add_pred, clear_pred)
        final_cost = costs[-1][-1]
        if final_cost == np.inf:
            transductions = [None]
        elif return_transduction:
            transductions = self._backtraces_to_transductions(first, second, backtraces,
                                                              final_cost, return_cost=False)
        if return_transduction:
            return final_cost, transductions
        else:
            return final_cost

    def transduce(self, first, second, threshold):
        """
        Возвращает все трансдукции, переводящие first в second,
        чья стоимость не превышает threshold
        Возвращает:
        ----------
        result : list
            список вида [(трансдукция, стоимость)]
        """
        add_pred = (lambda x, y: x <= threshold)
        clear_pred = (lambda x, y: False)
        update_func = (lambda x, y: min(x, y))
        costs, backtraces = self._fill_levenshtein_table(first, second,
                                                         update_func, add_pred, clear_pred,
                                                         threshold=threshold)
        result = self._backtraces_to_transductions(first, second,
                                                   backtraces, threshold, return_cost=True)
        return result

    def lower_transductions(self, word, max_cost, return_cost=True):
        """
        Возвращает все трансдукции с верхним элементом word,
        чья стоимость не превышает max_cost
    `   Возвращает:
        ----------
        result : list
            список вида [(трансдукция, стоимость)], если return_cost=True
            список трансдукций, если return_cost=False
            список отсортирован в порядке возрастания стоимости трансдукции
        """
        prefixes = [[] for i in range(len(word) + 1)]
        prefixes[0].append(((), 0.0))
        for pos in range(len(prefixes)):
            # вставки
            prefixes[pos] = self._perform_insertions(prefixes[pos], max_cost)
            max_upperside_length = min(len(word) - pos, self.max_up_length)
            for upperside_length in range(1, max_upperside_length + 1):
                up = word[pos: pos + upperside_length]
                for low, low_cost in self.operation_costs.get(up, dict()).items():
                    for transduction, cost in prefixes[pos]:
                        new_cost = cost + low_cost
                        if new_cost <= max_cost:
                            new_transduction = transduction + (up, low)
                            prefixes[pos + upperside_length].append((new_transduction, new_cost))
        answer = sorted(prefixes[-1], key=(lambda x: x[0]))
        if return_cost:
            return answer
        else:
            return [elem[0] for elem in answer]

    def lower(self, word, max_cost, return_cost=True):
        transductions = self.lower_transductions(word, max_cost, return_cost=True)
        answer = dict()
        for transduction, cost in transductions:
            low = "".join(elem[1] for elem in transductions)
            curr_cost = answer.get(low, None)
            if curr_cost is None or cost < curr_cost:
                answer[low] = cost
        answer = sorted(answer.items(), key=(lambda x: x[1]))
        if return_cost:
            return answer
        else:
            return [elem[0] for elem in answer]

    def upper(self, word, max_cost, return_cost=True):
        inversed_transducer = self.inverse()
        return inversed_transducer.lower(word, max_cost, return_cost)

    def upper_transductions(self, word, max_cost, return_cost=True):
        inversed_transducer = self.inverse()
        return inversed_transducer.lower_transductions(word, max_cost, return_cost)

    def _fill_levenshtein_table(self, first, second, update_func, add_pred, clear_pred,
                                threshold=None):
        """
        Функция, динамически заполняющая таблицу costs стоимости трансдукций,
        costs[i][j] --- минимальная стоимость трансдукции,
        переводящей first[:i] в second[:j]
        Аргументы:
        ----------
        first, second : string
            Верхний и нижний элементы трансдукции
        update_func : callable, float*float -> bool
            update_func(x, y) возвращает новое значение в ячейке таблицы costs,
            если старое значение --- y, а потенциально новое значение --- x
            везде update_func = min
        add_pred : callable : float*float -> bool
            add_pred(x, y) возвращает, производится ли добавление
            нового элемента p стоимости x в ячейку backtraces[i][j]
            в зависимости от значения costs[i][j]=y и текущей стоимости x
        clear_pred : callable : float*float -> bool
            clear_pred(x, y) возвращает, производится ли очистка
            ячейки backtraces[i][j] в зависимости от значения costs[i][j]=y
            и текущей стоимости x элемента p, добавляемого в эту ячейку
        Возвращает:
        -----------
        costs : array, dtype=float, shape=(len(first)+1, len(second)+1)
            массив, в ячейке с индексами i, j которого хранится
            минимальная стоимость трансдукции, переводящей first[:i] в second[:j]
        backtraces : array, dtype=list, shape=(len(first)+1, len(second)+1)
            массив, в ячейке с индексами i, j которого хранятся
            обратные ссылки на предыдущую ячейку в оптимальной трансдукции,
            приводящей в ячейку backtraces[i][j]
        """
        m, n = len(first), len(second)
        # если threshold=None, то в качестве порога берётся удвоенная стоимость
        # трансдукции, отображающей символы на одинаковых позициях друг в друга
        if threshold is None:
            threshold = 0.0
            for a, b in zip(first, second):
                threshold += self.get_operation_cost(a, b)
            if m > n:
                for a in first[n:]:
                    threshold += self.get_operation_cost(a, '')
            elif m < n:
                for b in second[m:]:
                    threshold += self.get_operation_cost('', b)
            threshold *= 2
        # инициализация возвращаемых массивов
        costs = np.zeros(shape=(m + 1, n + 1), dtype=np.float64)
        costs[:] = np.inf
        backtraces = [None] * (m + 1)
        for i in range(m + 1):
            backtraces[i] = [[] for j in range(n + 1)]
        costs[0][0] = 0.0
        for i in range(m + 1):
            for i_right in range(i, min(i + self.max_up_length, m) + 1):
                up = first[i: i_right]
                max_low_length = self.max_low_lengths_by_up.get(up, -1)
                if max_low_length == -1:  # no up key in transduction
                    continue
                up_costs = self.operation_costs[up]
                for j in range(n + 1):
                    if costs[i][j] > threshold:
                        continue
                    if len(backtraces[i][j]) == 0 and i + j > 0:
                        continue  # не нашлось обратных ссылок
                    for j_right in range((j if i_right > i else j + 1),
                                         min(j + max_low_length, n) + 1):
                        low = second[j: j_right]
                        curr_cost = up_costs.get(low, np.inf)
                        old_cost = costs[i_right][j_right]
                        new_cost = costs[i][j] + curr_cost
                        if new_cost > threshold:
                            continue
                        if add_pred(new_cost, old_cost):
                            if clear_pred(new_cost, old_cost):
                                backtraces[i_right][j_right] = []
                            costs[i_right][j_right] = update_func(new_cost, old_cost)
                            backtraces[i_right][j_right].append((i, j))
        return costs, backtraces

    def _make_reversed_operation_costs(self):
        """
        Заполняет массив _reversed_operation_costs
        на основе имеющегося массива operation_costs
        """
        _reversed_operation_costs = dict()
        for up, costs in self.operation_costs.items():
            for low, cost in costs.items():
                if low not in _reversed_operation_costs:
                    _reversed_operation_costs[low] = dict()
                _reversed_operation_costs[low][up] = cost
        self._reversed_operation_costs = _reversed_operation_costs

    def _make_maximal_key_lengths(self):
        """
        Вычисляет максимальную длину элемента low
        в элементарной трансдукции (up, low) для каждого up
        и максимальную длину элемента up
        в элементарной трансдукции (up, low) для каждого low
        """
        self.max_up_length = \
            (max(len(up) for up in self.operation_costs)
             if len(self.operation_costs) > 0 else -1)
        self.max_low_length = \
            (max(len(low) for low in self._reversed_operation_costs)
             if len(self._reversed_operation_costs) > 0 else -1)
        self.max_low_lengths_by_up, self.max_up_lengths_by_low = dict(), dict()
        for up, costs in self.operation_costs.items():
            self.max_low_lengths_by_up[up] = \
                max(len(low) for low in costs) if len(costs) > 0 else -1
        for low, costs in self._reversed_operation_costs.items():
            self.max_up_lengths_by_low[low] = \
                max(len(up) for up in costs) if len(costs) > 0 else -1

    def _backtraces_to_transductions(self, first, second, backtraces, threshold, return_cost=False):
        """
        Восстанавливает трансдукции по таблице обратных ссылок
        Аргументы:
        ----------
        first, second : string
            верхние и нижние элементы трансдукции
        backtraces : array-like, dtype=list, shape=(len(first)+1, len(second)+1)
            таблица обратных ссылок
        threshold : float
            порог для отсева трансдукций,
            возвращаются только трансдукции стоимостью <= threshold
        return_cost : bool (optional, default=False)
            если True, то вместе с трансдукциями возвращается их стоимость
        Возвращает:
        -----------
        result : list
            список вида [(трансдукция, стоимость)], если return_cost=True
            и вида [трансдукция], если return_cost=False,
            содержащий все трансдукции, переводящие first в second,
            чья стоимость не превышает threshold
        """
        m, n = len(first), len(second)
        agenda = [None] * (m + 1)
        for i in range(m + 1):
            agenda[i] = [[] for j in range(n + 1)]
        agenda[m][n] = [((), 0.0)]
        for i_right in range(m, -1, -1):
            for j_right in range(n, -1, -1):
                current_agenda = agenda[i_right][j_right]
                if len(current_agenda) == 0:
                    continue
                for (i, j) in backtraces[i_right][j_right]:
                    up, low = first[i:i_right], second[j:j_right]
                    add_cost = self.operation_costs[up][low]
                    for elem, cost in current_agenda:
                        new_cost = cost + add_cost
                        if new_cost <= threshold:  # удаление трансдукций большой стоимости
                            agenda[i][j].append((((up, low),) + elem, new_cost))
        if return_cost:
            return agenda[0][0]
        else:
            return [elem[0] for elem in agenda[0][0]]

    def _perform_insertions(self, initial, max_cost):
        """
        возвращает все трансдукции стоимости <= max_cost,
        которые можно получить из элементов initial
        Аргументы:
        ----------
        initial : list of tuples
            список исходных трансдукций вида [(трансдукция, стоимость)]
        max_cost : float
            максимальная стоимость трансдукции
        Возвращает:
        -----------
        final : list of tuples
            финальный список трансдукций вида [(трансдукция, стоимость)]
        """
        queue = list(initial)
        final = initial
        while len(queue) > 0:
            transduction, cost = queue[0]
            queue = queue[1:]
            for string, string_cost in self.operation_costs[""].items():
                new_cost = cost + string_cost
                if new_cost <= max_cost:
                    new_transduction = transduction + ("", string)
                    final.append((new_transduction, new_cost))
                    queue.append((new_transduction, new_cost))
        return final

    def _make_default_operation_costs(self, allow_spaces=False):
        """
        sets 1.0 cost for every replacement, insertion, deletion and transposition
        """
        self.operation_costs = dict()
        self.operation_costs[""] = {c: 1.0 for c in list(self.alphabet) + [' ']}
        for a in self.alphabet:
            current_costs = {c: 1.0 for c in self.alphabet}
            current_costs[a] = 0.0
            current_costs[""] = 1.0
            if allow_spaces:
                current_costs[" "] = 1.0
            self.operation_costs[a] = current_costs
        # транспозиции
        for a, b in itertools.permutations(self.alphabet, 2):
            self.operation_costs[a + b] = {b + a: 1.0}
        # пробелы
        if allow_spaces:
            self.operation_costs[" "] = {c: 1.0 for c in self.alphabet}
            self.operation_costs[" "][""] = 1.0


def levenshtein_item(album_name, user_uttr):
    flag = False
    items = album_name
    if type(album_name) != list:
        items = [album_name]
    vocab = set([item.lower().replace(' ', '$') for item in items])
    abet = set(c for w in vocab for c in w)
    abet.update(set(string.ascii_letters))
    searcher = LevenshteinSearcher(abet, vocab)
    for line in [user_uttr.lower()]:
        token = word_tokenize(line)
        for i in [6, 5, 4, 3, 2, 1]:
            if i <= len(token):
                grams = list(ngrams(token, i))
                for gram in grams:
                    gram = '$'.join(gram)
                    candidate = searcher.search(gram, 2)
                    if candidate:
                        candidate = candidate[0][0].replace('$', ' ')
                        flag = True
                        return flag

    return flag


def levenshtein_cand(album_name, user_uttr):
    flag = False
    items = album_name
    if type(album_name) != list:
        items = [album_name]
    vocab = set([item.lower().replace(' ', '$') for item in items])
    abet = set(c for w in vocab for c in w)
    abet.update(set(string.ascii_letters))
    searcher = LevenshteinSearcher(abet, vocab)
    candidate = ""
    for line in [user_uttr.lower()]:
        token = word_tokenize(line)
        for i in [6, 5, 4, 3, 2, 1]:
            if i <= len(token):
                grams = list(ngrams(token, i))
                for gram in grams:
                    gram = '$'.join(gram)
                    candidate = searcher.search(gram, 2)
                    if candidate:
                        candidate = candidate[0][0].replace('$', ' ')
                        flag = True
                        return flag, candidate

    return flag, candidate


def has_album(album_name: str):
    def has_album_condition(ctx: Context, actor: Actor, *args, **kwargs):
        return levenshtein_item(album_name, ctx.last_request)

    return has_album_condition


# def has_album(album_name: str):
#     def has_album_condition(ctx: Context, actor: Actor, *args, **kwargs):
#         flag = False
#         match = re.findall(album_name, ctx.last_request, re.IGNORECASE)
#         if match:
#             flag = True
#         return flag
#
#     return has_album_condition


def extract_entity(ctx, entity_type):
    vars = {"agent": ctx.misc.get("agent", {})}
    if vars["agent"]:
        user_uttr = state_utils.get_last_human_utterance(vars)
        annotations = user_uttr.get("annotations", {})
        logger.info(f"annotations {annotations}")
        if entity_type.startswith("tags"):
            tag = entity_type.split("tags:")[1]
            nounphrases = annotations.get("entity_detection", {}).get("labelled_entities", [])
            for nounphr in nounphrases:
                nounphr_text = nounphr.get("text", "")
                nounphr_label = nounphr.get("label", "")
                if nounphr_label == tag:
                    found_entity = nounphr_text
                    return found_entity
        elif entity_type.startswith("wiki"):
            wp_type = entity_type.split("wiki:")[1]
            found_entity, *_ = find_entity_by_types(annotations, [wp_type])
            if found_entity:
                return found_entity
        elif entity_type == "any_entity":
            entities = annotations.get("entity_detection", {}).get("entities", [])
            if entities:
                return entities[0]
        else:
            res = re.findall(entity_type, user_uttr["text"])
            if res:
                return res[0]
    return ""


def has_entities(entity_types):
    def has_entities_func(ctx: Context, actor: Actor, *args, **kwargs):
        flag = False
        if isinstance(entity_types, str):
            extracted_entity = extract_entity(ctx, entity_types)
            if extracted_entity:
                flag = True
        elif isinstance(entity_types, list):
            for entity_type in entity_types:
                extracted_entity = extract_entity(ctx, entity_type)
                if extracted_entity:
                    flag = True
                    break
        return flag

    return has_entities_func


def entities(**kwargs):
    slot_info = list(kwargs.items())

    def extract_entities(node_label: str, node: Node, ctx: Context, actor: Actor, *args, **kwargs):
        slot_values = ctx.misc.get("agent", {}).get("shared_memory", {}).get("slot_values", {})
        for slot_name, slot_types in slot_info:
            if isinstance(slot_types, str):
                extracted_entity = extract_entity(ctx, slot_types)
                if extracted_entity:
                    slot_values[slot_name] = extracted_entity
                    ctx.misc["agent"]["shared_memory"]["slot_values"] = slot_values
            elif isinstance(slot_types, list):
                for slot_type in slot_types:
                    extracted_entity = extract_entity(ctx, slot_type)
                    if extracted_entity:
                        slot_values[slot_name] = extracted_entity
                        ctx.misc["agent"]["shared_memory"]["slot_values"] = slot_values
        return node_label, node

    return extract_entities


# def has_entities(**kwargs):
#     def extract_entities(vars):
#         flag = False
#         shared_memory = state_utils.get_shared_memory(vars)
#         slot_values = shared_memory.get("slots", {})
#         for slot_name, slot_types in kwargs.items():
#             if isinstance(slot_types, str):
#                 extracted_entity = extract_entity(vars, slot_types)
#                 if extracted_entity:
#                     slot_values[slot_name] = extracted_entity
#                     state_utils.save_to_shared_memory(vars, slot_values=slot_values)
#                     flag = True
#             elif isinstance(slot_types, list):
#                 for slot_type in slot_types:
#                     extracted_entity = extract_entity(vars, slot_type)
#                     if extracted_entity:
#                         slot_values[slot_name] = extracted_entity
#                         state_utils.save_to_shared_memory(vars, slot_values=slot_values)
#                         flag = True
#         return flag
#
#     return extract_entities



def wants_to_see(item_name: str):
    def has_cond(ctx: Context, actor: Actor, *args, **kwargs):
        match = re.search(r"((.*i\swant\sto\s)|(.*i\swanna\s)|(.*go\sto.*)|(.*\slook\sat\s)|"
                          r"(.*show\sme\s)|(.*tell\sme\s))(?P<item>.*)", ctx.last_request, re.I)
        if match:
            item = match.group('item')
        else:
            return False
        return levenshtein_item(item_name, item)

    return has_cond


def not_visited_album(ctx: Context, actor: Actor, *args, **kwargs):
    return ctx.misc.get("album_counter", 0) < 12


def move_on(ctx: Context, actor: Actor, *args, **kwargs):
    return bool(re.findall("move on", ctx.last_request, re.IGNORECASE))


def has_songs(ctx: Context, actor: Actor, *args, **kwargs):
    songs = [
        "Hey Jude",
        "Don't Let Me Down",
        "We Can Work it Out",
        "Come Together",
        "Yellow Submarine",
        "Hello, Goodbye",
        "A Day In The Life",
        "Penny Lane",
        "Revolution",
        "Something",
        "Imagine",
        "Help",
    ]
    return levenshtein_item(songs, ctx.last_request)


def has_member(member_name: str):
    def has_member_condition(ctx: Context, actor: Actor, *args, **kwargs):
        return levenshtein_item(member_name, ctx.last_request)

    return has_member_condition


def has_correct_answer(ctx: Context, actor: Actor, *args, **kwargs):
    a = ["Abbey Road", "Hard Day's Night", "Liverpool"]
    return levenshtein_item(a, ctx.last_request)


def has_any_album(ctx: Context, actor: Actor, *args, **kwargs):
    albums = [
        "Please Please Me",
        "With the Beatles",
        "Introducing... The Beatles",
        "Meet the Beatles!",
        "Twist and Shout",
        "The Beatles' Second Album",
        "The Beatles' Long Tall Sally",
        "Hard Day's Night",
        "Something New",
        "Help",
        "Sgt. Pepper's Lonely Hearts Club Band",
        "White Album",
        "The Beatles Beat",
        "Another Beatles Christmas Record",
        "Beatles '65",
        "Beatles VI",
        "Five Nights In A Judo Arena",
        "The Beatles at the Hollywood Bowl",
        "Live! at the Star-Club in Hamburg, German; 1962",
        "The Black Album",
        "20 Exitos De Oro",
        "A Doll's House",
        "The Complete Silver Beatles",
        "Rock 'n' Roll Music Vol. 1",
        "Yellow Submarine",
        "Let It Be",
        "Beatles for Sale",
        "Revolver",
        "Abbey Road",
        "Rubber Soul",
    ]

    return levenshtein_item(albums, ctx.last_request)


def is_beatles_song(ctx: Context, actor: Actor, *args, **kwargs):
    songs = [
	'Title', '12-Bar Original', 'A Day in the Life', "Hard Day's Night",
	'A Shot of Rhythm and Blues', 'A Taste of Honey', 'Across the Universe', 'Act Naturally',
	"Ain't She Sweet", "All I've Got to Do", 'All My Loving', 'All Things Must Pass', 'All Together Now',
	'All You Need Is Love', 'And I Love Her', 'And Your Bird Can Sing', 'Anna (Go to Him)', 'Another Girl',
	'Any Time at All', 'Ask Me Why', "Baby It's You", "Baby's in Black", '"Baby', 'Back in the U.S.S.R.',
	'Bad Boy', 'Bad to Me', 'Beautiful Dreamer', 'Because I Know You Love Me So', 'Because', 'Being for the Benefit of Mr. Kite!',
	'Birthday', 'Blackbird', 'Blue Jay Way', 'Boys', 'Bésame Mucho', "Can't Buy Me Love", 'Carol', 'Carry That Weight', 'Catswalk',
	'Cayenne', 'Chains', 'Child of Nature', 'Christmas Time (Is Here Again)', 'Circles', 'Clarabella', 'Come and Get It', 'Come Together',
	'Cry Baby Cry', 'Cry for a Shadow', '"Crying', 'Day Tripper', 'Dear Prudence', 'Devil in Her Heart', 'Dig a Pony', 'Dig It', '"Dizzy',
	'Do You Want to Know a Secret?', 'Doctor Robert', "Don't Bother Me", "Don't Ever Change", "Don't Let Me Down", "Don't Pass Me By",
	'Drive My Car', 'Eight Days a Week', 'Eleanor Rigby', 'Etcetera', 'Every Little Thing',
	"Everybody's Got Something to Hide Except Me and My Monkey", "Everybody's Trying to Be My Baby", 'Fancy My Chances with You',
	'Fixing a Hole', 'Flying', 'For No One', 'For You Blue', 'Free as a Bird', 'From Me to You', 'From Us to You', 'Get Back',
	'Getting Better', 'Girl', 'Glad All Over', 'Glass Onion', 'Golden Slumbers', 'Good Day Sunshine', '"Good Morning', 'Good Night',
	'Goodbye', 'Got to Get You into My Life', '"Hallelujah', 'Happiness Is a Warm Gun', 'Heather', 'Hello Little Girl', '"Hello',
	'Help!', 'Helter Skelter', 'Her Majesty', 'Here Comes the Sun', '"Here', 'Hey Bulldog', 'Hey Jude', 'Hippy Hippy Shake',
	'Hold Me Tight', "Honey Don't", 'Honey Pie', 'How Do You Do It?', 'I Am the Walrus', 'I Call Your Name', "I Don't Want to Spoil the Party",
	'I Feel Fine', 'I Forgot to Remember to Forget', 'I Got a Woman', 'I Got to Find My Baby', "I Just Don't Understand", 'I Lost My Little Girl',
	'I Me Mine', 'I Need You', 'I Saw Her Standing There', 'I Should Have Known Better', 'I Wanna Be Your Man', 'I Want to Hold Your Hand',
	'I Want to Tell You', "I Want You (She's So Heavy)", 'I Will', "I'll Be Back", "I'll Be on My Way", "I'll Cry Instead", "I'll Follow the Sun",
	"I'll Get You", "I'll Keep You Satisfied", "I'm a Loser", "I'm Down", "I'm Gonna Sit Right Down and Cry (Over You)",
	"I'm Happy Just to Dance with You", "I'm In Love", "I'm Looking Through You", "I'm Only Sleeping", "I'm So Tired", "I'm Talking About You",
	"I'm Talking About You", "I've Got a Feeling", "I've Just Seen a Face", 'If I Fell', 'If I Needed Someone', "If You've Got Trouble",
	'In My Life', 'In Spite of All the Danger', "It Won't Be Long", "It's All Too Much", "It's Only Love", 'Jazz Piano Song', "Jessie's Dream",
	'Johnny B. Goode', 'Julia', 'Junk', '"Kansas City/Hey', 'Keep Your Hands Off My Baby', 'Komm Gib Mir Deine Hand', 'Lady Madonna',
	'Leave My Kitten Alone', 'Lend Me Your Comb', 'Let It Be', 'Like Dreamers Do', 'Little Child', 'Lonesome Tears in My Eyes', 'Long Tall Sally',
	'"Long', 'Looking Glass', 'Love Me Do', 'Love of the Loved', 'Love You To', 'Lovely Rita', 'Lucille', 'Lucy in the Sky with Diamonds', 'Madman',
	'Maggie Mae', 'Magical Mystery Tour', '"Mailman', 'Martha My Dear', 'Matchbox', "Maxwell's Silver Hammer", 'Mean Mr. Mustard', '"Memphis',
	'Michelle', 'Misery', "Money (That's What I Want)", 'Moonlight Bay', "Mother Nature's Son", 'Mr. Moonlight', 'My Bonnie', 'No Reply',
	'Norwegian Wood (This Bird Has Flown)', 'Not a Second Time', 'Not Guilty', "Nothin' Shakin' (But the Leaves on the Trees)", 'Nowhere Man',
	'"Ob-La-Di', "Octopus's Garden", 'Oh! Darling', 'Old Brown Shoe', 'One After 909', 'One and One Is Two', 'Only a Northern Song', 'Ooh! My Soul',
	'P.S. I Love You', 'Paperback Writer', 'Penny Lane', 'Piggies', 'Please Mr. Postman', 'Please Please Me', 'Polythene Pam', 'Rain', 'Real Love',
	'Revolution 1', 'Revolution 9', 'Revolution', '"Rip It Up/Shake', 'Rock and Roll Music', 'Rocky Raccoon', 'Roll Over Beethoven',
	'Run for Your Life', 'Savoy Truffle', "Searchin'", 'September in the Rain', 'Sexy Sadie', "Sgt. Pepper's Lonely Hearts Club Band (Reprise)",
	"Sgt. Pepper's Lonely Hearts Club Band", "Shakin' in the Sixties", 'She Came in Through the Bathroom Window', 'She Loves You',
	'She Said She Said', "She's a Woman", "She's Leaving Home", 'Shout', 'Sie Liebt Dich', 'Slow Down', 'So How Come (No One Loves Me)',
	'Soldier of Love (Lay Down Your Arms)', 'Some Other Guy', 'Something', 'Sour Milk Sea', 'Step Inside Love/Los Paranoias',
	'Strawberry Fields Forever', 'Sun King', 'Sure to Fall (In Love with You)', 'Sweet Little Sixteen', 'Take Good Care of My Baby',
	'Taking a Trip to Carolina', 'Taxman', 'Teddy Boy', 'Tell Me What You See', 'Tell Me Why', 'Thank You Girl', 'That Means a Lot',
	"That'll Be the Day", "That's All Right (Mama)", 'The Ballad of John and Yoko', 'The Continuing Story of Bungalow Bill', 'The End',
	'The Fool on the Hill', 'The Honeymoon Song', 'The Inner Light', 'The Long and Winding Road', 'The Night Before', 'The Saints',
	'The Sheik of Araby', 'The Word', "There's a Place", 'Things We Said Today', 'Think for Yourself', 'This Boy', 'Three Cool Cats',
	'Ticket to Ride', 'Till There Was You', 'Tip of My Tongue', 'To Know Her is to Love Her', 'Tomorrow Never Knows', 'Too Much Monkey Business',
	'Twist and Shout', 'Two of Us', 'Wait', 'Watching Rainbows', 'We Can Work It Out', 'What Goes On', "What You're Doing",
	"What's The New Mary Jane", 'When I Get Home', "When I'm Sixty-Four", 'While My Guitar Gently Weeps', "Why Don't We Do It in the Road?",
	'Wild Honey Pie', "Winston's Walk", 'With a Little Help from My Friends', 'Within You Without You', 'Woman', 'Words of Love',
	'Yellow Submarine', 'Yer Blues', 'Yes It Is', 'Yesterday', "You Can't Do That", 'You Know My Name (Look Up the Number)',
	'You Know What to Do', 'You Like Me Too Much', 'You Never Give Me Your Money', "You Won't See Me", "You'll Be Mine",
	"You're Going to Lose That Girl", "You've Got to Hide Your Love Away", "You've Really Got a Hold on Me", 'Young Blood',
    'Your Mother Should Know'
    ]
    songs_re = "|".join(songs)
    return bool(re.findall(songs_re, ctx.last_request, re.IGNORECASE))


def is_next(album_name: str):
    # albums_seq = {
    #     "Please Please Me": "With The Beatles",
    #     "With The Beatles": "Hard Day's Night",
    #     "Hard Day's Night": "Beatles For Sale",
    #     "Beatles For Sale": "Help",
    #     "Help": "Rubber Soul",
    #     "Rubber Soul": "Revolver",
    #     "Revolver": "Yellow Submarine",
    #     "Yellow Submarine": "Sgt. Pepper's Lonely Hearts Club Band",
    #     "Sgt. Pepper's Lonely Hearts Club Band": "White Album",
    #     "White Album": "Abbey Road",
    #     "Abbey Road": "Let It Be",
    #     "Let It Be": "Please Please Me"
    # }
    def next(ctx: Context, actor: Actor, *args, **kwargs):
        flag = False
        if ctx.misc.get("current_node") == album_name:
            flag = True
        return flag
    return next



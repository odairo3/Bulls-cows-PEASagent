import itertools
import math
import random
from abc import ABC, abstractmethod

class interfazAgente(ABC):
    @abstractmethod
    def start(self): pass
    @abstractmethod
    def try_attempt(self): pass
    @abstractmethod
    def discover(self, numeroLista): pass
    @abstractmethod
    def feedBack(self, retroalimentacionLista): pass

class bullsCowsAgent(interfazAgente):
    # Se calcula una sola vez a nivel de clase
    ALL_CANDIDATES = [list(p) for p in itertools.permutations(range(10), 4)]

    def __init__(self):
        self.secret = None
        self.hypothesis = None
        self.first_turn = True
        self.last_attempt = None

    def start(self):
        self.secret = random.sample(range(10), 4)
        self.hypothesis = list(self.ALL_CANDIDATES)
        self.first_turn = True
        self.last_attempt = None

    def try_attempt(self):
        attempt = self._select_next_attempt()
        self.last_attempt = attempt 
        return attempt

    def discover(self, numeroLista):
        cows, bulls = self.calculate_cows_bulls(self.secret, numeroLista)
        return [cows, bulls]

    def feedBack(self, retroalimentacionLista):
        cows, bulls = retroalimentacionLista[0], retroalimentacionLista[1]
        if self.last_attempt is not None:
            self._candidate_filtration(self.last_attempt, cows, bulls)

    @staticmethod
    def calculate_cows_bulls(secret, attempt):
        bulls = sum(s == a for s, a in zip(secret, attempt))
        cows = sum(a in secret for a in attempt) - bulls
        return cows, bulls

    def _candidate_filtration(self, attempt, real_cows, real_bulls):
        self.hypothesis = [
            cand for cand in self.hypothesis
            if self.calculate_cows_bulls(cand, attempt) == (real_cows, real_bulls)
        ]

    def _select_next_attempt(self):
        if self.first_turn:
            self.first_turn = False
            return [0, 1, 2, 3]

        if len(self.hypothesis) == 1:
            return self.hypothesis[0]

        best_attempt = None
        max_entropy = -1.0
        n = len(self.hypothesis)

        for attempt in self.hypothesis:
            frequencies = {}
            for cand in self.hypothesis:
                key = self.calculate_cows_bulls(cand, attempt)
                frequencies[key] = frequencies.get(key, 0) + 1

            entropy = 0.0
            for count in frequencies.values():
                p = count / n
                entropy -= p * math.log2(p)

            if entropy > max_entropy:
                max_entropy = entropy
                best_attempt = attempt

        return best_attempt
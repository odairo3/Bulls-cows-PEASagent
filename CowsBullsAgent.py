import itertools
import math
import random


class bullsCowsAgent:

    def __init__(self):

        self.all_candidates = [''.join(p) for p in itertools.permutations('0123456789', 4)]
        self.reset_round()


    def reset_round(self):
        self.hypothesis = list(self.all_candidates)
        self.first_turn = True

    @staticmethod
    def calculate_cows_bulls(secret, attempt):
        bulls = sum(s == i for s, i in zip(secret, attempt)) #Wtf does the zip function do
        cows = sum(i in secret for i in attempt) - bulls
        return cows, bulls

    def candidate_filtration(self, attempt, real_cows, real_bulls):
        self.hypothesis = [
            cand for cand in self.hypothesis
            if self.calculate_cows_bulls(cand, attempt) == (real_cows, real_bulls)
        ]

    def select_next_attempt(self):

        if self.first_turn:
            self.first_turn = False
            return "0123"
        # we need number format rules

        if len(self.hypothesis) == 1:
            return self.hypothesis[0]
        # i don't understand "self" in python

        best_attempt = None
        max_enthropy = -1.0
        n_all_candidates = len(self.hypothesis)

        for attempt in self.hypothesis:
            frecuencies = {}
            for cand in self.hypothesis:
                bulls_cows = self.calculate_cows_bulls(cand, attempt)
                frecuencies[bulls_cows] = frecuencies.get(bulls_cows, 0) + 1 #what is this getting from which dictionary?

            enthropy = 0.0
            for count in frecuencies.values(): #is {} a dictionary, then the things inside it are the values and their indexes the keys?
                probability = count/ n_all_candidates
                enthropy -= probability * math.log2(probability)

            if enthropy > max_enthropy: #why is it using negative numbers? liek its not even the property of shannons equation, its just... negative?
                max_enthropy = enthropy
                best_attempt = attempt
        # what does this do? find the smallest enthropy such that amongst the attempts we may choose the one that gives us the most info?
        return best_attempt


def simulate_game(secret=None):
    if secret is None:
        secret = ''.join(random.sample('0123456789', 4))

    agent = bullsCowsAgent()
    turns = 0
    print(f"--- Nueva Partida | Código Secreto: {secret} ---")

    while True:
        turns += 1
        attempt = agent.select_next_attempt()
        cows, bulls = bullsCowsAgent.calculate_cows_bulls(secret, attempt)
        candidates_left = len(agent.hypothesis)

        print(f"Turno {turns}: attempt = {attempt} | Resp = {bulls} fijas, {cows} Picas | Candidatos = {candidates_left}")

        if bulls == 4:
            print(f"¡Código adivinado en {turns} turns!\n")
            return turns

        agent.candidate_filtration(attempt, cows, bulls)


if __name__ == "__main__":
    # 1. Prueba con código fijo
    simulate_game("4815")

    # 2. Evaluación del rendimiento sobre 10 partidas aleatorias
    print("--- Evaluación en 10 partidas aleatorias ---")
    results = [simulate_game() for _ in range(10)]
    print(f"Promedio general: {sum(results) / len(results):.2f} turnos")
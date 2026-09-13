import itertools
import math
import random

class bullsCowsAgent:
    def __init__(self):
        # Pre-calculamos los 5040 candidatos posibles (10 dígitos, grupos de 4 sin repetición)
        self.all_candidates = [''.join(p) for p in itertools.permutations('0123456789', 4)]
        self.reset_round()

    def reset_round(self):
        # Al inicio de cada partida, la hipótesis contiene todos los números
        self.hypothesis = list(self.all_candidates)
        self.first_turn = True

    @staticmethod
    def calculate_cows_bulls(secret, attempt):
        # Forma súper rápida y elegante en Python de contar fijas y picas
        bulls = sum(s == i for s, i in zip(secret, attempt))
        cows = sum(i in secret for i in attempt) - bulls
        return cows, bulls

    def candidate_filtration(self, attempt, real_cows, real_bulls):
        # Filtramos dejando SOLO los candidatos que darían la misma respuesta
        self.hypothesis = [
            cand for cand in self.hypothesis
            if self.calculate_cows_bulls(cand, attempt) == (real_cows, real_bulls)
        ]

    def select_next_attempt(self):
        if self.first_turn:
            self.first_turn = False
            return "0123" # Una apertura óptima estándar

        # Si solo queda 1 candidato, ¡ganamos! No hay que calcular nada.
        n_candidates_left = len(self.hypothesis)
        if n_candidates_left == 1:
            return self.hypothesis[0]

        best_attempt = None
        # Inicializamos con infinito positivo porque buscamos MINIMIZAR este valor
        min_expected_size = float('inf') 
        
        # Convertimos a Set para que la búsqueda en el desempate sea instantánea O(1)
        hypothesis_set = set(self.hypothesis)

        # REGLA DE ORO DE COMPETENCIA: Iteramos sobre los 5.040, no solo sobre los restantes
        for attempt in self.all_candidates:
            frecuencies = {}
            # Vemos cómo este 'attempt' dividiría a los candidatos que nos quedan
            for cand in self.hypothesis:
                bulls_cows = self.calculate_cows_bulls(cand, attempt)
                frecuencies[bulls_cows] = frecuencies.get(bulls_cows, 0) + 1

            # Calculamos el Tamaño Esperado (Expected Size) sin usar logaritmos lentos
            expected_size = 0.0
            for count in frecuencies.values():
                expected_size += (count * count) / n_candidates_left

            # Actualizamos si encontramos una jugada que fragmente mejor el grupo
            if expected_size < min_expected_size:
                min_expected_size = expected_size
                best_attempt = attempt
            
            # DESEMPATE: Si dos jugadas son exactamente igual de buenas dividiendo...
            elif math.isclose(expected_size, min_expected_size):
                # ...elegimos la que AÚN es un candidato posible (nos da la chance de ganar en este turno)
                if attempt in hypothesis_set and best_attempt not in hypothesis_set:
                    best_attempt = attempt

        return best_attempt

def simulate_game(secret=None, silent=False):
    if secret is None:
        secret = ''.join(random.sample('0123456789', 4))
    
    agent = bullsCowsAgent()
    turns = 0
    if not silent:
        print(f"\n--- Nueva Partida | Código Secreto: {secret} ---")

    while True:
        turns += 1
        attempt = agent.select_next_attempt()
        cows, bulls = bullsCowsAgent.calculate_cows_bulls(secret, attempt)
        candidates_left = len(agent.hypothesis)

        if not silent:
            print(f"Turno {turns}: attempt = {attempt} | Resp = {bulls} fijas, {cows} Picas | Candidatos restantes = {candidates_left}")

        if bulls == 4:
            if not silent:
                print(f"¡Código adivinado en {turns} turnos!")
            return turns

        agent.candidate_filtration(attempt, cows, bulls)


if __name__ == "__main__":
    # Partida visible de demostración
    simulate_game("4815")

    # Prueba de estrés para medir el promedio real en competencia
    print("\n--- Evaluación en 50 partidas aleatorias (Silencioso) ---")
    print("Calculando... (Esto puede tomar unos segundos)")
    
    # Ponemos silent=True para no inundar la consola y solo ver el resultado
    results = [simulate_game(silent=True) for _ in range(50)]
    
    promedio = sum(results) / len(results)
    maximo_turnos = max(results)
    
    print(f"Promedio general de turnos: {promedio:.2f}")
    print(f"Peor partida (Máximo de turnos): {maximo_turnos}")
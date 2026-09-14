import itertools
import random

# =========================================================================
# AGENTE 1: EL COMPETIDOR FUERTE (Gana en ~5-7 turnos)
# =========================================================================
class AgenteNormal:
    """
    Este agente es sumamente eficiente. 
    Guarda las 5040 combinaciones posibles y, con cada feedback, 
    elimina todas las combinaciones que lógicamente ya no pueden ser la respuesta.
    """
    def __init__(self):
        self.candidatos = []
        self.ultimo_intento = []

    def start(self):
        # Genera las 5040 combinaciones posibles de 4 dígitos únicos (del 0 al 9)
        self.candidatos = [list(p) for p in itertools.permutations(range(10), 4)]

    def try_attempt(self):
        # Escoge una opción al azar de los candidatos lógicos que aún quedan
        self.ultimo_intento = random.choice(self.candidatos)
        return self.ultimo_intento

    def receive_feedback(self, picas, fijas):
        # Filtra las opciones imposibles basándose en la respuesta del juez
        nuevos_candidatos = []
        for cand in self.candidatos:
            # Simula cuántas picas y fijas tendría este candidato comparado con el último intento
            fijas_sim = sum(1 for x, y in zip(cand, self.ultimo_intento) if x == y)
            picas_sim = sum(1 for x in cand if x in self.ultimo_intento) - fijas_sim
            
            # Si el resultado simulado coincide con lo que dijo el juez, es un candidato válido
            if picas_sim == picas and fijas_sim == fijas:
                nuevos_candidatos.append(cand)
                
        self.candidatos = nuevos_candidatos



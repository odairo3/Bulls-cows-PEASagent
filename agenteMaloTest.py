import itertools
import random


# =========================================================================
# AGENTE 2: EL COMPETIDOR DÉBIL (Gana en ~2500 turnos)
# =========================================================================
class AgenteCaracol:
    """
    Este agente es el peor posible (sin romper las reglas de formato).
    Genera todas las combinaciones y las prueba en orden secuencial 
    ([0,1,2,3], [0,1,2,4], etc.).
    Ignora completamente el feedback, por lo que tardará cientos de turnos.
    """
    def __init__(self):
        self.todas_opciones = []
        self.indice = 0

    def start(self):
        # Genera todas las opciones ordenadas numéricamente
        self.todas_opciones = [list(p) for p in itertools.permutations(range(10), 4)]
        self.indice = 0

    def try_attempt(self):
        # Intenta la siguiente de la lista, sin saltarse ninguna
        intento = self.todas_opciones[self.indice]
        
        # Avanza al siguiente para el próximo turno, evitando repetir pero siendo ineficiente
        if self.indice < len(self.todas_opciones) - 1:
            self.indice += 1
            
        return intento

    def receive_feedback(self, picas, fijas):
        # ¡No hace absolutamente nada! Entra la información y la ignora.
        pass
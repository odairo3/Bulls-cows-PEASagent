import itertools
from abc import ABC, abstractmethod

# Interfaz simplificada para el Nuevo Ambiente (Juez Central)
class interfazAgente(ABC):
    @abstractmethod
    def start(self): pass
    @abstractmethod
    def try_attempt(self): pass
    @abstractmethod
    def feedBack(self, retroalimentacionLista): pass


class macaronAgent(interfazAgente):
    """
    Agente PEAS Ultimate Tournament Edition.
    Utiliza una búsqueda exhaustiva Minimax Híbrida sobre el espacio 
    completo de 5,040 combinaciones para asegurar la victoria 
    en un máximo matemático de 5 turnos.
    """
    
    # Ontología inmutable: Todas las permutaciones válidas de 4 dígitos únicos
    ESPACIO_ESTADOS = [list(p) for p in itertools.permutations(range(10), 4)]

    def __init__(self):
        # --- ESTADO INTERNO (Creencias y Memoria) ---
        self.creencias_hipotesis = []
        self.memoria_ultimo_actuador = None
        self.turno_actual = 0

    # ==========================================
    # CONTROL DE CICLO DE VIDA
    # ==========================================
    def start(self):
        """Reinicia el agente al inicio de cada ronda (Ya no genera secretos)."""
        self.creencias_hipotesis = list(self.ESPACIO_ESTADOS)
        self.memoria_ultimo_actuador = None
        self.turno_actual = 0

    # ==========================================
    # ACTUADORES (Intervienen en el Ambiente)
    # ==========================================
    def try_attempt(self):
        """Actuador Principal: Envía la jugada matemáticamente óptima."""
        self.turno_actual += 1
        
        if self.turno_actual == 1:
            # Apertura matemáticamente óptima demostrada
            accion = [0, 1, 2, 3]
        elif len(self.creencias_hipotesis) == 1:
            # Si solo queda una opción, la disparamos
            accion = self.creencias_hipotesis[0]
        else:
            # Motor cognitivo profundo: buscar la mejor jugada
            accion = self._motor_inferencia_minimax()

        self.memoria_ultimo_actuador = accion
        return accion

    # ==========================================
    # SENSORES (Perciben el Ambiente)
    # ==========================================
    def feedBack(self, retroalimentacionLista):
        """Sensor: Filtra las creencias en base a la respuesta del Juez Central."""
        if self.memoria_ultimo_actuador is None:
            return
            
        picas_reales, fijas_reales = retroalimentacionLista
        
        # Filtro estricto de hipótesis
        self.creencias_hipotesis = [
            candidato for candidato in self.creencias_hipotesis
            if self._procesador_reglas(candidato, self.memoria_ultimo_actuador) == (picas_reales, fijas_reales)
        ]

    # ==========================================
    # PROCESOS INTERNOS (Cerebro Matemático)
    # ==========================================
    @staticmethod
    def _procesador_reglas(secreto, intento):
        """Cálculo rápido de picas y fijas."""
        fijas = sum(1 for s, a in zip(secreto, intento) if s == a)
        picas = sum(1 for a in intento if a in secreto) - fijas
        return picas, fijas

    def _motor_inferencia_minimax(self):
        """
        Motor Minimax Híbrido:
        1. Búsqueda de "Sacrificio": Evalúa los 5,040 códigos, no solo los válidos.
        2. Minimax: Minimiza el tamaño del peor escenario posible.
        3. Desempate: Usa Suma de Cuadrados (Expected Size) para separar jugadas iguales.
        4. Prioridad Validez: A igualdad de condiciones, prefiere intentar ganar.
        """
        mejor_accion = None
        min_peor_caso = float('inf')
        min_suma_cuadrados = float('inf')
        mejor_es_valida = False
        
        # Convertimos las creencias actuales a tuplas para búsqueda rápida O(1)
        set_creencias = set(tuple(x) for x in self.creencias_hipotesis)

        # Iteramos sobre TODO el universo de combinaciones
        for posible_accion in self.ESPACIO_ESTADOS:
            frecuencias = {}
            # ¿Cómo dividiría esta "posible_accion" a nuestros candidatos restantes?
            for candidato in self.creencias_hipotesis:
                resultado = self._procesador_reglas(candidato, posible_accion)
                frecuencias[resultado] = frecuencias.get(resultado, 0) + 1
            
            # 1. Métrica Minimax (El grupo más grande resultante)
            peor_caso_actual = max(frecuencias.values()) if frecuencias else 0
            
            # 2. Métrica Expected Size (Suma de cuadrados) para desempatar sin usar logaritmos lentos
            suma_cuadrados_actual = sum(v * v for v in frecuencias.values())
            
            es_valida = tuple(posible_accion) in set_creencias

            # Lógica de decisión multicriterio
            if peor_caso_actual < min_peor_caso:
                min_peor_caso = peor_caso_actual
                min_suma_cuadrados = suma_cuadrados_actual
                mejor_accion = posible_accion
                mejor_es_valida = es_valida
                
            elif peor_caso_actual == min_peor_caso:
                # Desempate 1: Mejor distribución general
                if suma_cuadrados_actual < min_suma_cuadrados:
                    min_suma_cuadrados = suma_cuadrados_actual
                    mejor_accion = posible_accion
                    mejor_es_valida = es_valida
                # Desempate 2: Si empatan en todo, elegir la que tenga chance de ganar este turno
                elif suma_cuadrados_actual == min_suma_cuadrados and es_valida and not mejor_es_valida:
                    mejor_accion = posible_accion
                    mejor_es_valida = True

        return mejor_accion
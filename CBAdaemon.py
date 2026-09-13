import itertools
import math
import random
from abc import ABC, abstractmethod

# Interfaz requerida por el ambiente
class interfazAgente(ABC):
    @abstractmethod
    def start(self): pass
    @abstractmethod
    def try_attempt(self): pass
    @abstractmethod
    def discover(self, numeroLista): pass
    @abstractmethod
    def feedBack(self, retroalimentacionLista): pass


class AgentePEAS(interfazAgente):
    """
    Agente estructurado bajo el modelo PEAS.
    Opera como un ente reactivo (daemon-like) respondiendo a estímulos del entorno.
    """
    
    # Conocimiento base inmutable (Ontología del agente)
    ESPACIO_ESTADOS = [list(p) for p in itertools.permutations(range(10), 4)]

    def __init__(self):
        # --- ESTADO INTERNO (Creencias y Memoria) ---
        self.memoria_secreto = None
        self.creencias_hipotesis = None
        self.estado_primer_turno = True
        self.memoria_ultimo_actuador = None

    # ==========================================
    # CONTROL DE CICLO DE VIDA (Despertar/Reset)
    # ==========================================
    def start(self):
        """Inicializa el estado interno al comenzar una nueva ronda del torneo."""
        self.memoria_secreto = random.sample(range(10), 4)
        self.creencias_hipotesis = list(self.ESPACIO_ESTADOS)
        self.estado_primer_turno = True
        self.memoria_ultimo_actuador = None

    # ==========================================
    # ACTUADORES (Intervienen en el Ambiente)
    # ==========================================
    def try_attempt(self):
        """Actuador Principal: Modifica el ambiente enviando una jugada."""
        # Lógica de toma de decisiones basada en el estado actual
        if self.estado_primer_turno:
            self.estado_primer_turno = False
            accion = [0, 1, 2, 3]
        elif len(self.creencias_hipotesis) == 1:
            accion = self.creencias_hipotesis[0]
        else:
            accion = self._motor_inferencia_entropia()

        # Guardar en memoria para cuando el sensor reciba el feedback
        self.memoria_ultimo_actuador = accion
        return accion

    def discover(self, numeroLista):
        """
        Sensor y Actuador Simultáneo: 
        1. Sensa el intento del rival.
        2. Actúa devolviendo la evaluación [Picas, Fijas].
        """
        # Sensor procesa la información
        intento_rival = numeroLista
        
        # Actuador responde
        picas, fijas = self._procesador_reglas(self.memoria_secreto, intento_rival)
        return [picas, fijas]

    # ==========================================
    # SENSORES (Perciben el Ambiente)
    # ==========================================
    def feedBack(self, retroalimentacionLista):
        """Sensor Principal: Percibe el resultado de la acción previa y actualiza creencias."""
        if self.memoria_ultimo_actuador is None:
            return
            
        picas_reales = retroalimentacionLista[0]
        fijas_reales = retroalimentacionLista[1]
        
        # Actualización del estado de creencias (filtrado del espacio de estados)
        self.creencias_hipotesis = [
            candidato for candidato in self.creencias_hipotesis
            if self._procesador_reglas(candidato, self.memoria_ultimo_actuador) == (picas_reales, fijas_reales)
        ]

    # ==========================================
    # PROCESOS INTERNOS BÁSICOS (Cerebro)
    # ==========================================
    @staticmethod
    def _procesador_reglas(secreto, intento):
        """Lógica del mundo: Calcula (picas, fijas) dadas dos listas."""
        fijas = sum(s == a for s, a in zip(secreto, intento))
        picas = sum(a in secreto for a in intento) - fijas
        return picas, fijas

    def _motor_inferencia_entropia(self):
        """Proceso cognitivo pesado: Maximización de Shannon."""
        mejor_accion = None
        max_entropia = -1.0
        n_candidatos = len(self.creencias_hipotesis)

        for posible_accion in self.creencias_hipotesis:
            frecuencias = {}
            for candidato in self.creencias_hipotesis:
                resultado = self._procesador_reglas(candidato, posible_accion)
                frecuencias[resultado] = frecuencias.get(resultado, 0) + 1

            entropia_actual = 0.0
            for repeticiones in frecuencias.values():
                probabilidad = repeticiones / n_candidatos
                entropia_actual -= probabilidad * math.log2(probabilidad)

            if entropia_actual > max_entropia:
                max_entropia = entropia_actual
                mejor_accion = posible_accion

        return mejor_accion







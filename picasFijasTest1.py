import random

class PicasFijasAgent:

  def __init__(self):
    # Ajuste: Se declaran en el constructor para que cada instancia del agente 
    # tenga su propia memoria independiente.
    self.candidate_set = []
    self.my_number = []
    self.my_guess = []
    
    # Variables de compatibilidad para el ambiente GUI:
    self.secret = ""       # Para que la interfaz muestre el secreto
    self.hypothesis = []   # Para que el graficador cuente las hipótesis restantes

  def start(self):
    self.populate_candidate_set()
    self.choose_random_number()
    self.my_guess = [5,6,7,8]
    
    # Enlazar variables para la Interfaz Gráfica
    self.secret = str(self.my_number)
    self.hypothesis = self.candidate_set

  def populate_candidate_set(self):
    self.candidate_set = [[int(d) for d in str(n)] for n in range(1023, 9876 + 1) if len(set(str(n))) == 4]
    self.hypothesis = self.candidate_set

  def choose_random_number(self):
    self.my_number = random.choice(self.candidate_set)

  def try_attempt(self) -> list[int]:
    return self.my_guess

  def discover(self, enemy_guess) -> list[int]:
    # Ajuste de compatibilidad: Por si el oponente manda un string como "1234"
    formatted_guess = [int(x) for x in enemy_guess]
    return self.check_option(formatted_guess, self.my_number)

  def feedBack(self, enemy_answer: list[int]):
    self.clean_candidate_set(enemy_answer)
    # Pequeña validación de seguridad por si el set se vacía
    if self.candidate_set: 
        self.my_guess = random.choice(self.candidate_set)
    self.hypothesis = self.candidate_set # Actualizar la lista para la gráfica

  def clean_candidate_set(self, enemy_answer: list[int]):
    self.candidate_set = [opcion for opcion in self.candidate_set
                          if self.check_option(self.my_guess, opcion) == enemy_answer]

  def check_option(self, option:list[int], guessing_number: list[int]) -> list[int]:
    picas = 0
    fijas = 0

    for i in range(4):
      if option[i] in guessing_number:
        if option[i] == guessing_number[i]:
          fijas += 1
        else:
          picas += 1

    return [picas, fijas]
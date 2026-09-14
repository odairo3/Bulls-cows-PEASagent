import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import importlib
import sys
import os
import time
import threading
import queue
import concurrent.futures

# =========================================================================
# 1. ADAPTADOR UNIVERSAL (Duck Typing & Compatibilidad Transparente)
# =========================================================================
class AdaptadorUniversal:
    """
    Envuelve cualquier agente y estandariza la comunicación con el Ambiente.
    Soporta métodos como start, try_attempt/try_, evaluate/discover, 
    receive_feedback/feedBack, y propiedades/atributos secret/memoria_secreto.
    """
    def __init__(self, instancia_agente):
        self.agente = instancia_agente

    def start(self):
        if hasattr(self.agente, 'start'): 
            self.agente.start()

    @property
    def secret(self):
        return getattr(self.agente, 'secret', getattr(self.agente, 'memoria_secreto', [-1, -1, -1, -1]))

    def try_attempt(self):
        if hasattr(self.agente, 'try_attempt'): return self.agente.try_attempt()
        if hasattr(self.agente, 'try_'): return getattr(self.agente, 'try_')()
        return [-1, -1, -1, -1]

    def evaluate(self, intento):
        if hasattr(self.agente, 'evaluate'): return self.agente.evaluate(intento)
        if hasattr(self.agente, 'discover'): return self.agente.discover(intento)
        return [0, 0]

    def receive_feedback(self, picas, fijas):
        if hasattr(self.agente, 'receive_feedback'): 
            self.agente.receive_feedback(picas, fijas)
        elif hasattr(self.agente, 'feedBack'): 
            self.agente.feedBack([picas, fijas])

# =========================================================================
# 2. MOTOR DEL AMBIENTE (REGLAMENTO ESTRICTO)
# =========================================================================
class Ambiente:
    def __init__(self, log_callback=None):
        self.log = log_callback if log_callback else print
        self.reset_stats()
        
    def reset_stats(self):
        self.stats = {
            "victorias_A": 0, "victorias_B": 0, "empates": 0,
            "turnos_A": [], "turnos_B": [],
            "tiempo_A": 0.0, "tiempo_B": 0.0, "movs_A": 0, "movs_B": 0
        }
        self.ronda_actual = 0
        self.max_rondas = 3
        self.ronda_terminada = False

    def _es_valido_formato(self, lista):
        return isinstance(lista, list) and len(lista) == 4 and all(isinstance(x, int) and 0 <= x <= 9 for x in lista) and len(set(lista)) == 4

    def setup(self, claseA, claseB, nombreA, nombreB, n_rondas=3):
        self.reset_stats()
        self.max_rondas = n_rondas
        self.nombreA, self.nombreB = nombreA, nombreB
        self.claseA, self.claseB = claseA, claseB
        self.log("✅ Ambiente.setup completado: Agentes listos.")

    def initRound(self):
        self.ronda_actual += 1
        self.ronda_terminada = False
        self.ganador_ronda = None
        self.turno_actual = 0
        
        self.agenteA = AdaptadorUniversal(self.claseA())
        self.agenteB = AdaptadorUniversal(self.claseB())
        
        self.log(f"\n--- INICIANDO RONDA {self.ronda_actual} DE {self.max_rondas} ---")
        self.agenteA.start()
        self.agenteB.start()
        
        val_A, val_B = self._es_valido_formato(self.agenteA.secret), self._es_valido_formato(self.agenteB.secret)
        
        if not val_A and not val_B:
            self.log("🚨 Ambos agentes generaron secretos inválidos. Ronda empatada.")
            self.ronda_terminada, self.ganador_ronda = True, "Empate"
        elif not val_A:
            self.log(f"🚨 {self.nombreA} generó un secreto inválido. Pierde la ronda.")
            self.ronda_terminada, self.ganador_ronda = True, "B"
        elif not val_B:
            self.log(f"🚨 {self.nombreB} generó un secreto inválido. Pierde la ronda.")
            self.ronda_terminada, self.ganador_ronda = True, "A"

    def getAttempts(self):
        self.turno_actual += 1
        
        def pedir_intento(agente):
            t0 = time.perf_counter()
            intento = agente.try_attempt()
            t1 = time.perf_counter()
            return intento, (t1 - t0)

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futA = executor.submit(pedir_intento, self.agenteA)
            futB = executor.submit(pedir_intento, self.agenteB)
            intentoA, tiempoA = futA.result()
            intentoB, tiempoB = futB.result()

        self.stats["tiempo_A"] += tiempoA
        self.stats["tiempo_B"] += tiempoB
        self.stats["movs_A"] += 1
        self.stats["movs_B"] += 1

        if not self._es_valido_formato(intentoA):
            self.log(f"🚨 Intento inválido de {self.nombreA}: {intentoA}.")
            intentoA = [-1, -1, -1, -1]
            
        if not self._es_valido_formato(intentoB):
            self.log(f"🚨 Intento inválido de {self.nombreB}: {intentoB}.")
            intentoB = [-1, -1, -1, -1]

        self.log(f'"{self.nombreA}" intenta: {intentoA}')
        self.log(f'"{self.nombreB}" intenta: {intentoB}')
        return intentoA, intentoB

    def evaluateAttempts(self, intentoA, intentoB):
        fb_para_A = self.agenteB.evaluate(intentoA) if intentoA[0] != -1 else [0, 0]
        fb_para_B = self.agenteA.evaluate(intentoB) if intentoB[0] != -1 else [0, 0]
        
        validar = lambda fb: isinstance(fb, list) and len(fb) == 2 and (fb[0] + fb[1] <= 4)
        if not validar(fb_para_A): fb_para_A = [0, 0]
        if not validar(fb_para_B): fb_para_B = [0, 0]

        self.log(f'"{self.nombreB}" evalúa a A: ({fb_para_A[0]} Picas, {fb_para_A[1]} Fijas)')
        self.log(f'"{self.nombreA}" evalúa a B: ({fb_para_B[0]} Picas, {fb_para_B[1]} Fijas)')
        return fb_para_A, fb_para_B

    def dispatchFeedback(self, fb_para_A, fb_para_B):
        self.agenteA.receive_feedback(*fb_para_A)
        self.agenteB.receive_feedback(*fb_para_B)
        
        winA, winB = (fb_para_A == [0, 4]), (fb_para_B == [0, 4])
        
        if winA and winB:
            self.ganador_ronda, self.ronda_terminada = "Empate", True
            self.log(f"🤝 ¡Empate simultáneo en el turno {self.turno_actual}!")
        elif winA:
            self.ganador_ronda, self.ronda_terminada = "A", True
            self.log(f"🏆 ¡{self.nombreA} gana la ronda en el turno {self.turno_actual}!")
        elif winB:
            self.ganador_ronda, self.ronda_terminada = "B", True
            self.log(f"🏆 ¡{self.nombreB} gana la ronda en el turno {self.turno_actual}!")

        if self.ronda_terminada:
            if self.ganador_ronda == "A":
                self.stats["victorias_A"] += 1
                self.stats["turnos_A"].append(self.turno_actual)
            elif self.ganador_ronda == "B":
                self.stats["victorias_B"] += 1
                self.stats["turnos_B"].append(self.turno_actual)
            else:
                self.stats["empates"] += 1

    def getWinner(self):
        self.log("\n" + "="*45)
        self.log(f"🏁 TORNEO FINALIZADO ({self.max_rondas} Rondas)")
        self.log("="*45)
        vA, vB = self.stats["victorias_A"], self.stats["victorias_B"]
        if vA > vB: self.log(f"👑 GANADOR DEFINITIVO: {self.nombreA} ({vA} vs {vB} victorias)")
        elif vB > vA: self.log(f"👑 GANADOR DEFINITIVO: {self.nombreB} ({vB} vs {vA} victorias)")
        else: self.log(f"🤝 EL TORNEO FINALIZA EN EMPATE ({vA} victorias cada uno)")
        return self.stats

# =========================================================================
# 3. INTERFAZ GRÁFICA MULTI-THREADING (CRONÓMETRO EN TIEMPO REAL Y ESPECTADOR)
# =========================================================================
class AppTorneo:
    def __init__(self, root):
        self.root = root
        self.root.title("Torneo Picas y Fijas - Panel de Espectador")
        self.root.geometry("920x760")
        
        self.log_queue = queue.Queue()
        self.ambiente = Ambiente(log_callback=self.subir_log)
        self.agentes_cargados = {}
        
        # Estado del torneo y cronómetro
        self.ejecutando = False
        self.modo_auto = False
        self.tiempo_inicio = 0.0
        self.tiempo_acumulado = 0.0
        
        self.setup_ui()
        self.root.after(50, self.procesar_cola_logs)
        self.root.after(50, self.actualizar_cronometro)

    def setup_ui(self):
        # Panel Superior: Conexión y Combos
        f_top = tk.Frame(self.root, pady=5)
        f_top.pack(fill=tk.X)
        
        tk.Button(f_top, text="📁 Conectar Carpeta de Agentes", command=self.cargar_directorio, bg="#4CAF50", fg="white", font=("Arial", 9, "bold")).pack(pady=3)
        
        f_combo = tk.Frame(f_top)
        f_combo.pack()
        tk.Label(f_combo, text="Agente A:").grid(row=0, column=0, padx=5)
        self.cb_A = ttk.Combobox(f_combo, state="readonly", width=25)
        self.cb_A.grid(row=0, column=1, padx=5)
        
        tk.Label(f_combo, text="Agente B:").grid(row=0, column=2, padx=5)
        self.cb_B = ttk.Combobox(f_combo, state="readonly", width=25)
        self.cb_B.grid(row=0, column=3, padx=5)

        # Panel Espectador (Secretos visibles + Cronómetro)
        f_esp = tk.LabelFrame(self.root, text=" 👁️ PANEL ESPECTADOR ", font=("Arial", 10, "bold"), fg="#1565C0", bg="#E3F2FD", bd=2, relief=tk.GROOVE)
        f_esp.pack(fill=tk.X, padx=15, pady=5)

        self.lbl_crono = tk.Label(f_esp, text="⏱️ Tiempo: 00:00.0", font=("Consolas", 15, "bold"), fg="#D32F2F", bg="#E3F2FD")
        self.lbl_crono.pack(pady=4)

        f_sec = tk.Frame(f_esp, bg="#E3F2FD")
        f_sec.pack(fill=tk.X, pady=4)

        self.lbl_secA = tk.Label(f_sec, text="🔒 Secreto A: [ ? ]", font=("Consolas", 12, "bold"), fg="#0D47A1", bg="#E3F2FD")
        self.lbl_secA.pack(side=tk.LEFT, padx=30, expand=True)

        self.lbl_secB = tk.Label(f_sec, text="🔒 Secreto B: [ ? ]", font=("Consolas", 12, "bold"), fg="#B71C1C", bg="#E3F2FD")
        self.lbl_secB.pack(side=tk.RIGHT, padx=30, expand=True)

        # Controles
        f_btns = tk.Frame(self.root, pady=5)
        f_btns.pack()
        tk.Button(f_btns, text="⚙️ Preparar (3 Rondas)", command=lambda: self.preparar_torneo(3)).grid(row=0, column=0, padx=5)
        self.btn_paso = tk.Button(f_btns, text="👣 Turno a Turno", command=self.accion_paso, state=tk.DISABLED)
        self.btn_paso.grid(row=0, column=1, padx=5)
        self.btn_auto = tk.Button(f_btns, text="🤖 Modo Automático", command=self.accion_auto, state=tk.DISABLED)
        self.btn_auto.grid(row=0, column=2, padx=5)
        tk.Button(f_btns, text="📊 Torneo Masivo (100 Rondas)", command=lambda: self.preparar_torneo(100, auto=True), bg="#9C27B0", fg="white").grid(row=0, column=3, padx=5)

        # Log
        self.txt_log = scrolledtext.ScrolledText(self.root, width=100, height=24, bg="black", fg="white", font=("Consolas", 10))
        self.txt_log.pack(padx=15, pady=5, fill=tk.BOTH, expand=True)

    # --- Manejo del Cronómetro y Logs Thread-Safe ---
    def subir_log(self, mensaje):
        self.log_queue.put(mensaje)

    def procesar_cola_logs(self):
        while not self.log_queue.empty():
            msg = self.log_queue.get()
            self.txt_log.insert(tk.END, msg + "\n")
            self.txt_log.see(tk.END)
        self.root.after(50, self.procesar_cola_logs)

    def actualizar_cronometro(self):
        if self.ejecutando:
            transcurrido = self.tiempo_acumulado + (time.perf_counter() - self.tiempo_inicio)
            mins = int(transcurrido // 60)
            segs = int(transcurrido % 60)
            decs = int((transcurrido * 10) % 10)
            self.lbl_crono.config(text=f"⏱️ Tiempo: {mins:02d}:{segs:02d}.{decs}")
        self.root.after(50, self.actualizar_cronometro)

    def actualizar_panel_secretos(self):
        secA = getattr(self.ambiente.agenteA, 'secret', ['?'])
        secB = getattr(self.ambiente.agenteB, 'secret', ['?'])
        self.lbl_secA.config(text=f"🔑 Secreto {self.ambiente.nombreA}: {secA}")
        self.lbl_secB.config(text=f"🔑 Secreto {self.ambiente.nombreB}: {secB}")

    # --- Carga Dinámica de Agentes ---
    def cargar_directorio(self):
        carpeta = filedialog.askdirectory(title="Seleccionar carpeta de Agentes (.py)")
        if not carpeta: return
        
        sys.path.append(carpeta)
        for arch in os.listdir(carpeta):
            if arch.endswith(".py") and arch != "main.py":
                nombre_mod = arch[:-3]
                try:
                    modulo = importlib.import_module(nombre_mod)
                    for nombre, obj in modulo.__dict__.items():
                        if isinstance(obj, type) and hasattr(obj, 'start') and hasattr(obj, 'try_attempt'):
                            if obj.__name__ not in ["ABC", "interfazAgente", "InterfazAgente"]:
                                self.agentes_cargados[nombre] = obj
                except Exception as e:
                    print(f"Error cargando {arch}: {e}")
                    
        self.cb_A['values'] = list(self.agentes_cargados.keys())
        self.cb_B['values'] = list(self.agentes_cargados.keys())
        if self.agentes_cargados:
            self.cb_A.current(0)
            self.cb_B.current(min(1, len(self.agentes_cargados)-1))
            messagebox.showinfo("Directorio", f"Se encontraron {len(self.agentes_cargados)} agentes válidos.")

    # --- Flujo de Control ---
    def preparar_torneo(self, n_rondas, auto=False):
        nA, nB = self.cb_A.get(), self.cb_B.get()
        if not nA or not nB:
            messagebox.showerror("Error", "Selecciona dos agentes.")
            return
            
        self.txt_log.delete(1.0, tk.END)
        self.tiempo_acumulado = 0.0
        self.ambiente.setup(self.agentes_cargados[nA], self.agentes_cargados[nB], nA, nB, n_rondas)
        
        self.ambiente.initRound()
        self.actualizar_panel_secretos()
        
        self.btn_paso.config(state=tk.NORMAL)
        self.btn_auto.config(state=tk.NORMAL)
        
        if auto:
            self.accion_auto()

    def accion_paso(self):
        if not self.ejecutando:
            threading.Thread(target=self._hilo_ejecutar_turno, daemon=True).start()

    def accion_auto(self):
        self.modo_auto = True
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        if not self.ejecutando:
            threading.Thread(target=self._hilo_ejecutar_auto, daemon=True).start()

    def _hilo_ejecutar_turno(self):
        self.ejecutando = True
        self.tiempo_inicio = time.perf_counter()
        
        if self.ambiente.ronda_terminada:
            if self.ambiente.ronda_actual < self.ambiente.max_rondas:
                self.ambiente.initRound()
                self.root.after(0, self.actualizar_panel_secretos)
            else:
                self._finalizar_torneo()
                return

        if not self.ambiente.ronda_terminada:
            iA, iB = self.ambiente.getAttempts()
            fA, fB = self.ambiente.evaluateAttempts(iA, iB)
            self.ambiente.dispatchFeedback(fA, fB)

        self.tiempo_acumulado += (time.perf_counter() - self.tiempo_inicio)
        self.ejecutando = False

    def _hilo_ejecutar_auto(self):
        while self.modo_auto and (self.ambiente.ronda_actual <= self.ambiente.max_rondas):
            if self.ambiente.ronda_actual == self.ambiente.max_rondas and self.ambiente.ronda_terminada:
                break
            self._hilo_ejecutar_turno()
            time.sleep(0.01) # Pausa mínima para permitir renderizado
        self._finalizar_torneo()

    def _finalizar_torneo(self):
        self.ejecutando = False
        self.modo_auto = False
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        
        stats = self.ambiente.getWinner()
        
        calc_prom = lambda l: sum(l)/len(l) if l else 0
        t_mov_A = (stats["tiempo_A"]/stats["movs_A"])*1000 if stats["movs_A"] else 0
        t_mov_B = (stats["tiempo_B"]/stats["movs_B"])*1000 if stats["movs_B"] else 0
        total = self.ambiente.max_rondas
        
        reporte = (
            f"\n📊 ESTADÍSTICAS FINALES DEL TORNEO:\n"
            f"Victorias {self.ambiente.nombreA}: {(stats['victorias_A']/total)*100:.1f}%\n"
            f"Victorias {self.ambiente.nombreB}: {(stats['victorias_B']/total)*100:.1f}%\n"
            f"Empates: {(stats['empates']/total)*100:.1f}%\n"
            f"--- Rendimiento {self.ambiente.nombreA} ---\n"
            f"Turnos promedio para ganar: {calc_prom(stats['turnos_A']):.2f}\n"
            f"Tiempo de cómputo por turno: {t_mov_A:.4f} ms\n"
            f"--- Rendimiento {self.ambiente.nombreB} ---\n"
            f"Turnos promedio para ganar: {calc_prom(stats['turnos_B']):.2f}\n"
            f"Tiempo de cómputo por turno: {t_mov_B:.4f} ms\n"
        )
        self.subir_log(reporte)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppTorneo(root)
    root.mainloop()
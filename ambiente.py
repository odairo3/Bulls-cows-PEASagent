import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import matplotlib.pyplot as plt
import importlib
import threading
import time

# =========================================================================
# 1. ADAPTADOR DE AGENTES (Patrón Adapter)
# =========================================================================
class AgenteAdapter:
    """Envuelve a los agentes externos para que el motor del juego no 
    tenga que preocuparse por si usan 'try' o 'try_attempt'."""
    def __init__(self, instancia_agente):
        self.agente = instancia_agente

    def start(self):
        if hasattr(self.agente, "start"): 
            self.agente.start()

    def obtener_secreto(self):
        return getattr(self.agente, 'memoria_secreto', getattr(self.agente, 'secret', '?'))

    def hacer_intento(self):
        if hasattr(self.agente, "try"): return getattr(self.agente, "try")()
        elif hasattr(self.agente, "try_attempt"): return self.agente.try_attempt()
        return [0, 0, 0, 0]

    def descubrir(self, intento):
        if hasattr(self.agente, "discover"): return self.agente.discover(intento)
        return [0, 0]

    def recibir_feedback(self, picas_fijas):
        if hasattr(self.agente, "feedBack"): self.agente.feedBack(picas_fijas)

    def tamano_hipotesis(self):
        if hasattr(self.agente, "creencias_hipotesis"): return len(self.agente.creencias_hipotesis)
        if hasattr(self.agente, "hypothesis"): return len(self.agente.hypothesis)
        return 0

# =========================================================================
# 2. GESTOR DE AGENTES (Factory)
# =========================================================================
class GestorAgentes:
    """Se encarga exclusivamente de registrar e instanciar agentes desde archivos externos."""
    def __init__(self):
        self.registrados = {
            "Agente PEAS (Optimizado)": {"archivo": "CBAdaemon", "clase": "AgentePEAS"},
            "Agente Shannon (Entropía)": {"archivo": "testCowsBullsAgent", "clase": "bullsCowsAgent"},
            "Agente Base (Random)": {"archivo": "picasFijasTest1", "clase": "PicasFijasAgent"}
        }

    def agregar_agente(self, nombre, archivo, clase):
        modulo = importlib.import_module(archivo)
        getattr(modulo, clase) # Validar que exista
        self.registrados[nombre] = {"archivo": archivo, "clase": clase}

    def instanciar(self, nombre_visible):
        info = self.registrados[nombre_visible]
        instancia_cruda = getattr(importlib.import_module(info["archivo"]), info["clase"])()
        return AgenteAdapter(instancia_cruda)

# =========================================================================
# 3. LÓGICA DE JUEGO: UNA RONDA (SRP)
# =========================================================================
class PartidaIndividual:
    """Controla la lógica de un juego individual (paso a paso). No sabe nada de Tkinter."""
    def __init__(self, adaptador1, adaptador2):
        self.a1 = adaptador1
        self.a2 = adaptador2
        self.turno = 0
        self.terminado = False
        self.historial_a1 = []
        self.historial_a2 = []
        
        self.a1.start()
        self.a2.start()

    def jugar_turno(self):
        if self.terminado: return None
        self.turno += 1

        i1, i2 = self.a1.hacer_intento(), self.a2.hacer_intento()
        eval1, eval2 = self.a2.descubrir(i1), self.a1.descubrir(i2)

        self.historial_a1.append(self.a1.tamano_hipotesis())
        self.historial_a2.append(self.a2.tamano_hipotesis())

        self.a1.recibir_feedback(eval1)
        self.a2.recibir_feedback(eval2)

        gana1 = isinstance(eval1, list) and len(eval1) == 2 and eval1[1] == 4
        gana2 = isinstance(eval2, list) and len(eval2) == 2 and eval2[1] == 4
        
        if gana1 or gana2:
            self.terminado = True
            # Guardar el último estado de hipótesis
            self.historial_a1.append(self.a1.tamano_hipotesis())
            self.historial_a2.append(self.a2.tamano_hipotesis())

        return {
            "turno": self.turno,
            "intento1": i1, "eval1": eval1, "gana1": gana1,
            "intento2": i2, "eval2": eval2, "gana2": gana2
        }

# =========================================================================
# 4. LÓGICA DE JUEGO: TORNEO MASIVO ESTADÍSTICO
# =========================================================================
class TorneoEstadistico:
    """Ejecuta 100 simulaciones súper rápidas en memoria."""
    def __init__(self, gestor, nombre_a1, nombre_a2, n_rondas=100):
        self.gestor = gestor
        self.nombre_a1 = nombre_a1
        self.nombre_a2 = nombre_a2
        self.n_rondas = n_rondas

    def ejecutar(self, callback_progreso):
        stats = {
            "v_a1": 0, "v_a2": 0, "empates": 0,
            "turnos_a1": [], "turnos_a2": [],
            "tiempo_a1": 0.0, "tiempo_a2": 0.0,
            "mov_a1": 0, "mov_a2": 0
        }
        
        t_inicio_global = time.perf_counter()

        for i in range(self.n_rondas):
            if callback_progreso: callback_progreso(i + 1, self.n_rondas)
            
            a1 = self.gestor.instanciar(self.nombre_a1)
            a2 = self.gestor.instanciar(self.nombre_a2)
            a1.start()
            a2.start()

            juego_terminado = False
            turno = 1
            
            while turno <= 100 and not juego_terminado:
                # Agente 1
                t0 = time.perf_counter()
                i1 = a1.hacer_intento()
                e1 = a2.descubrir(i1)
                a1.recibir_feedback(e1)
                stats["tiempo_a1"] += (time.perf_counter() - t0)
                stats["mov_a1"] += 1

                # Agente 2
                t0 = time.perf_counter()
                i2 = a2.hacer_intento()
                e2 = a1.descubrir(i2)
                a2.recibir_feedback(e2)
                stats["tiempo_a2"] += (time.perf_counter() - t0)
                stats["mov_a2"] += 1

                gana1 = e1[1] == 4
                gana2 = e2[1] == 4

                if gana1 and gana2:
                    stats["empates"] += 1
                    juego_terminado = True
                elif gana1:
                    stats["v_a1"] += 1
                    stats["turnos_a1"].append(turno)
                    juego_terminado = True
                elif gana2:
                    stats["v_a2"] += 1
                    stats["turnos_a2"].append(turno)
                    juego_terminado = True
                
                turno += 1

        t_fin_global = time.perf_counter()
        return self._generar_reporte(stats, t_fin_global - t_inicio_global)

    def _generar_reporte(self, s, tiempo_total_sim):
        p_turnos_a1 = sum(s["turnos_a1"])/len(s["turnos_a1"]) if s["turnos_a1"] else 0
        p_turnos_a2 = sum(s["turnos_a2"])/len(s["turnos_a2"]) if s["turnos_a2"] else 0
        t_mov_a1 = (s["tiempo_a1"] / s["mov_a1"]) * 1000 if s["mov_a1"] else 0
        t_mov_a2 = (s["tiempo_a2"] / s["mov_a2"]) * 1000 if s["mov_a2"] else 0

        return (
            f"🎯 REPORTE ESTADÍSTICO ({self.n_rondas} Rondas)\n"
            f"Tiempo total: {tiempo_total_sim:.2f} s\n"
            f"--------------------------------------------------\n"
            f"🔵 {self.nombre_a1}:\n"
            f"  - Victorias: {s['v_a1']}%\n"
            f"  - Promedio Turnos para Ganar: {p_turnos_a1:.2f}\n"
            f"  - Tiempo total: {s['tiempo_a1']:.2f} s\n"
            f"  - Tiempo por mov: {t_mov_a1:.2f} ms\n"
            f"--------------------------------------------------\n"
            f"🔴 {self.nombre_a2}:\n"
            f"  - Victorias: {s['v_a2']}%\n"
            f"  - Promedio Turnos para Ganar: {p_turnos_a2:.2f}\n"
            f"  - Tiempo total: {s['tiempo_a2']:.2f} s\n"
            f"  - Tiempo por mov: {t_mov_a2:.2f} ms\n"
            f"--------------------------------------------------\n"
            f"🤝 Empates: {s['empates']}%\n"
        )

# =========================================================================
# 5. INTERFAZ GRÁFICA (Vista y Control de Eventos)
# =========================================================================
class PicasFijasGUI:
    """Se encarga exclusivamente de dibujar la pantalla y recibir clics."""
    def __init__(self, root):
        self.root = root
        self.root.title("Torneo Picas y Fijas - Entorno Educativo Avanzado")
        self.root.geometry("800x700")
        
        self.gestor = GestorAgentes()
        self.partida_actual = None
        
        self.modo_automatico = False
        self.simulacion_en_curso = False
        
        self.setup_ui()

    def setup_ui(self):
        # --- FRAME SUPERIOR ---
        frame_selectores = tk.Frame(self.root, pady=10)
        frame_selectores.pack(fill=tk.X)

        tk.Label(frame_selectores, text="Configuración del Torneo", font=("Arial", 12, "bold")).pack()

        frame_a1 = tk.Frame(frame_selectores)
        frame_a1.pack(side=tk.LEFT, padx=20)
        tk.Label(frame_a1, text="Agente 1 (Azul):").pack()
        self.combo_a1 = ttk.Combobox(frame_a1, values=list(self.gestor.registrados.keys()), state="readonly", width=25)
        self.combo_a1.current(0)
        self.combo_a1.pack()

        btn_nuevo_agente = tk.Button(frame_selectores, text="➕ Añadir Nuevo Agente", bg="#e0e0e0", command=self.abrir_ventana_nuevo_agente)
        btn_nuevo_agente.pack(side=tk.LEFT, padx=10, pady=15)

        frame_a2 = tk.Frame(frame_selectores)
        frame_a2.pack(side=tk.RIGHT, padx=20)
        tk.Label(frame_a2, text="Agente 2 (Rojo):").pack()
        self.combo_a2 = ttk.Combobox(frame_a2, values=list(self.gestor.registrados.keys()), state="readonly", width=25)
        self.combo_a2.current(1 if len(self.gestor.registrados) > 1 else 0)
        self.combo_a2.pack()

        # --- FRAME SECRETOS ---
        frame_secretos = tk.Frame(self.root, pady=5, bg="#e0f7fa")
        frame_secretos.pack(fill=tk.X)
        self.lbl_secreto_a1 = tk.Label(frame_secretos, text="A1: Esperando inicio...", font=("Arial", 11), fg="blue", bg="#e0f7fa")
        self.lbl_secreto_a1.pack(side=tk.LEFT, padx=50)
        self.lbl_secreto_a2 = tk.Label(frame_secretos, text="A2: Esperando inicio...", font=("Arial", 11), fg="red", bg="#e0f7fa")
        self.lbl_secreto_a2.pack(side=tk.RIGHT, padx=50)

        # --- FRAME CONSOLA ---
        frame_consola = tk.Frame(self.root, pady=10)
        frame_consola.pack(fill=tk.BOTH, expand=True, padx=20)
        self.txt_consola = scrolledtext.ScrolledText(frame_consola, width=80, height=15, font=("Courier", 10))
        self.txt_consola.pack(fill=tk.BOTH, expand=True)

        self.lbl_estado_sim = tk.Label(self.root, text="", font=("Arial", 10, "italic"), fg="green")
        self.lbl_estado_sim.pack()

        # --- FRAME CONTROLES ---
        frame_controles = tk.Frame(self.root, pady=10)
        frame_controles.pack(fill=tk.X)

        self.btn_iniciar = tk.Button(frame_controles, text="▶️ Iniciar 1 Ronda", font=("Arial", 10, "bold"), bg="#ffeb3b", command=self.iniciar_nueva_ronda)
        self.btn_iniciar.pack(side=tk.LEFT, padx=5)

        self.btn_paso = tk.Button(frame_controles, text="👣 Siguiente Paso", font=("Arial", 10), bg="#4caf50", fg="white", command=self.siguiente_paso, state=tk.DISABLED)
        self.btn_paso.pack(side=tk.LEFT, padx=5)

        self.btn_auto = tk.Button(frame_controles, text="🤖 Automático", font=("Arial", 10), bg="#2196f3", fg="white", command=self.activar_automatico, state=tk.DISABLED)
        self.btn_auto.pack(side=tk.LEFT, padx=5)

        self.btn_graficas = tk.Button(frame_controles, text="📊 Gráfica Deducción", font=("Arial", 10), bg="#ff9800", fg="white", command=self.mostrar_graficas, state=tk.DISABLED)
        self.btn_graficas.pack(side=tk.LEFT, padx=5)

        self.btn_sim_masiva = tk.Button(frame_controles, text="🚀 Análisis Estadístico (100 Tests)", font=("Arial", 10, "bold"), bg="#9c27b0", fg="white", command=self.lanzar_simulacion_masiva)
        self.btn_sim_masiva.pack(side=tk.RIGHT, padx=15)

    def log_mensaje(self, mensaje):
        self.txt_consola.insert(tk.END, mensaje + "\n")
        self.txt_consola.see(tk.END)

    def actualizar_combos(self):
        agentes = list(self.gestor.registrados.keys())
        self.combo_a1["values"] = agentes
        self.combo_a2["values"] = agentes

    def abrir_ventana_nuevo_agente(self):
        ventana_add = tk.Toplevel(self.root)
        ventana_add.title("Añadir Agente")
        ventana_add.geometry("350x250")
        
        tk.Label(ventana_add, text="Nombre visible:").pack(pady=5)
        entry_nombre = tk.Entry(ventana_add, width=30)
        entry_nombre.pack()
        
        tk.Label(ventana_add, text="Archivo (sin .py):").pack(pady=5)
        entry_archivo = tk.Entry(ventana_add, width=30)
        entry_archivo.pack()
        
        tk.Label(ventana_add, text="Clase:").pack(pady=5)
        entry_clase = tk.Entry(ventana_add, width=30)
        entry_clase.pack()

        def guardar():
            n, a, c = entry_nombre.get(), entry_archivo.get(), entry_clase.get()
            if n and a and c:
                try:
                    self.gestor.agregar_agente(n, a, c)
                    self.actualizar_combos()
                    messagebox.showinfo("Éxito", f"Agente '{n}' añadido.")
                    ventana_add.destroy()
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo cargar: {e}")

        tk.Button(ventana_add, text="Guardar", bg="#4caf50", fg="white", command=guardar).pack(pady=15)

    # --- LÓGICA: 1 RONDA ---
    def iniciar_nueva_ronda(self):
        try:
            a1 = self.gestor.instanciar(self.combo_a1.get())
            a2 = self.gestor.instanciar(self.combo_a2.get())
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo instanciar los agentes.\n{e}")
            return

        self.partida_actual = PartidaIndividual(a1, a2)
        self.modo_automatico = False

        self.lbl_secreto_a1.config(text=f"A1: {a1.obtener_secreto()}")
        self.lbl_secreto_a2.config(text=f"A2: {a2.obtener_secreto()}")

        self.txt_consola.delete(1.0, tk.END)
        self.log_mensaje(f"--- RONDA INDIVIDUAL: {self.combo_a1.get()} VS {self.combo_a2.get()} ---")
        
        self.btn_paso.config(state=tk.NORMAL)
        self.btn_auto.config(state=tk.NORMAL)
        self.btn_graficas.config(state=tk.DISABLED)

    def siguiente_paso(self):
        if not self.partida_actual or self.partida_actual.terminado: return
        
        res = self.partida_actual.jugar_turno()
        self.log_mensaje(f"Turno {res['turno']}: A1 intenta {res['intento1']} (P:{res['eval1'][0]}, F:{res['eval1'][1]}) | A2 intenta {res['intento2']} (P:{res['eval2'][0]}, F:{res['eval2'][1]})")

        if self.partida_actual.terminado:
            self.finalizar_juego(res['gana1'], res['gana2'], res['turno'])

    def activar_automatico(self):
        self.modo_automatico = True
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        self.ejecutar_loop_automatico()

    def ejecutar_loop_automatico(self):
        if self.partida_actual and not self.partida_actual.terminado and self.modo_automatico:
            self.siguiente_paso()
            self.root.after(400, self.ejecutar_loop_automatico)

    def finalizar_juego(self, gana1, gana2, turno):
        self.modo_automatico = False
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        self.btn_graficas.config(state=tk.NORMAL)
        
        msg = f"¡EMPATE EN TURNO {turno}!" if (gana1 and gana2) else (f"¡GANA A1 EN TURNO {turno}!" if gana1 else f"¡GANA A2 EN TURNO {turno}!")
        self.log_mensaje("\n" + "="*40 + "\n" + msg + "\n" + "="*40)

    def mostrar_graficas(self):
        if not self.partida_actual: return
        turnos = range(len(self.partida_actual.historial_a1))
        
        plt.figure(figsize=(9, 5))
        plt.plot(turnos, self.partida_actual.historial_a1, label='Agente 1', color='blue', marker='o')
        plt.plot(turnos, self.partida_actual.historial_a2, label='Agente 2', color='red', marker='x')
        plt.title('Reducción del Espacio de Hipótesis (1 Ronda)')
        plt.xlabel('Turnos')
        plt.ylabel('Hipótesis Restantes (log)')
        plt.yscale('log')
        plt.grid(True, which="both", ls="--", alpha=0.5)
        plt.legend()
        plt.tight_layout()
        plt.show()

    # --- LÓGICA: SIMULACIÓN MASIVA ---
    def lanzar_simulacion_masiva(self):
        if self.simulacion_en_curso: return
        
        self.simulacion_en_curso = True
        self.btn_iniciar.config(state=tk.DISABLED)
        self.btn_paso.config(state=tk.DISABLED)
        self.btn_auto.config(state=tk.DISABLED)
        self.btn_sim_masiva.config(state=tk.DISABLED)
        self.btn_graficas.config(state=tk.DISABLED)
        
        self.txt_consola.delete(1.0, tk.END)
        self.log_mensaje("Iniciando análisis estadístico de 100 rondas en segundo plano...")
        self.log_mensaje("El juego NO se congelará. Espera los resultados...\n")

        hilo = threading.Thread(target=self._hilo_masivo, daemon=True)
        hilo.start()

    def _hilo_masivo(self):
        try:
            torneo = TorneoEstadistico(self.gestor, self.combo_a1.get(), self.combo_a2.get(), 100)
            
            def puente_ui(actual, total):
                self.root.after(0, self.lbl_estado_sim.config, {"text": f"Procesando ronda {actual} / {total}..."})

            reporte = torneo.ejecutar(puente_ui)
            self.root.after(0, self._finalizar_simulacion_masiva, reporte)
        except Exception as e:
            self.root.after(0, self._finalizar_simulacion_masiva, f"Error durante la simulación: {e}")

    def _finalizar_simulacion_masiva(self, reporte):
        self.lbl_estado_sim.config(text="¡Simulación completada!")
        self.log_mensaje(reporte)
        
        self.simulacion_en_curso = False
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_sim_masiva.config(state=tk.NORMAL)
        
        if "Error" not in reporte:
            messagebox.showinfo("Resultados", reporte)
        else:
            messagebox.showerror("Error", reporte)

if __name__ == "__main__":
    root = tk.Tk()
    app = PicasFijasGUI(root)
    root.mainloop()
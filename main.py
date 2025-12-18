import flet as ft
from scipy.optimize import linprog
import matplotlib
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

# Configuración Anti-Crasheo para Mac
matplotlib.use('Agg')

def main(page: ft.Page):
    page.title = "Solver Master Pro"
    page.theme_mode = "light"
    page.window_width = 480
    page.window_height = 850
    page.scroll = "adaptive"
    page.padding = 20

    # --- COLORES HEXADECIMALES (Seguros) ---
    C_BLUE = "#1976D2"
    C_BLUE_LIGHT = "#E3F2FD"
    C_GREEN = "#388E3C"
    C_GREEN_LIGHT = "#E8F5E9"
    C_RED = "#D32F2F"
    C_RED_LIGHT = "#FFEBEE"
    C_GREY = "#757575"
    C_WHITE = "#FFFFFF"

    # --- ESTADO ---
    obj_inputs = [] 
    restricciones_rows = []
    
    # Memoria Gráfica
    state_grafico = {
        "constraints": [],
        "opt_x": 0, "opt_y": 0,
        "z_coeffs": [], "z_val": 0,
        "active": False
    }

    # --- LÓGICA DEL SLIDER ---
    def actualizar_escala_slider():
        max_val = 100.0
        for inp in obj_inputs:
            if inp.value: max_val = max(max_val, float(inp.value))
        for row in restricciones_rows:
            lim_inp = row[-1] 
            if lim_inp.value: max_val = max(max_val, float(lim_inp.value))
            for cell in row[:-2]:
                if cell.value: max_val = max(max_val, float(cell.value))

        new_max = max_val * 5
        if slider_r1.max != new_max:
            slider_r1.max = new_max
            if slider_r1.value > new_max: slider_r1.value = new_max
            page.update()

    # --- SOLVER ---
    def resolver(e):
        actualizar_escala_slider()
        
        num_vars = len(obj_inputs)
        can_graph = (num_vars == 2)
        
        try:
            es_max = dropdown_obj.value == "Maximizar"
            c, c_graph = [], []
            for inp in obj_inputs:
                val = float(inp.value) if inp.value else 0
                c.append(-val if es_max else val)
                c_graph.append(val)

            A_ub, b_ub = [], []
            raw_constraints = [] 

            for i, row_controls in enumerate(restricciones_rows):
                coeffs = []
                inputs_vars = row_controls[:-2] 
                signo = row_controls[-2].value
                limite_input = row_controls[-1]

                # LÓGICA: Solo R1 (i==0) obedece al Slider
                if i == 0 and switch_slider.value:
                    val_limite = slider_r1.value
                    limite_input.value = str(int(val_limite))
                else:
                    val_limite = float(limite_input.value) if limite_input.value else 0

                for inp in inputs_vars:
                    coeffs.append(float(inp.value) if inp.value else 0)

                raw_constraints.append({'a': coeffs, 'sign': signo, 'b': val_limite, 'id': i+1})

                if signo == "≤":
                    A_ub.append(coeffs)
                    b_ub.append(val_limite)
                elif signo == "≥":
                    coeffs_neg = [-x for x in coeffs]
                    A_ub.append(coeffs_neg)
                    b_ub.append(-val_limite)
                elif signo == "=":
                    A_ub.append(coeffs)
                    b_ub.append(val_limite)
                    A_ub.append([-x for x in coeffs])
                    b_ub.append(-val_limite)

            bounds = [(0, None) for _ in range(len(c))]
            res = linprog(c, A_ub=A_ub if A_ub else None, b_ub=b_ub if b_ub else None, bounds=bounds, method="highs")

            if res.success:
                val_z = -res.fun if es_max else res.fun
                
                # ÉXITO (VERDE)
                contenedor_resultados.bgcolor = C_GREEN_LIGHT
                contenedor_resultados.border = ft.border.all(1, C_GREEN)
                txt_status.value = "SOLUCIÓN ÓPTIMA"
                txt_status.color = C_GREEN
                txt_resultado_z.value = f"Z = {val_z:.2f}"
                
                det = ""
                for i, x in enumerate(res.x):
                    det += f"X{i+1}: {x:.2f}   "
                txt_detalle_vars.value = det

                if can_graph:
                    state_grafico.update({
                        "constraints": raw_constraints,
                        "opt_x": res.x[0], "opt_y": res.x[1],
                        "z_coeffs": c_graph, "z_val": val_z,
                        "active": True
                    })
                    crear_controles_checkbox()
                    dibujar_grafico()
                    contenedor_grafica.visible = True
                else:
                    contenedor_grafica.visible = False
            else:
                # FALLO (ROJO)
                contenedor_resultados.bgcolor = C_RED_LIGHT
                contenedor_resultados.border = ft.border.all(1, C_RED)
                txt_status.value = "NO HAY SOLUCIÓN"
                txt_status.color = C_RED
                txt_resultado_z.value = "---"
                txt_detalle_vars.value = "Verifica restricciones"
                contenedor_grafica.visible = False

        except Exception as ex:
            print(f"Error Solver: {ex}")
            pass
        
        page.update()

    # --- UI CHECKBOXES ---
    checkboxes_ui = ft.Column()
    check_values = {}

    def crear_controles_checkbox():
        checkboxes_ui.controls.clear()
        check_values.clear()
        
        for const in state_grafico["constraints"]:
            id_r = f"R{const['id']}"
            cb = ft.Checkbox(label=f"{id_r}", value=True, on_change=actualizar_grafico_evento)
            check_values[id_r] = cb
            checkboxes_ui.controls.append(cb)
        
        cb_z = ft.Checkbox(label="Objetivo Z", value=True, on_change=actualizar_grafico_evento)
        check_values["Z"] = cb_z
        checkboxes_ui.controls.append(cb_z)

        cb_region = ft.Checkbox(label="Sombreado", value=True, on_change=actualizar_grafico_evento)
        check_values["Region"] = cb_region
        checkboxes_ui.controls.append(cb_region)

    def actualizar_grafico_evento(e):
        dibujar_grafico()
        page.update()

    # --- DIBUJAR GRÁFICO (CORREGIDO PARA MAC) ---
    def dibujar_grafico():
        if not state_grafico["active"]: return

        try:
            plt.clf()
            # Ajustamos márgenes manualmente en lugar de usar bbox_inches='tight'
            fig, ax = plt.subplots(figsize=(6, 5))
            plt.subplots_adjust(left=0.15, right=0.95, top=0.9, bottom=0.15)
            
            opt_x = state_grafico["opt_x"]
            opt_y = state_grafico["opt_y"]
            max_limit = max(opt_x, opt_y, 10) * 1.6
            x_vals = np.linspace(0, max_limit, 400)
            colors = ['#1976D2', '#FF8F00', '#388E3C', '#7B1FA2', '#D32F2F']

            # Restricciones
            for i, const in enumerate(state_grafico["constraints"]):
                id_r = f"R{const['id']}"
                if not check_values[id_r].value: continue

                a1, a2 = const['a'][0], const['a'][1]
                b, sign = const['b'], const['sign']
                color = colors[i % len(colors)]

                if abs(a2) < 1e-9:
                    x_int = b / a1 if abs(a1) > 1e-9 else 0
                    ax.axvline(x=x_int, color=color, linestyle='-', label=id_r)
                    if check_values["Region"].value:
                        if sign == "≤": ax.axvspan(0, x_int, color=color, alpha=0.1)
                        elif sign == "≥": ax.axvspan(x_int, max_limit, color=color, alpha=0.1)
                else:
                    y_vals = (b - a1 * x_vals) / a2
                    ax.plot(x_vals, y_vals, color=color, linestyle='-', label=id_r)
                    if check_values["Region"].value:
                        if sign == "≤": ax.fill_between(x_vals, 0, y_vals, where=(y_vals>=0), color=color, alpha=0.1)
                        elif sign == "≥": ax.fill_between(x_vals, y_vals, max_limit, where=(y_vals>=0), color=color, alpha=0.1)

            # Función Z
            if check_values["Z"].value:
                c1, c2 = state_grafico["z_coeffs"]
                z_val = state_grafico["z_val"]
                if abs(c2) > 1e-9:
                    y_z = (z_val - c1 * x_vals) / c2
                    ax.plot(x_vals, y_z, color='red', linestyle='--', linewidth=2, label='Z')
                
                ax.plot(opt_x, opt_y, 'ro', markersize=8, markeredgecolor='black', zorder=10)
                ax.annotate(f'({opt_x:.1f}, {opt_y:.1f})', (opt_x, opt_y), textcoords="offset points", xytext=(10,10), ha='center', color='black', weight='bold')

            ax.set_xlim(0, max_limit)
            ax.set_ylim(0, max_limit)
            ax.set_xlabel('X1')
            ax.set_ylabel('X2')
            ax.grid(True, linestyle=':', alpha=0.5)
            ax.legend(loc='upper right', fontsize='small')
            ax.set_title("Región Factible")

            # AQUÍ ESTABA EL ERROR: Eliminamos bbox_inches='tight'
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100) 
            buf.seek(0)
            img_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close(fig)
            
            img_grafico.src_base64 = img_base64

        except Exception as ex:
            print(f"Error Grafico: {ex}")

    # --- UI COMPONENTES ---
    dropdown_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=140, text_size=13, on_change=resolver, bgcolor=C_WHITE, content_padding=8)
    row_obj_vars = ft.Row(wrap=True, spacing=10) 
    col_restricciones = ft.Column(spacing=8)

    def agregar_variable(e):
        idx = len(obj_inputs) + 1
        nuevo_input = ft.TextField(label=f"C{idx}", width=80, text_size=12, keyboard_type="number", on_change=resolver, bgcolor=C_WHITE, content_padding=10)
        obj_inputs.append(nuevo_input)
        row_obj_vars.controls.append(nuevo_input)
        for row in restricciones_rows:
            nuevo_res = ft.TextField(width=80, text_size=12, keyboard_type="number", on_change=resolver, bgcolor=C_WHITE, content_padding=10)
            row.insert(len(row)-2, nuevo_res)
        repintar_restricciones()
        page.update()

    def agregar_restriccion(e):
        row = []
        for _ in range(len(obj_inputs)):
            row.append(ft.TextField(width=80, text_size=12, keyboard_type="number", on_change=resolver, bgcolor=C_WHITE, content_padding=10))
        dd_signo = ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=65, text_size=14, content_padding=5, on_change=resolver, bgcolor="#F5F5F5")
        row.append(dd_signo)
        row.append(ft.TextField(width=90, text_size=12, keyboard_type="number", on_change=resolver, bgcolor=C_WHITE, content_padding=10, hint_text="Límite"))
        restricciones_rows.append(row)
        repintar_restricciones()
        page.update()

    def repintar_restricciones():
        col_restricciones.controls.clear()
        for i, row in enumerate(restricciones_rows):
            lbl = ft.Text(f"R{i+1}", weight="bold", size=12, width=30, color=C_GREY)
            bg = C_BLUE_LIGHT if (i == 0 and switch_slider.value) else "transparent"
            fila_cont = ft.Container(content=ft.Row([lbl] + row, wrap=True, spacing=5, alignment="start"), bgcolor=bg, padding=5, border_radius=8)
            col_restricciones.controls.append(fila_cont)

    # Panel Innovación
    lbl_slider_val = ft.Text("100", size=16, weight="bold", color=C_BLUE)
    slider_r1 = ft.Slider(min=0, max=500, divisions=100, value=100, label="{value}", active_color=C_BLUE, on_change=lambda e: [actualizar_lbl_slider(e), resolver(e)])
    def actualizar_lbl_slider(e): lbl_slider_val.value = f"{int(e.control.value)}"
    switch_slider = ft.Switch(label="Controlar R1 con Slider", value=True, active_color=C_BLUE, on_change=resolver)
    
    panel_innovacion = ft.Container(
        content=ft.Column([
            ft.Text("✨ Análisis de Sensibilidad (R1)", weight="bold", color=C_BLUE),
            ft.Row([switch_slider, ft.Container(expand=True), lbl_slider_val], alignment="spaceBetween"),
            slider_r1
        ]), bgcolor=C_BLUE_LIGHT, padding=15, border_radius=12
    )

    # Resultados
    txt_status = ft.Text("Esperando...", weight="bold", size=16)
    txt_resultado_z = ft.Text("Z: ---", size=20, weight="bold")
    txt_detalle_vars = ft.Text("", size=13, color=C_GREY)
    contenedor_resultados = ft.Container(content=ft.Column([txt_status, txt_resultado_z, txt_detalle_vars], horizontal_alignment="center"), padding=15, border_radius=12, bgcolor="#F5F5F5", width=400)

    # Gráfico
    img_grafico = ft.Image(src_base64="", width=450, height=400, fit=ft.ImageFit.CONTAIN)
    contenedor_grafica = ft.Column([
        ft.Divider(), ft.Text("Visualización Interactiva", weight="bold", size=16, color=C_BLUE),
        ft.Row([checkboxes_ui], wrap=True, alignment="center"),
        ft.Container(img_grafico, padding=5, border=ft.border.all(1, "#E0E0E0"), border_radius=10)
    ], visible=False, horizontal_alignment="center")

    btn_add_var = ft.ElevatedButton("Var (+)", on_click=agregar_variable)
    btn_add_res = ft.ElevatedButton("Restricción (+)", on_click=agregar_restriccion)

    page.add(ft.Column([
        ft.Text("Solver Master Pro", size=26, weight="bold", color=C_BLUE),
        ft.Row([dropdown_obj, btn_add_var], alignment="spaceBetween"),
        ft.Text("Función Objetivo:", size=12, weight="bold"),
        ft.Container(row_obj_vars, padding=10, bgcolor="#FAFAFA", border_radius=8),
        ft.Row([ft.Text("Restricciones:", size=12, weight="bold"), btn_add_res], alignment="spaceBetween"),
        col_restricciones,
        ft.Divider(), panel_innovacion,
        ft.Divider(), ft.Row([contenedor_resultados], alignment="center"),
        contenedor_grafica
    ]))

    agregar_variable(None)
    agregar_variable(None)
    agregar_restriccion(None)
    agregar_restriccion(None)

ft.app(target=main)
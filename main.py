import flet as ft
import math

def main(page: ft.Page):
    page.title = "Solver Pro Mobile"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 20
    # Ajuste para celular
    page.window_width = 380
    page.window_height = 800

    # --- COLORES ---
    C_BLUE = "#1976D2"
    C_BLUE_LIGHT = "#E3F2FD"
    C_GREEN = "#388E3C"
    C_GREEN_BG = "#E8F5E9"
    C_RED = "#D32F2F"
    C_RED_BG = "#FFEBEE"
    C_WHITE = "#FFFFFF"

    # --- VARIABLES GLOBALES ---
    obj_inputs = []
    restricciones_rows = []
    
    # --- MOTOR MATEMÁTICO (PYTHON PURO - SIN SCIPY) ---
    def resolver_simplex_puro(c, A, b, es_max):
        # Implementación simple del método Simplex para problemas estandar
        # Convertimos Max Z a Min -Z para estandarizar
        try:
            num_vars = len(c)
            num_rest = len(b)
            
            # Crear tabla inicial
            # Filas: Restricciones + Función Objetivo
            # Cols: Vars Originales + Vars Holgura + Solución
            tabla = []
            
            # Llenar restricciones con variables de holgura
            for i in range(num_rest):
                fila = A[i] + [0]*num_rest + [b[i]]
                fila[num_vars + i] = 1.0 # Holgura
                tabla.append(fila)
            
            # Llenar fila Z
            # Si es MAX: Z - c1x1 - c2x2... = 0  -> coefs negativos
            # Si es MIN: Z + c1x1 + c2x2... = 0
            if es_max:
                fila_z = [-val for val in c] + [0]*num_rest + [0]
            else:
                fila_z = [val for val in c] + [0]*num_rest + [0]
            
            tabla.append(fila_z)
            
            # Iteraciones Simplex
            while True:
                last_row = tabla[-1]
                # Buscar el más negativo en la fila Z (para entrar)
                min_val = min(last_row[:-1])
                if min_val >= -1e-9: # Optimidad alcanzada
                    break
                
                pivot_col = last_row.index(min_val)
                
                # Buscar variable de salida (Ratio test)
                min_ratio = float('inf')
                pivot_row = -1
                
                for i in range(num_rest):
                    col_val = tabla[i][pivot_col]
                    rhs_val = tabla[i][-1]
                    if col_val > 1e-9:
                        ratio = rhs_val / col_val
                        if ratio < min_ratio:
                            min_ratio = ratio
                            pivot_row = i
                
                if pivot_row == -1: return None # No acotado
                
                # Pivoteo Gauss-Jordan
                pivot_val = tabla[pivot_row][pivot_col]
                tabla[pivot_row] = [x / pivot_val for x in tabla[pivot_row]]
                
                for i in range(len(tabla)):
                    if i != pivot_row:
                        factor = tabla[i][pivot_col]
                        tabla[i] = [tabla[i][j] - factor * tabla[pivot_row][j] for j in range(len(tabla[0]))]

            # Extraer solución
            solucion = [0.0] * num_vars
            # Identificar variables básicas
            for j in range(num_vars):
                col = [tabla[i][j] for i in range(num_rest)]
                if col.count(1.0) == 1 and col.count(0.0) == num_rest - 1:
                    row_idx = col.index(1.0)
                    solucion[j] = tabla[row_idx][-1]
            
            valor_z = tabla[-1][-1]
            if es_max: valor_z *= 1 # El Z ya queda positivo en la tabla final usualmente
            else: valor_z *= -1 
            
            return solucion, valor_z

        except Exception:
            return None

    # --- LÓGICA DE LA APP ---
    def resolver(e):
        try:
            # 1. Leer Datos
            es_max = dropdown_obj.value == "Maximizar"
            c = []
            max_input_val = 0
            
            for inp in obj_inputs:
                val = float(inp.value) if inp.value else 0
                c.append(val)
                max_input_val = max(max_input_val, val)

            A = []
            b = []
            
            # Datos para graficar
            raw_constraints = []

            for i, row in enumerate(restricciones_rows):
                coeffs = []
                inputs_vars = row[:-2]
                signo = row[-2].value
                limite_inp = row[-1]

                # Slider R1
                if i == 0 and switch_slider.value:
                    val_limite = slider_r1.value
                    limite_inp.value = str(int(val_limite))
                else:
                    val_limite = float(limite_inp.value) if limite_inp.value else 0
                
                # Ajustar escala slider
                max_input_val = max(max_input_val, val_limite)

                for inp in inputs_vars:
                    val_coef = float(inp.value) if inp.value else 0
                    coeffs.append(val_coef)
                    max_input_val = max(max_input_val, val_coef)
                
                # Guardar para gráfico (solo soportamos <= para gráfico simple)
                raw_constraints.append({'a': coeffs, 'b': val_limite, 'id': i+1})
                
                A.append(coeffs)
                b.append(val_limite)

            # Ajustar Slider dinámicamente
            new_max = max(100, max_input_val * 2)
            if slider_r1.max != new_max:
                slider_r1.max = new_max
                page.update()

            # 2. Resolver (Motor Propio)
            resultado = resolver_simplex_puro(c, A, b, es_max)

            if resultado:
                sol_x, val_z = resultado
                
                # Mostrar Éxito
                cont_res.bgcolor = C_GREEN_BG
                cont_res.border = ft.border.all(1, C_GREEN)
                txt_status.value = "SOLUCIÓN ÓPTIMA"
                txt_status.color = C_GREEN
                txt_z.value = f"Z = {val_z:.2f}"
                
                det = ""
                for i, x in enumerate(sol_x):
                    det += f"X{i+1}: {x:.2f}  "
                txt_det.value = det

                # Graficar si hay 2 variables
                if len(c) == 2:
                    dibujar_grafico_nativo(raw_constraints, sol_x[0], sol_x[1], c, val_z)
                    cont_grafico.visible = True
                else:
                    cont_grafico.visible = False
            else:
                # Error
                cont_res.bgcolor = C_RED_BG
                cont_res.border = ft.border.all(1, C_RED)
                txt_status.value = "NO FACTIBLE / ERROR"
                txt_status.color = C_RED
                txt_z.value = "---"
                txt_det.value = "Verifica tus datos"
                cont_grafico.visible = False

        except Exception as ex:
            print(ex)
        
        page.update()

    # --- GRÁFICOS NATIVOS FLET (SIN MATPLOTLIB) ---
    chart_data_groups = []
    chart = ft.LineChart(
        data_series=chart_data_groups,
        border=ft.border.all(1, ft.colors.GREY_400),
        left_axis=ft.ChartAxis(labels_size=40),
        bottom_axis=ft.ChartAxis(labels_size=40),
        tooltip_bgcolor=ft.colors.with_opacity(0.8, ft.colors.BLUE_GREY),
        min_y=0, min_x=0,
        expand=True,
    )

    def dibujar_grafico_nativo(constraints, opt_x, opt_y, c, z_val):
        chart.data_series = []
        
        # Calcular rango maximo para ejes
        max_val = max(opt_x, opt_y, 10) * 1.5
        chart.max_x = max_val
        chart.max_y = max_val

        colors = [ft.colors.BLUE, ft.colors.ORANGE, ft.colors.PURPLE]

        # 1. Dibujar Restricciones (Líneas)
        for i, const in enumerate(constraints):
            a1, a2 = const['a'][0], const['a'][1]
            b = const['b']
            color = colors[i % len(colors)]
            
            points = []
            if abs(a2) < 1e-9: # Vertical x = b/a1
                if abs(a1) > 0:
                    x_int = b/a1
                    points = [ft.LineChartDataPoint(x_int, 0), ft.LineChartDataPoint(x_int, max_val)]
            elif abs(a1) < 1e-9: # Horizontal y = b/a2
                 if abs(a2) > 0:
                    y_int = b/a2
                    points = [ft.LineChartDataPoint(0, y_int), ft.LineChartDataPoint(max_val, y_int)]
            else:
                # Puntos de corte
                p1_y = b / a2 # si x=0
                p2_x = b / a1 # si y=0
                points = [ft.LineChartDataPoint(0, p1_y), ft.LineChartDataPoint(p2_x, 0)]

            # Agregar línea al chart
            chart.data_series.append(
                ft.LineChartData(
                    data_points=points,
                    stroke_width=2,
                    color=color,
                    title=f"R{const['id']}",
                    curved=False
                )
            )

        # 2. Dibujar Punto Óptimo
        chart.data_series.append(
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(opt_x, opt_y)],
                stroke_width=0,
                color=ft.colors.RED,
                point=True,
                title="Óptimo",
            )
        )
        page.update()


    # --- INTERFAZ UI ---
    dropdown_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=130, text_size=12, on_change=resolver, bgcolor=C_WHITE, content_padding=5)
    row_obj_vars = ft.Row(wrap=True, spacing=5)
    col_restricciones = ft.Column(spacing=5)

    def add_var(e):
        idx = len(obj_inputs) + 1
        inp = ft.TextField(label=f"C{idx}", width=70, text_size=12, keyboard_type="number", bgcolor=C_WHITE, content_padding=5, on_change=resolver)
        obj_inputs.append(inp)
        row_obj_vars.controls.append(inp)
        for row in restricciones_rows:
            row.insert(len(row)-2, ft.TextField(width=70, text_size=12, keyboard_type="number", bgcolor=C_WHITE, content_padding=5, on_change=resolver))
        page.update()

    def add_res(e):
        row = []
        for _ in obj_inputs:
            row.append(ft.TextField(width=70, text_size=12, keyboard_type="number", bgcolor=C_WHITE, content_padding=5, on_change=resolver))
        
        row.append(ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=60, text_size=12, content_padding=5, bgcolor="#F0F0F0", on_change=resolver))
        row.append(ft.TextField(hint_text="Lim", width=70, text_size=12, keyboard_type="number", bgcolor=C_WHITE, content_padding=5, on_change=resolver))
        
        restricciones_rows.append(row)
        
        # Pintar fila
        i = len(restricciones_rows)
        lbl = ft.Text(f"R{i}", size=12, weight="bold", color="grey")
        bg = C_BLUE_LIGHT if (i==1 and switch_slider.value) else "transparent"
        
        col_restricciones.controls.append(
            ft.Container(content=ft.Row([lbl]+row, wrap=True, spacing=5), bgcolor=bg, padding=5, border_radius=5)
        )
        page.update()

    # Panel Slider
    slider_r1 = ft.Slider(min=0, max=500, divisions=50, value=100, label="{value}", active_color=C_BLUE, on_change=resolver)
    switch_slider = ft.Switch(value=True, active_color=C_BLUE, on_change=resolver)
    panel_innov = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.TOUCH_APP, size=16, color=C_BLUE), ft.Text("Slider R1", color=C_BLUE, weight="bold")], spacing=5),
            ft.Row([switch_slider, slider_r1], alignment="spaceBetween")
        ]), bgcolor=C_BLUE_LIGHT, padding=10, border_radius=10
    )

    # Resultados
    txt_status = ft.Text("Esperando...", weight="bold")
    txt_z = ft.Text("Z: --", size=20, weight="bold")
    txt_det = ft.Text("Resultados", size=12, color="grey")
    cont_res = ft.Container(content=ft.Column([txt_status, txt_z, txt_det], horizontal_alignment="center"), padding=10, border_radius=10, bgcolor="#F0F0F0", width=300)

    # Gráfico Container
    cont_grafico = ft.Container(
        content=ft.Column([ft.Text("Gráfico Simple", weight="bold"), ft.Container(chart, height=300)], horizontal_alignment="center"),
        visible=False, padding=10, border=ft.border.all(1, "grey"), border_radius=10
    )

    # Botones
    btn_var = ft.ElevatedButton("+ Var", on_click=add_var, bgcolor=C_BLUE, color=C_WHITE)
    btn_res = ft.ElevatedButton("+ Restricción", on_click=add_res, bgcolor="#E0E0E0", color="black")

    # Layout
    page.add(
        ft.Text("Solver Pro (Mobile)", size=24, weight="bold", color=C_BLUE),
        ft.Row([dropdown_obj, btn_var], alignment="spaceBetween"),
        ft.Container(row_obj_vars, padding=5),
        ft.Row([ft.Text("Restricciones:", weight="bold"), btn_res], alignment="spaceBetween"),
        col_restricciones,
        ft.Divider(),
        panel_innov,
        ft.Divider(),
        ft.Row([cont_res], alignment="center"),
        cont_grafico
    )

    # Init
    add_var(None); add_var(None)
    add_res(None); add_res(None)

ft.app(target=main)

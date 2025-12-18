import flet as ft
import traceback

def main(page: ft.Page):
    # --- CONFIGURACIÓN INICIAL ---
    page.title = "Solver Master Pro"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 20
    page.window_width = 380
    page.window_height = 800

    # --- PALETA DE COLORES (HEXADECIMALES SEGUROS) ---
    # Usamos esto para evitar el error 'flet has no attribute colors'
    C_AZUL = "#1976D2"
    C_AZUL_CLARO = "#E3F2FD"
    C_VERDE = "#388E3C"
    C_VERDE_FONDO = "#E8F5E9"
    C_ROJO = "#D32F2F"
    C_ROJO_FONDO = "#FFEBEE"
    C_GRIS = "#757575"
    C_BLANCO = "#FFFFFF"

    # --- VARIABLES ---
    obj_inputs = []
    restricciones_rows = []

    # --- MOTOR MATEMÁTICO (SIMPLEX NATIVO) ---
    def resolver_simplex(c, A, b, es_max):
        try:
            num_vars = len(c)
            num_rest = len(b)
            tabla = []
            
            # Crear tabla inicial con holguras
            for i in range(num_rest):
                # Fila: [Coefs Originales] + [Holguras (0...1...0)] + [Solución]
                row = A[i] + [0.0] * num_rest + [b[i]]
                row[num_vars + i] = 1.0
                tabla.append(row)
            
            # Fila Z
            z_row = [-x if es_max else x for x in c] + [0.0] * num_rest + [0.0]
            tabla.append(z_row)
            
            # Iteraciones (Limitadas para seguridad)
            for _ in range(50):
                z = tabla[-1]
                min_val = min(z[:-1])
                if min_val >= -1e-9: break # Óptimo
                
                pivot_col = z.index(min_val)
                min_ratio = float('inf')
                pivot_row = -1
                
                for i in range(num_rest):
                    val = tabla[i][pivot_col]
                    if val > 1e-9:
                        ratio = tabla[i][-1] / val
                        if ratio < min_ratio:
                            min_ratio = ratio
                            pivot_row = i
                
                if pivot_row == -1: return None # No acotado
                
                # Pivoteo
                pivot_val = tabla[pivot_row][pivot_col]
                tabla[pivot_row] = [x / pivot_val for x in tabla[pivot_row]]
                for i in range(len(tabla)):
                    if i != pivot_row:
                        factor = tabla[i][pivot_col]
                        tabla[i] = [tabla[i][j] - factor * tabla[pivot_row][j] for j in range(len(tabla[0]))]
            
            # Extraer solución
            res_x = [0.0] * num_vars
            for j in range(num_vars):
                col = [tabla[i][j] for i in range(num_rest)]
                if col.count(1.0) == 1:
                    # Verificar que el resto sean ceros
                    is_basic = True
                    for val in col:
                        if abs(val) > 1e-9 and abs(val - 1.0) > 1e-9: is_basic = False
                    
                    if is_basic:
                        idx = col.index(1.0)
                        if idx < num_rest: res_x[j] = tabla[idx][-1]
            
            z_final = tabla[-1][-1] * (1 if es_max else -1)
            return res_x, z_final
        except:
            return None

    # --- LÓGICA DE ACTUALIZACIÓN ---
    def calcular(e):
        try:
            txt_error.visible = False
            
            # 1. Obtener Coeficientes Objetivo
            c = []
            max_val = 0
            for inp in obj_inputs:
                val_str = inp.value if inp.value else "0"
                val = float(val_str)
                c.append(val)
                max_val = max(max_val, val)
            
            # 2. Obtener Restricciones
            A = []
            b = []
            datos_grafico = []
            
            for i, row in enumerate(restricciones_rows):
                # Coeficientes
                row_coeffs = []
                inputs_coef = row[:-2]
                for inp in inputs_coef:
                    val_str = inp.value if inp.value else "0"
                    v = float(val_str)
                    row_coeffs.append(v)
                    max_val = max(max_val, v)
                
                # Limite (Slider o Texto)
                inp_lim = row[-1]
                if i == 0 and switch_slider.value:
                    val_b = slider.value
                    inp_lim.value = str(int(val_b)) # Reflejar en el input
                else:
                    val_b_str = inp_lim.value if inp_lim.value else "0"
                    val_b = float(val_b_str)
                
                max_val = max(max_val, val_b)
                
                A.append(row_coeffs)
                b.append(val_b)
                
                # Guardar para gráfico
                if len(c) == 2:
                    datos_grafico.append({'a': row_coeffs, 'b': val_b, 'id': i+1})

            # Ajustar Slider Max dinámicamente
            nuevo_max = max(100, max_val * 2)
            if slider.max != nuevo_max:
                slider.max = nuevo_max

            # 3. Resolver
            es_max = dd_obj.value == "Maximizar"
            resultado = resolver_simplex(c, A, b, es_max)
            
            if resultado:
                sol_x, sol_z = resultado
                
                # ÉXITO - Actualizar UI
                cont_res.bgcolor = C_VERDE_FONDO
                cont_res.border = ft.border.all(1, C_VERDE)
                txt_z.value = f"Z = {sol_z:.2f}"
                txt_z.color = C_VERDE
                
                # Formatear variables bonito: X1=2.5, X2=0.0
                txt_vars.value = "  |  ".join([f"X{i+1}={val:.2f}" for i, val in enumerate(sol_x)])
                
                # Graficar
                if len(c) == 2:
                    dibujar_grafico(datos_grafico, sol_x[0], sol_x[1])
                    cont_grafico.visible = True
                else:
                    cont_grafico.visible = False
            else:
                # ERROR MATEMÁTICO
                cont_res.bgcolor = C_ROJO_FONDO
                cont_res.border = ft.border.all(1, C_ROJO)
                txt_z.value = "No hay solución"
                txt_z.color = C_ROJO
                txt_vars.value = "Verifica las restricciones"
                cont_grafico.visible = False

        except Exception as ex:
            txt_error.value = f"Error: {str(ex)}"
            txt_error.visible = True
        
        page.update()

    # --- GRÁFICO ---
    chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, "#E0E0E0"), # Hex directo
        min_y=0, min_x=0,
        expand=True,
        tooltip_bgcolor="#263238" # Hex directo
    )

    def dibujar_grafico(restricciones, x1, x2):
        chart.data_series = []
        limit_axis = max(x1, x2, 10) * 1.5
        chart.max_x = limit_axis
        chart.max_y = limit_axis
        
        # Colores seguros en Hex
        colores_hex = [C_AZUL, "#FF9800", "#9C27B0", "#009688"]
        
        for idx, r in enumerate(restricciones):
            a1, a2 = r['a']
            b = r['b']
            color = colores_hex[idx % len(colores_hex)]
            puntos = []
            
            # Calcular cortes con ejes
            if abs(a2) < 0.001 and abs(a1) > 0.001: # Vertical
                val = b / a1
                puntos = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, limit_axis)]
            elif abs(a1) < 0.001 and abs(a2) > 0.001: # Horizontal
                val = b / a2
                puntos = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(limit_axis, val)]
            elif abs(a1) > 0.001 and abs(a2) > 0.001: # Diagonal
                y_corte = b / a2
                x_corte = b / a1
                puntos = [ft.LineChartDataPoint(0, y_corte), ft.LineChartDataPoint(x_corte, 0)]
            
            if puntos:
                chart.data_series.append(
                    ft.LineChartData(
                        data_points=puntos,
                        stroke_width=2,
                        color=color, # Usando Hex
                        title=f"R{r['id']}",
                    )
                )
        
        # Punto óptimo
        chart.data_series.append(
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x1, x2)],
                stroke_width=0,
                color=C_ROJO, # Usando Hex
                point=True,
                title="Óptimo"
            )
        )

    # --- INTERFAZ UI ---
    dd_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=140, on_change=calcular, bgcolor=C_BLANCO)
    
    row_vars = ft.Row(wrap=True, spacing=5)
    col_rest = ft.Column(spacing=5)
    
    def add_var(e):
        idx = len(obj_inputs) + 1
        inp = ft.TextField(label=f"C{idx}", width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
        obj_inputs.append(inp)
        row_vars.controls.append(inp)
        # Actualizar filas
        for r in restricciones_rows:
            r.insert(len(r)-2, ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        page.update()

    def add_rest(e):
        row = []
        for _ in obj_inputs:
            row.append(ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        row.append(ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥")], value="≤", width=60, content_padding=5, bgcolor="#F5F5F5", on_change=calcular))
        row.append(ft.TextField(width=70, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        restricciones_rows.append(row)
        
        # UI
        idx = len(restricciones_rows)
        bg = C_AZUL_CLARO if (idx == 1 and switch_slider.value) else "transparent"
        
        col_rest.controls.append(
            ft.Container(
                content=ft.Row([ft.Text(f"R{idx}", weight="bold")] + row, wrap=True, spacing=5, alignment="center"),
                bgcolor=bg, padding=5, border_radius=5
            )
        )
        page.update()

    # Panel Slider
    slider = ft.Slider(min=0, max=500, value=100, divisions=50, label="{value}", active_color=C_AZUL, on_change=calcular)
    switch_slider = ft.Switch(value=True, active_color=C_AZUL, on_change=calcular)
    
    panel_innov = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(name="touch_app", color=C_AZUL), ft.Text("Análisis R1", color=C_AZUL, weight="bold")]),
            ft.Row([switch_slider, ft.Container(content=slider, expand=True)], alignment="spaceBetween")
        ]),
        bgcolor=C_AZUL_CLARO, padding=10, border_radius=10
    )

    # Resultados
    txt_z = ft.Text("Z: ---", size=24, weight="bold")
    txt_vars = ft.Text("Introduce datos...", size=14)
    cont_res = ft.Container(
        content=ft.Column([txt_z, txt_vars], horizontal_alignment="center"),
        padding=15, border_radius=10, bgcolor="#F5F5F5", width=350,
        border=ft.border.all(1, "transparent")
    )

    # Gráfico
    cont_grafico = ft.Container(
        content=ft.Column([ft.Text("Gráfico de Región Factible", weight="bold"), ft.Container(content=chart, height=300)], horizontal_alignment="center"),
        padding=10, border=ft.border.all(1, "#E0E0E0"), border_radius=10, visible=False
    )
    
    txt_error = ft.Text("", color=C_ROJO, visible=False)

    # Layout Principal
    page.add(
        ft.Column([
            ft.Text("Solver Master Pro", size=26, weight="bold", color=C_AZUL),
            ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var, bgcolor=C_AZUL, color=C_BLANCO)], alignment="spaceBetween"),
            ft.Container(row_vars, padding=5),
            ft.Row([ft.Text("Restricciones", weight="bold"), ft.ElevatedButton("+Rest", on_click=add_rest)], alignment="spaceBetween"),
            col_rest,
            ft.Divider(),
            panel_innov,
            ft.Divider(),
            ft.Container(content=cont_res, alignment=ft.alignment.center),
            txt_error,
            cont_grafico
        ], scroll="adaptive")
    )
    
    # Init Default
    add_var(None); add_var(None)
    add_rest(None); add_rest(None)

ft.app(target=main)

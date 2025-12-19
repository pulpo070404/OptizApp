import flet as ft
import traceback

def main(page: ft.Page):
    # --- CONFIGURACIÓN DE PANTALLA ---
    page.title = "Solver Master Pro"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 15
    page.window_width = 380
    page.window_height = 800

    # --- COLORES HEXADECIMALES (Seguros) ---
    C_AZUL = "#1976D2"
    C_AZUL_BG = "#BBDEFB"
    C_NARANJA = "#FF9800"
    C_NARANJA_BG = "#FFE0B2"
    C_VERDE = "#388E3C"
    C_VERDE_BG = "#C8E6C9"
    C_ROJO = "#D32F2F"
    C_BLANCO = "#FFFFFF"
    C_GRIS = "#F5F5F5"
    C_NEGRO = "#000000"

    # --- VARIABLES GLOBALES ---
    obj_inputs = []
    restricciones_rows = []

    # --- WIDGET LEYENDA ---
    leyenda_container = ft.Row(wrap=True, alignment="center", spacing=10)

    # --- MOTOR MATEMÁTICO (SIMPLEX BIG-M CORREGIDO) ---
    def resolver_simplex(c, A, b, signos, es_max):
        try:
            M = 1000000.0  # Penalización Muy Grande
            num_vars = len(c)
            num_rest = len(b)
            
            # 1. Identificar Artificiales
            num_artificial = 0
            for s in signos:
                if s in [">=", "≥", "="]:
                    num_artificial += 1
            
            tabla = []
            art_indices = [] 
            art_counter = 0
            
            # 2. Construir Matriz Aumentada
            for i in range(num_rest):
                row = list(A[i])
                
                # Holguras (Slacks)
                slacks = [0.0] * num_rest
                s = signos[i]
                if s in ["<=", "≤"]:
                    slacks[i] = 1.0
                elif s in [">=", "≥"]:
                    slacks[i] = -1.0
                row.extend(slacks)
                
                # Artificiales
                arts = [0.0] * num_artificial
                if s in [">=", "≥", "="]:
                    arts[art_counter] = 1.0
                    art_indices.append((i, num_vars + num_rest + art_counter))
                    art_counter += 1
                row.extend(arts)
                
                # RHS (Solución)
                row.append(b[i])
                tabla.append(row)
            
            # 3. Fila Z (Función Objetivo)
            if es_max:
                z_row = [-val for val in c]
            else:
                z_row = [val for val in c]
                
            z_row.extend([0.0] * num_rest) # Holguras valen 0
            
            # CORRECCIÓN BIG-M: Penalización positiva en Z inicial
            z_row.extend([M] * num_artificial)
            z_row.append(0.0) # RHS de Z
            
            # 4. PRE-PROCESAMIENTO
            for r_idx, c_idx in art_indices:
                row_val = tabla[r_idx]
                for j in range(len(z_row)):
                    z_row[j] -= M * row_val[j]
            
            tabla.append(z_row)
            
            # 5. ITERACIONES
            for _ in range(100):
                z = tabla[-1]
                min_val = min(z[:-1]) # Criterio del más negativo
                if min_val >= -1e-9:
                    break # Óptimo
                
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
                
                # Gauss-Jordan
                pivot_val = tabla[pivot_row][pivot_col]
                tabla[pivot_row] = [x / pivot_val for x in tabla[pivot_row]]
                for i in range(len(tabla)):
                    if i != pivot_row:
                        factor = tabla[i][pivot_col]
                        tabla[i] = [tabla[i][j] - factor * tabla[pivot_row][j] for j in range(len(tabla[0]))]
            
            # 6. Extraer Resultados
            res_x = [0.0] * num_vars
            for j in range(num_vars):
                col = [tabla[i][j] for i in range(num_rest)]
                if col.count(1.0) == 1:
                    is_basic = True
                    for val in col:
                        if abs(val) > 1e-9 and abs(val - 1.0) > 1e-9: is_basic = False
                    if is_basic:
                        idx = col.index(1.0)
                        if idx < num_rest: res_x[j] = tabla[idx][-1]
            
            z_final = tabla[-1][-1]
            if not es_max:
                z_final *= -1
                
            return res_x, z_final
        except:
            return None

    # --- LÓGICA DE UI ---
    def calcular(e):
        try:
            txt_error.visible = False
            
            # Leer Objetivo
            c = []
            for inp in obj_inputs:
                v = float(inp.value) if inp.value else 0.0
                c.append(v)
            
            # Leer Restricciones
            A = []
            b = []
            signos = []
            datos_grafico = []
            
            max_val_intercept = 0 
            
            for i, row in enumerate(restricciones_rows):
                coefs = []
                # MODIFICADO: Leemos hasta el antepenúltimo porque ahora insertamos dinámicamente
                # Estructura: [Inp1, Inp2, ..., Dropdown, Lim]
                # Dropdown es -2, Lim es -1. Los inputs son todo lo anterior.
                inputs_solo = row[:-2] 
                
                for inp in inputs_solo:
                    v = float(inp.value) if inp.value else 0.0
                    coefs.append(v)
                
                dd_signo = row[-2]
                signos.append(dd_signo.value)
                
                inp_lim = row[-1]
                if i == 0 and switch_slider.value:
                    val_b = slider.value
                    inp_lim.value = str(int(val_b))
                    page.update()
                else:
                    val_b = float(inp_lim.value) if inp_lim.value else 0.0
                
                # Escala gráfico
                for coef in coefs:
                    if abs(coef) > 0.01:
                        max_val_intercept = max(max_val_intercept, val_b/coef)
                
                A.append(coefs)
                b.append(val_b)
                
                if len(c) == 2:
                    datos_grafico.append({'a': coefs, 'b': val_b, 'id': i+1})

            if slider.max < max_val_intercept:
                 slider.max = max(100, max_val_intercept * 1.5)

            # Resolver
            es_max = dd_obj.value == "Maximizar"
            res = resolver_simplex(c, A, b, signos, es_max)
            
            if res:
                sol_x, sol_z = res
                
                cont_res.bgcolor = C_VERDE_BG
                cont_res.border = ft.border.all(1, C_VERDE)
                txt_z.value = f"Z = {sol_z:.2f}"
                txt_z.color = C_VERDE
                txt_vars.value = " | ".join([f"X{k+1}={v:.2f}" for k,v in enumerate(sol_x)])
                
                if len(c) == 2:
                    dibujar_grafico(datos_grafico, sol_x[0], sol_x[1], c, sol_z)
                    cont_grafico.visible = True
                else:
                    cont_grafico.visible = False
            else:
                cont_res.bgcolor = "#FFEBEE"
                cont_res.border = ft.border.all(1, C_ROJO)
                txt_z.value = "Sin Solución"
                txt_z.color = C_ROJO
                txt_vars.value = "Región no factible"
                cont_grafico.visible = False
                
        except Exception as ex:
            txt_error.value = f"Error: {str(ex)}"
            txt_error.visible = True
            
        page.update()

    # --- GRÁFICO ---
    chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, "#E0E0E0"),
        min_y=0, min_x=0, expand=True,
        left_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X2"), title_size=15),
        bottom_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X1"), title_size=15),
        tooltip_bgcolor="#263238"
    )

    def dibujar_grafico(restricciones, opt_x1, opt_x2, c, z_val):
        chart.data_series = []
        leyenda_container.controls = []
        
        max_coord = 0
        for r in restricciones:
            a1, a2 = r['a']
            b = r['b']
            if abs(a1) > 0.01: max_coord = max(max_coord, b/a1)
            if abs(a2) > 0.01: max_coord = max(max_coord, b/a2)
        
        max_coord = max(max_coord, opt_x1, opt_x2)
        limit = max(10, max_coord * 1.2)
        
        chart.max_x = limit
        chart.max_y = limit
        
        colores = [C_AZUL, C_NARANJA, "#9C27B0", "#009688"]
        bg_colores = [C_AZUL_BG, C_NARANJA_BG, "#E1BEE7", "#B2DFDB"]
        
        for idx, r in enumerate(restricciones):
            a1, a2 = r['a']
            b = r['b']
            color = colores[idx % len(colores)]
            bg_color_hex = bg_colores[idx % len(bg_colores)]
            
            pts = []
            if abs(a2) < 0.01 and abs(a1) > 0.01: 
                val = b/a1
                pts = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, limit)]
            elif abs(a1) < 0.01 and abs(a2) > 0.01: 
                val = b/a2
                pts = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(limit, val)]
            elif abs(a1) > 0.01 and abs(a2) > 0.01:
                pts = [ft.LineChartDataPoint(0, b/a2), ft.LineChartDataPoint(b/a1, 0)]
            
            if pts:
                chart.data_series.append(
                    ft.LineChartData(
                        data_points=pts,
                        stroke_width=3, color=color, curved=False,
                        below_line_bgcolor=bg_color_hex
                    )
                )
                leyenda_container.controls.append(
                    ft.Row([ft.Container(width=12, height=12, bgcolor=color, border_radius=2), ft.Text(f"R{r['id']}", size=12)], spacing=2)
                )

        try:
            c1, c2 = c[0], c[1]
            z_pts = []
            if abs(c1) > 0.01 and abs(c2) > 0.01:
                y_int = z_val / c2
                x_int = z_val / c1
                z_pts = [ft.LineChartDataPoint(0, y_int), ft.LineChartDataPoint(x_int, 0)]
            if z_pts:
                 chart.data_series.append(ft.LineChartData(data_points=z_pts, stroke_width=2, color=C_ROJO, dash_pattern=[5, 5]))
                 leyenda_container.controls.append(ft.Row([ft.Container(width=12, height=12, bgcolor=C_ROJO, border_radius=6), ft.Text("Z", size=12, weight="bold", color=C_ROJO)], spacing=2))
        except: pass

        chart.data_series.append(ft.LineChartData(data_points=[ft.LineChartDataPoint(opt_x1, opt_x2)], stroke_width=0, color=C_ROJO, point=True))
        page.update()

    # --- UI COMPONENTES ---
    dd_obj = ft.Dropdown(
        options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")],
        value="Maximizar", width=140, bgcolor=C_BLANCO, on_change=calcular
    )
    
    row_vars = ft.Row(wrap=True, spacing=5)
    col_rest = ft.Column(spacing=5)
    
    # --- AQUÍ ESTÁ EL CAMBIO SOLICITADO (SINCRONIZACIÓN) ---
    def add_var(e):
        idx = len(obj_inputs) + 1
        # Agregar variable al objetivo
        inp = ft.TextField(label=f"C{idx}", width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
        obj_inputs.append(inp)
        row_vars.controls.append(inp)
        
        # AGREGAR COLUMNA A LAS RESTRICCIONES EXISTENTES
        # Recorremos la lista 'restricciones_rows' que tiene los controles
        for row in restricciones_rows:
            # Creamos el nuevo input
            new_rest_inp = ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
            # Insertamos ANTES del Dropdown (que está en la posición -2)
            row.insert(len(row)-2, new_rest_inp)
            
        page.update()

    def add_rest(e):
        row = []
        # Crear inputs basados en cuantas variables hay actualmente en 'obj_inputs'
        for _ in obj_inputs:
            row.append(ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        # DROPDOWN CON TODOS LOS SIGNOS
        dd_s = ft.Dropdown(
            options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")],
            value="≤", width=60, bgcolor=C_GRIS, content_padding=5, on_change=calcular
        )
        row.append(dd_s)
        row.append(ft.TextField(width=70, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        restricciones_rows.append(row)
        idx = len(restricciones_rows)
        bg = C_AZUL_BG if (idx == 1 and switch_slider.value) else "transparent"
        col_rest.controls.append(ft.Container(content=ft.Row([ft.Text(f"R{idx}", weight="bold")] + row, wrap=True, alignment="center"), bgcolor=bg, padding=5, border_radius=5))
        page.update()

    # --- NUEVA FUNCIÓN: RESET ---
    def reset_app(e):
        # 1. Limpiar datos lógicos
        obj_inputs.clear()
        restricciones_rows.clear()
        
        # 2. Limpiar UI
        row_vars.controls.clear()
        col_rest.controls.clear()
        cont_grafico.visible = False
        txt_z.value = "Z: ---"
        txt_vars.value = "..."
        cont_res.bgcolor = C_GRIS
        cont_res.border = None
        
        # 3. Recrear estado inicial (2 variables, 2 restricciones)
        # OJO: Llamamos a las funciones pasando 'None' para simular el click
        add_var(None) 
        add_var(None)
        add_rest(None)
        add_rest(None)
        
        page.update()

    slider = ft.Slider(min=0, max=500, value=100, divisions=100, label="{value}", active_color=C_AZUL, on_change=calcular)
    switch_slider = ft.Switch(value=True, active_color=C_AZUL, on_change=calcular)
    
    panel_innov = ft.Container(content=ft.Column([
            ft.Row([ft.Icon(name="touch_app", color=C_AZUL), ft.Text("Análisis R1", color=C_AZUL, weight="bold")]),
            ft.Row([switch_slider, ft.Container(slider, expand=True)], alignment="spaceBetween")
        ]), bgcolor=C_AZUL_BG, padding=10, border_radius=10)

    cont_res = ft.Container(content=ft.Column([txt_z := ft.Text("Z: ---", size=24, weight="bold"), txt_vars := ft.Text("...", size=14)], horizontal_alignment="center"), padding=15, border_radius=10, bgcolor=C_GRIS, width=350)
    cont_grafico = ft.Container(content=ft.Column([ft.Text("Gráfico de Solución", weight="bold"), leyenda_container, ft.Container(chart, height=350, width=350)], horizontal_alignment="center"), padding=10, border=ft.border.all(1, "#E0E0E0"), border_radius=10, visible=False, bgcolor=C_BLANCO)
    txt_error = ft.Text("", color=C_ROJO, visible=False)

    # Botón Reset (Basurero)
    btn_reset = ft.IconButton(icon=ft.icons.DELETE_FOREVER, icon_color=C_ROJO, tooltip="Resetear todo", on_click=reset_app)

    page.add(ft.Column([
        ft.Row([
            ft.Text("Solver Master Pro", size=26, weight="bold", color=C_AZUL),
            btn_reset # Agregado aquí
        ], alignment="spaceBetween"),
        ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var, bgcolor=C_AZUL, color=C_BLANCO)], alignment="spaceBetween"),
        ft.Container(row_vars, padding=5),
        ft.Row([ft.Text("Restricciones", weight="bold"), ft.ElevatedButton("+Rest", on_click=add_rest)], alignment="spaceBetween"),
        col_rest,
        ft.Divider(), panel_innov, ft.Divider(),
        ft.Container(cont_res, alignment=ft.alignment.center),
        txt_error, cont_grafico
    ], scroll="adaptive"))

    # INICIALIZACIÓN ORIGINAL (QUE SÍ FUNCIONA)
    # Se ejecuta al final, una sola vez.
    add_var(None); add_var(None)
    add_rest(None); add_rest(None)

ft.app(target=main)

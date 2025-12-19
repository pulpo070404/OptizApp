import flet as ft
import traceback

# --- MOTOR MATEMÁTICO (SIMPLEX BIG-M) ---
def resolver_simplex(c, A, b, signos, es_max):
    try:
        M = 1000000.0
        num_vars = len(c)
        num_rest = len(b)
        
        num_artificial = 0
        for s in signos:
            if s in [">=", "≥", "="]:
                num_artificial += 1
        
        tabla = []
        art_indices = [] 
        art_counter = 0
        
        for i in range(num_rest):
            row = list(A[i])
            slacks = [0.0] * num_rest
            s = signos[i]
            if s in ["<=", "≤"]: slacks[i] = 1.0
            elif s in [">=", "≥"]: slacks[i] = -1.0
            row.extend(slacks)
            
            arts = [0.0] * num_artificial
            if s in [">=", "≥", "="]:
                arts[art_counter] = 1.0
                art_indices.append((i, num_vars + num_rest + art_counter))
                art_counter += 1
            row.extend(arts)
            row.append(b[i])
            tabla.append(row)
        
        if es_max: z_row = [-val for val in c]
        else: z_row = [val for val in c]
            
        z_row.extend([0.0] * num_rest)
        z_row.extend([M] * num_artificial)
        z_row.append(0.0)
        
        for r_idx, c_idx in art_indices:
            row_val = tabla[r_idx]
            for j in range(len(z_row)):
                z_row[j] -= M * row_val[j]
        
        tabla.append(z_row)
        
        for _ in range(100):
            z = tabla[-1]
            min_val = min(z[:-1])
            if min_val >= -1e-9: break 
            
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
            
            if pivot_row == -1: return None
            
            pivot_val = tabla[pivot_row][pivot_col]
            tabla[pivot_row] = [x / pivot_val for x in tabla[pivot_row]]
            for i in range(len(tabla)):
                if i != pivot_row:
                    factor = tabla[i][pivot_col]
                    tabla[i] = [tabla[i][j] - factor * tabla[pivot_row][j] for j in range(len(tabla[0]))]
        
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
        if not es_max: z_final *= -1
            
        return res_x, z_final
    except:
        return None

def main(page: ft.Page):
    try:
        # --- CONFIGURACIÓN UI ---
        page.title = "Solver Pro"
        page.theme_mode = "light"
        page.scroll = "adaptive" 
        page.padding = 10
        
        # --- COLORES ---
        C_AZUL = "#1976D2"
        C_AZUL_BG = "#BBDEFB"
        C_VERDE = "#388E3C"
        C_VERDE_BG = "#C8E6C9"
        C_ROJO = "#D32F2F"
        C_BLANCO = "#FFFFFF"
        C_GRIS = "#F5F5F5"
        
        # Colores para gráfico (Línea, Fondo)
        GRAPH_COLORS = [
            (C_AZUL, C_AZUL_BG),
            ("#FF9800", "#FFE0B2"), # Naranja
            ("#9C27B0", "#E1BEE7"), # Morado
            ("#009688", "#B2DFDB")  # Verde Azulado
        ]

        # --- ESTADO ---
        obj_inputs = []       
        restricciones_rows = [] 

        # --- COMPONENTES GRÁFICOS ---
        leyenda_container = ft.Row(wrap=True, alignment="center", spacing=10)
        
        chart = ft.LineChart(
            data_series=[],
            border=ft.border.all(1, "#E0E0E0"),
            min_y=0, min_x=0, expand=True,
            left_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X2"), title_size=12),
            bottom_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X1"), title_size=12),
            tooltip_bgcolor="#263238"
        )

        # --- FUNCIONES DE DIBUJO AVANZADO ---
        def dibujar_grafico(restricciones, opt_x1, opt_x2, c, z_val):
            try:
                chart.data_series = []
                leyenda_container.controls = []
                
                # 1. Calcular escala del gráfico
                max_coord = 0
                for r in restricciones:
                    a1, a2 = r['a']
                    b = r['b']
                    # Evitar division por cero
                    if abs(a1) > 0.01: max_coord = max(max_coord, b/a1)
                    if abs(a2) > 0.01: max_coord = max(max_coord, b/a2)
                
                max_coord = max(max_coord, opt_x1, opt_x2)
                limit = max(10, max_coord * 1.3) # 30% de margen
                chart.max_x = limit
                chart.max_y = limit

                # 2. Dibujar Restricciones (Con sombreado)
                for idx, r in enumerate(restricciones):
                    a1, a2 = r['a']
                    b = r['b']
                    # Ciclo de colores
                    color_linea, color_fondo = GRAPH_COLORS[idx % len(GRAPH_COLORS)]
                    
                    pts = []
                    # Caso: Corte en ambos ejes
                    if abs(a1) > 0.01 and abs(a2) > 0.01:
                        pts = [ft.LineChartDataPoint(0, b/a2), ft.LineChartDataPoint(b/a1, 0)]
                    # Caso: Horizontal (solo corta X2)
                    elif abs(a1) < 0.01 and abs(a2) > 0.01: 
                        val = b/a2
                        pts = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(limit, val)]
                    # Caso: Vertical (solo corta X1)
                    elif abs(a2) < 0.01 and abs(a1) > 0.01: 
                        val = b/a1
                        pts = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, limit)]
                    
                    if pts:
                        chart.data_series.append(
                            ft.LineChartData(
                                data_points=pts, 
                                stroke_width=3, 
                                color=color_linea,
                                below_line_bgcolor=color_fondo, # <--- AQUÍ ESTÁ EL SOMBREADO
                                curved=False
                            )
                        )
                        # Agregar a Leyenda
                        leyenda_container.controls.append(
                            ft.Row([
                                ft.Container(width=12, height=12, bgcolor=color_linea, border_radius=2),
                                ft.Text(f"R{r['id']}", size=12, weight="bold")
                            ], spacing=2)
                        )

                # 3. Dibujar Línea Z (Objetivo) - Punteada Roja
                try:
                    c1, c2 = c[0], c[1]
                    # Solo dibujar si tiene pendiente (ambos coefs existen)
                    if abs(c1) > 0.01 and abs(c2) > 0.01:
                        # Ecuación Z: c1*x + c2*y = Z_opt
                        # Puntos de corte: (0, Z/c2) y (Z/c1, 0)
                        z_pts = [
                            ft.LineChartDataPoint(0, z_val/c2),
                            ft.LineChartDataPoint(z_val/c1, 0)
                        ]
                        chart.data_series.append(
                            ft.LineChartData(
                                data_points=z_pts, 
                                stroke_width=2, 
                                color=C_ROJO, 
                                dash_pattern=[5, 5] # <--- LÍNEA PUNTEADA
                            )
                        )
                        leyenda_container.controls.append(
                            ft.Row([
                                ft.Container(width=12, height=2, bgcolor=C_ROJO),
                                ft.Text("Z (Obj)", size=12, color=C_ROJO, weight="bold")
                            ], spacing=2)
                        )
                except: pass

                # 4. Dibujar Punto Óptimo
                chart.data_series.append(
                    ft.LineChartData(
                        data_points=[ft.LineChartDataPoint(opt_x1, opt_x2)], 
                        stroke_width=0, 
                        color=C_ROJO, 
                        point=True,
                        tooltip="Solución Óptima"
                    )
                )
                
            except Exception as e:
                print(f"Error dibujo: {e}")

        # --- CONTROLES DE INTERFAZ ---
        dd_obj = ft.Dropdown(
            options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")],
            value="Maximizar", width=140, bgcolor=C_BLANCO, text_size=14
        )
        
        row_vars = ft.Row(wrap=True, spacing=5)
        col_rest = ft.Column(spacing=5)
        
        cont_res = ft.Container(
            content=ft.Column([
                txt_z := ft.Text("Z: ---", size=24, weight="bold"), 
                txt_vars := ft.Text("...", size=14)
            ], horizontal_alignment="center"), 
            padding=15, border_radius=10, bgcolor=C_GRIS, width=350
        )
        
        cont_grafico = ft.Container(
            content=ft.Column([
                ft.Text("Gráfico de Solución", weight="bold"), 
                leyenda_container, 
                ft.Container(chart, height=350, width=320) 
            ], horizontal_alignment="center"), 
            padding=10, border=ft.border.all(1, "#E0E0E0"), 
            border_radius=10, visible=False, bgcolor=C_BLANCO
        )
        
        txt_error = ft.Text("", color=C_ROJO, visible=False)

        # --- LÓGICA PRINCIPAL ---
        def calcular(e):
            try:
                txt_error.visible = False
                # Leer Objetivo
                c = []
                for inp in obj_inputs:
                    c.append(float(inp.value) if inp.value else 0.0)
                
                # Leer Restricciones
                A = []; b = []; signos = []; datos_grafico = []
                max_val_intercept = 0 
                
                for i, row_control in enumerate(restricciones_rows):
                    inputs_vars = row_control.controls[1:-2] 
                    dd_signo = row_control.controls[-2]
                    inp_lim = row_control.controls[-1]

                    coefs = []
                    for inp in inputs_vars:
                        coefs.append(float(inp.value) if inp.value else 0.0)
                    
                    signos.append(dd_signo.value)
                    
                    # Slider
                    if i == 0 and switch_slider.value:
                        val_b = slider.value
                        inp_lim.value = str(int(val_b))
                    else:
                        val_b = float(inp_lim.value) if inp_lim.value else 0.0
                    
                    # Calcular intercepción para slider
                    for coef in coefs:
                        if abs(coef) > 0.01: max_val_intercept = max(max_val_intercept, val_b/coef)
                    
                    A.append(coefs); b.append(val_b)
                    # Guardar datos para grafico si son 2 variables
                    if len(c) == 2: datos_grafico.append({'a': coefs, 'b': val_b, 'id': i+1})

                # Ajustar slider dinámicamente
                if slider.max < max_val_intercept: slider.max = max(100, max_val_intercept * 1.5)

                # Solver
                es_max = dd_obj.value == "Maximizar"
                res = resolver_simplex(c, A, b, signos, es_max)
                
                if res:
                    sol_x, sol_z = res
                    cont_res.bgcolor = C_VERDE_BG
                    txt_z.value = f"Z = {sol_z:.2f}"
                    txt_vars.value = " | ".join([f"X{k+1}={v:.2f}" for k,v in enumerate(sol_x)])
                    
                    # Mostrar gráfico solo si hay 2 variables
                    if len(c) == 2:
                        dibujar_grafico(datos_grafico, sol_x[0], sol_x[1], c, sol_z)
                        cont_grafico.visible = True
                    else:
                        cont_grafico.visible = False
                else:
                    cont_res.bgcolor = "#FFEBEE"
                    txt_z.value = "Sin Solución"
                    txt_vars.value = "No Factible"
                    cont_grafico.visible = False
            except Exception as ex:
                txt_error.value = str(ex)
                txt_error.visible = True
            page.update()

        dd_obj.on_change = calcular
        
        def add_var(e):
            try:
                idx = len(obj_inputs) + 1
                inp = ft.TextField(label=f"C{idx}", width=60, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular, text_size=12)
                obj_inputs.append(inp)
                row_vars.controls.append(inp)
                for row_obj in restricciones_rows:
                    new_rest_input = ft.TextField(width=60, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular, text_size=12)
                    row_obj.controls.insert(len(row_obj.controls) - 2, new_rest_input)
                page.update()
            except Exception as ex:
                txt_error.value = f"Error Var: {ex}"; txt_error.visible = True; page.update()

        def add_rest(e):
            try:
                idx = len(restricciones_rows) + 1
                controls_list = [ft.Text(f"R{idx}", weight="bold", size=12)]
                for _ in obj_inputs:
                    controls_list.append(ft.TextField(width=60, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular, text_size=12))
                
                dd_s = ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=60, bgcolor=C_GRIS, content_padding=5, on_change=calcular, text_size=12)
                controls_list.append(dd_s)
                controls_list.append(ft.TextField(width=60, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular, text_size=12))
                
                new_row = ft.Row(controls_list, wrap=True, alignment="start", spacing=3)
                restricciones_rows.append(new_row)
                
                bg = C_AZUL_BG if (idx == 1 and switch_slider.value) else "transparent"
                col_rest.controls.append(ft.Container(content=new_row, bgcolor=bg, padding=5, border_radius=5))
                page.update()
            except Exception as ex:
                txt_error.value = f"Error Rest: {ex}"; txt_error.visible = True; page.update()

        def reset_app(e):
            obj_inputs.clear(); restricciones_rows.clear()
            row_vars.controls.clear(); col_rest.controls.clear()
            cont_res.bgcolor = C_GRIS; txt_z.value = "Z: ---"; txt_vars.value = "..."
            cont_grafico.visible = False; txt_error.visible = False
            add_var(None); add_var(None)
            add_rest(None); add_rest(None)
            page.update()

        slider = ft.Slider(min=0, max=500, value=100, divisions=100, active_color=C_AZUL, on_change=calcular)
        switch_slider = ft.Switch(value=True, active_color=C_AZUL, on_change=calcular)
        
        panel_innov = ft.Container(content=ft.Column([
                ft.Row([ft.Icon(name="touch_app", color=C_AZUL), ft.Text("Análisis R1", color=C_AZUL, weight="bold")]),
                ft.Row([switch_slider, ft.Container(slider, expand=True)], alignment="spaceBetween")
            ]), bgcolor=C_AZUL_BG, padding=10, border_radius=10)

        # Botón Reset corregido (ft.Icons)
        btn_reset = ft.IconButton(icon=ft.Icons.RESTART_ALT, icon_color=C_ROJO, on_click=reset_app)

        # Layout
        page.add(ft.Column([
            ft.Row([ft.Text("Solver Pro", size=20, weight="bold", color=C_AZUL), btn_reset], alignment="spaceBetween"),
            ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var, bgcolor=C_AZUL, color=C_BLANCO)], alignment="spaceBetween"),
            ft.Container(row_vars, padding=5),
            ft.Divider(),
            ft.Row([ft.Text("Restricciones", weight="bold"), ft.ElevatedButton("+Rest", on_click=add_rest)], alignment="spaceBetween"),
            col_rest,
            ft.Divider(), panel_innov, ft.Divider(),
            ft.Container(cont_res, alignment=ft.alignment.center),
            txt_error, 
            cont_grafico
        ], scroll="adaptive"))

        add_var(None); add_var(None)
        add_rest(None); add_rest(None)
    
    except Exception as e:
        page.clean()
        page.add(ft.Text(f"ERROR FATAL:\n{traceback.format_exc()}", color="red", size=14, selectable=True))
        page.update()

ft.app(target=main)

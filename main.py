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

    # --- COLORES ---
    C_AZUL = "#1976D2"
    C_AZUL_BG = "#BBDEFB"
    C_NARANJA = "#FF9800"
    C_NARANJA_BG = "#FFE0B2"
    C_VERDE = "#388E3C"
    C_VERDE_BG = "#C8E6C9"
    C_ROJO = "#D32F2F"
    C_BLANCO = "#FFFFFF"
    C_GRIS = "#F5F5F5"

    # --- VARIABLES ---
    obj_inputs = []
    restricciones_rows = []

    # --- WIDGETS GLOBALES ---
    # Leyenda personalizada (para evitar errores internos del chart)
    leyenda_container = ft.Row(wrap=True, alignment="center", spacing=10)

    # --- MOTOR MATEMÁTICO ---
    def resolver_simplex(c, A, b, es_max):
        try:
            num_vars = len(c)
            num_rest = len(b)
            tabla = []
            
            # Tabla Inicial
            for i in range(num_rest):
                row = A[i] + [0.0] * num_rest + [b[i]]
                row[num_vars + i] = 1.0
                tabla.append(row)
            
            z_row = [-x if es_max else x for x in c] + [0.0] * num_rest + [0.0]
            tabla.append(z_row)
            
            # Iteraciones
            for _ in range(50):
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
            
            # Resultado
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
            
            z_final = tabla[-1][-1] * (1 if es_max else -1)
            return res_x, z_final
        except:
            return None

    # --- LÓGICA DE ACTUALIZACIÓN ---
    def calcular(e):
        try:
            txt_error.visible = False
            
            # Leer C (Objetivo)
            c = []
            max_val_input = 0
            for inp in obj_inputs:
                v = float(inp.value) if inp.value else 0.0
                c.append(v)
                max_val_input = max(max_val_input, v)
            
            # Leer Restricciones
            A = []
            b = []
            datos_grafico = []
            
            for i, row in enumerate(restricciones_rows):
                coefs = []
                for inp in row[:-2]:
                    v = float(inp.value) if inp.value else 0.0
                    coefs.append(v)
                    max_val_input = max(max_val_input, v)
                
                inp_lim = row[-1]
                if i == 0 and switch_slider.value:
                    val_b = slider.value
                    inp_lim.value = str(int(val_b))
                    page.update()
                else:
                    val_b = float(inp_lim.value) if inp_lim.value else 0.0
                
                max_val_input = max(max_val_input, val_b)
                A.append(coefs)
                b.append(val_b)
                
                if len(c) == 2:
                    datos_grafico.append({'a': coefs, 'b': val_b, 'id': i+1})

            # Ajuste Slider
            if slider.max < max_val_input:
                slider.max = max(100, max_val_input * 2)

            # Resolver
            es_max = dd_obj.value == "Maximizar"
            res = resolver_simplex(c, A, b, es_max)
            
            if res:
                sol_x, sol_z = res
                
                # Mostrar Resultados
                cont_res.bgcolor = C_VERDE_BG
                cont_res.border = ft.border.all(1, C_VERDE)
                txt_z.value = f"Z = {sol_z:.2f}"
                txt_z.color = C_VERDE
                txt_vars.value = " | ".join([f"X{k+1}={v:.2f}" for k,v in enumerate(sol_x)])
                
                # Graficar
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
                txt_vars.value = "Revisar Restricciones"
                cont_grafico.visible = False
                
        except Exception as ex:
            txt_error.value = f"Error: {str(ex)}"
            txt_error.visible = True
            
        page.update()

    # --- GRÁFICO OPTIMIZADO ---
    chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, "#E0E0E0"),
        min_y=0,
        min_x=0,
        expand=True,
        # Ejes para que se vean los números
        left_axis=ft.ChartAxis(
            labels_size=40,
            title=ft.Text("X2", size=10),
            title_size=20
        ),
        bottom_axis=ft.ChartAxis(
            labels_size=40,
            title=ft.Text("X1", size=10),
            title_size=20
        ),
        tooltip_bgcolor="#263238"
    )

    def dibujar_grafico(restricciones, opt_x1, opt_x2, c, z_val):
        chart.data_series = []
        leyenda_container.controls = [] # Limpiar leyenda
        
        # Calcular Escala
        max_coord = max(opt_x1, opt_x2, 10) * 1.5
        chart.max_x = max_coord
        chart.max_y = max_coord
        
        colores = [C_AZUL, C_NARANJA, "#9C27B0", "#009688"]
        bg_colores = [C_AZUL_BG, C_NARANJA_BG, "#E1BEE7", "#B2DFDB"]
        
        # 1. Dibujar Restricciones
        for idx, r in enumerate(restricciones):
            a1, a2 = r['a']
            b = r['b']
            color = colores[idx % len(colores)]
            bg_color = bg_colores[idx % len(bg_colores)]
            
            pts = []
            if abs(a2) < 0.01 and abs(a1) > 0.01: # Vertical
                val = b/a1
                pts = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, max_coord)]
            elif abs(a1) < 0.01 and abs(a2) > 0.01: # Horizontal
                val = b/a2
                pts = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(max_coord, val)]
            elif abs(a1) > 0.01 and abs(a2) > 0.01: # Diagonal
                pts = [ft.LineChartDataPoint(0, b/a2), ft.LineChartDataPoint(b/a1, 0)]
            
            if pts:
                # Agregar línea con área sombreada suave
                chart.data_series.append(
                    ft.LineChartData(
                        data_points=pts,
                        stroke_width=3,
                        color=color,
                        curved=False,
                        stroke_cap_round=True,
                        below_line_bgcolor=ft.colors.with_opacity(0.2, color) # Sombreado seguro
                    )
                )
                # Agregar a leyenda
                leyenda_container.controls.append(
                    ft.Row([
                        ft.Container(width=12, height=12, bgcolor=color, border_radius=2),
                        ft.Text(f"R{r['id']}", size=12, weight="bold")
                    ], spacing=2)
                )

        # 2. Dibujar Línea Z (Función Objetivo)
        # Ecuación: c1*x1 + c2*x2 = Z  ->  x2 = (Z - c1*x1) / c2
        try:
            c1, c2 = c[0], c[1]
            z_pts = []
            if abs(c2) > 0.01:
                # Punto corte eje Y (x1=0)
                y_intercept = z_val / c2
                # Punto corte eje X (x2=0)
                x_intercept = z_val / c1 if abs(c1) > 0.01 else max_coord
                
                # Dibujar segmento largo que pase por el óptimo
                # Usaremos interceptos si están en rango, o bordes
                p1 = ft.LineChartDataPoint(0, y_intercept)
                p2 = ft.LineChartDataPoint(x_intercept, 0)
                z_pts = [p1, p2]
            
            if z_pts:
                 chart.data_series.append(
                    ft.LineChartData(
                        data_points=z_pts,
                        stroke_width=2,
                        color=C_ROJO,
                        dash_pattern=[5, 5], # Línea punteada
                        curved=False
                    )
                )
                 leyenda_container.controls.append(
                    ft.Row([
                        ft.Container(width=12, height=12, bgcolor=C_ROJO, border_radius=6),
                        ft.Text("Z (Obj)", size=12, weight="bold", color=C_ROJO)
                    ], spacing=2)
                )
        except:
            pass # Si falla Z, no importa, mostrar al menos las restricciones

        # 3. Punto Óptimo (Círculo Rojo)
        chart.data_series.append(
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(opt_x1, opt_x2)],
                stroke_width=0,
                color=C_ROJO,
                point=True,
            )
        )
        page.update()

    # --- UI LAYOUT ---
    dd_obj = ft.Dropdown(
        options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")],
        value="Maximizar",
        width=140,
        bgcolor=C_BLANCO,
        on_change=calcular
    )
    
    row_vars = ft.Row(wrap=True, spacing=5)
    col_rest = ft.Column(spacing=5)
    
    def add_var(e):
        idx = len(obj_inputs) + 1
        inp = ft.TextField(
            label=f"C{idx}",
            width=70,
            keyboard_type="number",
            bgcolor=C_BLANCO,
            content_padding=5,
            on_change=calcular
        )
        obj_inputs.append(inp)
        row_vars.controls.append(inp)
        for r in restricciones_rows:
            r.insert(len(r)-2, ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        page.update()

    def add_rest(e):
        row = []
        for _ in obj_inputs:
            row.append(ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        row.append(ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥")], value="≤", width=60, bgcolor=C_GRIS, content_padding=5, on_change=calcular))
        row.append(ft.TextField(width=70, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        restricciones_rows.append(row)
        
        idx = len(restricciones_rows)
        bg = C_AZUL_BG if (idx == 1 and switch_slider.value) else "transparent"
        
        col_rest.controls.append(ft.Container(
            content=ft.Row([ft.Text(f"R{idx}", weight="bold")] + row, wrap=True, alignment="center"),
            bgcolor=bg, padding=5, border_radius=5
        ))
        page.update()

    # Slider
    slider = ft.Slider(min=0, max=500, value=100, divisions=100, label="{value}", active_color=C_AZUL, on_change=calcular)
    switch_slider = ft.Switch(value=True, active_color=C_AZUL, on_change=calcular)
    
    panel_innov = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(name="touch_app", color=C_AZUL), ft.Text("Análisis R1", color=C_AZUL, weight="bold")]),
            ft.Row([switch_slider, ft.Container(slider, expand=True)], alignment="spaceBetween")
        ]), bgcolor=C_AZUL_BG, padding=10, border_radius=10
    )

    # Resultados
    txt_z = ft.Text("Z: ---", size=24, weight="bold")
    txt_vars = ft.Text("...", size=14)
    cont_res = ft.Container(
        content=ft.Column([txt_z, txt_vars], horizontal_alignment="center"),
        padding=15, border_radius=10, bgcolor=C_GRIS, width=350
    )
    
    # Gráfico Container
    cont_grafico = ft.Container(
        content=ft.Column([
            ft.Text("Gráfico de Solución", weight="bold"),
            leyenda_container, # Leyenda Arriba
            ft.Container(chart, height=350, width=350) # Tamaño fijo y cuadrado
        ], horizontal_alignment="center"),
        padding=10, border=ft.border.all(1, "#E0E0E0"), border_radius=10, visible=False, bgcolor=C_BLANCO
    )
    
    txt_error = ft.Text("", color=C_ROJO, visible=False)

    # LAYOUT
    page.add(ft.Column([
        ft.Text("Solver Master Pro", size=26, weight="bold", color=C_AZUL),
        ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var, bgcolor=C_AZUL, color=C_BLANCO)], alignment="spaceBetween"),
        ft.Container(row_vars, padding=5),
        ft.Row([ft.Text("Restricciones", weight="bold"), ft.ElevatedButton("+Rest", on_click=add_rest)], alignment="spaceBetween"),
        col_rest,
        ft.Divider(), panel_innov, ft.Divider(),
        ft.Container(cont_res, alignment=ft.alignment.center),
        txt_error, cont_grafico
    ], scroll="adaptive"))

    # Init
    add_var(None); add_var(None)
    add_rest(None); add_rest(None)

ft.app(target=main)

import flet as ft
import traceback

def main(page: ft.Page):
    # --- BLOQUE DE SEGURIDAD GLOBAL ---
    try:
        page.title = "Solver Pro Segura"
        page.theme_mode = "light"
        page.scroll = "adaptive"
        page.padding = 20
        page.window_width = 380
        page.window_height = 800

        # --- VARIABLES ---
        obj_inputs = []
        restricciones_rows = []
        
        # --- SOLVER SIMPLE (OPTIMIZADO) ---
        def resolver_logica(c, A, b, es_max):
            try:
                # Simplex muy básico para evitar bloqueos
                num_vars = len(c)
                num_rest = len(b)
                tabla = []
                # Crear tabla
                for i in range(num_rest):
                    row = A[i] + [0.0]*num_rest + [b[i]]
                    row[num_vars + i] = 1.0
                    tabla.append(row)
                
                z_row = [-x if es_max else x for x in c] + [0.0]*num_rest + [0.0]
                tabla.append(z_row)
                
                # Iterar (Máximo 20 iteraciones para no colgar el celular)
                for _ in range(20):
                    z = tabla[-1]
                    min_val = min(z[:-1])
                    if min_val >= -1e-9: break
                    
                    pivot_col = z.index(min_val)
                    min_ratio = float('inf')
                    pivot_row = -1
                    
                    for i in range(num_rest):
                        if tabla[i][pivot_col] > 1e-9:
                            ratio = tabla[i][-1] / tabla[i][pivot_col]
                            if ratio < min_ratio:
                                min_ratio = ratio
                                pivot_row = i
                    
                    if pivot_row == -1: return None
                    
                    # Gauss
                    pivot_val = tabla[pivot_row][pivot_col]
                    tabla[pivot_row] = [x/pivot_val for x in tabla[pivot_row]]
                    for i in range(len(tabla)):
                        if i != pivot_row:
                            f = tabla[i][pivot_col]
                            tabla[i] = [tabla[i][j] - f*tabla[pivot_row][j] for j in range(len(tabla[0]))]
                
                # Resultado
                res = [0.0]*num_vars
                for j in range(num_vars):
                    col = [tabla[i][j] for i in range(num_rest)]
                    if col.count(1.0) == 1:
                        idx = col.index(1.0)
                        if idx < num_rest: res[j] = tabla[idx][-1]
                
                z_final = tabla[-1][-1] * (1 if es_max else -1)
                return res, z_final
            except:
                return None

        # --- EVENTO DEL BOTÓN CALCULAR ---
        def clic_calcular(e):
            try:
                txt_error.visible = False
                
                # 1. Leer Objetivo
                c = []
                for inp in obj_inputs:
                    if inp.value == "": 
                        inp.value = "0"
                    c.append(float(inp.value))
                
                # 2. Leer Restricciones
                A = []
                b = []
                raw_rest = [] # Para gráfico
                
                for i, row in enumerate(restricciones_rows):
                    coefs = []
                    # Inputs variables
                    for inp in row[:-2]:
                        if inp.value == "": inp.value = "0"
                        coefs.append(float(inp.value))
                    
                    # Límite (Slider o Texto)
                    lim_inp = row[-1]
                    # Si es la primera fila y el slider está activo
                    if i == 0 and switch_slider.value:
                        val_b = slider.value
                    else:
                        if lim_inp.value == "": lim_inp.value = "0"
                        val_b = float(lim_inp.value)
                    
                    A.append(coefs)
                    b.append(val_b)
                    
                    # Guardar datos gráfico (solo si son 2 vars)
                    if len(c) == 2:
                        raw_rest.append({'a': coefs, 'b': val_b, 'id': i+1})

                # 3. Resolver
                es_max = dd_obj.value == "Maximizar"
                resultado = resolver_logica(c, A, b, es_max)
                
                if resultado:
                    sol_x, sol_z = resultado
                    txt_res_z.value = f"Z = {sol_z:.2f}"
                    txt_res_x.value = f"Variables: {sol_x}"
                    cont_res.bgcolor = "#E8F5E9" # Verde
                    
                    # 4. Graficar (Solo si hay 2 variables)
                    if len(c) == 2:
                        dibujar_grafico_seguro(raw_rest, sol_x[0], sol_x[1])
                        cont_grafico.visible = True
                    else:
                        cont_grafico.visible = False
                else:
                    txt_res_z.value = "Sin solución"
                    txt_res_x.value = "Revisa las restricciones"
                    cont_res.bgcolor = "#FFEBEE" # Rojo
                    cont_grafico.visible = False
                    
                page.update()
                
            except Exception as ex:
                txt_error.value = f"Error al calcular: {str(ex)}"
                txt_error.visible = True
                page.update()

        # --- GRÁFICO SEGURO ---
        chart = ft.LineChart(data_series=[], border=ft.border.all(1, "grey"), expand=True, min_x=0, min_y=0)
        
        def dibujar_grafico_seguro(restricciones, x1, x2):
            chart.data_series = []
            max_val = max(x1, x2, 10) * 1.5
            chart.max_x = max_val
            chart.max_y = max_val
            
            colores = [ft.colors.BLUE, ft.colors.ORANGE, ft.colors.TEAL]
            
            for i, r in enumerate(restricciones):
                a1, a2 = r['a']
                b = r['b']
                pts = []
                
                # Evitar división por cero
                if abs(a2) < 0.01 and abs(a1) > 0.01: # Vertical
                    val = b/a1
                    pts = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, max_val)]
                elif abs(a1) < 0.01 and abs(a2) > 0.01: # Horizontal
                    val = b/a2
                    pts = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(max_val, val)]
                elif abs(a1) > 0.01 and abs(a2) > 0.01: # Normal
                    pts = [ft.LineChartDataPoint(0, b/a2), ft.LineChartDataPoint(b/a1, 0)]
                
                if pts:
                    chart.data_series.append(ft.LineChartData(data_points=pts, color=colores[i%3], stroke_width=2))
            
            # Punto óptimo
            chart.data_series.append(ft.LineChartData(data_points=[ft.LineChartDataPoint(x1, x2)], color="red", stroke_width=0, point=True))

        # --- INTERFAZ ---
        dd_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=150)
        
        # Contenedores
        row_vars = ft.Row(wrap=True)
        col_rest = ft.Column()
        
        # Funciones UI
        def add_var(e):
            idx = len(obj_inputs)+1
            inp = ft.TextField(label=f"C{idx}", width=70, keyboard_type="number")
            obj_inputs.append(inp)
            row_vars.controls.append(inp)
            # Agregar col a restricciones
            for r in restricciones_rows:
                r.insert(len(r)-2, ft.TextField(width=70, keyboard_type="number"))
            page.update()

        def add_rest(e):
            row = []
            for _ in obj_inputs:
                row.append(ft.TextField(width=70, keyboard_type="number"))
            dd = ft.Dropdown(options=[ft.dropdown.Option("<="), ft.dropdown.Option(">=")], value="<=", width=70)
            lim = ft.TextField(width=70, keyboard_type="number", hint_text="Lim")
            row.append(dd)
            row.append(lim)
            restricciones_rows.append(row)
            col_rest.controls.append(ft.Row([ft.Text(f"R{len(restricciones_rows)}")] + row, wrap=True))
            page.update()

        # Slider
        slider = ft.Slider(min=0, max=500, value=100, label="{value}")
        switch_slider = ft.Switch(label="Usar Slider en R1", value=False)
        
        # Botones
        btn_calc = ft.ElevatedButton("CALCULAR", on_click=clic_calcular, bgcolor="blue", color="white", width=200)
        
        # Resultados
        txt_res_z = ft.Text("Presiona Calcular", size=20, weight="bold")
        txt_res_x = ft.Text("")
        cont_res = ft.Container(content=ft.Column([txt_res_z, txt_res_x]), padding=10, border_radius=10, bgcolor="#F5F5F5")
        
        # Gráfico
        cont_grafico = ft.Container(content=chart, height=300, visible=False)
        
        txt_error = ft.Text("", color="red", visible=False)

        # Armado
        page.add(
            ft.Text("Solver Seguro", size=25, weight="bold", color="blue"),
            ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var)]),
            row_vars,
            ft.Row([ft.Text("Restricciones"), ft.ElevatedButton("+Rest", on_click=add_rest)], alignment="spaceBetween"),
            col_rest,
            ft.Divider(),
            ft.Column([switch_slider, slider]),
            ft.Divider(),
            ft.Container(btn_calc, alignment=ft.alignment.center),
            txt_error,
            cont_res,
            cont_grafico
        )
        
        # Inicializar UI vacía
        add_var(None)
        add_var(None)
        add_rest(None)
        add_rest(None)

    except Exception:
        # PANTALLA ROJA DE LA MUERTE (Reporte de error)
        page.clean()
        page.add(
            ft.Column([
                ft.Text("ERROR FATAL AL INICIAR", color="red", size=20, weight="bold"),
                ft.Text(traceback.format_exc(), color="black", size=10)
            ], scroll="always")
        )

ft.app(target=main)

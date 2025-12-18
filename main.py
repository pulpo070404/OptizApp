import flet as ft
import math

def main(page: ft.Page):
    # Configuración de pantalla móvil
    page.title = "Solver Pro"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 15
    page.window_width = 380
    page.window_height = 800

    # --- CONSTANTES DE COLOR ---
    C_PRIMARY = "#1976D2"    # Azul fuerte
    C_SECONDARY = "#E3F2FD"  # Azul claro
    C_SUCCESS = "#388E3C"    # Verde
    C_ERROR = "#D32F2F"      # Rojo
    C_BG_RES = "#F5F5F5"     # Gris muy claro

    # --- ESTADO DE LA APP ---
    obj_inputs = []
    restricciones_rows = []
    
    # --- MOTOR MATEMÁTICO (SIMPLEX PURO - SIN LIBRERÍAS EXTERNAS) ---
    def resolver_simplex_nativo(c, A, b, es_max):
        """
        Resuelve Simplex usando listas nativas de Python.
        Evita usar Numpy/Scipy para compatibilidad total con Android.
        """
        try:
            num_vars = len(c)
            num_rest = len(b)
            
            # 1. Construir Tabla Inicial
            # Estructura: [Vars... | Holguras... | Solución]
            tabla = []
            
            # Filas de restricciones
            for i in range(num_rest):
                fila = A[i] + [0.0] * num_rest + [b[i]]
                fila[num_vars + i] = 1.0  # Variable de holgura
                tabla.append(fila)
            
            # Fila Z (Función Objetivo)
            # Max Z -> Z - c1x1 - ... = 0
            if es_max:
                fila_z = [-val for val in c] + [0.0] * num_rest + [0.0]
            else:
                fila_z = [val for val in c] + [0.0] * num_rest + [0.0]
            tabla.append(fila_z)
            
            # 2. Iteraciones del Simplex
            while True:
                # Buscar columna pivote (el valor más negativo en fila Z)
                fila_obj = tabla[-1]
                min_val = min(fila_obj[:-1])
                
                if min_val >= -1e-9:
                    break # Óptimo encontrado
                
                col_pivote = fila_obj.index(min_val)
                
                # Buscar fila pivote (Ratio Test)
                min_ratio = float('inf')
                fila_pivote_idx = -1
                
                for i in range(num_rest):
                    val_col = tabla[i][col_pivote]
                    val_sol = tabla[i][-1]
                    
                    if val_col > 1e-9:
                        ratio = val_sol / val_col
                        if ratio < min_ratio:
                            min_ratio = ratio
                            fila_pivote_idx = i
                            
                if fila_pivote_idx == -1:
                    return None # No acotado
                
                # 3. Operaciones Gauss-Jordan
                # Normalizar fila pivote
                pivote = tabla[fila_pivote_idx][col_pivote]
                tabla[fila_pivote_idx] = [x / pivote for x in tabla[fila_pivote_idx]]
                
                # Hacer ceros en las otras filas
                for i in range(len(tabla)):
                    if i != fila_pivote_idx:
                        factor = tabla[i][col_pivote]
                        nueva_fila = []
                        for j in range(len(tabla[0])):
                            val = tabla[i][j] - factor * tabla[fila_pivote_idx][j]
                            nueva_fila.append(val)
                        tabla[i] = nueva_fila

            # 4. Extraer Resultados
            soluciones = [0.0] * num_vars
            for j in range(num_vars):
                columna = [tabla[i][j] for i in range(num_rest)]
                # Si es columna básica (un 1 y puros 0s)
                es_basica = False
                if columna.count(1.0) == 1:
                    # Verificar que el resto sean ceros (con tolerancia)
                    ceros = sum(1 for x in columna if abs(x) < 1e-9)
                    if ceros == len(columna) - 1:
                        idx_uno = columna.index(1.0)
                        if idx_uno < num_rest: # No tomar fila Z
                             soluciones[j] = tabla[idx_uno][-1]

            valor_z = tabla[-1][-1]
            if es_max: valor_z *= 1 # Ajuste de signo según maximización
            else: valor_z *= -1
            
            return soluciones, valor_z

        except Exception:
            return None

    # --- LÓGICA DE INTERFAZ ---
    def procesar_calculo(e):
        try:
            # Recopilar Objetivo
            es_max = dd_objetivo.value == "Maximizar"
            coeffs_obj = []
            max_val_grafico = 0
            
            for inp in obj_inputs:
                v = float(inp.value) if inp.value else 0.0
                coeffs_obj.append(v)
                max_val_grafico = max(max_val_grafico, v)
                
            # Recopilar Restricciones
            matriz_A = []
            vector_b = []
            datos_grafico = [] # Para dibujar líneas
            
            for i, row in enumerate(restricciones_rows):
                # Estructura row: [Input1, Input2..., Dropdown, InputLimite]
                inputs_coef = row[:-2]
                dd_sign = row[-2]
                inp_lim = row[-1]
                
                # Lógica Slider R1
                if i == 0 and switch_slider.value:
                    val_limite = slider_r1.value
                    inp_lim.value = str(int(val_limite))
                else:
                    val_limite = float(inp_lim.value) if inp_lim.value else 0.0
                
                max_val_grafico = max(max_val_grafico, val_limite)
                
                # Coeficientes de la fila
                fila_coeffs = []
                for inp in inputs_coef:
                    v = float(inp.value) if inp.value else 0.0
                    fila_coeffs.append(v)
                    max_val_grafico = max(max_val_grafico, v)
                
                matriz_A.append(fila_coeffs)
                vector_b.append(val_limite)
                
                # Guardar datos puros para el gráfico
                datos_grafico.append({
                    'a': fila_coeffs,
                    'b': val_limite,
                    'sign': dd_sign.value, 
                    'id': i+1
                })
            
            # Ajustar Slider automáticamente
            nuevo_max_slider = max(100, max_val_grafico * 2)
            if slider_r1.max != nuevo_max_slider:
                slider_r1.max = nuevo_max_slider
                
            # RESOLVER
            res = resolver_simplex_nativo(coeffs_obj, matriz_A, vector_b, es_max)
            
            if res:
                sol_x, sol_z = res
                
                # Mostrar Éxito
                panel_resultados.bgcolor = "#E8F5E9" # Verde claro
                panel_resultados.border = ft.border.all(1, C_SUCCESS)
                txt_estado.value = "SOLUCIÓN ÓPTIMA"
                txt_estado.color = C_SUCCESS
                txt_z.value = f"Z = {sol_z:.2f}"
                
                detalles = "Variables: "
                for k, val in enumerate(sol_x):
                    detalles += f"X{k+1}={val:.2f}  "
                txt_detalles.value = detalles
                
                # Graficar (Si son 2 variables)
                if len(coeffs_obj) == 2:
                    dibujar_grafico(datos_grafico, sol_x[0], sol_x[1])
                    contenedor_grafico.visible = True
                else:
                    contenedor_grafico.visible = False
                    
            else:
                # Mostrar Error
                panel_resultados.bgcolor = "#FFEBEE" # Rojo claro
                panel_resultados.border = ft.border.all(1, C_ERROR)
                txt_estado.value = "NO HAY SOLUCIÓN"
                txt_estado.color = C_ERROR
                txt_z.value = "---"
                txt_detalles.value = "Verifica restricciones incompatibles"
                contenedor_grafico.visible = False
                
        except Exception as ex:
            txt_detalles.value = f"Error: {str(ex)}"
            
        page.update()

    # --- GRÁFICOS NATIVOS (FLET CHARTS) ---
    chart_lines = []
    chart_obj = ft.LineChart(
        data_series=chart_lines,
        border=ft.border.all(1, ft.colors.GREY_300),
        left_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X2")),
        bottom_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X1")),
        tooltip_bgcolor=ft.colors.with_opacity(0.8, C_PRIMARY),
        min_y=0, min_x=0,
        expand=True
    )

    def dibujar_grafico(restricciones, opt_x1, opt_x2):
        chart_obj.data_series = []
        
        # Calcular escala
        max_eje = max(opt_x1, opt_x2, 10) * 1.5
        chart_obj.max_x = max_eje
        chart_obj.max_y = max_eje
        
        colores = [ft.colors.BLUE, ft.colors.ORANGE, ft.colors.PURPLE, ft.colors.TEAL]
        
        # Dibujar líneas de restricción
        for idx, r in enumerate(restricciones):
            a1 = r['a'][0]
            a2 = r['a'][1]
            b = r['b']
            color = colores[idx % len(colores)]
            
            puntos = []
            
            # Caso 1: Línea vertical (a2 = 0)
            if abs(a2) < 1e-9:
                if abs(a1) > 1e-9:
                    x_val = b / a1
                    puntos = [ft.LineChartDataPoint(x_val, 0), ft.LineChartDataPoint(x_val, max_eje)]
            
            # Caso 2: Línea horizontal (a1 = 0)
            elif abs(a1) < 1e-9:
                if abs(a2) > 1e-9:
                    y_val = b / a2
                    puntos = [ft.LineChartDataPoint(0, y_val), ft.LineChartDataPoint(max_eje, y_val)]
            
            # Caso 3: Oblicua
            else:
                y_corte = b / a2 # Si x=0
                x_corte = b / a1 # Si y=0
                puntos = [ft.LineChartDataPoint(0, y_corte), ft.LineChartDataPoint(x_corte, 0)]
            
            if puntos:
                chart_obj.data_series.append(
                    ft.LineChartData(
                        data_points=puntos,
                        stroke_width=2,
                        color=color,
                        title=f"R{r['id']}",
                        curved=False
                    )
                )
        
        # Dibujar Punto Óptimo
        chart_obj.data_series.append(
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(opt_x1, opt_x2)],
                stroke_width=0,
                color=ft.colors.RED,
                point=True,
                title="Óptimo",
                stroke_cap_round=True
            )
        )

    # --- CONSTRUCCIÓN UI ---
    
    # 1. Cabecera
    dd_objetivo = ft.Dropdown(
        options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")],
        value="Maximizar", width=140, text_size=13, bgcolor="white", content_padding=8,
        on_change=procesar_calculo
    )
    
    # 2. Variables
    cont_vars = ft.Row(wrap=True, spacing=5)
    def agregar_variable(e):
        n = len(obj_inputs) + 1
        txt = ft.TextField(label=f"C{n}", width=70, text_size=12, keyboard_type="number", bgcolor="white", content_padding=5, on_change=procesar_calculo)
        obj_inputs.append(txt)
        cont_vars.controls.append(txt)
        
        # Actualizar filas de restricción existentes
        for row in restricciones_rows:
            nuevo_input = ft.TextField(width=70, text_size=12, keyboard_type="number", bgcolor="white", content_padding=5, on_change=procesar_calculo)
            row.insert(len(row)-2, nuevo_input)
            
        page.update()

    # 3. Restricciones
    col_restricciones = ft.Column(spacing=5)
    def agregar_restriccion(e):
        row = []
        # Inputs para cada variable
        for _ in range(len(obj_inputs)):
            row.append(ft.TextField(width=70, text_size=12, keyboard_type="number", bgcolor="white", content_padding=5, on_change=procesar_calculo))
        
        # Signo y Límite
        dd = ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=60, text_size=14, content_padding=0, bgcolor="#EEEEEE", on_change=procesar_calculo)
        lim = ft.TextField(hint_text="Lim", width=70, text_size=12, keyboard_type="number", bgcolor="white", content_padding=5, on_change=procesar_calculo)
        
        row.append(dd)
        row.append(lim)
        restricciones_rows.append(row)
        
        # Renderizar visualmente
        idx = len(restricciones_rows)
        bg = C_SECONDARY if (idx==1 and switch_slider.value) else "transparent"
        
        item = ft.Container(
            content=ft.Row([ft.Text(f"R{idx}", weight="bold", size=10, color="grey")] + row, wrap=True, spacing=5, alignment="center"),
            bgcolor=bg, padding=5, border_radius=5
        )
        col_restricciones.controls.append(item)
        page.update()

    # 4. Panel Innovación (Slider)
    slider_r1 = ft.Slider(min=0, max=500, divisions=50, value=100, label="{value}", active_color=C_PRIMARY, on_change=procesar_calculo)
    switch_slider = ft.Switch(value=True, active_color=C_PRIMARY, on_change=procesar_calculo)
    
    panel_innovacion = ft.Container(
        content=ft.Column([
            ft.Row([ft.Icon(ft.icons.TOUCH_APP, color=C_PRIMARY, size=18), ft.Text("Análisis R1", color=C_PRIMARY, weight="bold")], spacing=5),
            ft.Row([switch_slider, ft.Container(content=slider_r1, expand=True)], alignment="spaceBetween")
        ]),
        bgcolor=C_SECONDARY, padding=10, border_radius=10
    )

    # 5. Resultados
    txt_estado = ft.Text("Esperando datos...", weight="bold")
    txt_z = ft.Text("Z: ---", size=20, weight="bold")
    txt_detalles = ft.Text("", size=12, color="grey")
    
    panel_resultados = ft.Container(
        content=ft.Column([txt_estado, txt_z, txt_detalles], horizontal_alignment="center"),
        bgcolor=C_BG_RES, padding=15, border_radius=10, width=350, border=ft.border.all(1, "transparent")
    )
    
    # 6. Gráfico
    contenedor_grafico = ft.Container(
        content=ft.Column([
            ft.Text("Gráfico de Región Factible", weight="bold", color=C_PRIMARY),
            ft.Container(chart_obj, height=300, padding=10)
        ], horizontal_alignment="center"),
        visible=False,
        padding=10, border=ft.border.all(1, "#E0E0E0"), border_radius=10
    )

    # Botones
    btn_var = ft.ElevatedButton("+ Var", on_click=agregar_variable, bgcolor=C_PRIMARY, color="white")
    btn_res = ft.ElevatedButton("+ Restricción", on_click=agregar_restriccion)

    # LAYOUT FINAL
    page.add(
        ft.Column([
            ft.Text("Solver Pro Mobile", size=24, weight="bold", color=C_PRIMARY),
            ft.Row([dd_objetivo, btn_var], alignment="spaceBetween"),
            ft.Container(cont_vars, padding=5),
            ft.Divider(height=10, color="transparent"),
            ft.Row([ft.Text("Restricciones", weight="bold"), btn_res], alignment="spaceBetween"),
            col_restricciones,
            ft.Divider(),
            panel_innovacion,
            ft.Divider(height=10, color="transparent"),
            ft.Row([panel_resultados], alignment="center"),
            contenedor_grafico
        ], scroll="adaptive")
    )
    
    # Inicialización por defecto
    agregar_variable(None)
    agregar_variable(None)
    agregar_restriccion(None)
    agregar_restriccion(None)

ft.app(target=main)

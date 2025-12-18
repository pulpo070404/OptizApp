import flet as ft
import traceback

def main(page: ft.Page):
    # --- CONFIGURACIÓN ---
    page.title = "Solver Master Pro"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 20
    page.window_width = 380
    page.window_height = 800

    # --- COLORES HEXADECIMALES (Seguros para Android) ---
    C_AZUL = "#1976D2"
    C_AZUL_CLARO = "#E3F2FD"
    C_VERDE = "#388E3C"
    C_VERDE_FONDO = "#E8F5E9"
    C_ROJO = "#D32F2F"
    C_ROJO_FONDO = "#FFEBEE"
    C_BLANCO = "#FFFFFF"
    C_GRIS = "#757575"

    # --- VARIABLES GLOBALES ---
    obj_inputs = []
    restricciones_rows = []

    # --- MOTOR MATEMÁTICO (SIMPLEX) ---
    def resolver_simplex(c, A, b, es_max):
        try:
            num_vars = len(c)
            num_rest = len(b)
            tabla = []
            
            # Tabla inicial
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
                        f = tabla[i][pivot_col]
                        tabla[i] = [tabla[i][j] - f * tabla[pivot_row][j] for j in range(len(tabla[0]))]
            
            # Resultados
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

    # --- LÓGICA UI ---
    def calcular(e):
        try:
            txt_error.visible = False
            
            # 1. Datos Objetivo
            c = []
            max_val = 0
            for inp in obj_inputs:
                val = float(inp.value) if inp.value else 0.0
                c.append(val)
                max_val = max(max_val, val)
            
            # 2. Datos Restricciones
            A = []
            b = []
            datos_grafico = []
            
            for i, row in enumerate(restricciones_rows):
                coeffs = []
                for inp in row[:-2]:
                    v = float(inp.value) if inp.value else 0.0
                    coeffs.append(v)
                    max_val = max(max_val, v)
                
                inp_lim = row[-1]
                if i == 0 and switch_slider.value:
                    val_b = slider.value
                    inp_lim.value = str(int(val_b))
                    page.update() # Refrescar visualmente el input
                else:
                    val_b = float(inp_lim.value) if inp_lim.value else 0.0
                
                max_val = max(max_val, val_b)
                A.append(coeffs)
                b.append(val_b)
                
                if len(c) == 2:
                    datos_grafico.append({'a': coeffs, 'b': val_b, 'id': i+1})

            # Ajustar Slider
            if slider.max < max_val * 1.5:
                slider.max = max(100, max_val * 2)

            # 3. Resolver
            es_max = dd_obj.value == "Maximizar"
            res = resolver_simplex(c, A, b, es_max)
            
            if res:
                sol_x, sol_z = res
                cont_res.bgcolor = C_VERDE_FONDO
                cont_res.border = ft.border.all(1, C_VERDE)
                txt_z.value = f"Z = {sol_z:.2f}"
                txt_z.color = C_VERDE
                txt_vars.value = "  |  ".join([f"X{i+1}={val:.2f}" for i, val in enumerate(sol_x)])
                
                if len(c) == 2:
                    dibujar_grafico(datos_grafico, sol_x[0], sol_x[1])
                    cont_grafico.visible = True
                else:
                    cont_grafico.visible = False
            else:
                cont_res.bgcolor = C_ROJO_FONDO
                cont_res.border = ft.border.all(1, C_ROJO)
                txt_z.value = "Sin Solución"
                txt_z.color = C_ROJO
                txt_vars.value = "Datos no factibles"
                cont_grafico.visible = False

        except Exception as ex:
            txt_error.value = f"Error: {str(ex)}"
            txt_error.visible = True
        
        page.update()

    # --- GRÁFICO (CORREGIDO: SIN TITLE) ---
    chart = ft.LineChart(
        data_series=[],
        border=ft.border.all(1, "#E0E0E0"),
        min_y=0, min_x=0,
        expand=True,
        tooltip_bgcolor="#263238"
    )

    def dibujar_grafico(restricciones, x1, x2):
        chart.data_series = []
        limit = max(x1, x2, 10) * 1.5
        chart.max_x = limit
        chart.max_y = limit
        
        colores = [C_AZUL, "#FF9800", "#9C27B0", "#009688"]
        
        for idx, r in enumerate(restricciones):
            a1, a2 = r['a']
            b = r['b']
            color = colores[idx % len(colores)]
            pts = []
            
            # Cortes con ejes
            if abs(a2) < 0.01 and abs(a1) > 0.01: # Vertical
                val = b/a1
                pts = [ft.LineChartDataPoint(val, 0), ft.LineChartDataPoint(val, limit)]
            elif abs(a1) < 0.01 and abs(a2) > 0.01: # Horizontal
                val = b/a2
                pts = [ft.LineChartDataPoint(0, val), ft.LineChartDataPoint(limit, val)]
            elif abs(a1) > 0.01 and abs(a2) > 0.01: # Diagonal
                pts = [ft.LineChartDataPoint(0, b/a2), ft.LineChartDataPoint(b/a1, 0)]
            
            if pts:
                chart.data_series.append(
                    ft.LineChartData(
                        data_points=pts,
                        stroke_width=2,
                        color=color,
                        # AQUÍ QUITAMOS 'title' PARA EVITAR EL ERROR
                    )
                )
        
        # Punto Óptimo
        chart.data_series.append(
            ft.LineChartData(
                data_points=[ft.LineChartDataPoint(x1, x2)],
                stroke_width=0,
                color=C_ROJO,
                point=True,
                # AQUÍ TAMBIÉN QUITAMOS 'title'
            )
        )

    # --- UI COMPONENTES ---
    dd_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=140, on_change=calcular, bgcolor=C_BLANCO)
    
    row_vars = ft.Row(wrap=True, spacing=5)
    col_rest = ft.Column(spacing=5)
    
    def add_var(e):
        idx = len(obj_inputs) + 1
        inp = ft.TextField(label=f"C{idx}",

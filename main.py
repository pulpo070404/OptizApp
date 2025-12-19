import flet as ft

def main(page: ft.Page):
    # --- CONFIGURACIÓN BÁSICA ---
    page.title = "Solver Master Pro"
    page.theme_mode = "light"
    page.scroll = "adaptive"
    page.padding = 10
    page.window_width = 380
    page.window_height = 800

    # --- COLORES ---
    C_AZUL = "#1976D2"
    C_AZUL_BG = "#BBDEFB"
    C_VERDE = "#388E3C"
    C_VERDE_BG = "#C8E6C9"
    C_ROJO = "#D32F2F"
    C_GRIS = "#F5F5F5"
    C_BLANCO = "#FFFFFF"

    # --- VARIABLES GLOBALES DE ESTADO ---
    # Estas listas guardarán las referencias a los inputs para leerlos después
    # No usamos page.controls para leer datos, usamos estas listas.
    inputs_objetivo = [] 
    filas_restricciones = [] # Lista de filas (cada fila es una lista de controles)

    # --- MOTOR MATEMÁTICO (SIMPLEX BIG-M) ---
    def resolver_simplex(c, A, b, signos, es_max):
        try:
            M = 1000000.0
            num_vars = len(c)
            num_rest = len(b)
            
            num_art = 0
            for s in signos:
                if s in [">=", "≥", "="]: num_art += 1
            
            tabla = []
            art_indices = []
            art_count = 0
            
            for i in range(num_rest):
                row = list(A[i])
                slacks = [0.0]*num_rest
                if signos[i] in ["<=", "≤"]: slacks[i] = 1.0
                elif signos[i] in [">=", "≥"]: slacks[i] = -1.0
                row.extend(slacks)
                
                arts = [0.0]*num_art
                if signos[i] in [">=", "≥", "="]:
                    arts[art_count] = 1.0
                    art_indices.append((i, num_vars + num_rest + art_count))
                    art_count += 1
                row.extend(arts)
                row.append(b[i])
                tabla.append(row)
            
            if es_max: z_row = [-x for x in c]
            else: z_row = [x for x in c]
            
            z_row.extend([0.0]*num_rest)
            z_row.extend([M]*num_art)
            z_row.append(0.0)
            
            for r_idx, _ in art_indices:
                row_val = tabla[r_idx]
                for j in range(len(z_row)):
                    z_row[j] -= M * row_val[j]
            tabla.append(z_row)
            
            for _ in range(100):
                z = tabla[-1]
                min_val = min(z[:-1])
                if min_val >= -1e-9: break
                
                p_col = z.index(min_val)
                min_ratio = float('inf')
                p_row = -1
                
                for i in range(num_rest):
                    v = tabla[i][p_col]
                    if v > 1e-9:
                        ratio = tabla[i][-1] / v
                        if ratio < min_ratio:
                            min_ratio = ratio
                            p_row = i
                
                if p_row == -1: return None
                
                p_val = tabla[p_row][p_col]
                tabla[p_row] = [x/p_val for x in tabla[p_row]]
                for i in range(len(tabla)):
                    if i != p_row:
                        f = tabla[i][p_col]
                        tabla[i] = [tabla[i][j] - f*tabla[p_row][j] for j in range(len(tabla[0]))]
            
            res_x = [0.0]*num_vars
            for j in range(num_vars):
                col = [tabla[i][j] for i in range(num_rest)]
                if col.count(1.0) == 1:
                    basic = True
                    for x in col:
                        if abs(x) > 1e-9 and abs(x-1.0) > 1e-9: basic = False
                    if basic:
                        idx = col.index(1.0)
                        if idx < num_rest: res_x[j] = tabla[idx][-1]
            
            z_final = tabla[-1][-1]
            if not es_max: z_final *= -1
            return res_x, z_final
        except:
            return None

    # --- UI & LÓGICA ---
    
    # Contenedores visuales
    cont_obj_visual = ft.Row(wrap=True, spacing=5)
    cont_rest_visual = ft.Column(spacing=5)
    leyenda_container = ft.Row(wrap=True, alignment="center")

    chart = ft.LineChart(
        data_series=[], border=ft.border.all(1, "#E0E0E0"),
        min_y=0, min_x=0, expand=True,
        left_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X2"), title_size=15),
        bottom_axis=ft.ChartAxis(labels_size=30, title=ft.Text("X1"), title_size=15),
        tooltip_bgcolor="#263238"
    )

    def dibujar_grafico(restricciones, x1, x2, c, z):
        chart.data_series = []
        leyenda_container.controls = []
        mc = max(x1, x2, 10)
        for r in restricciones:
            a1,a2=r['a']; b=r['b']
            if abs(a1)>0.01: mc = max(mc, b/a1)
            if abs(a2)>0.01: mc = max(mc, b/a2)
        
        lim = mc * 1.2
        chart.max_x = lim
        chart.max_y = lim
        
        cols = [C_AZUL, "#FF9800", "#9C27B0", "#009688"]
        bg_cols = [C_AZUL_BG, "#FFE0B2", "#E1BEE7", "#B2DFDB"]
        
        for i, r in enumerate(restricciones):
            a1, a2 = r['a']; b = r['b']
            pts = []
            if abs(a2)<0.01 and abs(a1)>0.01: pts = [ft.LineChartDataPoint(b/a1,0), ft.LineChartDataPoint(b/a1,lim)]
            elif abs(a1)<0.01 and abs(a2)>0.01: pts = [ft.LineChartDataPoint(0,b/a2), ft.LineChartDataPoint(lim,b/a2)]
            elif abs(a1)>0.01 and abs(a2)>0.01: pts = [ft.LineChartDataPoint(0,b/a2), ft.LineChartDataPoint(b/a1,0)]
            
            if pts:
                chart.data_series.append(ft.LineChartData(data_points=pts, stroke_width=3, color=cols[i%4], curved=False, below_line_bgcolor=bg_cols[i%4]))
                leyenda_container.controls.append(ft.Row([ft.Container(width=10,height=10,bgcolor=cols[i%4]), ft.Text(f"R{r['id']}")], spacing=2))
        
        chart.data_series.append(ft.LineChartData(data_points=[ft.LineChartDataPoint(x1,x2)], stroke_width=0, color=C_ROJO, point=True))
        page.update()

    def calcular(e):
        try:
            txt_err.visible = False
            
            # Leer Objetivo
            c = []
            for inp in inputs_objetivo:
                v = float(inp.value) if inp.value else 0.0
                c.append(v)
            
            # Leer Restricciones
            A = []
            b = []
            signos = []
            datos_graf = []
            max_int = 0
            
            # Recorremos la lista lógica 'filas_restricciones'
            # Cada fila tiene: [Label, Input1, Input2..., Dropdown, Limit]
            # PERO OJO: El Label es Text, Inputs son TextField, Dropdown, Limit es TextField
            
            for i, row in enumerate(filas_restricciones):
                # Los coeficientes son todos los TextField ENTRE el Label y el Dropdown
                # El Label es index 0. Dropdown es index -2. Limit es index -1.
                
                inputs_coef = row[1:-2] 
                coefs = []
                for inp in inputs_coef:
                    v = float(inp.value) if inp.value else 0.0
                    coefs.append(v)
                
                dd = row[-2]
                lim = row[-1]
                signos.append(dd.value)
                
                if i == 0 and sw_slider.value:
                    val_b = slider.value
                    lim.value = str(int(val_b))
                    page.update()
                else:
                    val_b = float(lim.value) if lim.value else 0.0
                
                for co in coefs:
                    if abs(co) > 0.01: max_int = max(max_int, val_b/co)
                
                A.append(coefs)
                b.append(val_b)
                if len(c) == 2: datos_graf.append({'a':coefs, 'b':val_b, 'id':i+1})
            
            if slider.max < max_int: slider.max = max(100, max_int*1.5)
            
            es_max = dd_obj.value == "Maximizar"
            res = resolver_simplex(c, A, b, signos, es_max)
            
            if res:
                sx, sz = res
                panel_res.bgcolor = C_VERDE_BG
                panel_res.border = ft.border.all(1, C_VERDE)
                txt_z.value = f"Z = {sz:.2f}"
                txt_z.color = C_VERDE
                txt_vars.value = " | ".join([f"X{k+1}={v:.2f}" for k,v in enumerate(sx)])
                
                if len(c) == 2:
                    dibujar_grafico(datos_graf, sx[0], sx[1], c, sz)
                    cont_graf.visible = True
                else:
                    cont_graf.visible = False
            else:
                panel_res.bgcolor = C_ROJO_BG
                panel_res.border = ft.border.all(1, C_ROJO)
                txt_z.value = "Sin Solución"
                txt_z.color = C_ROJO
                txt_vars.value = "No Factible"
                cont_graf.visible = False
                
        except Exception as ex:
            txt_err.value = str(ex)
            txt_err.visible = True
        page.update()

    # --- BOTONES DE ACCIÓN ---
    
    def add_var_click(e):
        idx = len(inputs_objetivo) + 1
        
        # 1. Input Objetivo
        new_inp_obj = ft.TextField(label=f"C{idx}", width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
        inputs_objetivo.append(new_inp_obj)
        cont_obj_visual.controls.append(new_inp_obj)
        
        # 2. Input en cada Restricción existente
        for row in filas_restricciones:
            # Insertar antes del dropdown (index -2)
            new_inp_rest = ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
            row.insert(len(row)-2, new_inp_rest)
            
            # Actualizar visualmente el Row contenedor
            # El contenedor visual asociado a esta fila es difícil de rastrear si no guardamos referencia.
            # TRUCO: Reconstruimos la fila visual en el contenedor correspondiente.
            # Pero para hacerlo fácil con Flet, es mejor insertar en la lista de controles del Row visual.
            pass 
        
        # Sincronización visual forzada (recorremos los contenedores visuales)
        for container in cont_rest_visual.controls:
            row_control = container.content # Es un ft.Row
            new_vis_inp = ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
            # Insertar antes del dropdown (que es el penultimo control visual)
            row_control.controls.insert(len(row_control.controls)-2, new_vis_inp)

        page.update()

    def add_rest_click(e):
        idx = len(filas_restricciones) + 1
        
        # Crear lista lógica de controles para esta fila
        row_controls = []
        row_controls.append(ft.Text(f"R{idx}", weight="bold")) # Label
        
        # Inputs para variables actuales
        for _ in inputs_objetivo:
            row_controls.append(ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
            
        row_controls.append(ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=60, bgcolor=C_GRIS, content_padding=5, on_change=calcular))
        row_controls.append(ft.TextField(width=70, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
        
        # Guardar en lista lógica
        filas_restricciones.append(row_controls)
        
        # Agregar a visual
        bg = C_AZUL_BG if (idx==1 and sw_slider.value) else "transparent"
        cont_rest_visual.controls.append(ft.Container(content=ft.Row(row_controls, wrap=True, alignment="center"), bgcolor=bg, padding=5, border_radius=5))
        
        page.update()

    def reset_click(e):
        # Limpiar Listas Lógicas
        inputs_objetivo.clear()
        filas_restricciones.clear()
        
        # Limpiar Visuales
        cont_obj_visual.controls.clear()
        cont_rest_visual.controls.clear()
        
        # Reiniciar Estado Base (2 vars, 2 rest)
        iniciar_app() # Función auxiliar sin update
        
        # Resetear resultados
        txt_z.value = "Z: ---"
        txt_vars.value = "..."
        panel_res.bgcolor = C_GRIS
        panel_res.border = None
        cont_graf.visible = False
        
        page.update()

    # --- INICIALIZACIÓN (Función auxiliar) ---
    def iniciar_app():
        # Crear 2 Variables
        for i in range(2):
            inp = ft.TextField(label=f"C{i+1}", width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular)
            inputs_objetivo.append(inp)
            cont_obj_visual.controls.append(inp)
            
        # Crear 2 Restricciones
        for i in range(2):
            row = []
            row.append(ft.Text(f"R{i+1}", weight="bold"))
            for _ in range(2): 
                row.append(ft.TextField(width=70, keyboard_type="number", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
            row.append(ft.Dropdown(options=[ft.dropdown.Option("≤"), ft.dropdown.Option("≥"), ft.dropdown.Option("=")], value="≤", width=60, bgcolor=C_GRIS, content_padding=5, on_change=calcular))
            row.append(ft.TextField(width=70, keyboard_type="number", hint_text="Lim", bgcolor=C_BLANCO, content_padding=5, on_change=calcular))
            
            filas_restricciones.append(row)
            bg = C_AZUL_BG if i==0 else "transparent"
            cont_rest_visual.controls.append(ft.Container(content=ft.Row(row, wrap=True, alignment="center"), bgcolor=bg, padding=5, border_radius=5))

    # --- COMPONENTES FIJOS ---
    dd_obj = ft.Dropdown(options=[ft.dropdown.Option("Maximizar"), ft.dropdown.Option("Minimizar")], value="Maximizar", width=140, bgcolor=C_BLANCO, on_change=calcular)
    
    slider = ft.Slider(min=0, max=500, value=100, divisions=100, active_color=C_AZUL, on_change=calcular)
    sw_slider = ft.Switch(value=True, active_color=C_AZUL, on_change=calcular)
    
    panel_res = ft.Container(content=ft.Column([
        txt_z := ft.Text("Z: ---", size=24, weight="bold"),
        txt_vars := ft.Text("...", size=14)
    ], horizontal_alignment="center"), padding=15, border_radius=10, bgcolor=C_GRIS, width=350)
    
    cont_graf = ft.Container(content=ft.Column([
        ft.Text("Gráfico", weight="bold"), leyenda_container,
        ft.Container(chart, height=350, width=350)
    ], horizontal_alignment="center"), padding=10, border=ft.border.all(1, "#E0E0E0"), border_radius=10, visible=False, bgcolor=C_BLANCO)
    
    txt_err = ft.Text("", color=C_ROJO, visible=False)

    # --- EJECUCIÓN INICIAL ---
    iniciar_app() # Llenamos las listas ANTES de agregar a Page
    
    page.add(ft.Column([
        ft.Row([ft.Text("Solver Master Pro", size=26, weight="bold", color=C_AZUL),
                ft.IconButton(ft.icons.DELETE_FOREVER, icon_color=C_ROJO, on_click=reset_click)], alignment="spaceBetween"),
        ft.Row([dd_obj, ft.ElevatedButton("+Var", on_click=add_var_click, bgcolor=C_AZUL, color=C_BLANCO)], alignment="spaceBetween"),
        ft.Container(cont_obj_visual, padding=5),
        ft.Row([ft.Text("Restricciones", weight="bold"), ft.ElevatedButton("+Rest", on_click=add_rest_click)], alignment="spaceBetween"),
        cont_rest_visual,
        ft.Divider(),
        ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.icons.TOUCH_APP, color=C_AZUL), ft.Text("Análisis R1", color=C_AZUL, weight="bold")]),
            ft.Row([sw_slider, ft.Container(slider, expand=True)], alignment="spaceBetween")
        ]), bgcolor=C_AZUL_BG, padding=10, border_radius=10),
        ft.Divider(),
        ft.Container(panel_res, alignment=ft.alignment.center),
        txt_err, cont_graf
    ], scroll="adaptive"))

ft.app(target=main)

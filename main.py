import flet as ft
import traceback

def main(page: ft.Page):
    try:
        # --- AQUÍ EMPIEZA TU APP REAL ---
        
        # 1. Configuración básica
        page.title = "Solver Pro Mobile"
        page.theme_mode = "light"
        page.scroll = "adaptive"
        page.window_width = 380
        page.window_height = 800
        
        # 2. Verificar si hay rastros de librerías prohibidas
        # (Esto no debería fallar si requirements.txt está limpio, pero por si acaso)
        import math
        
        # 3. Interfaz Simple para probar que Flet funciona
        titel = ft.Text("¡La App Funciona!", size=30, weight="bold", color="blue")
        subtitel = ft.Text("Si ves esto, el problema eran las librerías antiguas.", size=16)
        
        # --- CÓDIGO DEL SOLVER (Simplificado para evitar errores ocultos) ---
        # Si esto funciona, iremos agregando la complejidad poco a poco.
        
        def resolver(e):
             txt_res.value = "Calculando..."
             page.update()
        
        btn = ft.ElevatedButton("Probar Botón", on_click=resolver)
        txt_res = ft.Text("Esperando acción...")

        page.add(
            ft.Column([
                titel,
                subtitel,
                ft.Divider(),
                btn,
                txt_res
            ], alignment="center", horizontal_alignment="center")
        )
        
        # --- FIN DE TU APP REAL ---

    except Exception:
        # SI ALGO FALLA, ESTO TE LO MOSTRARÁ EN PANTALLA
        page.add(
            ft.Column([
                ft.Text("⚠️ ERROR CRÍTICO ⚠️", color="red", size=30, weight="bold"),
                ft.Text("Por favor envía foto de este error:", color="black"),
                ft.Container(
                    content=ft.Text(traceback.format_exc(), color="red", size=12, selectable=True),
                    bgcolor="#FFEBEE",
                    padding=10,
                    border_radius=5
                )
            ])
        )

ft.app(target=main)

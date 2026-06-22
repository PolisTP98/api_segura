import os
import requests
import time

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "api_key_temporal_super_secreta")

headers = {
    "x-api-key": API_KEY, 
    "Content-Type": "application/json"
}

def post_data(endpoint, data, context_name = ""):
    url = f"{API_URL}{endpoint}"
    response = requests.post(url, json = data, headers = headers)
    
    if response.status_code in [200, 201]:
        print(f"Creado ({context_name}): {data.get('nombre') or data.get('email') or 'Relación exitosa'}")
        return response.json()
    else:
        print(f"Error al crear ({context_name}) '{data.get('nombre') or data.get('email')}': {response.status_code} - {response.text}")
        return None

def poblar_base_de_datos():
    admin_data = {
        "nombre_completo": "Isaac Abdiel Sánchez López", 
        "email": "admin@littlecaesars.com", 
        "contrasena": "$2b$12$K1qR8yWv7MxZ9pB4V3L2e.O6uY0Gf5sHwI8nS3mXzR1oP2qR3sT4u", 
        "es_admin": True
    }
    
    post_data("/api/usuarios", admin_data, "Admin")
    
    login_resp = requests.post(
        f"{API_URL}/login", 
        json = {"email": admin_data["email"], "contrasena": admin_data["contrasena"]}, 
        headers = {"x-api-key": API_KEY}
    )
    if login_resp.status_code == 200:
        token = login_resp.json()["access_token"]
        headers["Authorization"] = f"Bearer {token}"
        print("\nToken obtenido correctamente, permisos de escritura concedidos")
    else:
        print("\nError de autenticación")
        return

    ids = {
        "unidades": {}, "categorias": {}, "ingredientes": {}, "productos": {}, "combos": {}
    }

    unidades = ["Gramo (g)", "Mililitro (ml)", "Pieza (pz)"]
    for u in unidades:
        res = post_data("/api/unidades", {"nombre": u}, "Unidad")
        if res: ids["unidades"][u] = res["id_unidad_medida"]

    categorias = ["Pizzas clásicas", "Especialidades", "Complementos", "Bebidas"]
    for c in categorias:
        res = post_data("/api/categorias", {"nombre": c}, "Categoría")
        if res: ids["categorias"][c] = res["id_categoria"]

    ingredientes = [
        ("Masa fresca", "Gramo (g)"), 
        ("Salsa de tomate", "Gramo (g)"), 
        ("Queso mozzarella", "Gramo (g)"), 
        ("Pepperoni", "Pieza (pz)"), 
        ("Pimiento", "Gramo (g)"), 
        ("Mantequilla de ajo", "Mililitro (ml)"), 
        ("Queso parmesano", "Gramo (g)"), 
        ("Refresco de cola", "Mililitro (ml)")
    ]
    for nombre, unidad in ingredientes:
        id_unidad = ids["unidades"].get(unidad)
        if id_unidad:
            res = post_data("/api/ingredientes", {"id_unidad_medida": id_unidad, "nombre": nombre}, "Ingrediente")
            if res: ids["ingredientes"][nombre] = res["id_ingrediente"]

    productos = [
        ("Hot-N-Ready Pepperoni", "Pizzas clásicas", "La clásica pizza de pepperoni lista para llevar."), 
        ("Hula Hawaiian", "Especialidades", "Pizza con jamón y piña."), 
        ("Crazy Bread", "Complementos", "8 piezas de pan recién horneado con mantequilla de ajo y parmesano."), 
        ("Refresco familiar 2L", "Bebidas", "Refresco de cola de 2 litros.")
    ]
    for nombre, cat, desc in productos:
        id_cat = ids["categorias"].get(cat)
        if id_cat:
            res = post_data("/api/productos", {"id_categoria": id_cat, "nombre": nombre, "descripcion": desc}, "Producto")
            if res: ids["productos"][nombre] = res["id_producto"]

    recetas = [
        ("Hot-N-Ready Pepperoni", "Masa fresca", 350.00), 
        ("Hot-N-Ready Pepperoni", "Salsa de tomate", 100.00), 
        ("Hot-N-Ready Pepperoni", "Queso mozzarella", 200.00), 
        ("Hot-N-Ready Pepperoni", "Pepperoni", 30.00), 
        
        ("Crazy Bread", "Masa fresca", 200.00), 
        ("Crazy Bread", "Mantequilla de ajo", 50.00), 
        ("Crazy Bread", "Queso parmesano", 25.00), 
        
        ("Refresco familiar 2L", "Refresco de cola", 2000.00)
    ]
    print("\nInyectando recetas (Productos -> Ingredientes)...")
    for prod, ing, cant in recetas:
        id_p = ids["productos"].get(prod)
        id_p = ids["productos"].get(prod)
        id_i = ids["ingredientes"].get(ing)
        if id_p and id_i:
            post_data("/api/productos/ingredientes", {
                "id_producto": id_p, 
                "id_ingrediente": id_i, 
                "cantidad": cant
            }, "Receta")

    combos = [
        ("Combo clásico HNR", "1 Pizza Hot-N-Ready Pepperoni + 1 Crazy Bread + Refresco 2L")
    ]
    for nombre, desc in combos:
        res = post_data("/api/combos", {"nombre": nombre, "descripcion": desc}, "Combo")
        if res: ids["combos"][nombre] = res["id_combo"]

    asignaciones_combos = [
        ("Combo clásico HNR", "Hot-N-Ready Pepperoni", 1), 
        ("Combo clásico HNR", "Crazy Bread", 1), 
        ("Combo clásico HNR", "Refresco familiar 2L", 1)
    ]
    for combo, prod, cant in asignaciones_combos:
        id_c = ids["combos"].get(combo)
        id_p = ids["productos"].get(prod)
        if id_c and id_p:
            post_data("/api/combos/productos", {
                "id_combo": id_c, 
                "id_producto": id_p, 
                "cantidad": cant
            }, "Producto -> Combo")
    print("\nBase de datos poblada exitosamente")

if __name__ == "__main__":
    print("Esperando a que el backend esté listo en la red...")
    time.sleep(5)
    poblar_base_de_datos()
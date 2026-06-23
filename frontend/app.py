import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, session
import jwt

load_dotenv()

app = Flask(__name__)


# ----------------------------------
# | CONFIGURACIÓN DE VARIABLES     |
# ----------------------------------

app.secret_key = os.getenv("FRONTEND_SECRET_KEY", "frontend_key_temporal_super_secreta")
API_KEY = os.getenv("API_KEY", "api_key_temporal_super_secreta")
API_URL = os.getenv("API_URL", "http://localhost:8000")

def construir_headers():
    # CONSTRUYE LOS HEADERS REQUERIDOS POR LA API (API KEY Y JWT)
    headers = {
        "x-api-key": API_KEY
    }
    token = session.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers

def llamar_api(method, endpoint, json = None):
    # FUNCIÓN GENÉRICA PARA HACER PETICIONES AL BACKEND
    url = f"{API_URL}{endpoint}"
    try:
        respuesta = requests.request(
            method = method, 
            url = url, 
            headers = construir_headers(), 
            json = json, 
            timeout = 5
        )
        try:
            contenido = respuesta.json()
        except ValueError:
            contenido = respuesta.text
        return {
            "ok": respuesta.ok, 
            "status_code": respuesta.status_code, 
            "url": url, 
            "data": contenido
        }
    except requests.RequestException as error:
        return {
            "ok": False, 
            "status_code": None, 
            "url": url, 
            "data": {"error": "No se pudo conectar con la API", "detail": str(error)}
        }


# ----------------------------
# | RUTA PRINCIPAL DE LA APP |
# ----------------------------

@app.route("/", methods = ["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        accion = request.form.get("accion")
        
        # LÓGICA DE AUTENTICACIÓN
        if accion == "login":
            email = request.form.get("email")
            contrasena = request.form.get("contrasena")
            resultado = llamar_api("POST", "/login", json = {"email": email, "contrasena": contrasena})
            if resultado["ok"]:
                token = resultado["data"].get("access_token")
                session["access_token"] = token
                try:
                    payload = jwt.decode(token, options = {"verify_signature": False})
                    session["usuario"] = {
                        "id": payload.get("sub"),
                        "email": payload.get("email"),
                        "es_admin": payload.get("es_admin")
                    }
                except Exception:
                    pass
        elif accion == "logout":
            session.pop("access_token", None)
            session.pop("usuario", None)
            resultado = {"ok": True, "status_code": 200, "data": {"message": "Sesión cerrada correctamente"}}
            
        # USUARIOS
        elif accion == "crear_usuario":
            datos = {
                "nombre_completo": request.form.get("nombre_completo"),
                "email": request.form.get("email"),
                "contrasena": request.form.get("contrasena"),
                "es_admin": request.form.get("es_admin") == "true"
            }
            resultado = llamar_api("POST", "/api/usuarios", json = datos)
        elif accion == "consultar_usuario":
            id_usuario = request.form.get("id_usuario")
            resultado = llamar_api("GET", f"/api/usuarios/{id_usuario}")
            
        # CATEGORÍAS E INGREDIENTES
        elif accion == "listar_categorias":
            resultado = llamar_api("GET", "/api/categorias")
        elif accion == "crear_categoria":
            nombre = request.form.get("nombre_categoria")
            resultado = llamar_api("POST", "/api/categorias", json = {"nombre": nombre})
        elif accion == "crear_ingrediente":
            datos = {
                "nombre": request.form.get("nombre_ingrediente"),
                "id_unidad_medida": int(request.form.get("id_unidad_medida"))
            }
            resultado = llamar_api("POST", "/api/ingredientes", json = datos)
            
        # PRODUCTOS
        elif accion == "listar_productos":
            resultado = llamar_api("GET", "/api/productos")
        elif accion == "crear_producto":
            datos = {
                "id_categoria": int(request.form.get("id_categoria")),
                "nombre": request.form.get("nombre_producto"),
                "descripcion": request.form.get("descripcion_producto") or None
            }
            resultado = llamar_api("POST", "/api/productos", json = datos)
        elif accion == "asignar_ingrediente":
            datos = {
                "id_producto": int(request.form.get("id_producto")),
                "id_ingrediente": int(request.form.get("id_ingrediente")),
                "cantidad": float(request.form.get("cantidad"))
            }
            resultado = llamar_api("POST", "/api/productos/ingredientes", json = datos)
            
        # COMBOS
        elif accion == "listar_combos":
            resultado = llamar_api("GET", "/api/combos")
        elif accion == "crear_combo":
            datos = {
                "nombre": request.form.get("nombre_combo"),
                "descripcion": request.form.get("descripcion_combo") or None
            }
            resultado = llamar_api("POST", "/api/combos", json = datos)
        elif accion == "agregar_producto_combo":
            datos = {
                "id_combo": int(request.form.get("id_combo")),
                "id_producto": int(request.form.get("id_producto")),
                "cantidad": int(request.form.get("cantidad_producto_combo"))
            }
            resultado = llamar_api("POST", "/api/combos/productos", json = datos)

    # OBTENCIÓN AUTOMÁTICA DE LISTAS DE REFERENCIA PARA SELECTORES FLUIDOS
    categorias = []
    productos = []
    ingredientes = []
    combos = []
    unidades = []
    
    if session.get("access_token"):
        res_cat = llamar_api("GET", "/api/categorias")
        if res_cat["ok"]: categorias = res_cat["data"]
        
        res_prod = llamar_api("GET", "/api/productos")
        if res_prod["ok"]: productos = res_prod["data"]
        
        res_ing = llamar_api("GET", "/api/ingredientes")
        if res_ing["ok"]: ingredientes = res_ing["data"]
            
        res_comb = llamar_api("GET", "/api/combos")
        if res_comb["ok"]: combos = res_comb["data"]
            
        res_unid = llamar_api("GET", "/api/unidades")
        if res_unid["ok"]: unidades = res_unid["data"]

    return render_template(
        "index.html", 
        usuario = session.get("usuario"), 
        token = session.get("access_token"), 
        resultado = resultado, 
        api_url = API_URL,
        categorias = categorias,
        productos = productos,
        ingredientes = ingredientes,
        combos = combos,
        unidades = unidades
    )

if __name__ == "__main__":
    app.run(host = "0.0.0.0", port = 9000, debug = True)
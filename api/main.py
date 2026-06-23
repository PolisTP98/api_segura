import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import bcrypt
from dotenv import load_dotenv
from jose import JWTError, jwt
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.orm import Session

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware

import json

from database import get_db
from models import(
    Usuario, UnidadMedida, Ingrediente, CategoriaProducto, 
    Producto, ProductoIngrediente, Combo, ComboProducto
)

load_dotenv()


# --------------------------------------------------------------
# | CONFIGURACIÓN DE RESPUESTA JSON PARA CARACTERES EN ESPAÑOL |
# --------------------------------------------------------------

class NativeJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content, 
            ensure_ascii = False, 
            allow_nan = False, 
            indent = None, 
            separators = (",", ":"),
        ).encode("utf-8")

app = FastAPI(
    title = "API de Little Caesars", 
    description = "API segura con API Key, JWT, RBAC, protección BOLA/IDOR y Rate Limiting", 
    version = "1.0.0", 
    default_response_class = NativeJSONResponse
)


# ----------------------------------
# | CONFIGURACIÓN DE RATE LIMITING |
# ----------------------------------

limiter = Limiter(key_func = get_remote_address, default_limits = ["100/minute"], storage_uri = "memory://")
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

@app.exception_handler(RateLimitExceeded)
def rate_limit_handler(request: Request, exceeded: RateLimitExceeded):
    return JSONResponse(
        status_code = 429, 
        content = {"error": "Demasiadas solicitudes", "message": "Has excedido el límite permitido"}
    )


# --------------------------
# | VARIABLES DE SEGURIDAD |
# --------------------------

API_KEY_VALIDA = os.getenv("API_KEY", "api_key_temporal_super_secreta")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_key_temporal_super_secreta")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

bearer_scheme = HTTPBearer(auto_error = False)


# ---------------------------------------------
# | ESQUEMAS PYDANTIC (Data Transfer Objects) |
# ---------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    contrasena: str

class UsuarioCreate(BaseModel):
    nombre_completo: str
    email: EmailStr
    contrasena: str
    es_admin: bool = False

class UsuarioOut(BaseModel):
    id_usuario: int
    nombre_completo: str
    email: str
    es_admin: bool
    model_config = ConfigDict(from_attributes = True)

class UnidadMedidaSchema(BaseModel):
    nombre: str

class UnidadMedidaOut(UnidadMedidaSchema):
    id_unidad_medida: int
    model_config = ConfigDict(from_attributes = True)

class IngredienteSchema(BaseModel):
    id_unidad_medida: int
    nombre: str

class IngredienteOut(IngredienteSchema):
    id_ingrediente: int
    model_config = ConfigDict(from_attributes = True)

class CategoriaProductoSchema(BaseModel):
    nombre: str

class CategoriaProductoOut(CategoriaProductoSchema):
    id_categoria: int
    model_config = ConfigDict(from_attributes = True)

class ProductoSchema(BaseModel):
    id_categoria: int
    nombre: str
    descripcion: Optional[str] = None

class ProductoOut(ProductoSchema):
    id_producto: int
    model_config = ConfigDict(from_attributes = True)

class ProductoIngredienteSchema(BaseModel):
    id_producto: int
    id_ingrediente: int
    cantidad: float

class ComboSchema(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ComboOut(ComboSchema):
    id_combo: int
    model_config = ConfigDict(from_attributes = True)

class ComboProductoSchema(BaseModel):
    id_combo: int
    id_producto: int
    cantidad: int


# ------------------------------------------
# | DEPENDENCIAS DE SEGURIDAD Y UTILIDADES |
# ------------------------------------------

def validar_api_key(x_api_key: Optional[str] = Header(default = None, alias = "x-api-key")):
    if x_api_key != API_KEY_VALIDA:
        raise HTTPException(status_code = 401, detail = "API Key inválida o no enviada")
    return True

def obtener_hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verificar_contrasena(contrasena_plana: str, hash_contrasena: str) -> bool:
    if isinstance(hash_conn_str := hash_contrasena, bytes):
        hash_conn_str = hash_contrasena.decode("utf-8")
    hash_corregido = hash_conn_str.replace("$2y$", "$2b$")
    return bcrypt.checkpw(
        contrasena_plana.encode("utf-8"), 
        hash_corregido.encode("utf-8")
    )

def crear_token(usuario: Usuario):
    expiracion = datetime.now(timezone.utc) + timedelta(minutes = ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(usuario.id_usuario), 
        "email": usuario.email, 
        "es_admin": usuario.es_admin, 
        "exp": expiracion
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm = JWT_ALGORITHM)

def obtener_usuario_actual(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
):
    if credentials is None:
        raise HTTPException(status_code = 401, detail = "Token JWT no enviado")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms = [JWT_ALGORITHM])
        id_usuario = payload.get("sub")
        if id_usuario is None:
            raise HTTPException(status_code = 401, detail = "Token inválido")
    except JWTError:
        raise HTTPException(status_code = 401, detail = "El token es inválido o expiró")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == int(id_usuario)).first()
    if not usuario:
        raise HTTPException(status_code = 401, detail = "Usuario no encontrado")
    return usuario

def requiere_admin(usuario_actual: Usuario = Depends(obtener_usuario_actual)):
    # RBAC: VERIFICA SI EL USUARIO TIENE PRIVILEGIOS DE ADMINISTRADOR
    if not usuario_actual.es_admin:
        raise HTTPException(status_code = 403, detail = "Requiere privilegios de administrador")
    return usuario_actual


# ------------------------------
# | ENDPOINTS DE AUTENTICACIÓN |
# ------------------------------

@app.post("/login", tags = ["Autenticación"])
@limiter.limit("5/minute")
def login(request: Request, datos_login: LoginRequest, api_key: bool = Depends(validar_api_key), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == datos_login.email).first()
    if not usuario or not verificar_contrasena(datos_login.contrasena, usuario.contrasena):
        raise HTTPException(status_code = 401, detail = "Credenciales inválidas")
    return {"access_token": crear_token(usuario), "token_type": "bearer"}


# ------------------------------------------------
# | ENDPOINTS DE USUARIOS (BOLA/IDOR PROTECTION) |
# ------------------------------------------------

@app.post("/api/usuarios", response_model = UsuarioOut, tags = ["Usuarios"])
@limiter.limit("10/minute")
def crear_usuario(
    request: Request, 
    user_in: UsuarioCreate, 
    admin: Usuario = Depends(requiere_admin), 
    api_key: bool = Depends(validar_api_key), 
    db: Session = Depends(get_db)
):
    if db.query(Usuario).filter(Usuario.email == user_in.email).first():
        raise HTTPException(status_code = 400, detail = "El email ya está registrado")
    nuevo_usuario = Usuario(
        nombre_completo = user_in.nombre_completo, 
        email = user_in.email, 
        contrasena = obtener_hash_contrasena(user_in.contrasena), 
        es_admin = user_in.es_admin
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario

@app.get("/api/usuarios/{id_usuario}", response_model = UsuarioOut, tags = ["Usuarios"])
@limiter.limit("30/minute")
def obtener_usuario(
    request: Request, id_usuario: int, 
    api_key: bool = Depends(validar_api_key), 
    usuario_actual: Usuario = Depends(obtener_usuario_actual), 
    db: Session = Depends(get_db)
):
    # PROTECCIÓN BOLA/IDOR: UN USUARIO NO ADMIN SOLO PUEDE VERSE A SÍ MISMO
    if not usuario_actual.es_admin and usuario_actual.id_usuario != id_usuario:
        raise HTTPException(status_code = 403, detail = "Acceso denegado: No puedes consultar datos de otro usuario")
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code = 404, detail = "Usuario no encontrado")
    return usuario

@app.delete("/api/usuarios/{id_usuario}", tags = ["Usuarios"])
def eliminar_usuario(id_usuario: int, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code = 404, detail = "Usuario no encontrado")
    db.delete(usuario)
    db.commit()
    return {"message": "Usuario eliminado"}


# ---------------------------------------------------------------------------------------
# | ENDPOINTS DE TABLAS DE TIPO CATÁLOGO (UnidadMedida, CategoriaProducto, Ingrediente) |
# ---------------------------------------------------------------------------------------

# LECTURA: USUARIOS AUTENTICADOS | ESCRITURA: ADMINISTRADORES
@app.get("/api/categorias", response_model = List[CategoriaProductoOut], tags = ["Categorías"])
def obtener_categorias(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    return db.query(CategoriaProducto).all()

@app.post("/api/categorias", response_model = CategoriaProductoOut, tags = ["Categorías"])
def crear_categoria(categoria_producto_in: CategoriaProductoSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    nueva_categoria_producto = CategoriaProducto(**categoria_producto_in.model_dump())
    db.add(nueva_categoria_producto)
    db.commit()
    db.refresh(nueva_categoria_producto)
    return nueva_categoria_producto

@app.get("/api/unidades", response_model = List[UnidadMedidaOut], tags = ["Unidades de medida"])
def obtener_unidades(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    return db.query(UnidadMedida).all()

@app.post("/api/unidades", response_model = UnidadMedidaOut, tags = ["Unidades de medida"])
def crear_unidad(unidad_medida_in: UnidadMedidaSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    nueva_unidad_medida = UnidadMedida(**unidad_medida_in.model_dump())
    db.add(nueva_unidad_medida)
    db.commit()
    db.refresh(nueva_unidad_medida)
    return nueva_unidad_medida

@app.get("/api/ingredientes", response_model = List[IngredienteOut], tags = ["Ingredientes"])
def obtener_ingredientes(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    return db.query(Ingrediente).all()

@app.post("/api/ingredientes", response_model = IngredienteOut, tags = ["Ingredientes"])
def crear_ingrediente(ingrediente_in: IngredienteSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    nuevo_ingrediente = Ingrediente(**ingrediente_in.model_dump())
    db.add(nuevo_ingrediente)
    db.commit()
    db.refresh(nuevo_ingrediente)
    return nuevo_ingrediente


# --------------------------
# | ENDPOINTS DE PRODUCTOS |
# --------------------------

@app.get("/api/productos", response_model = List[ProductoOut], tags = ["Productos"])
def obtener_productos(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    return db.query(Producto).all()

@app.post("/api/productos", response_model = ProductoOut, tags = ["Productos"])
def crear_producto(producto_in: ProductoSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    nuevo_producto = Producto(**producto_in.model_dump())
    db.add(nuevo_producto)
    db.commit()
    db.refresh(nuevo_producto)
    return nuevo_producto

@app.delete("/api/productos/{id_producto}", tags = ["Productos"])
def eliminar_producto(id_producto: int, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    producto = db.query(Producto).filter(Producto.id_producto == id_producto).first()
    if not producto:
        raise HTTPException(status_code = 404, detail = "Producto no encontrado")
    db.delete(producto)
    db.commit()
    return {"message": "Producto eliminado"}

@app.post("/api/productos/ingredientes", tags = ["Productos"])
def agregar_ingrediente_a_producto(
    producto_ingrediente_in: ProductoIngredienteSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)
):
    nuevo_producto_ingrediente = ProductoIngrediente(**producto_ingrediente_in.model_dump())
    db.add(nuevo_producto_ingrediente)
    db.commit()
    return {"message": "Ingrediente asignado al producto"}


# -----------------------
# | ENDPOINTS DE COMBOS |
# -----------------------

@app.get("/api/combos", response_model = List[ComboOut], tags = ["Combos"])
def obtener_combos(usuario: Usuario = Depends(obtener_usuario_actual), db: Session = Depends(get_db)):
    return db.query(Combo).all()

@app.post("/api/combos", response_model = ComboOut, tags = ["Combos"])
def crear_combo(combo_in: ComboSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)):
    nuevo_combo = Combo(**combo_in.model_dump())
    db.add(nuevo_combo)
    db.commit()
    db.refresh(nuevo_combo)
    return nuevo_combo

@app.post("/api/combos/productos", tags = ["Combos"])
def agregar_producto_a_combo(
    combo_producto_in: ComboProductoSchema, admin: Usuario = Depends(requiere_admin), db: Session = Depends(get_db)
):
    nuevo_combo_producto = ComboProducto(**combo_producto_in.model_dump())
    db.add(nuevo_combo_producto)
    db.commit()
    return {"message": "Producto agregado al combo"}
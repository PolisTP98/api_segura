import os
import sys
import time
import bcrypt

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "api"))

from api.database import SessionLocal
from api.models import (
    Usuario, UnidadMedida, CategoriaProducto, Ingrediente, 
    Producto, ProductoIngrediente, Combo, ComboProducto
)

SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "superadmin_password_temporal_super_secreta")

def obtener_hash_contrasena(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def poblar_base_de_datos():
    db = SessionLocal()
    try:
        print("Iniciando la inserción directa de datos en la base de datos...")

        # 1) CREAR USUARIO ADMINISTRADOR
        admin_data = {
            "nombre_completo": "Isaac Abdiel Sánchez López", 
            "email": "admin@littlecaesars.com", 
            "contrasena": SUPERADMIN_PASSWORD, 
            "es_admin": True
        }
        
        admin_existente = db.query(Usuario).filter(Usuario.email == admin_data["email"]).first()
        if not admin_existente:
            password_hash = obtener_hash_contrasena(admin_data["contrasena"])
            nuevo_admin = Usuario(
                nombre_completo = admin_data["nombre_completo"], 
                email = admin_data["email"], 
                contrasena = password_hash, 
                es_admin = admin_data["es_admin"]
            )
            db.add(nuevo_admin)
            db.commit()
        
        ids = {
            "unidades": {}, "categorias": {}, "ingredientes": {}, "productos": {}, "combos": {}
        }

        # 2) UNIDADES DE MEDIDA
        unidades = ["Gramo (g)", "Mililitro (ml)", "Pieza (pz)"]
        for u in unidades:
            u_existente = db.query(UnidadMedida).filter(UnidadMedida.nombre == u).first()
            if not u_existente:
                nueva_unidad = UnidadMedida(nombre=u)
                db.add(nueva_unidad)
                db.commit()
                db.refresh(nueva_unidad)
                ids["unidades"][u] = nueva_unidad.id_unidad_medida
            else:
                ids["unidades"][u] = u_existente.id_unidad_medida

        # 3) CATEGORÍAS
        categorias = ["Pizzas clásicas", "Especialidades", "Complementos", "Bebidas"]
        for c in categorias:
            c_existente = db.query(CategoriaProducto).filter(CategoriaProducto.nombre == c).first()
            if not c_existente:
                nueva_cat = CategoriaProducto(nombre=c)
                db.add(nueva_cat)
                db.commit()
                db.refresh(nueva_cat)
                ids["categorias"][c] = nueva_cat.id_categoria
            else:
                ids["categorias"][c] = c_existente.id_categoria

        # 4) INGREDIENTES
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
                ing_existente = db.query(Ingrediente).filter(Ingrediente.nombre == nombre).first()
                if not ing_existente:
                    nuevo_ing = Ingrediente(id_unidad_medida=id_unidad, nombre=nombre)
                    db.add(nuevo_ing)
                    db.commit()
                    db.refresh(nuevo_ing)
                    ids["ingredientes"][nombre] = nuevo_ing.id_ingrediente
                else:
                    ids["ingredientes"][nombre] = ing_existente.id_ingrediente

        # 5) PRODUCTOS
        productos = [
            ("Hot-N-Ready Pepperoni", "Pizzas clásicas", "La clásica pizza de pepperoni lista para llevar"), 
            ("Hula Hawaiian", "Especialidades", "Pizza con jamón y piña"), 
            ("Crazy Bread", "Complementos", "8 piezas de pan recién horneado con mantequilla de ajo y parmesano"), 
            ("Refresco familiar 2l", "Bebidas", "Refresco de cola de 2 litros")
        ]
        for nombre, cat, desc in productos:
            id_cat = ids["categorias"].get(cat)
            if id_cat:
                prod_existente = db.query(Producto).filter(Producto.nombre == nombre).first()
                if not prod_existente:
                    nuevo_prod = Producto(id_categoria=id_cat, nombre=nombre, descripcion=desc)
                    db.add(nuevo_prod)
                    db.commit()
                    db.refresh(nuevo_prod)
                    ids["productos"][nombre] = nuevo_prod.id_producto
                else:
                    ids["productos"][nombre] = prod_existente.id_producto

        # 6) RECETAS (PRODUCTOS -> INGREDIENTES)
        recetas = [
            ("Hot-N-Ready Pepperoni", "Masa fresca", 350.00), 
            ("Hot-N-Ready Pepperoni", "Salsa de tomate", 100.00), 
            ("Hot-N-Ready Pepperoni", "Queso mozzarella", 200.00), 
            ("Hot-N-Ready Pepperoni", "Pepperoni", 30.00), 
            
            ("Crazy Bread", "Masa fresca", 200.00), 
            ("Crazy Bread", "Mantequilla de ajo", 50.00), 
            ("Crazy Bread", "Queso parmesano", 25.00), 
            
            ("Refresco familiar 2l", "Refresco de cola", 2000.00)
        ]
        print("\nInyectando recetas (Productos -> Ingredientes)...")
        for prod, ing, cant in recetas:
            id_p = ids["productos"].get(prod)
            id_i = ids["ingredientes"].get(ing)
            if id_p and id_i:
                receta_existente = db.query(ProductoIngrediente).filter(
                    ProductoIngrediente.id_producto == id_p,
                    ProductoIngrediente.id_ingrediente == id_i
                ).first()
                if not receta_existente:
                    nueva_receta = ProductoIngrediente(id_producto=id_p, id_ingrediente=id_i, cantidad=cant)
                    db.add(nueva_receta)
        db.commit()

        # 7) NOMBRES DE COMBOS
        combos = [
            ("Combo clásico HNR", "1 Pizza Hot-N-Ready Pepperoni + 1 Crazy Bread + Refresco 2l")
        ]
        for nombre, desc in combos:
            combo_existente = db.query(Combo).filter(Combo.nombre == nombre).first()
            if not combo_existente:
                nuevo_combo = Combo(nombre=nombre, descripcion=desc)
                db.add(nuevo_combo)
                db.commit()
                db.refresh(nuevo_combo)
                ids["combos"][nombre] = nuevo_combo.id_combo
            else:
                ids["combos"][nombre] = combo_existente.id_combo

        # 8) ASIGNACIONES DE COMBOS (PRODUCTOS -> COMBOS)
        asignaciones_combos = [
            ("Combo clásico HNR", "Hot-N-Ready Pepperoni", 1), 
            ("Combo clásico HNR", "Crazy Bread", 1), 
            ("Combo clásico HNR", "Refresco familiar 2l", 1)
        ]
        for combo, prod, cant in asignaciones_combos:
            id_c = ids["combos"].get(combo)
            id_p = ids["productos"].get(prod)
            if id_c and id_p:
                asig_existente = db.query(ComboProducto).filter(
                    ComboProducto.id_combo == id_c,
                    ComboProducto.id_producto == id_p
                ).first()
                if not asig_existente:
                    nueva_asig = ComboProducto(id_combo=id_c, id_producto=id_p, cantidad=cant)
                    db.add(nueva_asig)
        db.commit()
        print("\nBASE DE DATOS POBLADA EXITOSAMENTE")
    except Exception as error:
        db.rollback()
        print(f"\nERROR AL POBLAR LA BASE DE DATOS: {error}")
    finally:
        db.close()

if __name__ == "__main__":
    time.sleep(5)
    poblar_base_de_datos()
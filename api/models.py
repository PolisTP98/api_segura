from sqlalchemy import (
    Column, 
    Integer, 
    SmallInteger, 
    String, 
    Numeric, 
    Boolean, 
    Identity, 
    ForeignKey, 
    CheckConstraint
)
from sqlalchemy.orm import relationship
from database import Base


# ---------------------
# | ESQUEMA "lcs_cat" |
# ---------------------

class UnidadMedida(Base):
    __tablename__ = "unidades_medida"
    __table_args__ = {"schema": "lcs_cat"}

    id_unidad_medida = Column(Integer, Identity(always = True), primary_key = True)
    nombre = Column(String(20), nullable = False, unique = True)
    # RELACIONES
    ingredientes = relationship(
        "Ingrediente", 
        back_populates = "unidad_medida"
    )

class Ingrediente(Base):
    __tablename__ = "ingredientes"
    __table_args__ = {"schema": "lcs_cat"}

    id_ingrediente = Column(Integer, Identity(always = True), primary_key = True)
    id_unidad_medida = Column(
        Integer, 
        ForeignKey(
            "lcs_cat.unidades_medida.id_unidad_medida", 
            name = "fk_ingrediente_unidad_medida"
            ), 
        nullable = False
    )
    nombre = Column(String(100), nullable = False, unique = True)
    # RELACIONES
    unidad_medida = relationship(
        "UnidadMedida", 
        back_populates = "ingredientes"
    )
    productos = relationship(
        "ProductoIngrediente", 
        back_populates = "ingrediente"
    )

class CategoriaProducto(Base):
    __tablename__ = "categorias_productos"
    __table_args__ = {"schema": "lcs_cat"}

    id_categoria = Column(Integer, Identity(always = True), primary_key = True)
    nombre = Column(String(20), nullable = False, unique = True)
    # RELACIONES
    productos = relationship(
        "Producto", 
        back_populates = "categoria"
    )


# ---------------------
# | ESQUEMA "lcs_usu" |
# ---------------------

class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        CheckConstraint(
            "email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'", 
            name = "ck_usuario_email"
        ), 
        {"schema": "lcs_usu"}
    )

    id_usuario = Column(Integer, Identity(always = True), primary_key = True)
    nombre_completo = Column(String(255), nullable = False)
    email = Column(String(255), unique = True, nullable = False)
    contrasena = Column(String(255), nullable = False)
    es_admin = Column(Boolean, nullable = False, default = False, server_default = "false")


# ---------------------
# | ESQUEMA "lcs_pro" |
# ---------------------    

class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = {"schema": "lcs_pro"}

    id_producto = Column(Integer, Identity(always = True), primary_key = True)
    id_categoria = Column(
        Integer, 
        ForeignKey(
            "lcs_cat.categorias_productos.id_categoria", 
            name = "fk_producto_categoria"
        ), 
        nullable = False
    )
    nombre = Column(String(100), nullable = False, unique = True)
    descripcion = Column(String(255))
    # RELACIONES
    categoria = relationship(
        "CategoriaProducto", 
        back_populates = "productos"
    )
    ingredientes = relationship(
        "ProductoIngrediente", 
        back_populates = "producto", 
        cascade = "all, delete-orphan"
    )
    combos = relationship(
        "ComboProducto", 
        back_populates = "producto", 
        cascade = "all, delete-orphan"
    )

class ProductoIngrediente(Base):
    __tablename__ = "producto_ingredientes"
    __table_args__ = (
        CheckConstraint(
            "cantidad > 0",
            name = "ck_producto_ingrediente_cantidad"
        ), 
        {"schema": "lcs_pro"}
    )

    id_producto = Column(
        Integer, 
        ForeignKey(
            "lcs_pro.productos.id_producto", 
            name = "fk_producto_ingrediente", 
            ondelete = "CASCADE", 
            onupdate = "CASCADE"
        ), 
        primary_key = True
    )
    id_ingrediente = Column(
        Integer, 
        ForeignKey(
            "lcs_cat.ingredientes.id_ingrediente", 
            name = "fk_ingrediente_producto"
        ), 
        primary_key = True
    )
    cantidad = Column(Numeric(7, 2), nullable = False)
    # RELACIONES
    producto = relationship(
        "Producto", 
        back_populates = "ingredientes"
    )
    ingrediente = relationship(
        "Ingrediente", 
        back_populates = "productos"
    )

class Combo(Base):
    __tablename__ = "combos"
    __table_args__ = {"schema": "lcs_pro"}

    id_combo = Column(Integer, Identity(always = True), primary_key = True)
    nombre = Column(String(100), nullable = False)
    descripcion = Column(String(500))
    # RELACIONES
    productos = relationship(
        "ComboProducto", 
        back_populates = "combo", 
        cascade = "all, delete-orphan"
    )

class ComboProducto(Base):
    __tablename__ = "combos_productos"
    __table_args__ = (
        CheckConstraint(
            "cantidad > 0", 
            name = "ck_combo_producto_cantidad"
        ), 
        {"schema": "lcs_pro"}
    )

    id_combo = Column(
        Integer, 
        ForeignKey(
            "lcs_pro.combos.id_combo", 
            name = "fk_producto_combo", 
            ondelete = "CASCADE", 
            onupdate = "CASCADE"
        ), 
        primary_key = True
    )
    id_producto = Column(
        Integer, 
        ForeignKey(
            "lcs_pro.productos.id_producto", 
            name = "fk_combo_producto", 
            ondelete = "CASCADE", 
            onupdate = "CASCADE"
        ), 
        primary_key = True
    )
    cantidad = Column(
        SmallInteger, 
        nullable = False
    )
    combo = relationship(
        "Combo", 
        back_populates = "productos"
    )
    producto = relationship(
        "Producto", 
        back_populates = "combos"
    )
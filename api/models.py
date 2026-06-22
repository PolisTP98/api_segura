from sqlalchemy import (
    Column,
    Integer,
    SmallInteger,
    String,
    Numeric,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


# ==========================
# ESQUEMA lcs_cat
# ==========================

class UnidadMedida(Base):
    __tablename__ = "unidades_medida"
    __table_args__ = {"schema": "lcs_cat"}

    id_unidad_medida = Column(Integer, primary_key=True)
    nombre = Column(String(20), nullable=False, unique=True)

    ingredientes = relationship(
        "Ingrediente",
        back_populates="unidad_medida"
    )


class Ingrediente(Base):
    __tablename__ = "ingredientes"
    __table_args__ = {"schema": "lcs_cat"}

    id_ingrediente = Column(Integer, primary_key=True)

    id_unidad_medida = Column(
        Integer,
        ForeignKey(
            "lcs_cat.unidades_medida.id_unidad_medida"
        ),
        nullable=False
    )

    nombre = Column(String(100), nullable=False, unique=True)

    unidad_medida = relationship(
        "UnidadMedida",
        back_populates="ingredientes"
    )

    productos = relationship(
        "ProductoIngrediente",
        back_populates="ingrediente"
    )


class CategoriaProducto(Base):
    __tablename__ = "categorias_productos"
    __table_args__ = {"schema": "lcs_cat"}

    id_categoria = Column(Integer, primary_key=True)
    nombre = Column(String(20), nullable=False, unique=True)

    productos = relationship(
        "Producto",
        back_populates="categoria"
    )


# ==========================
# ESQUEMA lcs_pro
# ==========================

class Producto(Base):
    __tablename__ = "productos"
    __table_args__ = {"schema": "lcs_pro"}

    id_producto = Column(Integer, primary_key=True)

    id_categoria = Column(
        Integer,
        ForeignKey(
            "lcs_cat.categorias_productos.id_categoria"
        ),
        nullable=False
    )

    nombre = Column(String(100), nullable=False, unique=True)
    descripcion = Column(String(255))

    categoria = relationship(
        "CategoriaProducto",
        back_populates="productos"
    )

    ingredientes = relationship(
        "ProductoIngrediente",
        back_populates="producto",
        cascade="all, delete-orphan"
    )

    combos = relationship(
        "ComboProducto",
        back_populates="producto"
    )


class ProductoIngrediente(Base):
    __tablename__ = "producto_ingredientes"
    __table_args__ = (
        CheckConstraint("cantidad > 0"),
        {"schema": "lcs_pro"}
    )

    id_producto = Column(
        Integer,
        ForeignKey(
            "lcs_pro.productos.id_producto",
            ondelete="CASCADE",
            onupdate="CASCADE"
        ),
        primary_key=True
    )

    id_ingrediente = Column(
        Integer,
        ForeignKey(
            "lcs_cat.ingredientes.id_ingrediente"
        ),
        primary_key=True
    )

    cantidad = Column(
        Numeric(7, 2),
        nullable=False
    )

    producto = relationship(
        "Producto",
        back_populates="ingredientes"
    )

    ingrediente = relationship(
        "Ingrediente",
        back_populates="productos"
    )


class Combo(Base):
    __tablename__ = "combos"
    __table_args__ = {"schema": "lcs_pro"}

    id_combo = Column(Integer, primary_key=True)

    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255))

    productos = relationship(
        "ComboProducto",
        back_populates="combo"
    )


class ComboProducto(Base):
    __tablename__ = "combos_productos"
    __table_args__ = {"schema": "lcs_pro"}

    id_combo = Column(
        Integer,
        ForeignKey("lcs_pro.combos.id_combo"),
        primary_key=True
    )

    id_producto = Column(
        Integer,
        ForeignKey("lcs_pro.productos.id_producto"),
        primary_key=True
    )

    cantidad = Column(
        SmallInteger,
        nullable=False
    )

    combo = relationship(
        "Combo",
        back_populates="productos"
    )

    producto = relationship(
        "Producto",
        back_populates="combos"
    )

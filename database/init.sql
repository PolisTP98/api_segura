/*
---------------------------------------------------
| ESTRUCTURA DE LA BASE DE DATOS "little_caesars" |
---------------------------------------------------
*/

-- CREAR ESQUEMA PARA LOS TABLAS DE TIPO CATÁLOGO
create schema if not exists lcs_cat;
-- CREAR ESQUEMA PARA LAS TABLAS DE USUARIOS
create schema if not exists lcs_usu;
-- CREAR ESQUEMA PARA LAS TABLAS DE PRODUCTOS
create schema if not exists lcs_pro;

-- BORRAR LAS TABLAS EN ORDEN INVERSO PARA EVITAR ERRORES DE LLAVE FORÁNEA
drop table if exists lcs_pro.combos_productos;
drop table if exists lcs_pro.combos;
drop table if exists lcs_pro.producto_ingredientes;
drop table if exists lcs_pro.productos;
drop table if exists lcs_usu.usuarios;
drop table if exists lcs_cat.categorias_productos;
drop table if exists lcs_cat.ingredientes;
drop table if exists lcs_cat.unidades_medida;


/*
---------------------------
| TABLAS DE TIPO CATÁLOGO |
---------------------------
*/

-- ALMACENAR LAS UNIDADES DE MEDIDA DE LOS INGREDIENTES DE LOS PRODUCTOS
create table lcs_cat.unidades_medida(
    id_unidad_medida int generated always as identity primary key,
    nombre varchar(20) unique not null
);

-- ALMACENAR LOS INGREDIENTES DE LOS PRODUCTOS
create table lcs_cat.ingredientes(
    id_ingrediente int generated always as identity primary key,
    id_unidad_medida int not null,
    nombre varchar(100) unique not null,
    constraint fk_ingrediente_unidad_medida 
        foreign key(id_unidad_medida) 
        references lcs_cat.unidades_medida(id_unidad_medida)
);

-- ALMACENAR LAS CATEGORÍAS DE LOS PRODUCTOS
create table lcs_cat.categorias_productos(
    id_categoria int generated always as identity primary key,
    nombre varchar(20) unique not null
);


/*
----------------------
| TABLAS PRINCIPALES |
----------------------
*/

-- ALMACENAR LOS USUARIOS
create table lcs_usu.usuarios(
    id_usuario int generated always as identity primary key,
    nombre_completo varchar(255) not null,
    email varchar(255) unique not null 
        constraint ck_usuario_email 
        check(email ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    contrasena varchar(255) not null,
    es_admin boolean not null default false
);

-- ALMACENAR LOS PRODUCTOS
create table lcs_pro.productos(
    id_producto int generated always as identity primary key,
    id_categoria int not null,
    nombre varchar(100) unique not null,
    descripcion varchar(255),
    constraint fk_producto_categoria 
        foreign key(id_categoria) 
        references lcs_cat.categorias_productos(id_categoria)
);

-- ALMACENAR LOS INGREDIENTES DE CADA PRODUCTO
create table lcs_pro.producto_ingredientes(
    id_producto int not null,
    id_ingrediente int not null,
    cantidad numeric(7, 2) not null 
        constraint ck_producto_ingrediente_cantidad 
        check(cantidad > 0),
    constraint fk_producto_ingrediente 
        foreign key(id_producto) 
        references lcs_pro.productos(id_producto) 
        on delete cascade 
        on update cascade,
    constraint fk_ingrediente_producto 
        foreign key(id_ingrediente) 
        references lcs_cat.ingredientes(id_ingrediente),
    primary key(id_producto, id_ingrediente)
);

-- ALMACENAR LOS NOMBRES DE LOS COMBOS DE LOS PRODUCTOS
create table lcs_pro.combos(
    id_combo int generated always as identity primary key,
    nombre varchar(100) not null,
    descripcion varchar(255)
);

-- ALMACENAR LOS COMBOS DE LOS PRODUCTOS
create table lcs_pro.combos_productos(
    id_combo int not null,
    id_producto int not null,
    cantidad smallint not null 
        constraint ck_combo_producto_cantidad 
        check(cantidad > 0),
    constraint fk_combo_producto 
        foreign key(id_producto) 
        references lcs_pro.productos(id_producto) 
        on delete cascade 
        on update cascade,
    constraint fk_producto_combo 
        foreign key(id_combo) 
        references lcs_pro.combos(id_combo) 
        on delete cascade 
        on update cascade,
    primary key(id_combo, id_producto)
);
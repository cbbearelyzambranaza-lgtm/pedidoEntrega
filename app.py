from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from functools import wraps

import json
import folium

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_muy_segura'  # Cambia esto en producción

app.config['SQLALCHEMY_DATABASE_URI'] = \
    'mysql+mysqlconnector://{usuario}:{clave}@{servidor}/{database}?charset=utf8'.format(
        usuario='arelyzam',
        clave='mysqlroot',
        servidor='arelyzam.mysql.pythonanywhere-services.com',
        database='arelyzam$pedidoEntrega'
    )



db = SQLAlchemy(app)

class Usuarios(db.Model):
    nombre = db.Column(db.String(40),nullable=False )
    usuario = db.Column(db.String(20), primary_key=True)
    clave = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    correo = db.Column(db.String(80), nullable=False)


class Productos(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    articulo = db.Column(db.String(50), nullable=False)
    descripcion = db.Column(db.String(100), nullable=False)
    precio_venta = db.Column(db.DECIMAL(9,2), nullable=False)
    stock_minimo = db.Column(db.Integer, nullable=False)
    existencia = db.Column(db.Integer, nullable=False)

class Clientes(db.Model):
    id_cliente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    local_barrio = db.Column(db.String(50), nullable=False)
    direccion = db.Column(db.String(100), nullable=False)
    telefono = db.Column(db.String(20), nullable=False)
    correo = db.Column(db.String(80), nullable=False)
    coordenadas = db.Column(db.String(50), nullable=False)
    ciudad = db.Column(db.String(50), nullable=False)

class Pedidos(db.Model):
    num_pedido = db.Column(db.String(40), primary_key=True)
    id_cliente = db.Column(
        db.Integer,
        db.ForeignKey('clientes.id_cliente', ondelete='RESTRICT', onupdate='CASCADE'),
        nullable=False
    )
    fecha = db.Column(db.Date, nullable=False)
    codigo_producto = db.Column(db.String(80), nullable=False)
    producto = db.Column(db.String(80), nullable=False)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    estado = db.Column(db.String(30), nullable=False)

    # relación opcional (muy recomendable)
    cliente = db.relationship('Clientes', backref=db.backref('pedidos', lazy=True))




# Base de datos simulada de clientes
CLIENTES_DB = {
    "CLI001": {
        "codigo": "CLI001",
        "cliente": "Juan Pérez",
        "fecha": "2024-06-01",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "articulos": [
            {"id": 1, "nombre": "Laptop Dell", "cantidad": 2, "precio": 1200.00},
            {"id": 2, "nombre": "Mouse Inalámbrico", "cantidad": 5, "precio": 25.00},
            {"id": 3, "nombre": "Teclado Mecánico", "cantidad": 3, "precio": 80.00},
            {"id": 4, "nombre": "Monitor 24\"", "cantidad": 2, "precio": 300.00},
            {"id": 5, "nombre": "Webcam HD", "cantidad": 1, "precio": 150.00}
        ]
    },
    "CLI002": {
        "codigo": "CLID002",
        "cliente": "María García",
        "fecha": "2024-06-02",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "articulos": [
            {"id": 1, "nombre": "Smartphone Samsung", "cantidad": 1, "precio": 800.00},
            {"id": 2, "nombre": "Funda Protectora", "cantidad": 2, "precio": 15.00},
            {"id": 3, "nombre": "Cargador Rápido", "cantidad": 1, "precio": 35.00},
            {"id": 4, "nombre": "Auriculares Bluetooth", "cantidad": 1, "precio": 120.00},
            {"id": 5, "nombre": "Protector de Pantalla", "cantidad": 3, "precio": 10.00}
        ]
    },
    "CLI003": {
        "codigo": "CLI003",
        "cliente": "Carlos López",
        "fecha": "2024-06-03",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "articulos": [
            {"id": 1, "nombre": "Tablet iPad", "cantidad": 1, "precio": 600.00},
            {"id": 2, "nombre": "Apple Pencil", "cantidad": 1, "precio": 130.00},
            {"id": 3, "nombre": "Funda Smart Cover", "cantidad": 1, "precio": 45.00},
            {"id": 4, "nombre": "Adaptador USB-C", "cantidad": 2, "precio": 25.00},
            {"id": 5, "nombre": "Cable Lightning", "cantidad": 1, "precio": 20.00}
        ]
    }
}


# Base de datos simulada de pedidos
PEDIDOS_DB = {
    "PED001": {
        "numero": "PED001",
        "cliente": "Juan Pérez",
        "fecha": "2024-06-01",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "estado": "Pendiente",
        "articulos": [
            {"id": 1, "nombre": "Laptop Dell", "cantidad": 2, "precio": 1200.00},
            {"id": 2, "nombre": "Mouse Inalámbrico", "cantidad": 5, "precio": 25.00},
            {"id": 3, "nombre": "Teclado Mecánico", "cantidad": 3, "precio": 80.00},
            {"id": 4, "nombre": "Monitor 24\"", "cantidad": 2, "precio": 300.00},
            {"id": 5, "nombre": "Webcam HD", "cantidad": 1, "precio": 150.00}
        ]
    },
    "PED002": {
        "numero": "PED002",
        "cliente": "María García",
        "fecha": "2024-06-02",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "estado": "Pendiente",
        "articulos": [
            {"id": 1, "nombre": "Smartphone Samsung", "cantidad": 1, "precio": 800.00},
            {"id": 2, "nombre": "Funda Protectora", "cantidad": 2, "precio": 15.00},
            {"id": 3, "nombre": "Cargador Rápido", "cantidad": 1, "precio": 35.00},
            {"id": 4, "nombre": "Auriculares Bluetooth", "cantidad": 1, "precio": 120.00},
            {"id": 5, "nombre": "Protector de Pantalla", "cantidad": 3, "precio": 10.00}
        ]
    },
    "PED003": {
        "numero": "PED003",
        "cliente": "Carlos López",
        "fecha": "2024-06-03",
        "direccion": "Av. Los Sauces # 345",
        "telefono": "7777 7777",
        "ciudad": "Cochabamba",
        "estado": "Pendiente",
        "articulos": [
            {"id": 1, "nombre": "Tablet iPad", "cantidad": 1, "precio": 600.00},
            {"id": 2, "nombre": "Apple Pencil", "cantidad": 1, "precio": 130.00},
            {"id": 3, "nombre": "Funda Smart Cover", "cantidad": 1, "precio": 45.00},
            {"id": 4, "nombre": "Adaptador USB-C", "cantidad": 2, "precio": 25.00},
            {"id": 5, "nombre": "Cable Lightning", "cantidad": 1, "precio": 20.00}
        ]
    }
}




def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Por favor, inicia sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        #registro_usuario = Usuarios.query.filter_by(usuario=request.form['username']).first()

        # Buscar usuario con clave primaria = "johndoe"
        #usuario = Usuarios.query.get("seller3")
        registro_usuario = Usuarios.query.get(username)

        if not(registro_usuario):
            flash('Usuario o contraseña incorrectos', 'error')
            return render_template('login.html')

        usuario = registro_usuario.usuario

        if registro_usuario and registro_usuario.clave == password:
            session['username'] = username
            session['role'] = registro_usuario.role
            flash(f'Bienvenido, {username}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('role', None)
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')



@app.route('/ver_mapa')
def ver_mapa():
    if 'username' not in session or session['username'] == None:
        return redirect(url_for('login'))

    # Crear el mapa centrado en Cochabamba
    m = folium.Map(location=[-17.3935, -66.1570], zoom_start=15)

    # Lista de tiendas con sus datos
    tiendas = [
        {
            'nombre': 'Doña Filomena',
            'contacto': 'Filomena Delgado',
            'direccion': 'Calle La Tablada #4533',
            'telefono': '77788899',
            'pedido': '1001',
            'foto': 'tienda_barrio.jpg',
            'ubicacion': [-17.3935, -66.1570]
        },
        {
            'nombre': 'Abarrotes El Carmen',
            'contacto': 'Carmen Rojas',
            'direccion': 'Av. Blanco Galindo Km 2',
            'telefono': '76543210',
            'pedido': '1002',
            'foto': 'tienda_carmen.jpg',
            'ubicacion': [-17.3850, -66.1700]
        },
        {
            'nombre': 'Minimarket Los Andes',
            'contacto': 'Juan Mamani',
            'direccion': 'Av. América Este #345',
            'telefono': '70707070',
            'pedido': '1002',
            'foto': 'tienda_andes.jpg',
            'ubicacion': [-17.3980, -66.1420]
        },
        {
            'nombre': 'Tienda Don Pedro',
            'contacto': 'Pedro Flores',
            'direccion': 'Calle Jordán #1234',
            'telefono': '71234567',
            'pedido': '1003',
            'foto': 'tienda_pedro.jpg',
            'ubicacion': [-17.4050, -66.1610]
        },
        {
            'nombre': 'Mercadito Central',
            'contacto': 'María Gutiérrez',
            'direccion': 'Av. Ayacucho #887',
            'telefono': '78901234',
            'pedido': '1004',
            'foto': 'tienda_central.jpg',
            'ubicacion': [-17.3925, -66.1480]
        },
        {
            'nombre': 'Almacén El Sol',
            'contacto': 'Roberto Mendoza',
            'direccion': 'Av. Heroínas #765',
            'telefono': '76767676',
            'pedido': '1005',
            'foto': 'tienda_sol.jpg',
            'ubicacion': [-17.3880, -66.1550]
        },
        {
            'nombre': 'Tienda Doña Rosa',
            'contacto': 'Rosa Méndez',
            'direccion': 'Calle Hamiraya #432',
            'telefono': '79876543',
            'pedido': '1006',
            'foto': 'tienda_rosa.jpg',
            'ubicacion': [-17.4010, -66.1520]
        }
    ]

    # Agregar marcadores para cada tienda
    for tienda in tiendas:
        foto_url = url_for('static', filename='fotos/tienda_barrio.jpg')

        popup_content = f"""<table border=1 class="table table-success table-striped">
            <tr><td colspan="2"><img src='{ foto_url }' width='250' height='200'></td></tr>
            <tr><td>Tienda:</td><td>{ tienda['nombre'] }</td></tr>
            <tr><td>Contacto:</td><td>{ tienda['contacto'] }</td></tr>
            <tr><td>Dirección:</td><td>{ tienda['direccion'] }</td></tr>
            <tr><td>Teléfono:</td><td>{ tienda['telefono'] }</td></tr>
            <tr><td>Pedido:</td><td>{ tienda['pedido'] }</td></tr>
            <!--tr><td colspan="2"><center><a class="btn btn-primary" href="/pedido" style="color: white;">Ver Pedido</a></center></td></tr-->
            </table>"""

        folium.Marker(
            location=tienda['ubicacion'],
            popup=folium.Popup(popup_content, max_width=300),
            tooltip=f'Tienda: {tienda["nombre"]}',
            icon=folium.Icon(color='blue', icon='shopping-cart', prefix='fa')
        ).add_to(m)

    # Guardar el mapa en un archivo HTML
    path='/home/arelyzam/mysite/static/mapa_cbb.html'
    m.save(path)
    mapa_html = m._repr_html_()

    # Renderizar la plantilla HTML
    return render_template('mapa.html', mapa=mapa_html)


@app.route('/pedido')
def pedido():
    if 'username' not in session or session['role'] != 'driver':    ## == None:
        return redirect(url_for('login'))
    return render_template("pedido.html")


@app.route('/buscar_pedido', methods=['GET', 'POST'])
def buscar_pedido():
    if 'username' not in session or session['role'] != 'driver':
        return redirect(url_for('login'))


    pedido = None
    error = None
    success = None
    total = 0

    if request.method == 'POST':
        numero_pedido = request.form.get('numero_pedido', '').strip().upper()

        if not numero_pedido:
            error = "Por favor, ingrese un número de pedido."
        elif numero_pedido in PEDIDOS_DB:
            pedido = PEDIDOS_DB[numero_pedido]
            # Calcular total
            total = sum(art['cantidad'] * art['precio'] for art in pedido['articulos'])
        else:
            error = f"El pedido '{numero_pedido}' no existe en el sistema."

    return render_template('pedido.html',
                                pedido=pedido,
                                error=error,
                                success=success,
                                total=total,
                                pedidos_ejemplo=True)

@app.route('/actualizar_pedido', methods=['POST'])
def actualizar_pedido():
    numero_pedido = request.form.get('numero_pedido')

    if numero_pedido not in PEDIDOS_DB:
        return render_template('pedido.html',
                                    error="Pedido no encontrado.")

    # Actualizar artículos
    pedido = PEDIDOS_DB[numero_pedido]

    try:
        for articulo in pedido['articulos']:
            articulo_id = articulo['id']
            articulo['nombre'] = request.form.get(f'nombre_{articulo_id}', '').strip()
            articulo['cantidad'] = int(request.form.get(f'cantidad_{articulo_id}', 0))
            articulo['precio'] = float(request.form.get(f'precio_{articulo_id}', 0))

            # Validaciones básicas
            if not articulo['nombre']:
                raise ValueError("El nombre del artículo no puede estar vacío.")
            if articulo['cantidad'] <= 0:
                raise ValueError("La cantidad debe ser mayor a cero.")
            if articulo['precio'] < 0:
                raise ValueError("El precio no puede ser negativo.")

        # Calcular nuevo total
        total = sum(art['cantidad'] * art['precio'] for art in pedido['articulos'])

        return render_template('pedido.html',
                                    pedido=pedido,
                                    success="Pedido actualizado correctamente.",
                                    total=total)

    except (ValueError, TypeError) as e:
        return render_template('pedido2.html',
                                    pedido=pedido,
                                    error=f"Error al actualizar: {str(e)}",
                                    total=sum(art['cantidad'] * art['precio'] for art in pedido['articulos']))


@app.route('/preventa')
def preventa():
    if 'username' not in session or session['role'] != 'seller':
        return redirect(url_for('login'))
    productos = Productos.query.all()
    return render_template("preventa.html", productos = productos)

@app.route('/buscar_cliente', methods=['GET', 'POST'])
def buscar_cliente():
    codigo = None
    error = None
    productos = Productos.query.all()

    if request.method == 'POST':
        id_cliente_str = request.form.get('codigo_cliente', '').strip()

        if not id_cliente_str:
            error = "Por favor, ingrese un ID de cliente."
        else:
            try:
                id_cliente = int(id_cliente_str)  # <-- convertir a entero
                cliente = Clientes.query.get(id_cliente)
                if cliente:
                    codigo = cliente
                else:
                    error = f"El cliente con ID '{id_cliente}' no existe."
            except ValueError:
                error = "El ID de cliente debe ser un número."

    return render_template('preventa.html',
                           codigo=codigo,
                           error=error,
                           success=None,
                           total=0,
                           productos=productos)


@app.route('/usuarios')
def index():
    if 'username' not in session or session['username'] == None:
        return redirect(url_for('login'))

    usuarios = Usuarios.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/agregar_usuario', methods=['GET', 'POST'])
def agregar_usuario():
    if request.method == 'POST':
        nuevo_usuario = Usuarios(
            nombre=request.form['nombre'],
            usuario=request.form['usuario'],
            clave=request.form['clave'],
            role=request.form['role'],
            correo=request.form['correo']
        )
        db.session.add(nuevo_usuario)
        db.session.commit()
        usuarios = Usuarios.query.all()
        return render_template('usuarios.html', usuarios=usuarios)
    return render_template('agregar_usuarios.html')


#@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@app.route('/editar_usuario/<id>', methods=['GET', 'POST'])
def editar_usuario(id):
    usuario = Usuarios.query.get(id)

    if request.method == 'POST':
        usuario.nombre = request.form['nombre']
        usuario.usuario = request.form['usuario']
        usuario.clave = request.form['clave']
        usuario.role = request.form['role']
        usuario.correo = request.form['correo']

        db.session.add(usuario)
        db.session.commit()

        usuarios = Usuarios.query.all()
        return render_template('usuarios.html', usuarios=usuarios)

    return render_template('editar_usuarios.html', usuario=usuario)


#@app.route('/eliminar_usuario/<int:id>')
@app.route('/eliminar_usuario/<id>')
def eliminar_usuario(id):
    usuario = Usuarios.query.get(id)
    db.session.delete(usuario)
    db.session.commit()
    usuarios = Usuarios.query.all()
    return render_template('usuarios.html', usuarios=usuarios)

@app.route('/grabar_pedido', methods=['POST'])
def grabar_pedido():
    if 'username' not in session or session['role'] != 'seller':
        return redirect(url_for('login'))

    id_cliente = request.form.get('id_cliente')
    cliente = Clientes.query.get(id_cliente)
    if not cliente:
        flash("No se pudo encontrar el cliente.", "error")
        productos = Productos.query.all()
        return render_template('preventa.html', productos=productos, total=0)

    productos = Productos.query.all()
    fecha_actual = datetime.now().date()

    try:
        # Generar un num_pedido único, por ejemplo: CLI001-20251212-001
        from random import randint
        num_pedido_base = f"{id_cliente}-{fecha_actual.strftime('%Y%m%d')}"
        contador = 1

        for producto in productos:
            cantidad = int(request.form.get(f'cantidad_{producto.id}', 0))
            precio = float(request.form.get(f'precio_{producto.id}', producto.precio_venta))

            if cantidad > 0:
                num_pedido = f"{num_pedido_base}-{contador:03d}"
                nuevo_pedido = Pedidos(
                    num_pedido=num_pedido,
                    id_cliente=id_cliente,
                    fecha=fecha_actual,
                    codigo_producto=str(producto.id),
                    producto=producto.articulo,
                    precio_venta=precio,
                    cantidad=cantidad,
                    estado='PREVENTA'
                )
                db.session.add(nuevo_pedido)
                contador += 1

        db.session.commit()
        flash("Pedido(s) grabado(s) correctamente.", "success")
        return redirect(url_for('preventa'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error al grabar el pedido: {str(e)}", "error")
        return redirect(url_for('preventa'))

# =========================
# CREAR TABLAS (SOLO 1 VEZ)
# =========================
with app.app_context():
    db.create_all()

    # =========================
# INSERTAR CLIENTES INICIALES (SOLO UNA VEZ)
# =========================
with app.app_context():
    clientes_iniciales = [
        ('Tienda Don Luis', 'Queru Queru', 'Av. Blanco Galindo #123', '76451234', 'donluis@gmail.com', '-17.3921,-66.1583', 'Cochabamba'),
        ('Mini Market Ana', 'Sarco', 'Calle Melchor Pérez #45', '70112233', 'ana@gmail.com', '-17.3810,-66.1702', 'Cochabamba'),
        ('Distribuidora El Sol', 'La Recoleta', 'Av. América #789', '68995544', 'elsol@gmail.com', '-17.3945,-66.1550', 'Cochabamba'),
        ('Abarrotes San Juan', 'Quillacollo', 'Calle Bolívar #12', '73441122', 'sanjuan@gmail.com', '-17.3910,-66.2815', 'Quillacollo'),
        ('Supermercado Central', 'Centro', 'Av. Heroínas #456', '72233445', 'central@gmail.com', '-17.3930,-66.1560', 'Cochabamba'),
        ('Tienda La Economía', 'Villa Pagador', 'Calle Pando #89', '69887766', 'economia@gmail.com', '-17.4200,-66.1655', 'Cochabamba'),
        ('Almacén Los Andes', 'Sacaba', 'Av. Villazón Km 4', '71223344', 'andes@gmail.com', '-17.3950,-66.0400', 'Sacaba'),
        ('Minimarket San Pedro', 'Zona Sur', 'Calle Aroma #22', '76554433', 'sanpedro@gmail.com', '-17.4102,-66.1801', 'Cochabamba')
    ]

    for c in clientes_iniciales:
        # Evitar duplicados verificando por nombre y dirección
        existente = Clientes.query.filter_by(nombre=c[0], direccion=c[2]).first()
        if not existente:
            nuevo_cliente = Clientes(
                nombre=c[0],
                local_barrio=c[1],
                direccion=c[2],
                telefono=c[3],
                correo=c[4],
                coordenadas=c[5],
                ciudad=c[6]
            )
            db.session.add(nuevo_cliente)
    db.session.commit()
    print("Clientes iniciales agregados correctamente.")



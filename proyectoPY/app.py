from flask import Flask, render_template, request, redirect, url_for, flash, session
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
import os

# Importar forms
from forms import LoginForm, RegisterForm, ArticuloWikipediaForm, NuevaCategoriaForm, EditarCategoriaForm

# Importar API de Wikipedia
from wikipedia_api import buscar_articulo_wikipedia

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'mi-clave-super-secreta-12345')

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def conectar_mongodb():
    """Conecta a MongoDB y devuelve la base de datos"""
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://admin:password123@db:27017/proyecto_db?authSource=admin')
    cliente = MongoClient(mongo_uri)
    return cliente.proyecto_db

def login_requerido(f):
    """Decorador para proteger rutas que requieren autenticación"""
    @wraps(f)
    def decorada(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, inicia sesión para acceder', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorada

# ============================================
# RUTAS DE AUTENTICACIÓN
# ============================================

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    """Registro de nuevos usuarios"""
    form = RegisterForm()
    
    if form.validate_on_submit():
        db = conectar_mongodb()
        
        # Verificar si el email ya existe
        if db.usuarios.find_one({'email': form.email.data}):
            flash('Este email ya está registrado', 'danger')
            return render_template('register.html', form=form)
        
        # Crear nuevo usuario con configuración por defecto
        nuevo_usuario = {
            'nombre': form.nombre.data,
            'email': form.email.data,
            'password': generate_password_hash(form.password.data),
            'fecha_registro': datetime.utcnow(),
            'coleccion_publica': False  # Por defecto, colección privada
        }
        
        resultado = db.usuarios.insert_one(nuevo_usuario)
        
        # Guardar en sesión inmediatamente
        session['usuario_id'] = str(resultado.inserted_id)
        session['usuario_nombre'] = form.nombre.data
        
        flash('Registro exitoso! Bienvenido', 'success')
        return redirect(url_for('inicio'))
    
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión de usuarios"""
    form = LoginForm()
    
    if form.validate_on_submit():
        db = conectar_mongodb()
        
        # Buscar usuario por email
        usuario = db.usuarios.find_one({'email': form.email.data})
        
        if usuario and check_password_hash(usuario['password'], form.password.data):
            # Guardar en sesión
            session['usuario_id'] = str(usuario['_id'])
            session['usuario_nombre'] = usuario['nombre']
            
            flash('Sesión iniciada correctamente', 'success')
            return redirect(url_for('inicio'))
        else:
            flash('Email o contraseña incorrectos', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    """Cerrar sesión"""
    session.clear()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('inicio'))

# ============================================
# RUTA PARA CONFIGURACIÓN DE PRIVACIDAD
# ============================================

@app.route('/configuracion/privacidad', methods=['GET', 'POST'])
@login_requerido
def configurar_privacidad():
    """Configurar si la colección del usuario es pública o privada"""
    db = conectar_mongodb()
    
    if request.method == 'POST':
        publica = request.form.get('coleccion_publica') == 'true'
        
        db.usuarios.update_one(
            {'_id': ObjectId(session['usuario_id'])},
            {'$set': {'coleccion_publica': publica}}
        )
        
        flash(f'Tu colección ahora es {"pública" if publica else "privada"}', 'success')
        return redirect(url_for('inicio'))
    
    # Obtener configuración actual
    usuario = db.usuarios.find_one({'_id': ObjectId(session['usuario_id'])})
    coleccion_publica = usuario.get('coleccion_publica', False)
    
    return render_template('configurar_privacidad.html', coleccion_publica=coleccion_publica)

# ============================================
# RUTAS PÚBLICAS
# ============================================

@app.route('/')
def inicio():
    """Página de inicio"""
    db = conectar_mongodb()
    
    total_articulos = db.articulos.count_documents({}) if 'articulos' in db.list_collection_names() else 0
    total_usuarios = db.usuarios.count_documents({})
    
    # Categorías base
    categorias_base = ['Ciencia', 'Historia', 'Arte', 'Tecnología', 'Deportes', 'Biografías', 'Geografía', 'Otros']
    estadisticas = {}
    
    usuario_id = session.get('usuario_id')
    
    if usuario_id:
        # Usuario logueado: mostrar SOLO sus categorías
        if 'articulos' in db.list_collection_names():
            for cat in categorias_base:
                estadisticas[cat] = db.articulos.count_documents({
                    'usuario_id': usuario_id,
                    'categoria': cat
                })
            
            # Categorías personalizadas
            categorias_personalizadas = db.articulos.distinct('categoria', {
                'usuario_id': usuario_id,
                'categoria': {'$nin': categorias_base}
            })
            
            for cat in categorias_personalizadas:
                if cat and cat not in estadisticas:
                    estadisticas[cat] = db.articulos.count_documents({
                        'usuario_id': usuario_id,
                        'categoria': cat
                    })
    else:
        # Visitante: mostrar totales generales de artículos PÚBLICOS
        for cat in categorias_base:
            estadisticas[cat] = db.articulos.count_documents({
                'categoria': cat,
                'publico': True
            }) if 'articulos' in db.list_collection_names() else 0
    
    # Eliminar categorías con 0 artículos
    estadisticas = {k: v for k, v in estadisticas.items() if v > 0}
    
    return render_template('inicio.html', 
                         total_items=total_articulos,
                         total_usuarios=total_usuarios,
                         estadisticas=estadisticas)

@app.route('/coleccion/publica')
def ver_coleccion_publica():
    """Vista pública: todos los artículos marcados como públicos de TODOS los usuarios"""
    db = conectar_mongodb()
    
    if 'articulos' in db.list_collection_names():
        # Mostrar SOLO artículos con publico=True
        articulos = list(db.articulos.find({
            'publico': True
        }).sort('fecha_guardado', -1).limit(100))
    else:
        articulos = []
    
    return render_template('coleccion_publica.html', articulos=articulos)

# ============================================
# RUTAS PRIVADAS (REQUIEREN LOGIN)
# ============================================

@app.route('/coleccion')
@login_requerido
def ver_coleccion():
    """Vista privada: TODOS los artículos del usuario (públicos y privados)"""
    db = conectar_mongodb()
    
    if 'articulos' in db.list_collection_names():
        # Todos los artículos del usuario (sin filtro de publico)
        articulos = list(db.articulos.find({
            'usuario_id': session['usuario_id']
        }).sort('fecha_guardado', -1))
    else:
        articulos = []
    
    return render_template('coleccion.html', articulos=articulos)

@app.route('/coleccion/categoria/<categoria>')
@login_requerido
def ver_coleccion_por_categoria(categoria):
    """Ver artículos de una categoría específica (solo del usuario)"""
    db = conectar_mongodb()
    
    # Decodificar categoría
    categoria = categoria.replace('_', ' ')
    
    # Buscar artículos de esa categoría del usuario actual
    if 'articulos' in db.list_collection_names():
        articulos = list(db.articulos.find({
            'usuario_id': session['usuario_id'],
            'categoria': categoria
        }).sort('fecha_guardado', -1))
    else:
        articulos = []
    
    # Obtener todas las categorías del usuario
    categorias_usuario = db.articulos.distinct('categoria', {'usuario_id': session['usuario_id']})
    
    return render_template('coleccion_por_categoria.html', 
                         articulos=articulos, 
                         categoria_actual=categoria,
                         categorias=categorias_usuario)

@app.route('/buscar-wikipedia', methods=['GET', 'POST'])
@login_requerido
def buscar_wikipedia():
    """Buscar artículos en Wikipedia"""
    if request.method == 'POST':
        titulo = request.form.get('titulo_busqueda')
        if not titulo:
            flash('Introduce un título para buscar', 'warning')
            return redirect(url_for('buscar_wikipedia'))
        
        # Buscar en Wikipedia
        resultado, error = buscar_articulo_wikipedia(titulo)
        
        if error:
            flash(f'Error: {error}', 'danger')
            return render_template('buscar_wikipedia.html')
        
        # Guardar temporalmente en sesión
        session['wikipedia_resultado'] = resultado
        
        return redirect(url_for('guardar_articulo_wikipedia'))
    
    return render_template('buscar_wikipedia.html')

@app.route('/guardar-wikipedia', methods=['GET', 'POST'])
@login_requerido
def guardar_articulo_wikipedia():
    """Guardar artículo encontrado en Wikipedia"""
    db = conectar_mongodb()
    
    # Obtener categorías personalizadas del usuario
    categorias_personalizadas = []
    if 'categorias_personalizadas' in db.list_collection_names():
        categorias_personalizadas = list(db.categorias_personalizadas.find(
            {'usuario_id': session['usuario_id']}
        ).sort('nombre', 1))
    
    # Crear opciones para el select
    opciones = [('', '-- Selecciona --')]
    
    # Categorías predefinidas
    for cat in ['Ciencia', 'Historia', 'Arte', 'Tecnología', 'Deportes', 'Biografías', 'Geografía']:
        opciones.append((cat, cat))
    
    # Categorías personalizadas
    for cat in categorias_personalizadas:
        opciones.append((cat['nombre'], f"✨ {cat['nombre']}"))
    
    # Añadir 'Otros'
    opciones.append(('Otros', 'Otros'))
    
    form = ArticuloWikipediaForm()
    form.categoria.choices = opciones
    
    datos_wiki = session.get('wikipedia_resultado', {})
    
    if request.method == 'GET' and datos_wiki:
        form.titulo.data = datos_wiki.get('titulo')
        form.resumen.data = datos_wiki.get('resumen')
        form.url.data = datos_wiki.get('url')
        if 'categoria_sugerida' in datos_wiki:
            opciones_validas = [c[0] for c in opciones if c[0]]
            if datos_wiki['categoria_sugerida'] in opciones_validas:
                form.categoria.data = datos_wiki['categoria_sugerida']
    
    if form.validate_on_submit():
        # Obtener configuración de privacidad del usuario
        usuario = db.usuarios.find_one({'_id': ObjectId(session['usuario_id'])})
        publico_por_defecto = usuario.get('coleccion_publica', False)
        
        articulo = {
            'titulo': form.titulo.data,
            'resumen': form.resumen.data,
            'url': form.url.data,
            'categoria': form.categoria.data,
            'notas': form.notas.data,
            'fecha_guardado': datetime.utcnow(),
            'usuario_id': session['usuario_id'],
            'usuario_nombre': session['usuario_nombre'],
            'fuente': 'Wikipedia',
            'publico': publico_por_defecto  # Nuevo campo: público/privado
        }
        
        db.articulos.insert_one(articulo)
        session.pop('wikipedia_resultado', None)
        
        flash('Artículo guardado en tu colección', 'success')
        categoria_url = form.categoria.data.replace(' ', '_')
        return redirect(url_for('ver_coleccion_por_categoria', categoria=categoria_url))
    
    return render_template('guardar_wikipedia.html', form=form)

@app.route('/articulo/<id>')
@login_requerido
def ver_articulo(id):
    """Ver un artículo completo (solo si es del usuario)"""
    db = conectar_mongodb()
    
    try:
        articulo = db.articulos.find_one({
            '_id': ObjectId(id),
            'usuario_id': session['usuario_id']
        })
    except:
        flash('Artículo no encontrado', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    if not articulo:
        flash('No tienes permiso para ver este artículo', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    return render_template('articulo_detalle.html', articulo=articulo)

@app.route('/articulo/publico/<id>', methods=['POST'])
@login_requerido
def toggle_publico_articulo(id):
    """Cambiar un artículo de público a privado o viceversa"""
    db = conectar_mongodb()
    
    try:
        articulo = db.articulos.find_one({
            '_id': ObjectId(id),
            'usuario_id': session['usuario_id']
        })
    except:
        flash('Artículo no encontrado', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    if not articulo:
        flash('No tienes permiso para modificar este artículo', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    nuevo_estado = not articulo.get('publico', False)
    
    db.articulos.update_one(
        {'_id': ObjectId(id)},
        {'$set': {'publico': nuevo_estado}}
    )
    
    flash(f'Artículo ahora es {"público" if nuevo_estado else "privado"}', 'success')
    return redirect(url_for('ver_articulo', id=id))

@app.route('/editar-articulo/<id>', methods=['GET', 'POST'])
@login_requerido
def editar_articulo(id):
    """Editar un artículo guardado"""
    db = conectar_mongodb()
    
    try:
        articulo = db.articulos.find_one({
            '_id': ObjectId(id),
            'usuario_id': session['usuario_id']
        })
    except:
        flash('Artículo no encontrado', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    if not articulo:
        flash('No tienes permiso para editar este artículo', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    # Obtener categorías para el select
    categorias_personalizadas = []
    if 'categorias_personalizadas' in db.list_collection_names():
        categorias_personalizadas = list(db.categorias_personalizadas.find(
            {'usuario_id': session['usuario_id']}
        ).sort('nombre', 1))
    
    opciones = []
    for cat in ['Ciencia', 'Historia', 'Arte', 'Tecnología', 'Deportes', 'Biografías', 'Geografía']:
        opciones.append((cat, cat))
    
    for cat in categorias_personalizadas:
        opciones.append((cat['nombre'], f"{cat['nombre']}"))
    
    opciones.append(('Otros', 'Otros'))
    
    form = ArticuloWikipediaForm()
    form.categoria.choices = opciones
    
    if form.validate_on_submit():
        db.articulos.update_one(
            {'_id': ObjectId(id)},
            {'$set': {
                'titulo': form.titulo.data,
                'resumen': form.resumen.data,
                'url': form.url.data,
                'categoria': form.categoria.data,
                'notas': form.notas.data,
                'fecha_edicion': datetime.utcnow()
            }}
        )
        flash('Artículo actualizado correctamente', 'success')
        categoria_url = form.categoria.data.replace(' ', '_')
        return redirect(url_for('ver_coleccion_por_categoria', categoria=categoria_url))
    
    if request.method == 'GET':
        form.titulo.data = articulo['titulo']
        form.resumen.data = articulo['resumen']
        form.url.data = articulo['url']
        form.categoria.data = articulo['categoria']
        form.notas.data = articulo.get('notas', '')
    
    return render_template('editar_articulo.html', form=form, articulo=articulo)

@app.route('/eliminar-articulo/<id>', methods=['POST'])
@login_requerido
def eliminar_articulo(id):
    """Eliminar un artículo de la colección"""
    db = conectar_mongodb()
    
    try:
        resultado = db.articulos.delete_one({
            '_id': ObjectId(id),
            'usuario_id': session['usuario_id']
        })
        
        if resultado.deleted_count > 0:
            flash('Artículo eliminado de tu colección', 'success')
        else:
            flash('No se pudo eliminar el artículo', 'danger')
    except:
        flash('Error al eliminar el artículo', 'danger')
    
    return redirect(url_for('ver_coleccion'))

# ============================================
# RUTAS PARA CATEGORÍAS
# ============================================

@app.route('/categoria/nueva', methods=['GET', 'POST'])
@login_requerido
def nueva_categoria():
    """Crear una nueva categoría personalizada"""
    form = NuevaCategoriaForm()
    
    if form.validate_on_submit():
        db = conectar_mongodb()
        nombre_categoria = form.nombre.data.strip()
        
        # Verificar si ya existe
        existe = db.categorias_personalizadas.find_one({
            'usuario_id': session['usuario_id'],
            'nombre': nombre_categoria
        })
        
        if existe:
            flash(f'La categoría "{nombre_categoria}" ya existe', 'warning')
        else:
            # Guardar nueva categoría
            db.categorias_personalizadas.insert_one({
                'usuario_id': session['usuario_id'],
                'nombre': nombre_categoria,
                'fecha_creacion': datetime.utcnow()
            })
            flash(f'Categoría "{nombre_categoria}" creada correctamente', 'success')
            return redirect(url_for('ver_coleccion_por_categoria', 
                                  categoria=nombre_categoria.replace(' ', '_')))
    
    return render_template('nueva_categoria.html', form=form)

@app.route('/categoria/editar/<nombre_categoria>', methods=['GET', 'POST'])
@login_requerido
def editar_categoria(nombre_categoria):
    """Renombrar una categoría existente"""
    nombre_categoria = nombre_categoria.replace('_', ' ')
    db = conectar_mongodb()
    
    # Verificar que la categoría existe
    categoria = db.categorias_personalizadas.find_one({
        'usuario_id': session['usuario_id'],
        'nombre': nombre_categoria
    })
    
    if not categoria:
        flash('Categoría no encontrada', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    form = EditarCategoriaForm()
    
    if form.validate_on_submit():
        nuevo_nombre = form.nuevo_nombre.data.strip()
        
        # Verificar que no exista otra con ese nombre
        existe = db.categorias_personalizadas.find_one({
            'usuario_id': session['usuario_id'],
            'nombre': nuevo_nombre
        })
        
        if existe:
            flash(f'Ya existe una categoría llamada "{nuevo_nombre}"', 'warning')
        else:
            # Actualizar nombre en categorías personalizadas
            db.categorias_personalizadas.update_one(
                {'_id': categoria['_id']},
                {'$set': {'nombre': nuevo_nombre}}
            )
            
            # Actualizar todos los artículos con esa categoría
            db.articulos.update_many(
                {
                    'usuario_id': session['usuario_id'],
                    'categoria': nombre_categoria
                },
                {'$set': {'categoria': nuevo_nombre}}
            )
            
            flash(f'Categoría renombrada a "{nuevo_nombre}"', 'success')
            return redirect(url_for('ver_coleccion_por_categoria', 
                                  categoria=nuevo_nombre.replace(' ', '_')))
    
    if request.method == 'GET':
        form.nuevo_nombre.data = nombre_categoria
    
    return render_template('editar_categoria.html', form=form, categoria=nombre_categoria)

@app.route('/categoria/eliminar/<nombre_categoria>', methods=['POST'])
@login_requerido
def eliminar_categoria(nombre_categoria):
    """Eliminar una categoría y mover sus artículos a 'Otros'"""
    nombre_categoria = nombre_categoria.replace('_', ' ')
    db = conectar_mongodb()
    
    # No permitir eliminar 'Otros'
    if nombre_categoria == 'Otros':
        flash('No se puede eliminar la categoría "Otros"', 'danger')
        return redirect(url_for('ver_coleccion'))
    
    # Mover artículos a 'Otros'
    resultado = db.articulos.update_many(
        {
            'usuario_id': session['usuario_id'],
            'categoria': nombre_categoria
        },
        {'$set': {'categoria': 'Otros'}}
    )
    
    # Eliminar de categorías personalizadas
    db.categorias_personalizadas.delete_one({
        'usuario_id': session['usuario_id'],
        'nombre': nombre_categoria
    })
    
    flash(f'Categoría "{nombre_categoria}" eliminada. {resultado.modified_count} artículos movidos a "Otros"', 'success')
    return redirect(url_for('ver_coleccion'))

# ============================================
# EJECUTAR LA APLICACIÓN
# ============================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
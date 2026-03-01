from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, URLField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, URL, ValidationError, Optional, EqualTo
import re

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[
        DataRequired(message="Email obligatorio"),
        Email(message="Email no válido")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="Contraseña obligatoria"),
        Length(min=6, message="Mínimo 6 caracteres")
    ])
    submit = SubmitField('Iniciar Sesión')

class RegisterForm(FlaskForm):
    nombre = StringField('Nombre completo', validators=[
        DataRequired(message="Nombre obligatorio"),
        Length(min=3, max=50, message="Entre 3 y 50 caracteres")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email obligatorio"),
        Email(message="Email no válido")
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message="Contraseña obligatoria"),
        Length(min=6, message="Mínimo 6 caracteres")
    ])
    confirm_password = PasswordField('Confirmar contraseña', validators=[
        DataRequired(message="Confirma tu contraseña"),
        EqualTo('password', message="Las contraseñas no coinciden")
    ])
    submit = SubmitField('Registrarse')
    
    def validate_password(self, field):
        if not re.search(r'[A-Za-z]', field.data) or not re.search(r'\d', field.data):
            raise ValidationError('La contraseña debe contener letras y números')

class ArticuloWikipediaForm(FlaskForm):
    titulo = StringField('Título del artículo', validators=[
        DataRequired(message="El título es obligatorio"),
        Length(min=3, max=200)
    ])
    
    resumen = TextAreaField('Resumen', validators=[
        DataRequired(message="El resumen es obligatorio")
    ])
    
    url = URLField('URL de Wikipedia', validators=[
        DataRequired(message="La URL es obligatoria"),
        URL(message="URL no válida")
    ])
    
    categoria = SelectField('Categoría', choices=[], validators=[
        DataRequired(message="Selecciona una categoría")
    ])
    
    notas = TextAreaField('Mis notas', validators=[Optional()])
    
    submit = SubmitField('Guardar en mi colección')

class NuevaCategoriaForm(FlaskForm):
    nombre = StringField('Nombre de la categoría', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=2, max=50, message="Entre 2 y 50 caracteres")
    ])
    submit = SubmitField('Crear categoría')

class EditarCategoriaForm(FlaskForm):
    nuevo_nombre = StringField('Nuevo nombre', validators=[
        DataRequired(message="El nombre es obligatorio"),
        Length(min=2, max=50, message="Entre 2 y 50 caracteres")
    ])
    submit = SubmitField('Renombrar categoría')
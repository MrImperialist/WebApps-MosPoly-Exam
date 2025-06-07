from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.secret_key = 'devkey'

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# --- Модели ---
class User(UserMixin):
    def __init__(self, id, username, password, role):
        self.id = id
        self.username = username
        self.password_hash = generate_password_hash(password)
        self.role = role
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Фиктивные пользователи
users = {
    'admin': User(1, 'admin', 'admin', 'admin'),
    'tech': User(2, 'tech', 'tech', 'tech'),
    'user': User(3, 'user', 'user', 'user'),
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == str(user_id):
            return user
    return None

# --- Формы ---
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

# --- Фиктивные данные оборудования ---
equipment_list = [
    {'id': 1, 'name': 'Принтер', 'inventory_number': '1001', 'category': 'Печать', 'status': 'Работает'},
    {'id': 2, 'name': 'Сканер', 'inventory_number': '1002', 'category': 'Сканирование', 'status': 'Не работает'},
]

# --- Маршруты ---
@app.route('/')
def index():
    class Dummy:
        role = getattr(current_user, 'role', None)
    # Заглушка
    return render_template('index.html', equipment=equipment_list, pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1}, current_user=current_user if current_user.is_authenticated else Dummy())

@app.route('/equipment')
@login_required
def equipment_list_view():
    class Dummy:
        role = getattr(current_user, 'role', None)
    return render_template('index.html', equipment=equipment_list, pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1}, current_user=current_user)

@app.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    eq = next((e for e in equipment_list if e['id'] == id), None)
    if not eq:
        flash('Оборудование не найдено', 'error')
        return redirect(url_for('index'))
    class DummyForm:
        hidden_tag = lambda self: ''
        date = type('F', (), {'label': 'Дата', '__call__': lambda s: '<input>'})()
        comment = type('F', (), {'label': 'Комментарий', '__call__': lambda s: '<input>'})()
    eq['maintenance'] = []
    return render_template('view-equipment.html', equipment=eq, maintenance_form=DummyForm(), current_user=current_user)

@app.route('/equipment/<int:id>/edit')
@login_required
def edit_equipment(id):
    flash('Редактирование пока не реализовано', 'info')
    return redirect(url_for('view_equipment', id=id))

@app.route('/equipment/<int:id>/delete')
@login_required
def delete_equipment(id):
    flash('Удаление пока не реализовано', 'info')
    return redirect(url_for('index'))

@app.route('/equipment/<int:equipment_id>/maintenance', methods=['POST'])
@login_required
def add_maintenance(equipment_id):
    flash('Добавление обслуживания пока не реализовано', 'info')
    return redirect(url_for('view_equipment', id=equipment_id))

@app.route('/maintenance')
@login_required
def maintenance_list():
    flash('Список обслуживания пока не реализован', 'info')
    return redirect(url_for('index'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        user = users.get(form.username.data)
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Вы успешно вошли', 'success')
            return redirect(url_for('index'))
        else:
            error = True
    return render_template('login.html', form=form, error=error)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True) 
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from models import db, Equipment, Category, ResponsiblePerson, EquipmentPhoto, User
from flask_migrate import Migrate
from sqlalchemy import and_

app = Flask(__name__)
app.secret_key = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:wSpkzSsdTTfQIQROZqrdPjt0ZHGbt08D@dpg-d13hqi49c44c739c6h70-a.frankfurt-postgres.render.com/exam_6vhb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

users = {}

@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Для выполнения данного действия необходимо пройти процедуру аутентификации', 'error')
    return redirect(url_for('login'))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Формы ---
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

# --- Маршруты ---
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    status = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    sort = request.args.get('sort', 'purchase_date')
    order = request.args.get('order', 'desc')

    query = Equipment.query
    if category_id:
        query = query.filter(Equipment.category_id == category_id)
    if status:
        query = query.filter(Equipment.status == status)
    if date_from:
        query = query.filter(Equipment.purchase_date >= date_from)
    if date_to:
        query = query.filter(Equipment.purchase_date <= date_to)
    if sort == 'purchase_date':
        if order == 'desc':
            query = query.order_by(Equipment.purchase_date.desc())
        else:
            query = query.order_by(Equipment.purchase_date.asc())
    else:
        query = query.order_by(Equipment.purchase_date.desc())

    pagination = query.paginate(page=page, per_page=10, error_out=False)
    equipment = pagination.items
    categories = Category.query.all()
    statuses = [choice for choice in Equipment.status.type.enums]
    return render_template('index.html', equipment=equipment, pagination=pagination, categories=categories, statuses=statuses, current_user=current_user)

@app.route('/equipment')
@login_required
def equipment_list_view():
    class Dummy:
        role = getattr(current_user, 'role', None)
    return render_template('index.html', equipment=Equipment.query.all(), pagination={'has_prev': False, 'has_next': False, 'page': 1, 'pages': 1}, current_user=current_user)

@app.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    eq = Equipment.query.get(id)
    if not eq:
        flash('Оборудование не найдено', 'error')
        return redirect(url_for('index'))
    class DummyForm:
        hidden_tag = lambda self: ''
        date = type('F', (), {'label': 'Дата', '__call__': lambda s: '<input>'})()
        comment = type('F', (), {'label': 'Комментарий', '__call__': lambda s: '<input>'})()
    eq.maintenance = []
    return render_template('view-equipment.html', equipment=eq, maintenance_form=DummyForm(), current_user=current_user)

@app.route('/equipment/<int:id>/edit')
@login_required
def edit_equipment(id):
    flash('Редактирование пока не реализовано', 'info')
    return redirect(url_for('view_equipment', id=id))

@app.route('/equipment/<int:id>/delete', methods=['POST'])
@login_required
def delete_equipment(id):
    if not current_user.is_authenticated or current_user.role != 'admin':
        flash('У вас недостаточно прав для выполнения данного действия', 'error')
        return redirect(url_for('index'))
    eq = Equipment.query.get_or_404(id)
    # Удаление связанных фото и файлов
    for photo in eq.photos:
        db.session.delete(photo)
    db.session.delete(eq)
    db.session.commit()
    flash('Оборудование успешно удалено', 'success')
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
        user = User.query.filter_by(username=form.username.data).first()
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
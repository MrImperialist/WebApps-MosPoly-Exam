import os
import io
import csv
import hashlib
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, DecimalField, RadioField, TextAreaField
from wtforms.fields import DateField, FileField
from wtforms.validators import DataRequired, Optional
from flask_sqlalchemy import SQLAlchemy
from models import db, Equipment, Category, ResponsiblePerson, EquipmentPhoto, User, MaintenanceHistory
from flask_migrate import Migrate
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.jinja_env.add_extension('jinja2.ext.do')
app.secret_key = 'devkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:wSpkzSsdTTfQIQROZqrdPjt0ZHGbt08D@dpg-d13hqi49c44c739c6h70-a.frankfurt-postgres.render.com/exam_6vhb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Для выполнения данного действия необходимо пройти процедуру аутентификации.'
login_manager.login_message_category = "error"

# --- Декораторы прав доступа ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('У вас недостаточно прав для выполнения данного действия.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def tech_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'tech']:
            flash('У вас недостаточно прав для выполнения данного действия.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Формы ---
class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class EquipmentForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired()])
    inventory_number = StringField('Инвентарный номер', validators=[DataRequired()])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    purchase_date = DateField('Дата покупки', format='%Y-%m-%d', validators=[DataRequired()])
    cost = DecimalField('Стоимость', validators=[DataRequired()])
    status = RadioField('Статус', validators=[DataRequired()])
    note = TextAreaField('Примечание', validators=[Optional()])
    photo = FileField('Фотография оборудования', validators=[Optional()])
    submit = SubmitField('Сохранить')

class MaintenanceForm(FlaskForm):
    date = DateField('Дата обслуживания', format='%Y-%m-%d', validators=[DataRequired()])
    maintenance_type = StringField('Тип обслуживания', validators=[DataRequired()])
    comment = TextAreaField('Комментарий', validators=[DataRequired()])
    submit = SubmitField('Добавить запись')


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


@app.route('/equipment/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_equipment():
    return manage_equipment()

@app.route('/equipment/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_equipment(id):
    return manage_equipment(id)

def manage_equipment(id=None):
    if id:
        equipment = Equipment.query.get_or_404(id)
        form = EquipmentForm(obj=equipment)
        form.photo.validators = [Optional()]
        form_title = "Редактирование оборудования"
    else:
        equipment = Equipment()
        form = EquipmentForm()
        form_title = "Добавление оборудования"

    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by('name').all()]
    form.status.choices = [(s, s) for s in Equipment.status.type.enums]

    if form.validate_on_submit():
        try:
            form.populate_obj(equipment)
            
            if not id:
                db.session.add(equipment)

            photo_file = form.photo.data
            if photo_file:
                file_content = photo_file.read()
                md5_hash = hashlib.md5(file_content).hexdigest()
                
                existing_photo = EquipmentPhoto.query.filter_by(md5_hash=md5_hash).first()
                
                if existing_photo:
                    if existing_photo not in equipment.photos:
                        equipment.photos.append(existing_photo)
                else:
                    new_photo = EquipmentPhoto(
                        filename='temp',
                        mime_type=photo_file.mimetype,
                        md5_hash=md5_hash
                        )
                    equipment.photos.append(new_photo)
                    db.session.add(new_photo)
                    db.session.flush() 
                    
                    _, extension = os.path.splitext(secure_filename(photo_file.filename))
                    filename = f"{new_photo.id}{extension}"
                    new_photo.filename = filename
                    
                    photo_file.seek(0)
                    photo_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            db.session.commit()
            
            flash('Данные об оборудовании сохранены', 'success')
            return redirect(url_for('view_equipment', id=equipment.id))

        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error: {e}")
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.', 'error')
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"An unexpected error occurred: {e}")
            flash('При сохранении данных возникла непредвиденная ошибка.', 'error')
    
    return render_template('equipment-form.html', form=form, form_title=form_title)


@app.route('/equipment/<int:id>')
@login_required
def view_equipment(id):
    eq = Equipment.query.get_or_404(id)
    form = MaintenanceForm()
    return render_template('view-equipment.html', equipment=eq, current_user=current_user, maintenance_form=form)


@app.route('/equipment/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_equipment(id):
    eq = Equipment.query.get_or_404(id)
    try:
        # Удаление связанных записей обслуживания
        MaintenanceHistory.query.filter_by(equipment_id=id).delete()

        for photo in eq.photos:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)
            if os.path.exists(file_path):
                os.remove(file_path)
        
        db.session.delete(eq)
        db.session.commit()
        flash('Оборудование удалено', 'success')
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting equipment: {e}")
        flash('Произошла ошибка при удалении оборудования.', 'error')

    return redirect(url_for('index'))

@app.route('/equipment/<int:equipment_id>/maintenance/add', methods=['GET', 'POST'])
@login_required
@tech_or_admin_required
def add_maintenance(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    form = MaintenanceForm()
    
    if form.validate_on_submit():
        try:
            new_record = MaintenanceHistory(
                equipment_id=equipment.id,
                date=form.date.data,
                maintenance_type=form.maintenance_type.data,
                comment=form.comment.data
            )
            db.session.add(new_record)
            db.session.commit()
            flash('Запись об обслуживании успешно добавлена.', 'success')
            return redirect(url_for('view_equipment', id=equipment_id))
        except SQLAlchemyError as e:
            db.session.rollback()
            app.logger.error(f"Database error on adding maintenance: {e}")
            flash('При добавлении записи возникла ошибка.', 'error')

    return render_template('maintenance-form.html', form=form, equipment=equipment)


@app.route('/maintenance')
@login_required
@tech_or_admin_required
def maintenance_list():
    page = request.args.get('page', 1, type=int)
    query = MaintenanceHistory.query.order_by(MaintenanceHistory.date.desc())
    pagination = query.paginate(page=page, per_page=15, error_out=False)
    records = pagination.items
    return render_template('maintenance-list.html', records=records, pagination=pagination)


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

@app.route('/export/csv')
@login_required
@admin_required
def export_csv():    
    string_io = io.StringIO()
    csv_writer = csv.writer(string_io)
    headers = [
        'Название', 'Инвентарный номер', 'Категория', 'Дата покупки', 'Статус',
        'Первоначальная стоимость', 'Накопленная амортизация', 'Текущая стоимость'
    ]
    csv_writer.writerow(headers)
    
    all_equipment = Equipment.query.all()
    
    for item in all_equipment:
        row = [
            item.name,
            item.inventory_number,
            item.category.name,
            item.purchase_date.strftime('%Y-%m-%d'),
            item.status,
            f"{item.cost:.2f}",
            f"{item.accumulated_depreciation:.2f}",
            f"{item.current_value:.2f}"
        ]
        csv_writer.writerow(row)
        
    output = string_io.getvalue()
    response = Response(output.encode('utf-8-sig'), mimetype='text/csv')
    response.headers["Content-Disposition"] = "attachment; filename=equipment_export.csv"
    
    return response

if __name__ == '__main__':
    app.run(debug=True)
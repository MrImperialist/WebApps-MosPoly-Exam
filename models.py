from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Numeric
from flask_login import UserMixin
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

db = SQLAlchemy()

equipment_status_enum = ENUM('В эксплуатации', 'На ремонте', 'Списано', name='equipment_status', create_type=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String)

class ResponsiblePerson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String, nullable=False)
    position = db.Column(db.String, nullable=False)
    contact_info = db.Column(db.String, nullable=False)

equipment_responsible = db.Table('equipment_responsible',
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id'), primary_key=True),
    db.Column('responsible_id', db.Integer, db.ForeignKey('responsible_person.id'), primary_key=True)
)

equipment_photos_association = db.Table('equipment_photos_association',
    db.Column('equipment_id', db.Integer, db.ForeignKey('equipment.id', ondelete="CASCADE"), primary_key=True),
    db.Column('photo_id', db.Integer, db.ForeignKey('equipment_photo.id', ondelete="CASCADE"), primary_key=True)
)

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    inventory_number = db.Column(db.String, unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    purchase_date = db.Column(db.Date, nullable=False)
    cost = db.Column(Numeric, nullable=False)
    status = db.Column(equipment_status_enum, nullable=False)
    category = db.relationship('Category', backref='equipments')
    responsible = db.relationship('ResponsiblePerson', secondary=equipment_responsible, backref='equipments')
    photos = db.relationship('EquipmentPhoto', secondary=equipment_photos_association, backref='equipments')

    @property
    def months_in_use(self):
        today = date.today()
        # разница в годах * 12 + разница в месяцах
        return (today.year - self.purchase_date.year) * 12 + today.month - self.purchase_date.month

    @property
    def accumulated_depreciation(self):
        USEFUL_LIFE_MONTHS = 60
        cost = Decimal(self.cost)
        
        if self.months_in_use <= 0 or cost == 0:
            return Decimal('0.00')
            
        monthly_depreciation = cost / USEFUL_LIFE_MONTHS
        total_depreciation = monthly_depreciation * self.months_in_use
        
        # Амортизация не может превышать стоимость
        return min(cost, total_depreciation).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    @property
    def current_value(self):
        cost = Decimal(self.cost)
        current_val = cost - self.accumulated_depreciation
        return current_val.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class EquipmentPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    mime_type = db.Column(db.String, nullable=False)
    md5_hash = db.Column(db.String, unique=True, nullable=False)

class MaintenanceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    maintenance_type = db.Column(db.String, nullable=False)
    comment = db.Column(db.String)
    equipment = db.relationship('Equipment', backref='maintenance_history')

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, nullable=False)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

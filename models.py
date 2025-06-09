from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy import Numeric
from flask_login import UserMixin

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

class EquipmentPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String, nullable=False)
    mime_type = db.Column(db.String, nullable=False)
    md5_hash = db.Column(db.String, nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    equipment = db.relationship('Equipment', backref='photos')

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

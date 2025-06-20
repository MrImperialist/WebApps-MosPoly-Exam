"""Initial migration

Revision ID: a3a6d89ebe76
Revises: 
Create Date: 2025-06-09 21:10:09.190035

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a3a6d89ebe76'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('category',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('responsible_person',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('full_name', sa.String(), nullable=False),
    sa.Column('position', sa.String(), nullable=False),
    sa.Column('contact_info', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('password_hash', sa.String(), nullable=False),
    sa.Column('role', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('username')
    )
    op.create_table('equipment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('inventory_number', sa.String(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('purchase_date', sa.Date(), nullable=False),
    sa.Column('cost', sa.Numeric(), nullable=False),
    sa.Column('status', postgresql.ENUM('В эксплуатации', 'На ремонте', 'Списано', name='equipment_status'), nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['category.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('inventory_number')
    )
    op.create_table('equipment_photo',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('mime_type', sa.String(), nullable=False),
    sa.Column('md5_hash', sa.String(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('equipment_responsible',
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('responsible_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
    sa.ForeignKeyConstraint(['responsible_id'], ['responsible_person.id'], ),
    sa.PrimaryKeyConstraint('equipment_id', 'responsible_id')
    )
    op.create_table('maintenance_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('maintenance_type', sa.String(), nullable=False),
    sa.Column('comment', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipment.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('maintenance_history')
    op.drop_table('equipment_responsible')
    op.drop_table('equipment_photo')
    op.drop_table('equipment')
    op.drop_table('user')
    op.drop_table('responsible_person')
    op.drop_table('category')
    # ### end Alembic commands ###

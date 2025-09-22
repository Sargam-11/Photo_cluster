"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create persons table
    op.create_table('persons',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=False),
        sa.Column('photo_count', sa.Integer(), nullable=False),
        sa.Column('face_embedding', sa.ARRAY(sa.Float()), nullable=False),
        sa.Column('cluster_confidence', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create photos table
    op.create_table('photos',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('original_url', sa.String(length=500), nullable=False),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=False),
        sa.Column('web_url', sa.String(length=500), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('width', sa.Integer(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('taken_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processed', sa.Boolean(), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create face_detections table
    op.create_table('face_detections',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('photo_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('person_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('bounding_box', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('face_embedding', sa.ARRAY(sa.Float()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['person_id'], ['persons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['photo_id'], ['photos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_photos_filename', 'photos', ['filename'])
    op.create_index('ix_photos_processed', 'photos', ['processed'])
    op.create_index('ix_face_detections_photo_id', 'face_detections', ['photo_id'])
    op.create_index('ix_face_detections_person_id', 'face_detections', ['person_id'])
    op.create_index('ix_persons_photo_count', 'persons', ['photo_count'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_persons_photo_count', table_name='persons')
    op.drop_index('ix_face_detections_person_id', table_name='face_detections')
    op.drop_index('ix_face_detections_photo_id', table_name='face_detections')
    op.drop_index('ix_photos_processed', table_name='photos')
    op.drop_index('ix_photos_filename', table_name='photos')
    
    # Drop tables
    op.drop_table('face_detections')
    op.drop_table('photos')
    op.drop_table('persons')
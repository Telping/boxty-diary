from app import db
from datetime import datetime

class DiaryEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    location_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    media = db.relationship('Media', backref='entry', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', secondary='entry_tags', backref='entries', lazy=True)

    def __repr__(self):
        return f'<DiaryEntry {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'date': self.date.isoformat(),
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_name': self.location_name,
            'media': [m.to_dict() for m in self.media],
            'tags': [t.name for t in self.tags]
        }


class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)  # 'image' or 'video'
    file_path = db.Column(db.String(500), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('diary_entry.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Media {self.filename}>'

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'media_type': self.media_type,
            'file_path': self.file_path,
            'uploaded_at': self.uploaded_at.isoformat()
        }


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'


# Association table for many-to-many relationship
entry_tags = db.Table('entry_tags',
    db.Column('entry_id', db.Integer, db.ForeignKey('diary_entry.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

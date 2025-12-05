from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from app import db
from app.models import DiaryEntry, Media, Tag
from werkzeug.utils import secure_filename
import os
from datetime import datetime

main = Blueprint('main', __name__)

ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm'}

def allowed_file(filename, file_type):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False


@main.route('/')
def index():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return render_template('index.html', entries=entries)


@main.route('/entry/new', methods=['GET', 'POST'])
def new_entry():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        date_str = request.form.get('date')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        location_name = request.form.get('location_name')
        tags_str = request.form.get('tags', '')

        # Parse date
        entry_date = datetime.fromisoformat(date_str) if date_str else datetime.utcnow()

        # Create entry
        entry = DiaryEntry(
            title=title,
            description=description,
            date=entry_date,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            location_name=location_name
        )

        # Handle tags
        if tags_str:
            tag_names = [t.strip() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                entry.tags.append(tag)

        db.session.add(entry)
        db.session.flush()  # Get entry.id

        # Handle file uploads
        files = request.files.getlist('media')
        upload_folder = os.path.join('app', 'static', 'uploads')

        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp}_{filename}"

                # Determine media type
                if allowed_file(file.filename, 'image'):
                    media_type = 'image'
                elif allowed_file(file.filename, 'video'):
                    media_type = 'video'
                else:
                    continue

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # Save to database
                media = Media(
                    filename=filename,
                    media_type=media_type,
                    file_path=f'uploads/{filename}',
                    entry_id=entry.id
                )
                db.session.add(media)

        db.session.commit()
        flash('Diary entry created successfully!', 'success')
        return redirect(url_for('main.index'))

    return render_template('new_entry.html')


@main.route('/entry/<int:entry_id>')
def view_entry(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)
    return render_template('view_entry.html', entry=entry)


@main.route('/entry/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    entry = DiaryEntry.query.get_or_404(entry_id)

    # Delete associated media files
    upload_folder = os.path.join('app', 'static', 'uploads')
    for media in entry.media:
        file_path = os.path.join(upload_folder, media.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    db.session.delete(entry)
    db.session.commit()
    flash('Diary entry deleted successfully!', 'success')
    return redirect(url_for('main.index'))


@main.route('/map')
def map_view():
    entries = DiaryEntry.query.filter(
        DiaryEntry.latitude.isnot(None),
        DiaryEntry.longitude.isnot(None)
    ).all()
    return render_template('map.html', entries=entries)


@main.route('/api/entries')
def api_entries():
    entries = DiaryEntry.query.order_by(DiaryEntry.date.desc()).all()
    return jsonify([entry.to_dict() for entry in entries])


@main.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join('app', 'static', 'uploads')
    return send_from_directory(upload_folder, filename)

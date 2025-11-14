from flask_socketio import join_room, emit
from flask_login import current_user
from flask import request

# Handlers are registered on import because SocketIO was initialized in app.__init__
from app import socketio
from app.utils.security import rate_limit


@socketio.on('connect')
def handle_connect():
    # Optionally authenticate here; for now, accept and let client join rooms explicitly
    emit('connected', {'ok': True})


@socketio.on('join_patient_room')
def handle_join_patient_room(data):
    try:
        patient_id = int(data.get('patient_id')) if data else None
    except Exception:
        patient_id = None
    if not patient_id:
        emit('error', {'message': 'patient_id required'})
        return
    room = f"patient_{patient_id}"
    join_room(room)
    emit('joined_room', {'room': room}, to=room)


@socketio.on('typing')
def handle_typing(data):
    # Broadcast typing indicator to the same room
    patient_id = (data or {}).get('patient_id')
    if not patient_id:
        return
    room = f"patient_{patient_id}"
    emit('typing', {
        'patient_id': patient_id,
        'user_id': getattr(current_user, 'id', None)
    }, to=room, include_self=False)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    patient_id = (data or {}).get('patient_id')
    if not patient_id:
        return
    room = f"patient_{patient_id}"
    emit('stop_typing', {
        'patient_id': patient_id,
        'user_id': getattr(current_user, 'id', None)
    }, to=room, include_self=False)


@socketio.on('mark_read')
@rate_limit(max_requests=30, window_seconds=60)
def handle_mark_read(data):
    """Mark message(s) as read and broadcast read receipt to room"""
    from app import db
    from app.models import Message
    from datetime import datetime
    # rate_limit decorator imported at module level
    
    message_id = (data or {}).get('message_id')
    patient_id = (data or {}).get('patient_id')
    
    if not message_id or not patient_id:
        emit('error', {'message': 'message_id and patient_id required'})
        return
    
    # Update message in DB
    msg = Message.query.get(message_id)
    if msg and not msg.is_read:
        msg.is_read = True
        msg.read_at = datetime.utcnow()
        db.session.commit()
        
        # Broadcast read receipt to room
        room = f"patient_{patient_id}"
        emit('message_read', {
            'message_id': message_id,
            'patient_id': patient_id,
            'read_at': msg.read_at.strftime('%d.%m.%Y %H:%M'),
            'reader_id': getattr(current_user, 'id', None)
        }, to=room)

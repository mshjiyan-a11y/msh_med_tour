"""Real-time lead updates via WebSocket/SocketIO"""

from flask import request
from flask_socketio import emit, join_room, leave_room
from app import socketio, db
from app.models.meta_lead import FacebookLead
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)

# Active WebSocket connections tracking
LEAD_ROOMS = {}  # {user_id: {lead_id, ...}}


@socketio.on('connect', namespace='/facebook-leads')
def connect():
    """User connects to real-time leads"""
    if not current_user.is_authenticated:
        return False
    
    if not getattr(current_user, 'is_superadmin', False)():
        return False
    
    user_id = current_user.id
    emit('connected', {'data': f'User {user_id} connected to leads stream'})
    logger.info(f"User {user_id} connected to real-time leads")


@socketio.on('join_lead', namespace='/facebook-leads')
def join_lead(data):
    """Join specific lead room for updates"""
    if not current_user.is_authenticated or not getattr(current_user, 'is_superadmin', False)():
        return
    
    user_id = current_user.id
    lead_id = data.get('lead_id')
    room = f'lead_{lead_id}'
    
    join_room(room)
    
    if user_id not in LEAD_ROOMS:
        LEAD_ROOMS[user_id] = set()
    LEAD_ROOMS[user_id].add(lead_id)
    
    logger.info(f"User {user_id} joined lead {lead_id} room")
    emit('joined', {'lead_id': lead_id})


@socketio.on('leave_lead', namespace='/facebook-leads')
def leave_lead(data):
    """Leave specific lead room"""
    if not current_user.is_authenticated:
        return
    
    user_id = current_user.id
    lead_id = data.get('lead_id')
    room = f'lead_{lead_id}'
    
    leave_room(room)
    
    if user_id in LEAD_ROOMS:
        LEAD_ROOMS[user_id].discard(lead_id)
    
    logger.info(f"User {user_id} left lead {lead_id} room")


def broadcast_lead_update(lead_id, event_type, data=None):
    """Broadcast lead update to all subscribed users"""
    room = f'lead_{lead_id}'
    
    message = {
        'lead_id': lead_id,
        'event_type': event_type,
        'timestamp': db.func.now(),
    }
    
    if data:
        message.update(data)
    
    socketio.emit(
        'lead_updated',
        message,
        room=room,
        namespace='/facebook-leads'
    )
    
    logger.debug(f"Broadcast update for lead {lead_id}: {event_type}")


def broadcast_lead_created(lead):
    """Broadcast new lead to dashboard"""
    socketio.emit(
        'lead_created',
        {
            'lead_id': lead.id,
            'name': lead.full_name(),
            'email': lead.email,
            'phone': lead.phone,
            'distributor_id': lead.distributor_id,
            'status': lead.status
        },
        room='leads_dashboard',
        namespace='/facebook-leads'
    )


def broadcast_stats_update():
    """Broadcast updated statistics"""
    from app.models.meta_lead import FacebookLead
    
    stats = {
        'total': FacebookLead.query.count(),
        'new': FacebookLead.query.filter_by(status='new').count(),
        'assigned': FacebookLead.query.filter_by(status='assigned').count(),
        'contacted': FacebookLead.query.filter_by(status='contacted').count(),
        'converted': FacebookLead.query.filter_by(status='converted').count(),
        'rejected': FacebookLead.query.filter_by(status='rejected').count(),
    }
    
    socketio.emit(
        'stats_updated',
        stats,
        room='leads_dashboard',
        namespace='/facebook-leads'
    )


@socketio.on('disconnect', namespace='/facebook-leads')
def disconnect():
    """User disconnects"""
    if current_user.is_authenticated:
        user_id = current_user.id
        if user_id in LEAD_ROOMS:
            del LEAD_ROOMS[user_id]
        logger.info(f"User {user_id} disconnected from real-time leads")

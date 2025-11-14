from app import create_app, socketio

app = create_app()

# Setup Meta Lead Sync Scheduler
try:
    from app.utils.meta_scheduler import setup_meta_scheduler
    scheduler = setup_meta_scheduler()
except Exception as e:
    print(f"Warning: Could not setup Meta scheduler: {e}")
    scheduler = None

if __name__ == '__main__':
    # Use SocketIO server to enable real-time features
    socketio.run(app, debug=True)
from flask_socketio import emit, join_room, leave_room
from flask import request

def register_socketio_events(socketio_instance):
    @socketio_instance.on('connect')
    def handle_connect(auth_data=None):
        print(f"Client connected: {request.sid}")
        emit('status', {'message': 'Connected to alerts. Please join a room.'}, room=request.sid)

    @socketio_instance.on('join_alert_room')
    def on_join(data):
        user_id = data.get('user_id')
        if user_id:
            room_name = f'user_alerts_{user_id}'
            join_room(room_name)
            print(f"User {user_id} (sid: {request.sid}) explicitly joined room {room_name}")
            emit('status', {'message': f'Successfully joined alert room: {room_name}.'}, room=request.sid)
        else:
            emit('error', {'message': 'user_id is required to join an alert room.'}, room=request.sid)

    @socketio_instance.on('disconnect')
    def handle_disconnect():
        print(f"Client disconnected: {request.sid}")

def push_alert_to_clinician(socketio_instance, clinician_user_id: int, alert_data: dict):
    if not socketio_instance:
        print("Error: SocketIO instance not available for pushing alert.")
        return
    room_name = f'user_alerts_{clinician_user_id}'
    try:
        socketio_instance.emit('new_alert', alert_data, room=room_name)
        print(f"Pushed alert to room {room_name}: {alert_data.get('message', 'N/A')}")
    except Exception as e:
        print(f"Error pushing alert to room {room_name}: {str(e)}")

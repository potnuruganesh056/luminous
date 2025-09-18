# Part 2 of API routes - AI control, user settings, and email functions
import time
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.redis_db import get_all_data_from_db, save_all_data_to_db, get_all_users_from_db, save_all_users_to_db
from utils.helpers import get_user_data, save_user_data
from mqtt.client import mqtt_client
from config import Config
from utils.email_helper import send_detection_email_thread

ai_api_bp = Blueprint('ai_api', __name__)

@ai_api_bp.route('/global-ai-signal', methods=['POST'])
@login_required # It's safer to require a login for this
def global_ai_signal():
    data = request.get_json()
    if data is None or 'state' not in data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    human_detected = data.get('state', False)
    
    try:
        # MODIFICATION: Use Redis helpers
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        # Iterate through the rooms of the current user
        for room in user_data.get('rooms', []):
            for appliance in room.get('appliances', []):
                if not appliance.get('locked', False):
                    appliance['state'] = human_detected
        
        save_all_data_to_db(all_data)
        
        # ... (your MQTT logic) ...
        if mqtt_client:
            mqtt_client.publish(Config.MQTT_TOPIC_COMMAND, f"global:all:ai:{int(human_detected)}")

        # Line around global_ai_signal function - these variables are used but not defined:
        action_str = "ON" if human_detected else "OFF"  # Add this line
        updated_count = sum(1 for room in user_data.get('rooms', []) 
                           for appliance in room.get('appliances', []) 
                           if not appliance.get('locked', False))  # Add this line
        
        message = f"Global signal processed. Turned {action_str} {updated_count} unlocked appliances."
        return jsonify({"status": "success", "message": message}), 200
        
    except Exception as e:
        current_app.logger.error(f"Error in global_ai_signal: {e}")
        return jsonify({"status": "error", "message": "An internal error occurred"}), 500

@ai_api_bp.route('/get-user-settings', methods=['GET'])
@login_required
def get_user_settings():
    """
    Fetches all settings for the current user from the Redis database.
    """
    try:
        # 1. Get the user's application data (settings, rooms, etc.) from the 'data' key in Redis
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id, {})
        settings = user_data.get('user_settings', {})

        # 2. Get the user's authentication record (for google_id, etc.) from the 'users' key in Redis
        all_users = get_all_users_from_db()
        user_record = next((u for u in all_users if u.get('id') == current_user.id), None)

        # 3. Merge the information into one object for the frontend
        if user_record:
            settings['google_id'] = user_record.get('google_id')
            settings['github_id'] = user_record.get('github_id')
            settings['has_password'] = user_record.get('password_hash') is not None
        
        return jsonify(settings), 200
    except Exception as e:
        print(f"Error in /api/get-user-settings: {e}")
        return jsonify({"status": "error", "message": "Could not load user settings."}), 500
        
@ai_api_bp.route('/set-user-settings', methods=['POST'])
@login_required
def set_user_settings():
    try:
        new_settings = request.json
        user_data = get_user_data()
        user_data['user_settings'].update(new_settings)
        save_user_data(user_data)
        return jsonify({"status": "success", "message": "Settings updated."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_api_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data_from_request = request.json
        new_password = data_from_request['new_password']
        
        # MODIFICATION: Use the new Redis helper functions
        all_users = get_all_users_from_db()
        user_found = next((user for user in all_users if user['id'] == current_user.id), None)
        
        if not user_found:
            return jsonify({"status": "error", "message": "User not found."}), 404

        # Logic for setting a password for the first time (for OAuth users)
        if not user_found.get('password_hash'):
            user_found['password_hash'] = generate_password_hash(new_password)
            save_all_users_to_db(all_users)
            return jsonify({"status": "success", "message": "Password set successfully."}), 200

        # Logic for changing an existing password
        old_password = data_from_request.get('old_password')
        if not old_password or not check_password_hash(user_found['password_hash'], old_password):
            return jsonify({"status": "error", "message": "Invalid old password."}), 400
            
        user_found['password_hash'] = generate_password_hash(new_password)
        save_all_users_to_db(all_users)
        return jsonify({"status": "success", "message": "Password updated successfully."}), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_api_bp.route('/set-global-ai-control', methods=['POST'])
@login_required
def set_global_ai_control():
    try:
        data_from_request = request.json
        state = data_from_request['state']
        user_data = get_user_data()

        for room in user_data['rooms']:
            room['ai_control'] = state
        
        save_user_data(user_data)
        
        action = "enabled" if state else "disabled"
        message = f"AI control for all rooms has been {action}."
        
        return jsonify({"status": "success", "message": message}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_api_bp.route('/ai-detection-signal', methods=['POST'])
@login_required
def ai_detection_signal():
    try:
        data_from_request = request.json
        room_id = data_from_request.get('room_id') # Can be None for global
        state = data_from_request['state']
        
        user_data = get_user_data()

        if room_id:
            # Per-room control
            room = next((r for r in user_data['rooms'] if r['id'] == room_id), None)
            if not room:
                return jsonify({"status": "error", "message": "Room not found."}), 404
            
            for appliance in room['appliances']:
                if not appliance['locked']:
                    appliance['state'] = state
        else:
            # Global control
            for room in user_data['rooms']:
                for appliance in room['appliances']:
                    if not appliance['locked']:
                        appliance['state'] = state

        user_data['last_command'] = {
            "room_id": room_id,
            "state": state,
            "timestamp": int(time.time())
        }
        
        save_user_data(user_data)

        if mqtt_client:
            topic_payload = f"{current_user.id}:{room_id or 'all'}:ai:{int(state)}"
            mqtt_client.publish(Config.MQTT_TOPIC_COMMAND, topic_payload)

        action = "activated" if state else "deactivated"
        message = f"AI control has been {action}."
        
        return jsonify({"status": "success", "message": message}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@ai_api_bp.route('/send-detection-email', methods=['POST'])
@login_required
def send_detection_email():
    try:
        data_from_request = request.json
        room_name = data_from_request.get('room_name')
        is_global = data_from_request.get('is_global', False)
        image_data = data_from_request['image_data']
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_data = get_user_data()
        recipient_email = user_data['user_settings']['email']
        
        if not recipient_email:
            print("No recipient email found in user settings. Email not sent.")
            return jsonify({"status": "error", "message": "User email not set for notifications."}), 400
        
        if is_global:
            subject = "Luminous Home System Alert: Human Detected at Home"
            message_text = "A human has been detected at your home. All unlocked appliances have been activated."
        else:
            subject = "Luminous Home System Alert: Motion Detected!"
            message_text = f"Motion has been detected in your room: {room_name}"

        body_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #fff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);">
                    <h2 style="color: #d9534f;">Luminous Home System Alert!</h2>
                    <hr style="border: 1px solid #ddd;">
                    <p>Dear {current_user.username},</p>
                    <p>This is an automated alert from your Luminous Home System.</p>
                    <p>{message_text}</p>
                    <p>Time of detection: <strong>{timestamp}</strong></p>
                    <p>Please find the captured image attached below:</p>
                    <img src="cid:myimage" alt="Motion Detection Alert" style="max-width: 100%; height: auto; border-radius: 5px;">
                </div>
            </body>
        </html>
        """
        
        send_detection_email_thread(recipient_email, subject, body_html, image_data)
        
        print("API call to send email initiated.")
        return jsonify({"status": "success", "message": "Email alert sent."}), 200
        
    except Exception as e:
        print(f"Error in send_detection_email endpoint: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

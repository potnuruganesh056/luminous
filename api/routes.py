import time
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database.redis_db import get_all_data_from_db, save_all_data_to_db, get_all_users_from_db, save_all_users_to_db
from utils.helpers import get_user_data, save_user_data
from mqtt.client import mqtt_client
from config import Config
from utils.email_helper import send_detection_email_thread
from analytics.data_processing import load_analytics_data, calculate_statistics

api_bp = Blueprint('api', __name__)

@api_bp.route('/esp/check-in', methods=['GET'])
def check_in():
    # MODIFICATION: Use Redis helpers
    all_data = get_all_data_from_db()
    user_id = request.args.get('user_id')
    user_data = all_data.get(user_id, {})
    last_command = user_data.get('last_command', {})
    
    if last_command and last_command.get('timestamp', 0) > user_data.get('last_command_sent_time', 0):
        user_data['last_command_sent_time'] = last_command['timestamp']
        save_all_data_to_db(all_data)
        return jsonify(last_command), 200
    
    return jsonify({}), 200
    
@api_bp.route('/add-appliance', methods=['POST'])
@login_required
def add_appliance():
    try:
        data = request.get_json()
        # 1. Validate Input
        if not all(k in data for k in ['room_id', 'name', 'relay_number']):
            return jsonify({"status": "error", "message": "Missing required fields."}), 400
        
        room_id = data['room_id']
        appliance_name = data['name']
        relay_number = int(data['relay_number'])

        # 2. Load Data
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        # 3. Find & Modify
        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404
            
        new_appliance_id = str(int(time.time() * 1000)) # Unique ID based on timestamp

        room['appliances'].append({
            "id": new_appliance_id, "name": appliance_name, "state": False,
            "locked": False, "timer": None, "relay_number": relay_number
        })
        
        # 4. Save Data
        save_all_data_to_db(all_data)
        
        return jsonify({"status": "success", "appliance_id": new_appliance_id}), 200
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"status": "error", "message": f"Invalid request data: {e}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

@api_bp.route('/get-rooms-and-appliances', methods=['GET'])
@login_required
def get_rooms_and_appliances():
    all_data = get_all_data_from_db()
    user_data = all_data.get(current_user.id, {})
    return jsonify(user_data.get('rooms', []))

@api_bp.route('/update-room-settings', methods=['POST'])
@login_required
def update_room_settings():
    try:
        req_data = request.get_json()
        room_id = req_data['room_id']
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404
        
        if 'name' in req_data:
            room['name'] = req_data['name']
        if 'ai_control' in req_data:
            room['ai_control'] = req_data['ai_control']
            
        save_all_data_to_db(all_data)
        
        return jsonify({"status": "success", "message": "Room settings updated."}), 200
    except (KeyError, TypeError):
        return jsonify({"status": "error", "message": "Invalid request data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500
        
@api_bp.route('/delete-room', methods=['POST'])
@login_required
def delete_room():
    try:
        room_id = request.json['room_id']
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        original_room_count = len(user_data.get('rooms', []))
        user_data['rooms'] = [r for r in user_data.get('rooms', []) if r['id'] != room_id]

        if len(user_data['rooms']) == original_room_count:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Room deleted."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Missing room_id."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

@api_bp.route('/add-room', methods=['POST'])
@login_required
def add_room():
    try:
        data_from_request = request.json
        room_name = data_from_request['name']
        user_data = get_user_data()
        new_room_id = str(len(user_data['rooms']) + 1)
        user_data['rooms'].append({"id": new_room_id, "name": room_name, "ai_control": False, "appliances": []})
        save_user_data(user_data)
        return jsonify({"status": "success", "room_id": new_room_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/delete-appliance', methods=['POST'])
@login_required
def delete_appliance():
    try:
        data = request.get_json()
        room_id = data['room_id']
        appliance_id = data['appliance_id']

        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        original_app_count = len(room.get('appliances', []))
        room['appliances'] = [a for a in room.get('appliances', []) if a['id'] != appliance_id]
        
        if len(room['appliances']) == original_app_count:
             return jsonify({"status": "error", "message": "Appliance not found."}), 404

        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Appliance deleted."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Missing room_id or appliance_id."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500
        
@api_bp.route('/set-appliance-state', methods=['POST'])
@login_required
def set_appliance_state():
    try:
        data = request.get_json()
        
        # 1. Input Validation: Check for required keys
        if not all(k in data for k in ['room_id', 'appliance_id', 'state']):
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        room_id = data['room_id']
        appliance_id = data['appliance_id']
        state = data['state']
        
        # 2. Load data and find the specific user's records
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404
        
        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404
            
        appliance = next((a for a in room.get('appliances', []) if a['id'] == appliance_id), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404
            
        # 3. Apply the changes
        appliance['state'] = state
        if not state:
            appliance['timer'] = None # Clear timer when turned off

        # 4. Save the entire data object back to Redis
        save_all_data_to_db(all_data)
        
        # ... (Your MQTT logic here) ...
        if mqtt_client:
            mqtt_client.publish(Config.MQTT_TOPIC_COMMAND, f"{current_user.id}:{room_id}:{appliance_id}:{appliance['relay_number']}:{int(state)}")
        
        action = "turned ON" if state else "turned OFF"
        message = f"Appliance '{appliance['name']}' in room '{room['name']}' has been {action}."
        
        return jsonify({"status": "success", "message": message}), 200

    except Exception as e:
        # 5. Log the detailed error for the developer and return a generic message to the user
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

@api_bp.route('/set-appliance-name', methods=['POST'])
@login_required
def set_appliance_name():
    try:
        data = request.json
        room_id = data['room_id']
        appliance_id = data['appliance_id']
        name = data['name']

        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        appliance = next((a for a in room.get('appliances', []) if a['id'] == appliance_id), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404
        
        appliance['name'] = name
        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Name updated."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid request data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@api_bp.route('/set-lock', methods=['POST'])
@login_required
def set_lock():
    try:
        data = request.json
        appliance_id = data['appliance_id']
        room_id = data['room_id']
        locked = data['locked']
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        appliance = next((a for a in room.get('appliances', []) if a['id'] == appliance_id), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404

        appliance['locked'] = bool(locked)
        save_all_data_to_db(all_data)
        
        return jsonify({"status": "success", "message": "Lock state updated."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid request data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@api_bp.route('/update-appliance-settings', methods=['POST'])
@login_required
def update_appliance_settings():
    try:
        req_data = request.get_json()
        # 1. Input Validation
        required_keys = ['room_id', 'appliance_id', 'name', 'relay_number', 'new_room_id']
        if not all(key in req_data for key in required_keys):
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        # 2. Load data
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        # 3. Find and Modify
        original_room = next((r for r in user_data['rooms'] if r['id'] == req_data['room_id']), None)
        if not original_room:
            return jsonify({"status": "error", "message": "Original room not found."}), 404
        
        appliance = next((a for a in original_room['appliances'] if a['id'] == req_data['appliance_id']), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404
        
        appliance['name'] = str(req_data['name']) # Sanitize by casting to string
        appliance['relay_number'] = int(req_data['relay_number']) # Sanitize by casting to int

        if req_data['new_room_id'] != req_data['room_id']:
            target_room = next((r for r in user_data['rooms'] if r['id'] == req_data['new_room_id']), None)
            if not target_room:
                return jsonify({"status": "error", "message": "Target room not found."}), 404
            
            target_room['appliances'].append(appliance)
            original_room['appliances'] = [a for a in original_room['appliances'] if a['id'] != req_data['appliance_id']]

        # 4. Save data
        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Appliance settings updated."}), 200

    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"status": "error", "message": "Invalid data format."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

@api_bp.route('/set-timer', methods=['POST'])
@login_required
def set_timer():
    try:
        data = request.json
        room_id = data['room_id']
        appliance_id = data['appliance_id']
        timer_timestamp = data.get('timer') # Can be null
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        appliance = next((a for a in room.get('appliances', []) if a['id'] == appliance_id), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404

        appliance['timer'] = timer_timestamp
        if timer_timestamp:
            appliance['state'] = True
        
        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Timer set."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid request data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500


@api_bp.route('/save-room-order', methods=['POST'])
@login_required
def save_room_order():
    try:
        new_order_ids = request.json['order']
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404
        
        room_map = {room['id']: room for room in user_data.get('rooms', [])}
        user_data['rooms'] = [room_map[id] for id in new_order_ids if id in room_map]
        
        save_all_data_to_db(all_data)
        return jsonify({"status": "success"}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid order data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@api_bp.route('/save-appliance-order', methods=['POST'])
@login_required
def save_appliance_order():
    try:
        data = request.json
        room_id = data['room_id']
        new_order_ids = data['order']
        
        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404
        
        appliance_map = {appliance['id']: appliance for appliance in room.get('appliances', [])}
        room['appliances'] = [appliance_map[id] for id in new_order_ids if id in appliance_map]
        
        save_all_data_to_db(all_data)
        return jsonify({"status": "success"}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid order data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

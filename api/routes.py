import time
import uuid
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database.redis_db import get_all_data_from_db, save_all_data_to_db, get_all_users_from_db, save_all_users_to_db
from admin.api_routes import get_all_boards_from_db, save_all_boards_to_db
from utils.helpers import get_user_data, save_user_data
from utils.encryption import decrypt_data
from utils.email_helper import send_detection_email_thread
from analytics.data_processing import load_analytics_data, calculate_statistics
from config import Config

api_bp = Blueprint('api', __name__)

# --- ESP Check-in Queue for Device Communication ---
check_in_queue = {}

@api_bp.route('/esp/checkin/<string:relay_id>')
def esp_checkin(relay_id):
    """
    Check-in endpoint for ESP devices. Devices poll this to get commands.
    Security is implicitly handled by the unguessable `relay_id` UUID.
    """
    command = check_in_queue.pop(relay_id, None)
    if command:
        return jsonify(command), 200
    return jsonify({}), 204  # No Content

# --- Board Management ---

@api_bp.route('/register-board', methods=['POST'])
@login_required
def register_board():
    """Register a board to a room and user"""
    data = request.get_json()
    room_id = data.get('room_id')
    board_id = data.get('board_id')

    if not room_id or not board_id:
        return jsonify({"status": "error", "message": "Room ID and Board ID are required."}), 400

    all_boards = get_all_boards_from_db()
    board = all_boards.get(board_id)

    if not board:
        return jsonify({"status": "error", "message": "Board ID is not valid or has not been generated."}), 404
    if board.get('owner_id') and board.get('owner_id') != current_user.id:
        return jsonify({"status": "error", "message": "This board is already registered to another user."}), 409

    board['owner_id'] = current_user.id
    board['room_id'] = room_id
    save_all_boards_to_db(all_boards)
    
    return jsonify({"status": "success", "message": f"Board {board_id} successfully registered to your room."}), 200

@api_bp.route('/unregister-board', methods=['POST'])
@login_required
def unregister_board():
    """Unregister a board and remove all associated appliances"""
    board_id = request.json.get('board_id')
    all_boards = get_all_boards_from_db()
    all_data = get_all_data_from_db()
    user_data = all_data.get(current_user.id, {})
    
    board = all_boards.get(board_id)
    if not board or board.get('owner_id') != current_user.id:
        return jsonify({"status": "error", "message": "Board not found or you are not the owner."}), 404

    # Remove all appliances in all rooms linked to this board
    appliances_removed = 0
    for room in user_data.get('rooms', []):
        original_count = len(room.get('appliances', []))
        room['appliances'] = [app for app in room.get('appliances', []) if app.get('board_id') != board_id]
        appliances_removed += original_count - len(room['appliances'])
            
    # Reset the board's status
    board['owner_id'] = None
    board['room_id'] = None
    if 'relays' in board:
        for relay in board['relays']:
            relay['is_occupied'] = False

    save_all_boards_to_db(all_boards)
    save_all_data_to_db(all_data)
    
    message = f"Board {board_id} unregistered"
    if appliances_removed > 0:
        message += f" and {appliances_removed} appliances removed"
    
    return jsonify({"status": "success", "message": message + "."})

@api_bp.route('/my-boards', methods=['GET'])
@login_required
def get_my_boards():
    """Get all boards owned by the current user"""
    all_boards = get_all_boards_from_db()
    my_boards = [b for b in all_boards.values() if b.get('owner_id') == current_user.id]
    return jsonify(my_boards)

@api_bp.route('/available-relays/<room_id>', methods=['GET'])
@login_required
def get_available_relays(room_id):
    """Get available relays in a room for adding new appliances"""
    all_boards = get_all_boards_from_db()
    user_data = get_user_data()
    
    # Get the room to check which relays are occupied
    room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
    if not room:
        return jsonify([])
    
    # Get occupied relays from appliances
    occupied_relays = {appliance.get('relay_id') for appliance in room.get('appliances', []) if appliance.get('relay_id')}
    
    available_relays = []
    for board in all_boards.values():
        if board.get('owner_id') == current_user.id and board.get('room_id') == room_id:
            # Handle both relay structures (relays list or relay_ids list)
            if 'relays' in board:
                # New structure with relay objects
                free_relays = [r for r in board.get('relays', []) if not r.get('is_occupied')]
            else:
                # Legacy structure with relay_ids list
                relay_ids = board.get('relay_ids', [])
                free_relays = [
                    {"id": relay_id, "name": f"Relay {i+1}"}
                    for i, relay_id in enumerate(relay_ids)
                    if relay_id not in occupied_relays
                ]
            
            if free_relays:
                available_relays.append({
                    "board_id": board['board_id'],
                    "relays": free_relays
                })
    
    return jsonify(available_relays)

# --- Room Management ---

@api_bp.route('/get-rooms-and-appliances', methods=['GET'])
@login_required
def get_rooms_and_appliances():
    """Get all rooms and appliances for the current user"""
    all_data = get_all_data_from_db()
    user_data = all_data.get(current_user.id, {})
    return jsonify(user_data.get('rooms', []))

@api_bp.route('/add-room', methods=['POST'])
@login_required
def add_room():
    """Add a new room"""
    try:
        data = request.json
        room_name = data['name']
        user_data = get_user_data()
        
        # Generate unique room ID
        new_room_id = str(int(time.time() * 1000))
        new_room = {
            "id": new_room_id, 
            "name": room_name, 
            "ai_control": False, 
            "appliances": []
        }
        
        if 'rooms' not in user_data:
            user_data['rooms'] = []
        user_data['rooms'].append(new_room)
        
        save_user_data(user_data)
        return jsonify({"status": "success", "room_id": new_room_id}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@api_bp.route('/delete-room', methods=['POST'])
@login_required
def delete_room():
    """Delete a room and unregister associated boards"""
    room_id = request.json.get('room_id')
    all_data = get_all_data_from_db()
    all_boards = get_all_boards_from_db()
    user_data = all_data.get(current_user.id, {})

    if not any(r['id'] == room_id for r in user_data.get('rooms', [])):
        return jsonify({"status": "error", "message": "Room not found."}), 404

    # Unregister all boards associated with this room
    boards_cleared = 0
    for board in all_boards.values():
        if board.get('owner_id') == current_user.id and board.get('room_id') == room_id:
            board['owner_id'] = None
            board['room_id'] = None
            boards_cleared += 1
            if 'relays' in board:
                for relay in board['relays']:
                    relay['is_occupied'] = False

    user_data['rooms'] = [r for r in user_data.get('rooms', []) if r['id'] != room_id]
    
    save_all_data_to_db(all_data)
    save_all_boards_to_db(all_boards)
    
    message = "Room deleted"
    if boards_cleared > 0:
        message += f" and {boards_cleared} associated boards released"
    
    return jsonify({"status": "success", "message": message + "."})

@api_bp.route('/update-room-settings', methods=['POST'])
@login_required
def update_room_settings():
    """Update room settings (name, AI control)"""
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

@api_bp.route('/save-room-order', methods=['POST'])
@login_required
def save_room_order():
    """Save new room order after drag & drop"""
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

# --- Appliance Management ---

@api_bp.route('/add-appliance', methods=['POST'])
@login_required
def add_appliance():
    """Add a new appliance to a room"""
    data = request.get_json()
    room_id, name = data.get('room_id'), data.get('name')
    board_id, relay_id = data.get('board_id'), data.get('relay_id')

    if not all([room_id, name, board_id, relay_id]):
        return jsonify({"status": "error", "message": "Missing required fields."}), 400

    all_data = get_all_data_from_db()
    all_boards = get_all_boards_from_db()
    user_data = all_data.get(current_user.id, {})
    room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
    board = all_boards.get(board_id)

    if not room:
        return jsonify({"status": "error", "message": "Room not found."}), 404
    if not board or board.get('owner_id') != current_user.id:
        return jsonify({"status": "error", "message": "Board not found or you are not the owner."}), 404

    # Check if relay is available
    relay = next((r for r in board.get('relays', []) if r['id'] == relay_id), None)
    if not relay or relay.get('is_occupied'):
        return jsonify({"status": "error", "message": "Relay is not available or already occupied."}), 409
        
    # Mark relay as occupied
    relay['is_occupied'] = True
    
    # Create new appliance
    new_appliance = {
        "id": uuid.uuid4().hex, 
        "name": name, 
        "state": False,
        "locked": False, 
        "timer": None, 
        "board_id": board_id, 
        "relay_id": relay_id
    }
    room.setdefault('appliances', []).append(new_appliance)

    save_all_data_to_db(all_data)
    save_all_boards_to_db(all_boards)
    return jsonify({"status": "success", "message": f"Appliance '{name}' added successfully.", "appliance_id": new_appliance['id']})

@api_bp.route('/delete-appliance', methods=['POST'])
@login_required
def delete_appliance():
    """Delete an appliance and free its relay"""
    try:
        data = request.get_json()
        room_id = data['room_id']
        appliance_id = data['appliance_id']

        all_data = get_all_data_from_db()
        all_boards = get_all_boards_from_db()
        user_data = all_data.get(current_user.id)
        
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
        if not room:
            return jsonify({"status": "error", "message": "Room not found."}), 404

        appliance_to_delete = next((app for app in room.get('appliances', []) if app['id'] == appliance_id), None)
        if not appliance_to_delete:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404

        # Free the relay
        board_id, relay_id = appliance_to_delete.get('board_id'), appliance_to_delete.get('relay_id')
        if board_id and relay_id and board_id in all_boards:
            relay = next((r for r in all_boards[board_id].get('relays', []) if r['id'] == relay_id), None)
            if relay:
                relay['is_occupied'] = False

        room['appliances'] = [app for app in room['appliances'] if app['id'] != appliance_id]
        
        save_all_data_to_db(all_data)
        save_all_boards_to_db(all_boards)
        return jsonify({"status": "success", "message": "Appliance deleted."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Missing room_id or appliance_id."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

@api_bp.route('/set-appliance-state', methods=['POST'])
@login_required
def set_appliance_state():
    """Set appliance on/off state"""
    data = request.get_json()
    room_id, appliance_id, state = data['room_id'], data['appliance_id'], data['state']
    
    user_data = get_user_data()
    room = next((r for r in user_data.get('rooms', []) if r['id'] == room_id), None)
    if not room: 
        return jsonify({"status": "error", "message": "Room not found."}), 404
    
    appliance = next((a for a in room.get('appliances', []) if a['id'] == appliance_id), None)
    if not appliance: 
        return jsonify({"status": "error", "message": "Appliance not found."}), 404

    # Security check: Verify user owns the board
    board_id = appliance.get('board_id')
    all_boards = get_all_boards_from_db()
    board = all_boards.get(board_id)
    if not board or board.get('owner_id') != current_user.id:
        return jsonify({"status": "error", "message": "Authorization error: You do not own this board."}), 403

    appliance['state'] = state
    if not state: 
        appliance['timer'] = None  # Clear timer when turning off
    save_user_data(user_data)

    # Queue command for ESP device
    relay_id = appliance.get('relay_id')
    if relay_id:
        check_in_queue[relay_id] = {"state": int(state)}
        
    action = "turned ON" if state else "turned OFF"
    return jsonify({"status": "success", "message": f"'{appliance['name']}' has been {action}."}), 200

@api_bp.route('/update-appliance-settings', methods=['POST'])
@login_required
def update_appliance_settings():
    """Update appliance settings including name, relay, and room assignment"""
    try:
        req_data = request.get_json()
        
        # Handle both legacy and new API formats
        if 'relay_number' in req_data:
            # Legacy format
            required_keys = ['room_id', 'appliance_id', 'name', 'relay_number', 'new_room_id']
        else:
            # New format
            required_keys = ['room_id', 'appliance_id', 'name', 'board_id', 'relay_id', 'new_room_id']
            
        if not all(key in req_data for key in required_keys):
            return jsonify({"status": "error", "message": "Missing required fields."}), 400

        all_data = get_all_data_from_db()
        user_data = all_data.get(current_user.id)
        if not user_data:
            return jsonify({"status": "error", "message": "User data not found."}), 404

        original_room = next((r for r in user_data['rooms'] if r['id'] == req_data['room_id']), None)
        if not original_room:
            return jsonify({"status": "error", "message": "Original room not found."}), 404
        
        appliance = next((a for a in original_room['appliances'] if a['id'] == req_data['appliance_id']), None)
        if not appliance:
            return jsonify({"status": "error", "message": "Appliance not found."}), 404
        
        # Update appliance properties
        appliance['name'] = str(req_data['name'])
        
        # Handle both legacy and new relay assignment
        if 'relay_number' in req_data:
            appliance['relay_number'] = int(req_data['relay_number'])
        else:
            appliance['board_id'] = req_data['board_id']
            appliance['relay_id'] = req_data['relay_id']

        # Move to different room if requested
        if req_data['new_room_id'] != req_data['room_id']:
            target_room = next((r for r in user_data['rooms'] if r['id'] == req_data['new_room_id']), None)
            if not target_room:
                return jsonify({"status": "error", "message": "Target room not found."}), 404
            
            target_room['appliances'].append(appliance)
            original_room['appliances'] = [a for a in original_room['appliances'] if a['id'] != req_data['appliance_id']]

        save_all_data_to_db(all_data)
        return jsonify({"status": "success", "message": "Appliance settings updated."}), 200

    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"status": "error", "message": "Invalid data format."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal server error occurred."}), 500

@api_bp.route('/save-appliance-order', methods=['POST'])
@login_required
def save_appliance_order():
    """Save new appliance order after drag & drop"""
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

# --- Additional Appliance Features ---

@api_bp.route('/set-appliance-name', methods=['POST'])
@login_required
def set_appliance_name():
    """Update appliance name"""
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
    """Set appliance lock state"""
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

@api_bp.route('/set-timer', methods=['POST'])
@login_required
def set_timer():
    """Set appliance timer"""
    try:
        data = request.json
        room_id = data['room_id']
        appliance_id = data['appliance_id']
        timer_timestamp = data.get('timer')  # Can be null to clear timer
        
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
            appliance['state'] = True  # Turn on appliance when timer is set
        
        save_all_data_to_db(all_data)
        message = "Timer set" if timer_timestamp else "Timer cleared"
        return jsonify({"status": "success", "message": message + "."}), 200
    except KeyError:
        return jsonify({"status": "error", "message": "Invalid request data."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": "An internal error occurred."}), 500

# --- QR Code Processing ---

@api_bp.route('/extract-qr-data', methods=['POST'])
def extract_qr_data():
    """Extract and validate QR code data for board registration"""
    encrypted_text = request.json.get('encrypted_data')
    if not encrypted_text:
        return jsonify({"error": "Missing 'encrypted_data' field."}), 400
        
    try:
        decrypted_board_info = decrypt_data(encrypted_text)
        
        if decrypted_board_info and 'board_id' in decrypted_board_info:
            all_boards = get_all_boards_from_db()
            board_id = decrypted_board_info['board_id']
            board_status = all_boards.get(board_id)

            if not board_status:
                return jsonify({"error": "Board does not exist in the database."}), 404
            
            if board_status.get('is_suspended'):
                return jsonify({"error": "This board has been suspended."}), 403
            
            return jsonify(decrypted_board_info), 200
        else:
            return jsonify({"error": "Decryption failed. Invalid or tampered data."}), 400
    except Exception as e:
        return jsonify({"error": "Failed to process QR data."}), 400

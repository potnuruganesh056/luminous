import uuid
import json
from flask import Blueprint, jsonify, request
from admin.routes import admin_required
from utils.email_helper import send_mass_email_thread
from utils.encryption import encrypt_data # <-- Import the new encryptor
from database.redis_db import (
    get_all_users_from_db, save_all_users_to_db,
    get_all_data_from_db, save_all_data_to_db,
    redis_client
)
from flask_login import current_user

admin_api_bp = Blueprint('admin_api', __name__)

def _generate_random_hex(length=32):
    return secrets.token_hex(length // 2)

def _generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def _generate_random_int(max_digits=8):
    return random.randint(0, 10**max_digits - 1)

def get_all_boards_from_db():
    boards_json = redis_client.get('boards')
    return json.loads(boards_json) if boards_json else {}

def save_all_boards_to_db(boards_dict):
    redis_client.set('boards', json.dumps(boards_dict))

@admin_api_bp.route('/generate-board', methods=['POST'])
@admin_required
def generate_board():
    """
    Generates a new board from detailed form data.
    Fills in any missing fields with random data.
    """
    data = request.get_json()
    
    # Process and randomize fields if they are missing
    board_id = data.get('board_id') or _generate_random_hex()
    num_relays = int(data.get('number_of_relays') or 4)
    version = data.get('version_number') or "1.0.0"
    build = data.get('build_number') or _generate_random_int(4)
    
    # Process provided relays or generate new ones
    provided_relays = data.get('relays', [])
    relays = []
    for i in range(num_relays):
        if i < len(provided_relays) and provided_relays[i].get('id'):
            relay_id = provided_relays[i]['id']
        else:
            relay_id = _generate_random_hex(32)
            
        relays.append({
            "id": relay_id,
            "name": f"Relay {i+1}",
            "is_occupied": False
        })

    board_data = {
        "board_id": board_id,
        "number_of_relays": num_relays,
        "version_number": version,
        "build_number": build,
        "relays": relays,
        "additional_features": data.get('additional_features', {}),
        "owner_id": None,
        "room_id": None,
        "is_suspended": False
    }
    
    all_boards = get_all_boards_from_db()
    all_boards[board_id] = board_data
    save_all_boards_to_db(all_boards)
    
    return jsonify({
        "status": "success",
        "message": f"Board {board_id} created.",
        "qr_data": board_id,
        "board_id": board_id
    }), 200


@admin_api_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Fetches all users for the admin dashboard."""
    users = get_all_users_from_db()
    data = get_all_data_from_db()
    
    user_list = []
    for user in users:
        user_info = data.get(user['id'], {}).get('user_settings', {})
        user_list.append({
            "id": user['id'],
            "username": user['username'],
            "email": user_info.get('email', 'N/A'),
            "is_admin": user.get('is_admin', False),
            "is_suspended": user.get('is_suspended', False) # <-- ADDED
        })
    return jsonify(user_list)

@admin_api_bp.route('/delete-user', methods=['POST'])
@admin_required
def delete_user():
    user_id_to_delete = request.json['user_id']
    if user_id_to_delete == current_user.id:
        return jsonify({"status": "error", "message": "Admin cannot delete themselves."}), 400
    
    users = get_all_users_from_db()
    data = get_all_data_from_db()
    updated_users = [user for user in users if user.get('id') != user_id_to_delete]
    if user_id_to_delete in data: del data[user_id_to_delete]
        
    save_all_users_to_db(updated_users)
    save_all_data_to_db(data)
    return jsonify({"status": "success", "message": f"User {user_id_to_delete} has been deleted."})

@admin_api_bp.route('/boards', methods=['GET'])
@admin_required
def get_all_boards():
    """Fetches all generated boards for the admin dashboard."""
    all_boards = get_all_boards_from_db()
    board_list = []
    for board_id, board in all_boards.items():
        # Ensure is_suspended field exists
        board['is_suspended'] = board.get('is_suspended', False) # <-- ADDED
        board_list.append(board)
    return jsonify(board_list)



@admin_api_bp.route('/delete-board', methods=['POST'])
@admin_required
def delete_board():
    board_id_to_delete = request.json['board_id']
    all_boards = get_all_boards_from_db()
    if board_id_to_delete in all_boards:
        del all_boards[board_id_to_delete]
        save_all_boards_to_db(all_boards)
        return jsonify({"status": "success", "message": f"Board {board_id_to_delete} has been deleted."})
    return jsonify({"status": "error", "message": "Board not found."}), 404

@admin_api_bp.route('/delete-boards', methods=['POST'])
@admin_required
def delete_boards():
    """Deletes a list of specified boards."""
    data = request.get_json()
    board_ids_to_delete = data.get('board_ids', [])

    if not board_ids_to_delete:
        return jsonify({"status": "error", "message": "No board IDs provided."}), 400
    
    all_boards = get_all_boards_from_db()
    deleted_count = 0
    for board_id in board_ids_to_delete:
        if board_id in all_boards:
            del all_boards[board_id]
            deleted_count += 1
            
    save_all_boards_to_db(all_boards)
    return jsonify({"status": "success", "message": f"{deleted_count} board(s) have been deleted."})

@admin_api_bp.route('/delete-all-boards', methods=['POST'])
@admin_required
def delete_all_boards():
    """Deletes all boards from the database."""
    save_all_boards_to_db({}) # Save an empty dictionary
    return jsonify({"status": "success", "message": "All boards have been deleted."})


@admin_api_bp.route('/suspend-user', methods=['POST'])
@admin_required
def suspend_user():
    """Suspends or un-suspends a user."""
    data = request.json
    user_id = data['user_id']
    suspend_status = data['status']

    if user_id == current_user.id:
        return jsonify({"status": "error", "message": "Admin cannot change their own status."}), 400

    users = get_all_users_from_db()
    user_found = False
    for user in users:
        if user.get('id') == user_id:
            user['is_suspended'] = suspend_status
            user_found = True
            break
    
    if user_found:
        save_all_users_to_db(users)
        action = "suspended" if suspend_status else "unsuspended"
        return jsonify({"status": "success", "message": f"User {user_id} has been {action}."})
    return jsonify({"status": "error", "message": "User not found."}), 404

@admin_api_bp.route('/suspend-board', methods=['POST'])
@admin_required
def suspend_board():
    """Suspends or un-suspends a board."""
    data = request.json
    board_id = data['board_id']
    suspend_status = data['status']

    boards = get_all_boards_from_db()
    if board_id in boards:
        boards[board_id]['is_suspended'] = suspend_status
        save_all_boards_to_db(boards)
        action = "suspended" if suspend_status else "unsuspended"
        return jsonify({"status": "success", "message": f"Board {board_id} has been {action}."})
    return jsonify({"status": "error", "message": "Board not found."}), 404

@admin_api_bp.route('/send-mass-email', methods=['POST'])
@admin_required
def send_mass_email():
    data = request.json
    subject, body = data.get('subject'), data.get('body')
    if not subject or not body:
        return jsonify({"status": "error", "message": "Subject and body are required."}), 400

    recipients = {
        user_data.get('user_settings', {}).get('email')
        for user_data in get_all_data_from_db().values()
        if user_data.get('user_settings', {}).get('email')
    }
    
    if not recipients:
        return jsonify({"status": "error", "message": "No users with valid emails found."}), 404

    send_mass_email_thread(list(recipients), subject, body)
    return jsonify({"status": "success", "message": f"Email dispatch initiated for {len(recipients)} users."})

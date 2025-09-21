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

def get_all_boards_from_db():
    boards_json = redis_client.get('boards')
    return json.loads(boards_json) if boards_json else {}

def save_all_boards_to_db(boards_dict):
    redis_client.set('boards', json.dumps(boards_dict))

@admin_api_bp.route('/generate-board', methods=['POST'])
@admin_required
def generate_board():
    data = request.get_json()
    number_of_relays = int(data.get('relay_count', 4))
    
    board_id = uuid.uuid4().hex[:8]
    relays = [
        {"id": uuid.uuid4().hex[:16], "name": f"Relay {i+1}", "is_occupied": False}
        for i in range(number_of_relays)
    ]
    
    board_data = {
        "board_id": board_id,
        "number_of_relays": number_of_relays,
        "version_number": "1.0.0",
        "build_number": 1,
        "owner_id": None,
        "relays": relays, # <-- Use the new list of objects
        "additional_features": {}
    }
    
    all_boards = get_all_boards_from_db()
    all_boards[board_id] = board_data
    save_all_boards_to_db(all_boards)
    
    # --- USE STRONG ENCRYPTION ---
    encrypted_string = encrypt_data(board_data)
    if not encrypted_string:
        return jsonify({"status": "error", "message": "Failed to encrypt board data."}), 500
    
    return jsonify({
        "status": "success",
        "message": f"Board {board_id} created.",
        "qr_data": encrypted_string, # This is now the encrypted string
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

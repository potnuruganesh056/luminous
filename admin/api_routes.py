import uuid
import json
import base64
from flask import Blueprint, jsonify, request
from admin.routes import admin_required
from database.redis_db import (
    get_all_users_from_db, save_all_users_to_db,
    get_all_data_from_db, save_all_data_to_db,
    redis_client
)

admin_api_bp = Blueprint('admin_api', __name__, url_prefix='/admin')

def get_all_boards_from_db():
    """Fetches and decodes the 'boards' dictionary from Redis."""
    boards_json = redis_client.get('boards')
    return json.loads(boards_json) if boards_json else {}

def save_all_boards_to_db(boards_dict):
    """Encodes and saves the 'boards' dictionary to Redis."""
    redis_client.set('boards', json.dumps(boards_dict))

@admin_api_bp.route('/generate-board', methods=['POST'])
@admin_required
def generate_board():
    """Generates a new board, saves it to DB, and returns QR data."""
    data = request.get_json()
    number_of_relays = int(data.get('relay_count', 4))
    
    board_id = uuid.uuid4().hex[:8]
    relay_ids = [uuid.uuid4().hex[:16] for _ in range(number_of_relays)]
    
    board_data = {
        "board_id": board_id,
        "number_of_relays": number_of_relays,
        "version_number": "1.0.0",
        "build_number": 1,
        "relay_ids": relay_ids,
        "additional_features": {}
    }
    
    # Save the new board to the database
    all_boards = get_all_boards_from_db()
    all_boards[board_id] = board_data
    save_all_boards_to_db(all_boards)
    
    # Prepare data for QR code (JSON string -> bytes -> base64)
    json_string = json.dumps(board_data)
    base64_string = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
    
    return jsonify({
        "status": "success",
        "message": f"Board {board_id} created with {number_of_relays} relays.",
        "qr_data": base64_string,
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
            "is_admin": user.get('is_admin', False)
        })
    return jsonify(user_list)

@admin_api_bp.route('/delete-user', methods=['POST'])
@admin_required
def delete_user():
    """Permanently deletes a user from the system."""
    user_id_to_delete = request.json['user_id']
    
    users = get_all_users_from_db()
    data = get_all_data_from_db()
    
    # Prevent admin from deleting themselves
    if user_id_to_delete == current_user.id:
        return jsonify({"status": "error", "message": "Admin cannot delete themselves."}), 400
        
    # Remove from users list
    updated_users = [user for user in users if user.get('id') != user_id_to_delete]
    
    # Remove from data dictionary
    if user_id_to_delete in data:
        del data[user_id_to_delete]
        
    save_all_users_to_db(updated_users)
    save_all_data_to_db(data)
    
    return jsonify({"status": "success", "message": f"User {user_id_to_delete} has been deleted."})

# Add other admin API routes (delete board, send email) here later...

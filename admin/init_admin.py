from werkzeug.security import generate_password_hash
from database.redis_db import (
    get_all_users_from_db, save_all_users_to_db, 
    get_all_data_from_db, save_all_data_to_db
)
from auth.models import get_user_by_email, create_default_user_data

def init_admin(app):
    """
    Checks for and creates/updates the primary admin user on startup
    based on environment variables. This function is called from app.py.
    """
    with app.app_context():
        admin_email = app.config.get('ADMIN_EMAIL')
        admin_username = app.config.get('ADMIN_USERNAME')
        admin_password = app.config.get('ADMIN_PASSWORD')
        admin_google_id = app.config.get('ADMIN_GOOGLE_ID')
        admin_github_id = app.config.get('ADMIN_GITHUB_ID')

        if not all([admin_email, admin_username, admin_password]):
            print("INFO: Admin credentials not set in environment. Skipping admin initialization.")
            return

        all_users = get_all_users_from_db()
        all_data = get_all_data_from_db()
        admin_user_record = get_user_by_email(admin_email)
        hashed_password = generate_password_hash(admin_password)

        if not admin_user_record:
            print(f"INFO: Admin user '{admin_email}' not found. Creating new admin account.")
            new_user_id = str(int(all_users[-1]['id']) + 1) if all_users else "1"
            new_admin_user = {
                'id': new_user_id, 'username': admin_username, 'password_hash': hashed_password,
                'google_id': admin_google_id, 
                'github_id': admin_github_id,
                'is_admin': True
            }
            all_users.append(new_admin_user)
            all_data[new_user_id] = create_default_user_data(name=admin_username, email=admin_email)
        else:
            print(f"INFO: Found user '{admin_email}'. Verifying admin status and credentials.")
            admin_id = admin_user_record['id']
            for user in all_users:
                if user['id'] == admin_id:
                    user.update({
                        'username': admin_username, 'password_hash': hashed_password,
                        'google_id': admin_google_id,
                        'github_id': admin_github_id,
                        'is_admin': True
                    })
                    break
            if admin_id in all_data:
                all_data[admin_id]['user_settings']['name'] = admin_username
                all_data[admin_id]['user_settings']['email'] = admin_email
            else: 
                all_data[admin_id] = create_default_user_data(name=admin_username, email=admin_email)

        save_all_users_to_db(all_users)
        save_all_data_to_db(all_data)
        print("SUCCESS: Admin account initialization complete.")

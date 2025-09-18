import threading
import base64
from flask import current_app
from flask_mail import Message, Mail

mail = Mail() # This should be initialized in your app.py, which it is.

def send_detection_email_thread(recipient, subject, body, image_data):
    """Send detection email in a separate thread."""
    def send_email():
        with current_app.app_context():
            print(f"Preparing to send detection email to {recipient}...")
            try:
                msg = Message(subject=subject, recipients=[recipient])
                msg.html = body
                
                if image_data:
                    # Your existing image attachment logic...
                    image_binary = base64.b64decode(image_data.split(',')[1])
                    msg.attach("detection_alert.png", "image/png", image_binary)
                    
                mail.send(msg)
                print(f"Email sent successfully to {recipient}!")
            except Exception as e:
                print(f"Error sending detection email: {e}")

    thread = threading.Thread(target=send_email)
    thread.daemon = True
    thread.start()

# --- NEW FUNCTION ---
def send_mass_email_thread(recipients, subject, body):
    """Send a mass email to a list of recipients using BCC in a thread."""
    def send_email():
        with current_app.app_context():
            print(f"Preparing to send mass email to {len(recipients)} users...")
            try:
                # The 'sender' is pulled from MAIL_DEFAULT_SENDER in your config
                # We don't set 'recipients' in the constructor, we use 'bcc'
                msg = Message(subject=subject)
                msg.html = f"<p>{body.replace('\n', '<br>')}</p>" # Basic HTML formatting
                msg.bcc = recipients # Use Blind Carbon Copy for privacy
                
                mail.send(msg)
                print(f"Mass email sent successfully!")
            except Exception as e:
                print(f"Error sending mass email: {e}")
    
    thread = threading.Thread(target=send_email)
    thread.daemon = True
    thread.start()

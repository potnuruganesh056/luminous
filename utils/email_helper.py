import threading
import base64
from flask import current_app
from flask_mail import Message, Mail

mail = Mail()

def send_detection_email_thread(recipient, subject, body, image_data):
    """Send email in a separate thread to prevent blocking."""
    def send_email():
        with current_app.app_context():
            print(f"Preparing to send email to {recipient}...")
            try:
                if not recipient or not subject or not body:
                    print("Email sending failed: Missing required fields")
                    return
                
                msg = Message(
                    subject=subject,
                    recipients=[recipient]
                )
                msg.html = body
                
                if image_data:
                    try:
                        if ',' in image_data:
                            image_binary = base64.b64decode(image_data.split(',')[1])
                        else:
                            image_binary = base64.b64decode(image_data)
                        
                        msg.attach(
                            "detection_alert.png",
                            "image/png",
                            image_binary
                        )
                    except Exception as img_error:
                        print(f"Error processing image attachment: {img_error}")
                        
                mail.send(msg)
                print(f"Email sent successfully to {recipient}!")
                
            except Exception as e:
                print(f"Error sending email: {e}")
    
    email_thread = threading.Thread(target=send_email)
    email_thread.daemon = True
    email_thread.start()

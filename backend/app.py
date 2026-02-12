from flask import Flask, request, jsonify
from flask_cors import CORS
import pytesseract
from PIL import Image
from pdf2image import convert_from_bytes
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import io
import sqlite3
from datetime import datetime
import json
import secrets
from classifier_wrapper import PetitionClassifier

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize ML classifier
classifier = PetitionClassifier()

# Create uploads directory
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Database setup
def init_db():
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS petitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            file_path TEXT NOT NULL,
            extracted_text TEXT NOT NULL,
            department TEXT NOT NULL,
            priority TEXT NOT NULL,
            email_sent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Sent',
            ack_token TEXT UNIQUE,
            work_completed_date TIMESTAMP,
            work_completed_file TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create users table with role and department fields
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            department TEXT,
            reset_token TEXT UNIQUE,
            reset_token_expiry TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default admin user if not exists
    c.execute("SELECT * FROM users WHERE username = 'hari2005'")
    if not c.fetchone():
        c.execute('''
            INSERT INTO users (username, password, email, role) 
            VALUES (?, ?, ?, ?)
        ''', ('hari2005', 'SVKGKTH2005', 'harikrushnan2005@gamil.com', 'admin'))
    
    # Insert department users if not exist
    department_users = [
        ('water.petition2025@gmail.com', 'water123', 'water.petition2025@gmail.com', 'department', 'Water'),
        ('electricity.petition2025@gmail.com', 'electricity123', 'electricity.petition2025@gmail.com', 'department', 'Electricity'),
        ('civil.petition2025@gmail.com', 'civil123', 'civil.petition2025@gmail.com', 'department', 'Civil'),
        ('crime.petition2025@gmail.com', 'crime123', 'crime.petition2025@gmail.com', 'department', 'Crime'),
        ('sanitation.petition2025@gmail.com', 'sanitation123', 'sanitation.petition2025@gmail.com', 'department', 'Sanitation'),
        ('road.petition2025@gmail.com', 'roads123', 'road.petition2025@gmail.com', 'department', 'Roads')
    ]
    
    for username, password, email, role, department in department_users:
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if not c.fetchone():
            c.execute('''
                INSERT INTO users (username, password, email, role, department) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password, email, role, department))
    
    conn.commit()
    conn.close()

init_db()

# Department email mapping
DEPARTMENT_EMAILS = {
    "water": "water.petition2025@gmail.com",
    "electricity": "electricity.petition2025@gmail.com",
    "civil": "civil.petition2025@gmail.com",
    "crime": "crime.petition2025@gmail.com",
    "sanitation": "sanitation.petition2025@gmail.com",
    "roads": "road.petition2025@gmail.com"
}

def extract_text_from_file(file):
    """Extract text using OCR"""
    try:
        if file.content_type == 'application/pdf':
            images = convert_from_bytes(file.read())
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            return text.strip()
        else:
            image = Image.open(file)
            return pytesseract.image_to_string(image).strip()
    except Exception as e:
        print(f"OCR Error: {e}")
        return None

def send_email(department, petition_text, file_name, file_path, priority="medium", complaint_type="general", petition_id=None, ack_token=None):
    """Send email to department with attachment"""
    gmail_user = os.getenv('GMAIL_USER')
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not gmail_user or not gmail_password:
        raise Exception("Email credentials not configured")
    
    to_email = DEPARTMENT_EMAILS.get(department, "default@gov.in")
    
    # Generate acknowledgment URL
    ack_url = f"http://127.0.0.1:5000/api/acknowledge/{ack_token}" if ack_token else None
    
    msg = MIMEMultipart()
    msg['From'] = gmail_user
    msg['To'] = to_email
    
    # Add emoji to subject based on priority
    priority_emoji = "🔴" if priority.upper() == "URGENT" else "🟡" if priority.upper() == "HIGH" else "🟢"
    msg['Subject'] = f"{priority_emoji} New {priority.upper()} {complaint_type.upper()} Petition"
    
    # Priority color styling
    priority_color = "#dc2626" if priority.upper() == "URGENT" else "#f59e0b" if priority.upper() == "HIGH" else "#16a34a"
    
    # Create HTML email body
    body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            h1 {{
                color: #333;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .petition-details {{
                background-color: #f3f4f6;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            .detail-row {{
                margin: 10px 0;
            }}
            .label {{
                font-weight: bold;
                color: #666;
            }}
            .priority {{
                color: {priority_color};
                font-weight: bold;
            }}
            .extracted-content {{
                margin: 20px 0;
            }}
            .content-box {{
                border-left: 4px solid #3b82f6;
                padding-left: 16px;
                margin: 10px 0;
                color: #555;
            }}
            .footer {{
                color: #666;
                font-size: 14px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <h1>New Petition Received</h1>
        
        <div class="petition-details">
            <div class="detail-row">
                <span class="label">Complaint Type:</span> {complaint_type.upper()}
            </div>
            <div class="detail-row">
                <span class="label">Priority:</span> <span class="priority">{priority.upper()}</span>
            </div>
            <div class="detail-row">
                <span class="label">File Name:</span> {file_name}
            </div>
            {f'<div class="detail-row"><span class="label">Petition ID:</span> {petition_id}</div>' if petition_id else ''}
        </div>
        
        <div class="extracted-content">
            <strong>Extracted Content:</strong>
            <div class="content-box">
                {petition_text.replace(chr(10), '<br>')}
            </div>
        </div>
        
        {f'''
        <div style="margin: 30px 0; padding: 20px; background-color: #f0f9ff; border-radius: 8px; text-align: center;">
            <p style="margin-bottom: 15px; font-size: 16px; color: #333;">Please acknowledge receipt of this petition:</p>
            <a href="{ack_url}" style="display: inline-block; padding: 12px 30px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 6px; font-weight: bold;">Acknowledge Petition</a>
        </div>
        ''' if ack_url else ''}
        
        <p class="footer">This is an automated message from the Petition Classification System.</p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(body, 'html'))
    
    # Attach the petition file
    try:
        with open(file_path, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_name}'
            )
            msg.attach(part)
    except Exception as e:
        print(f"Attachment Error: {e}")
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        raise e

@app.route('/api/upload', methods=['POST'])
def upload_petition():
    """Handle petition upload, OCR, classification, and storage"""
    if 'files' not in request.files:
        return jsonify({"error": "No files provided"}), 400
    
    files = request.files.getlist('files')
    results = []
    
    for file in files:
        try:
            # Save uploaded file
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.seek(0)  # Reset file pointer
            file.save(file_path)
            
            # Reset file pointer for OCR
            file.seek(0)
            
            # Extract text using OCR
            extracted_text = extract_text_from_file(file)
            
            if not extracted_text:
                results.append({
                    "file_name": file.filename,
                    "error": "Failed to extract text"
                })
                continue
            
            # Classify using ML models
            classification = classifier.classify(extracted_text)
            department = classification['department']
            priority = classification['priority']
            
            # Save to database
            conn = sqlite3.connect('petitions.db')
            c = conn.cursor()
            c.execute('''
                INSERT INTO petitions (file_name, file_path, extracted_text, department, priority)
                VALUES (?, ?, ?, ?, ?)
            ''', (file.filename, file_path, extracted_text, department, priority))
            petition_id = c.lastrowid
            conn.commit()
            conn.close()
            
            results.append({
                "id": petition_id,
                "file_name": file.filename,
                "department": department,
                "priority": priority,
                "extracted_text": extracted_text[:100] + "...",
                "success": True
            })
            
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "error": str(e)
            })
    
    return jsonify({"results": results}), 200

@app.route('/api/petitions', methods=['GET'])
def get_petitions():
    """Get all petitions"""
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('''SELECT id, file_name, file_path, extracted_text, department, priority, email_sent, status, ack_token, work_completed_date, work_completed_file, created_at 
                 FROM petitions ORDER BY created_at DESC''')
    rows = c.fetchall()
    conn.close()
    
    petitions = []
    for row in rows:
        petitions.append({
            "id": row[0],
            "file_name": row[1],
            "file_path": row[2],
            "extracted_text": row[3],
            "department": row[4],
            "priority": row[5],
            "email_sent": bool(row[6]),
            "status": row[7],
            "ack_token": row[8],
            "work_completed_date": row[9],
            "work_completed_file": row[10],
            "created_at": row[11]
        })
    
    return jsonify({"petitions": petitions}), 200

@app.route('/api/send-email/<int:petition_id>', methods=['POST'])
def send_petition_email(petition_id):
    """Send petition to department via email with attachment"""
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('SELECT id, file_name, file_path, extracted_text, department, priority FROM petitions WHERE id = ?', (petition_id,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Petition not found"}), 404
    
    try:
        # Generate unique acknowledgment token
        ack_token = secrets.token_urlsafe(32)
        
        # row = [id, file_name, file_path, extracted_text, department, priority]
        send_email(
            department=row[4], 
            petition_text=row[3], 
            file_name=row[1], 
            file_path=row[2],
            priority=row[5],
            complaint_type=row[4].upper(),
            petition_id=row[0],
            ack_token=ack_token
        )
        c.execute('UPDATE petitions SET email_sent = 1, ack_token = ? WHERE id = ?', (ack_token, petition_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True}), 200
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/acknowledge/<token>', methods=['GET'])
def acknowledge_petition(token):
    """Acknowledge petition receipt"""
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('SELECT id FROM petitions WHERE ack_token = ?', (token,))
    row = c.fetchone()
    
    if not row:
        conn.close()
        return jsonify({"error": "Invalid acknowledgment token"}), 404
    
    c.execute('UPDATE petitions SET status = ? WHERE ack_token = ?', ('Acknowledged', token))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "Petition acknowledged successfully"}), 200

@app.route('/api/petitions/<int:petition_id>/complete', methods=['POST'])
def complete_petition(petition_id):
    """Upload work completion document"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    try:
        # Save completion file
        file_path = os.path.join(UPLOAD_FOLDER, f'completed_{petition_id}_{file.filename}')
        file.save(file_path)
        
        # Update petition
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        c.execute('''UPDATE petitions 
                     SET status = ?, work_completed_date = ?, work_completed_file = ? 
                     WHERE id = ?''', 
                  ('Completed', datetime.now().isoformat(), file_path, petition_id))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/petitions/<int:petition_id>/file', methods=['GET'])
def get_petition_file(petition_id):
    """Serve the petition file"""
    from flask import send_file
    
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('SELECT file_path, file_name FROM petitions WHERE id = ?', (petition_id,))
    row = c.fetchone()
    conn.close()
    
    if not row:
        return jsonify({"error": "Petition not found"}), 404
    
    file_path, file_name = row
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(file_path, as_attachment=False, download_name=file_name)

@app.route('/api/petitions/<int:petition_id>/work-file', methods=['GET'])
def get_work_file(petition_id):
    """Serve the work completed file"""
    from flask import send_file
    
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('SELECT work_completed_file FROM petitions WHERE id = ?', (petition_id,))
    row = c.fetchone()
    conn.close()
    
    if not row or not row[0]:
        return jsonify({"error": "Work completion file not found"}), 404
    
    file_path = row[0]
    
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    
    return send_file(file_path, as_attachment=True)

@app.route('/api/petitions/<int:petition_id>/status', methods=['PUT'])
def update_petition_status(petition_id):
    """Update petition status"""
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"error": "Status is required"}), 400
    
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    c.execute('UPDATE petitions SET status = ? WHERE id = ?', (new_status, petition_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True}), 200

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get statistics for dashboard"""
    conn = sqlite3.connect('petitions.db')
    c = conn.cursor()
    
    # Total by priority
    c.execute('SELECT priority, COUNT(*) FROM petitions GROUP BY priority')
    priority_counts = dict(c.fetchall())
    
    # Total by department
    c.execute('SELECT department, COUNT(*) FROM petitions GROUP BY department')
    department_counts = dict(c.fetchall())
    
    conn.close()
    
    return jsonify({
        "priority_counts": priority_counts,
        "department_counts": department_counts
    }), 200

@app.route('/api/petitions/clear/<priority>', methods=['DELETE'])
def clear_priority_petitions(priority):
    """Clear petitions by priority"""
    try:
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        
        # Get file paths before deleting
        c.execute('SELECT file_path FROM petitions WHERE priority = ?', (priority,))
        file_paths = [row[0] for row in c.fetchall()]
        
        # Delete from database
        c.execute('DELETE FROM petitions WHERE priority = ?', (priority,))
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        # Delete physical files
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({"success": True, "deleted": deleted_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/petitions/clear-all', methods=['DELETE'])
def clear_all_petitions():
    """Clear all petitions"""
    try:
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        
        # Get all file paths before deleting
        c.execute('SELECT file_path FROM petitions')
        file_paths = [row[0] for row in c.fetchall()]
        
        # Delete all from database
        c.execute('DELETE FROM petitions')
        deleted_count = c.rowcount
        conn.commit()
        conn.close()
        
        # Delete all physical files
        for file_path in file_paths:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        return jsonify({"success": True, "deleted": deleted_count}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/signup', methods=['POST'])
def signup():
    """User signup with email only"""
    try:
        data = request.json
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        
        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400
        
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (email,))
        if c.fetchone():
            conn.close()
            return jsonify({"error": "An account with this email already exists"}), 409
        
        c.execute('''
            INSERT INTO users (username, password, email, role) 
            VALUES (?, ?, ?, ?)
        ''', (email, password, email, 'admin'))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Account created successfully"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        c.execute('SELECT id, username, password, email, role, department FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and user[2] == password:  # user[2] is password column
            return jsonify({
                "success": True,
                "username": user[1],
                "email": user[3],
                "role": user[4],
                "department": user[5]
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email"""
    try:
        data = request.json
        username = data.get('username')
        
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expiry = datetime.now().timestamp() + 3600  # 1 hour from now
        
        c.execute('''
            UPDATE users 
            SET reset_token = ?, reset_token_expiry = ? 
            WHERE username = ?
        ''', (reset_token, expiry, username))
        conn.commit()
        conn.close()
        
        # Send reset email
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if not gmail_user or not gmail_password:
            return jsonify({"error": "Email not configured"}), 500
        
        user_email = user[3]  # user[3] is email column
        # Use frontend URL from environment variable, fallback to localhost
        frontend_url = os.getenv('FRONTEND_URL', 'https://id-preview--a0b65845-62e3-4fd3-80f2-2c80fbabeed6.lovable.app')
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"
        
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = user_email
        msg['Subject'] = "🔐 Password Reset Request"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2 style="color: #333; margin-bottom: 20px;">Password Reset Request</h2>
                <p style="color: #666; line-height: 1.6;">
                    You have requested to reset your password. Click the button below to create a new password:
                </p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" 
                       style="background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%); 
                              color: white; 
                              padding: 15px 40px; 
                              text-decoration: none; 
                              border-radius: 8px; 
                              font-weight: bold;
                              display: inline-block;">
                        Reset Password
                    </a>
                </div>
                <p style="color: #999; font-size: 12px; margin-top: 30px;">
                    This link will expire in 1 hour. If you didn't request this, please ignore this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(gmail_user, gmail_password)
            server.send_message(msg)
        
        return jsonify({"success": True, "message": "Reset email sent"}), 200
    except Exception as e:
        print(f"Password reset error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token"""
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')
        
        conn = sqlite3.connect('petitions.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE reset_token = ?', (token,))
        user = c.fetchone()
        
        if not user:
            return jsonify({"error": "Invalid reset token"}), 400
        
        # Check if token expired
        expiry = user[7]  # user[7] is reset_token_expiry column
        if datetime.now().timestamp() > expiry:
            return jsonify({"error": "Reset token expired"}), 400
        
        # Update password and clear token
        c.execute('''
            UPDATE users 
            SET password = ?, reset_token = NULL, reset_token_expiry = NULL 
            WHERE reset_token = ?
        ''', (new_password, token))
        conn.commit()
        conn.close()
        
        return jsonify({"success": True, "message": "Password updated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

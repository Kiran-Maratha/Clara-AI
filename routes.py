from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Chat, Message
import logging
import os
import re
import random
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PASSWORD_REGEX = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]).{8,}$")
PASSWORD_ERROR = "Password must be at least 8 characters and include an uppercase letter, a number, and a special character (e.g. !@#$%)."

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

def send_otp_email(to_email, otp):
    sender_email = os.getenv('GMAIL_EMAIL')
    sender_password = os.getenv('GMAIL_APP_PASSWORD')
    
    print(f"\n--- DEVELOPMENT OTP TRACKER: {otp} allocated to {to_email} ---\n")
    
    if not sender_email or not sender_password:
        return False

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = 'Your Clara AI Verification Code'

    body = f"Identity requested.\n\nYour Clara AI secure verification code is: {otp}\n\nThis code will expire natively in 10 minutes."
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def is_malicious(value):
    if not isinstance(value, str):
        return False
    val_lower = value.lower()
    
    # Heuristic SQL injection check
    sqli_patterns = ['drop table', 'union select', 'delete from', ' or 1=1', 'truncate table']
    if any(p in val_lower for p in sqli_patterns):
        return True
        
    # Heuristic XSS check
    xss_patterns = ['<script', 'javascript:', 'onload=', 'onerror=', 'document.cookie', 'eval(']
    if any(p in val_lower for p in xss_patterns):
        return True
        
    return False

@main_bp.before_app_request
def check_for_injections():
    if request.method in ['POST', 'PUT', 'PATCH']:
        if request.form:
            for key, value in request.form.items():
                if is_malicious(value):
                    return jsonify({"error": "Security exception: Malicious input detected (SQLi/XSS). Request blocked."}), 403
        
        if request.is_json and request.get_json(silent=True):
            data = request.get_json(silent=True)
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, str) and is_malicious(value):
                        return jsonify({"error": "Security exception: Malicious input detected (SQLi/XSS). Request blocked."}), 403

@main_bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = db.session.get(User, user_id)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if not g.user:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        # Safely acquire form items
        g.user.full_name = request.form.get('full_name', g.user.full_name)
        g.user.job_title = request.form.get('job_title', g.user.job_title)
        g.user.department = request.form.get('department', g.user.department)
        
        # Handle file upload securely
        profile_file = request.files.get('profile_pic')
        if profile_file and profile_file.filename != '':
            filename = secure_filename(profile_file.filename)
            unique_filename = f"{g.user.id}_{filename}"
            upload_dir = os.path.join(current_app.root_path, 'static', 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            save_path = os.path.join(upload_dir, unique_filename)
            profile_file.save(save_path)
            g.user.profile_pic = unique_filename
            
        db.session.commit()
        return redirect(url_for('main.settings'))

    return render_template('settings.html')

@main_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if not g.user:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_new_password = request.form.get('confirm_new_password')
        
        if not check_password_hash(g.user.password, current_password):
            return render_template('change_password.html', error="Current authentication credentials incorrect.")
            
        if not PASSWORD_REGEX.match(new_password):
            return render_template('change_password.html', error=PASSWORD_ERROR)
            
        if new_password == confirm_new_password:
            otp = str(random.randint(100000, 999999))
            session['pending_new_password'] = generate_password_hash(new_password)
            session['otp'] = otp
            session['otp_time'] = time.time()
            session['otp_action'] = 'change_password'
            
            send_otp_email(g.user.email, otp)
            return redirect(url_for('auth.verify_otp'))
            
        return render_template('change_password.html', error="Secure passwords do not sequentially align.")
        
    return render_template('change_password.html')

@main_bp.route('/api/chat', methods=['POST'])
def chat():
    if not g.user:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json(silent=True)
    if not data:
        data = request.form
        
    if not data or 'message' not in data:
        return jsonify({"error": "Message required."}), 400
        
    user_message = data.get('message', '')
    chat_id = data.get('chat_id')
    issue_context = data.get('issue_context', '').strip() or 'General IT Support'
    
    # Process file attachments
    attachments = request.files.getlist('attachments')
    file_paths = []
    attachment_labels = []
    
    if attachments:
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'chat')
        os.makedirs(upload_dir, exist_ok=True)
        for f in attachments:
            if f and f.filename:
                safe_name = secure_filename(f.filename)
                unique_name = f"{int(time.time())}_{safe_name}"
                save_path = os.path.join(upload_dir, unique_name)
                f.save(save_path)
                file_paths.append(save_path)
                attachment_labels.append(safe_name)
                
    if not user_message and not attachments:
        return jsonify({"error": "Message or attachment required."}), 400
        
    # Append labels so it renders in history UI
    db_message = user_message
    if attachment_labels:
        files_str = ", ".join(attachment_labels)
        db_message = f"{user_message}\n\n*[Attached File(s): {files_str}]*" if user_message else f"*[Attached File(s): {files_str}]*"
    
    if chat_id:
        chat_session = Chat.query.filter_by(id=chat_id, user_id=g.user.id).first()
        if not chat_session:
            return jsonify({"error": "Chat session not found."}), 404
            
        # Update title if it was a "New Chat" and we now have a better user message
        if chat_session.title == "New Chat" and user_message:
            new_title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            chat_session.title = new_title
            db.session.commit()
    else:
        chat_title = user_message[:50] + "..." if len(user_message) > 50 else (attachment_labels[0] if attachment_labels else "New Chat")
        chat_session = Chat(user_id=g.user.id, title=chat_title)
        db.session.add(chat_session)
        db.session.commit()
        
    user_msg_entry = Message(chat_id=chat_session.id, sender='user', content=db_message)
    db.session.add(user_msg_entry)
    db.session.commit()
    
    history_lines = []
    messages = Message.query.filter_by(chat_id=chat_session.id).order_by(Message.created_at).all()
    for msg in messages:
        sender_label = "USER:" if msg.sender == 'user' else "CLARA AI:"
        history_lines.append(f"{sender_label} {msg.content}")
    chat_history_text = "\n".join(history_lines)
    
    from ai_service import analyze_request, generate_response
    
    # Bot 1: Analysis
    structured_json = analyze_request(db_message, media=file_paths if file_paths else None, issue_context=issue_context, chat_history_text=chat_history_text)
    if not structured_json:
        structured_json = '{"intent": "Unknown", "core_questions": [], "extracted_context": "None"}'
        
    # Bot 2: Response Generation
    ai_response = generate_response(structured_json, chat_history_text)
    
    # If the response is the specific offline/rate-limit message, return as error rather than storing
    if "sorry ai currently offline" in ai_response or "RESOURCE_EXHAUSTED" in ai_response:
        error_msg = "ai is currently handling too many requests. please wait a moment before trying again." if "RESOURCE_EXHAUSTED" in ai_response else ai_response
        return jsonify({
            "error": error_msg,
            "chat_id": chat_session.id
        }), 503

    ai_msg_entry = Message(chat_id=chat_session.id, sender='ai', content=ai_response)
    db.session.add(ai_msg_entry)
    db.session.commit()
    
    return jsonify({
        "response": ai_response,
        "chat_id": chat_session.id,
        "title": chat_session.title
    })

@main_bp.route('/api/chat/<int:chat_id>/star', methods=['POST'])
def star_chat(chat_id):
    if not g.user:
        return jsonify({"error": "Unauthorized"}), 401
    chat_session = Chat.query.filter_by(id=chat_id, user_id=g.user.id).first()
    if not chat_session:
        return jsonify({"error": "Not found"}), 404
    chat_session.is_starred = not chat_session.is_starred
    db.session.commit()
    return jsonify({"starred": chat_session.is_starred})

@main_bp.route('/api/chat/<int:chat_id>', methods=['DELETE'])
def delete_chat(chat_id):
    if not g.user:
        return jsonify({"error": "Unauthorized"}), 401
    chat_session = Chat.query.filter_by(id=chat_id, user_id=g.user.id).first()
    if not chat_session:
        return jsonify({"error": "Not found"}), 404
    
    db.session.delete(chat_session)
    db.session.commit()
    return jsonify({"success": True})

@main_bp.route('/api/chat/<int:chat_id>/messages', methods=['GET'])
def get_chat_messages(chat_id):
    if not g.user:
        return jsonify({"error": "Unauthorized"}), 401
    chat_session = Chat.query.filter_by(id=chat_id, user_id=g.user.id).first()
    if not chat_session:
        return jsonify({"error": "Not found"}), 404
    messages = [
        {"sender": m.sender, "content": m.content}
        for m in chat_session.messages
    ]
    return jsonify({"messages": messages, "title": chat_session.title})

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not EMAIL_REGEX.match(email):
            return redirect(url_for('auth.login'))
            
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            otp = str(random.randint(100000, 999999))
            session['pending_user_id'] = user.id
            session['otp'] = otp
            session['otp_time'] = time.time()
            session['otp_action'] = 'login'
            send_otp_email(email, otp)
            return redirect(url_for('auth.verify_otp'))
            
    return render_template('login.html', register=False)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not email or not EMAIL_REGEX.match(email):
            return render_template('login.html', register=True, error="Please enter a valid email address.")
            
        if not password or not PASSWORD_REGEX.match(password):
            return render_template('login.html', register=True, error=PASSWORD_ERROR)
        
        if password != confirm_password:
            return render_template('login.html', register=True, error="Passwords do not match.")

        user = User.query.filter_by(email=email).first()
        if user:
            return render_template('login.html', register=True, error="An account with this email already exists. Please log in instead.")

        hashed_password = generate_password_hash(password)
        otp = str(random.randint(100000, 999999))
        
        session['pending_user'] = {
            'full_name': full_name,
            'email': email,
            'password': hashed_password
        }
        session['otp'] = otp
        session['otp_time'] = time.time()
        session['otp_action'] = 'register'
        
        send_otp_email(email, otp)
        return redirect(url_for('auth.verify_otp'))
    return render_template('login.html', register=True)
    
@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'otp' not in session:
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if time.time() - session.get('otp_time', 0) > 600:
            session.pop('otp', None)
            return render_template('verify_otp.html', error="OTP expired. Please reboot process.")
        
        if user_otp == session['otp']:
            action = session.get('otp_action')
            
            if action == 'register':
                pending = session.get('pending_user')
                new_user = User(
                    full_name=pending['full_name'],
                    email=pending['email'],
                    password=pending['password']
                )
                db.session.add(new_user)
                db.session.commit()
                session['user_id'] = new_user.id
                
            elif action == 'login':
                session['user_id'] = session.get('pending_user_id')
                
            elif action == 'forgot_password':
                session['allow_password_reset'] = True
                session.pop('otp', None)
                return redirect(url_for('auth.reset_password'))
                
            elif action == 'change_password':
                g.user.password = session.get('pending_new_password')
                db.session.commit()
                session.pop('otp', None)
                session.pop('pending_new_password', None)
                session.pop('otp_action', None)
                return redirect(url_for('main.settings'))
                
            session.pop('otp', None)
            session.pop('pending_user', None)
            session.pop('pending_user_id', None)
            session.pop('otp_action', None)
            return redirect(url_for('main.index'))
            
        return render_template('verify_otp.html', error="Invalid authorization code. Please try again.")
        
    return render_template('verify_otp.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    step = 'email'
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'send_otp':
            email = request.form.get('email')
            if not email or not EMAIL_REGEX.match(email):
                return render_template('reset_password.html', step='email', error="Invalid email format.")
            user = User.query.filter_by(email=email).first()
            if user:
                otp = str(random.randint(100000, 999999))
                session['reset_email'] = email
                session['reset_otp'] = otp
                session['reset_otp_time'] = time.time()
                send_otp_email(email, otp)
                return render_template('reset_password.html', step='otp')
            return render_template('reset_password.html', step='email', error="Email not bound to active schemas.")
            
        elif action == 'verify_otp':
            user_otp = request.form.get('otp')
            if time.time() - session.get('reset_otp_time', 0) > 600:
                session.pop('reset_otp', None)
                return render_template('reset_password.html', step='email', error="OTP expired. Please reboot process.")
            if user_otp == session.get('reset_otp'):
                session['allow_password_reset'] = True
                session.pop('reset_otp', None)
                return render_template('reset_password.html', step='password')
            return render_template('reset_password.html', step='otp', error="Invalid authorization code.")
            
        elif action == 'reset_password':
            if not session.get('allow_password_reset'):
                return redirect(url_for('auth.login'))
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            if not password or not PASSWORD_REGEX.match(password):
                return render_template('reset_password.html', step='password', error=PASSWORD_ERROR)
            if password == confirm_password:
                email = session.get('reset_email')
                user = User.query.filter_by(email=email).first()
                if user:
                    user.password = generate_password_hash(password)
                    db.session.commit()
                    session.pop('allow_password_reset', None)
                    session.pop('reset_email', None)
                    session['user_id'] = user.id
                    return redirect(url_for('main.index'))
            return render_template('reset_password.html', step='password', error="Secure passwords do not sequentially align.")
            
    if session.get('allow_password_reset'):
        step = 'password'
    elif session.get('reset_otp'):
        step = 'otp'
        
    return render_template('reset_password.html', step=step)
    
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

from flask import Blueprint, render_template, request, jsonify, current_app, session, redirect, url_for, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, Admin, Message, Chat, User
import os
import random
import time
from routes import send_otp_email

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.before_request
def load_admin():
    admin_id = session.get('admin_id')
    if admin_id is None:
        g.admin = None
    else:
        g.admin = db.session.get(Admin, admin_id)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.admin:
        return redirect(url_for('admin.dashboard'))
        
    error = None
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(email=email).first()
        if admin and check_password_hash(admin.password, password):
            otp = str(random.randint(100000, 999999))
            session['pending_admin_id'] = admin.id
            session['admin_otp'] = otp
            session['admin_otp_time'] = time.time()
            
            if send_otp_email(email, otp):
                return redirect(url_for('admin.verify_otp'))
            else:
                error = "Failed to send verification email. Please check your network connection."
                session.pop('admin_otp', None)
        else:
            error = "Invalid admin credentials."
            
    return render_template('admin_login.html', error=error)

@admin_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'admin_otp' not in session:
        return redirect(url_for('admin.login'))
        
    error = None
    if request.method == 'POST':
        user_otp = request.form.get('otp')
        
        if time.time() - session.get('admin_otp_time', 0) > 600:
            session.pop('admin_otp', None)
            return render_template('admin_verify_otp.html', error="OTP expired. Please try again.")
            
        if user_otp == session['admin_otp']:
            session['admin_id'] = session.get('pending_admin_id')
            session.pop('admin_otp', None)
            session.pop('pending_admin_id', None)
            session.pop('admin_otp_time', None)
            return redirect(url_for('admin.dashboard'))
        else:
            error = "Invalid authorization code."
            
    return render_template('admin_verify_otp.html', error=error)

@admin_bp.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def dashboard():
    if not g.admin:
        return redirect(url_for('admin.login'))
        
    error = request.args.get('error')
    success = request.args.get('success')
        
    # Query all disliked messages
    disliked_msgs = Message.query.filter_by(feedback=-1).order_by(Message.created_at.desc()).all()
    
    # We want to find the user's prompt just before this message in the chat
    feedback_items = []
    for amsg in disliked_msgs:
        chat = Chat.query.get(amsg.chat_id)
        # Find the message immediately preceding it
        prev = Message.query.filter(Message.chat_id == chat.id, Message.created_at < amsg.created_at, Message.sender == 'user').order_by(Message.created_at.desc()).first()
        feedback_items.append({
            'chat_title': chat.title if chat else 'Deleted Chat',
            'user_email': chat.user.email if (chat and chat.user) else 'Unknown User',
            'user_prompt': prev.content if prev else 'N/A',
            'ai_response': amsg.content,
            'timestamp': amsg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    # List uploaded files
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'knowledge_base')
    knowledge_files = []
    if os.path.exists(upload_dir):
        knowledge_files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
        
    admins = Admin.query.all()
        
    return render_template('admin_dashboard.html', feedback_items=feedback_items, knowledge_files=knowledge_files, admins=admins, error=error, success=success)

@admin_bp.route('/add_admin', methods=['POST'])
def add_admin():
    if not g.admin:
        return jsonify({"error": "Unauthorized"}), 401
        
    email = request.form.get('email')
    password = request.form.get('password')
    
    if not email or not password:
        return redirect(url_for('admin.dashboard', error="Email and password required."))
        
    if Admin.query.filter_by(email=email).first():
        return redirect(url_for('admin.dashboard', error="Admin already exists."))
        
    new_admin = Admin(email=email, password=generate_password_hash(password))
    db.session.add(new_admin)
    db.session.commit()
    
    return redirect(url_for('admin.dashboard', success="Admin created successfully!"))

@admin_bp.route('/train', methods=['POST'])
def train():
    if not g.admin:
        return jsonify({"error": "Unauthorized"}), 401
        
    file = request.files.get('knowledge_file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'knowledge_base')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, filename))
        return redirect(url_for('admin.dashboard', success=f"Knowledge File '{filename}' Uploaded Successfully!"))
        
    return redirect(url_for('admin.dashboard', error="No file provided."))

@admin_bp.route('/delete_file/<filename>', methods=['POST'])
def delete_file(filename):
    if not g.admin:
        return jsonify({"error": "Unauthorized"}), 401
        
    safe_name = secure_filename(filename)
    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'knowledge_base')
    file_path = os.path.join(upload_dir, safe_name)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for('admin.dashboard', success=f"File {safe_name} removed."))
        
    return redirect(url_for('admin.dashboard', error="File not found."))

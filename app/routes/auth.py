from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app.models.user import User
from app import db

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.dashboard'))
            
        flash('Geçersiz kullanıcı adı veya şifre', 'danger')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            flash('Tüm alanları doldurunuz', 'warning')
        elif not current_user.check_password(current_password):
            flash('Mevcut şifre yanlış', 'danger')
        elif new_password != confirm_password:
            flash('Yeni şifreler eşleşmiyor', 'danger')
        elif len(new_password) < 6:
            flash('Şifre en az 6 karakter olmalıdır', 'warning')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Şifreniz başarıyla güncellendi', 'success')
            return redirect(url_for('auth.profile'))
            
    return render_template('auth/profile.html')
from flask import redirect, url_for, flash, render_template, request
from flask_login import login_user, logout_user, current_user
from app import db, oauth
from app.auth import bp
from app.models import User

@bp.route('/login')
def login():
    redirect_uri = url_for('auth.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = token.get('userinfo')
    if user_info:
        user = User.query.filter_by(email=user_info['email']).first()
        if not user:
            user = User(
                google_id=user_info.get('sub'),
                email=user_info['email'],
                name=user_info['name'],
                profile_pic=user_info.get('picture')
            )
            
            # Auto-promote first user
            if User.query.count() == 0:
                user.is_admin = True
                
            db.session.add(user)
            db.session.commit()
        login_user(user)
        return redirect(url_for('main.index'))
    return redirect(url_for('main.index'))

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

from flask import render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from app.models import get_db
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def is_valid_number(value):

    pattern = r'^\+?[\d\s\-()]{8,}$'
    if not re.match(pattern, value):
        return False
    
    # Count actual digits
    digit_count = sum(c.isdigit() for c in value)
    return 8 <= digit_count <= 15  # Reasonable phone number length

def init_app_routes(app):
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            if not email or not password or not confirm_password:
                flash('Please fill in all fields', 'error')
                return render_template('register.html')

            if password != confirm_password:
                flash('Passwords do not match', 'error')
                return render_template('register.html')

            hashed_password = generate_password_hash(password)
            
            db = get_db()
            try:
                db.execute(
                    'INSERT INTO Rubrica_login (email, password) VALUES (?, ?)',
                    (email, hashed_password)
                )
                db.commit()
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                flash('Email already exists', 'error')
                return render_template('register.html')
        
        return render_template('register.html')

    @app.route('/', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            
            if not email or not password:
                flash('Please fill in all fields', 'error')
                return render_template('login.html')
            
            db = get_db()
            user = db.execute(
                'SELECT * FROM Rubrica_login WHERE email = ?',
                (email,)
            ).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['user_email'] = user['email']
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials', 'error')
        return render_template('login.html')

    @app.route('/home')
    @login_required
    def home():
        try:
            db = get_db()
            rubrica = db.execute(
                'SELECT * FROM Rubrica WHERE utente_id = ? ORDER BY nome',
                (session['user_id'],)
            ).fetchall()
            return render_template('index.html', rubrica=rubrica)
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('login'))

    @app.route('/aggiungi', methods=['GET', 'POST'])
    @login_required
    def aggiungi():
        if request.method == 'POST':
            required_fields = ['nome', 'cognome', 'email']
            for field in required_fields:
                if not request.form.get(field):
                    flash(f'{field.capitalize()} is required', 'error')
                    return redirect(url_for('aggiungi'))

            # Validate phone number if provided
            phone = request.form.get('telefono')
            if phone and not is_valid_number(phone):
                flash('Invalid phone number format', 'error')
                return redirect(url_for('aggiungi'))

            try:
                db = get_db()
                db.execute('''
                    INSERT INTO Rubrica (
                        nome, cognome, sesso, data_nascita, 
                        telefono, email, citta, utente_id
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    request.form.get('nome'),
                    request.form.get('cognome'),
                    request.form.get('sesso'),
                    request.form.get('data_nascita'),
                    request.form.get('telefono'),
                    request.form.get('email'),
                    request.form.get('citta'),
                    session['user_id']
                ))
                db.commit()
                flash('Contact added successfully', 'success')
                return redirect(url_for('home'))
            except sqlite3.Error as e:
                flash(f'Error adding contact: {str(e)}', 'error')
                return redirect(url_for('aggiungi'))

        try:
            with open('cities.csv', 'r', encoding='utf-8') as f:
                cities = [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            cities = []
            flash('Cities file not found. Using empty list.', 'warning')

        return render_template('form.html', cities=cities)

    @app.route('/update_contact', methods=['POST'])
    @login_required
    def update_contact():
        try:
            contact_id = request.form.get('id')
            field = request.form.get('field')
            value = request.form.get('value')

            allowed_fields = {
                'nome', 'cognome', 'sesso', 'data_nascita', 
                'telefono', 'email', 'citta'
            }
            
            if field not in allowed_fields:
                return jsonify({'error': 'Invalid field'}), 400

            # Validate required fields
            if field in ['nome', 'cognome', 'email'] and not value:
                return jsonify({'error': f'{field.capitalize()} cannot be empty'}), 400

            # Validate email format if updating email
            if field == 'email' and '@' not in value:
                return jsonify({'error': 'Invalid email format'}), 400

            # Add validation for telephone number
            if field == 'telefono' and value:  # Only validate if value is not empty
                if not is_valid_number(value):
                    return jsonify({'error': 'Invalid phone number format'}), 400

            db = get_db()
            
            # Verify the contact belongs to the current user
            contact = db.execute(
                'SELECT * FROM Rubrica WHERE id = ? AND utente_id = ?',
                (contact_id, session['user_id'])
            ).fetchone()
            
            if not contact:
                return jsonify({'error': 'Contact not found'}), 404

            query = f'UPDATE Rubrica SET {field} = ? WHERE id = ? AND utente_id = ?'
            db.execute(query, (value, contact_id, session['user_id']))
            db.commit()
            
            return jsonify({'message': 'Updated successfully'}), 200

        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/delete/<int:id>')
    @login_required
    def delete_contact(id):
        try:
            db = get_db()
            result = db.execute(
                'DELETE FROM Rubrica WHERE id = ? AND utente_id = ?',
                (id, session['user_id'])
            )
            db.commit()
            
            if result.rowcount > 0:
                flash('Contact deleted successfully', 'success')
            else:
                flash('Contact not found', 'error')
                
        except sqlite3.Error as e:
            flash(f'Error deleting contact: {str(e)}', 'error')
        
        return redirect(url_for('home'))

    @app.route('/search')
    @login_required
    def search():
        query = request.args.get('q', '').strip()
        if query:
            try:
                db = get_db()
                search_query = f'%{query}%'
                contacts = db.execute('''
                    SELECT * FROM Rubrica 
                    WHERE utente_id = ? 
                    AND (
                        nome LIKE ? OR 
                        cognome LIKE ? OR 
                        email LIKE ? OR 
                        citta LIKE ? OR
                        telefono LIKE ?
                    )
                    ORDER BY nome
                ''', (session['user_id'], search_query, search_query, 
                      search_query, search_query, search_query)).fetchall()
                
                return jsonify([dict(row) for row in contacts])
            except sqlite3.Error as e:
                return jsonify({'error': str(e)}), 500
        return jsonify([])

    @app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        if request.method == 'POST':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not all([current_password, new_password, confirm_password]):
                flash('All fields are required', 'error')
                return render_template('profile.html')

            db = get_db()
            user = db.execute(
                'SELECT * FROM Rubrica_login WHERE id = ?',
                (session['user_id'],)
            ).fetchone()

            if not check_password_hash(user['password'], current_password):
                flash('Current password is incorrect', 'error')
                return render_template('profile.html')

            if new_password != confirm_password:
                flash('New passwords do not match', 'error')
                return render_template('profile.html')

            if len(new_password) < 6:
                flash('Password must be at least 6 characters long', 'error')
                return render_template('profile.html')

            try:
                hashed_password = generate_password_hash(new_password)
                db.execute(
                    'UPDATE Rubrica_login SET password = ? WHERE id = ?',
                    (hashed_password, session['user_id'])
                )
                db.commit()
                flash('Password updated successfully', 'success')
            except sqlite3.Error as e:
                flash(f'Error updating password: {str(e)}', 'error')

        return render_template('profile.html')

    @app.route('/export')
    @login_required
    def export_contacts():
        try:
            db = get_db()
            contacts = db.execute('''
                SELECT nome, cognome, sesso, data_nascita, telefono, email, citta 
                FROM Rubrica 
                WHERE utente_id = ?
                ORDER BY nome
            ''', (session['user_id'],)).fetchall()
            
            return jsonify([dict(row) for row in contacts])
        except sqlite3.Error as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out successfully', 'info')
        return redirect(url_for('login'))

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    return app
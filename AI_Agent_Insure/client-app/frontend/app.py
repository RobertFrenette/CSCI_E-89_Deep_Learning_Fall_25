"""
Flask application for Client Frontend
Modern customer-facing portal for AI Agent Insurance
"""
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import requests
import os
from functools import wraps
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# API Configuration
API_BASE_URL = os.getenv('CLIENT_BACKEND_URL', 'http://localhost:8001')


def get_auth_headers():
    """Get authorization headers with JWT token from session"""
    token = session.get('access_token')
    if token:
        return {'Authorization': f'Bearer {token}'}
    return {}


def login_required(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Home page with marketing content"""
    from datetime import datetime
    return render_template('index.html', current_year=datetime.now().year)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login - handles both modal and page requests"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Call FastAPI login endpoint
            response = requests.post(
                f'{API_BASE_URL}/api/auth/login',
                data={
                    'username': username,
                    'password': password
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            
            if response.status_code == 200:
                data = response.json()
                session['access_token'] = data['access_token']
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                error_data = response.json()
                flash(error_data.get('detail', 'Invalid username or password.'), 'error')
        except requests.exceptions.RequestException as e:
            flash('Unable to connect to server. Please try again later.', 'error')
    
    # If GET request, redirect to home page
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration - handles both modal and page requests"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        policy_number = request.form.get('policy_number')
        
        if not all([username, email, password, policy_number]):
            flash('All fields are required.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Call FastAPI register endpoint
            response = requests.post(
                f'{API_BASE_URL}/api/auth/register',
                json={
                    'username': username,
                    'email': email,
                    'password': password,
                    'policy_number': policy_number
                }
            )
            
            if response.status_code == 201:
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('index', show='login'))
            else:
                error_data = response.json()
                flash(error_data.get('detail', 'Registration failed.'), 'error')
        except requests.exceptions.RequestException as e:
            flash('Unable to connect to server. Please try again later.', 'error')
    
    # If GET request, redirect to home page
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard with policy overview"""
    try:
        # Get user profile
        user_response = requests.get(
            f'{API_BASE_URL}/api/user/me',
            headers=get_auth_headers()
        )
        
        if user_response.status_code != 200:
            flash('Unable to load user profile.', 'error')
            return redirect(url_for('index'))
        
        user = user_response.json()
        
        # Get user policies
        policies_response = requests.get(
            f'{API_BASE_URL}/api/user/policies',
            headers=get_auth_headers()
        )
        
        policies = []
        if policies_response.status_code == 200:
            policies = policies_response.json()
        
        return render_template('dashboard.html', user=user, policies=policies)
    
    except requests.exceptions.RequestException as e:
        flash('Unable to connect to server. Please try again later.', 'error')
        return redirect(url_for('index'))


@app.route('/policies')
@login_required
def policies():
    """List all user policies"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/user/policies',
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            policies = response.json()
            return render_template('policies.html', policies=policies)
        else:
            flash('Unable to load policies.', 'error')
            return redirect(url_for('dashboard'))
    
    except requests.exceptions.RequestException as e:
        flash('Unable to connect to server. Please try again later.', 'error')
        return redirect(url_for('dashboard'))


@app.route('/policies/<policy_number>')
@login_required
def policy_details(policy_number):
    """View detailed policy information"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/user/policies/{policy_number}',
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            policy = response.json()
            return render_template('policy_details.html', policy=policy)
        elif response.status_code == 404:
            flash('Policy not found.', 'error')
            return redirect(url_for('policies'))
        else:
            flash('Unable to load policy details.', 'error')
            return redirect(url_for('policies'))
    
    except requests.exceptions.RequestException as e:
        flash('Unable to connect to server. Please try again later.', 'error')
        return redirect(url_for('policies'))


@app.route('/claims', methods=['GET', 'POST'])
@login_required
def claims():
    """Submit a new claim"""
    if request.method == 'POST':
        # Get form data
        policy_number = request.form.get('policy_number')
        claim_type = request.form.get('claim_type')
        claim_amount = request.form.get('claim_amount')
        description = request.form.get('description')
        
        if not all([policy_number, claim_type, claim_amount]):
            flash('Policy number, claim type, and amount are required.', 'error')
            return render_template('claims.html')
        
        try:
            # TODO: Implement POST /api/claims endpoint in FastAPI backend
            # For now, just show a message
            flash('Claim submission feature coming soon!', 'info')
            return redirect(url_for('claims'))
        except Exception as e:
            flash('Unable to submit claim. Please try again later.', 'error')
    
    # Get user policies for the form dropdown
    try:
        policies_response = requests.get(
            f'{API_BASE_URL}/api/user/policies',
            headers=get_auth_headers()
        )
        policies = policies_response.json() if policies_response.status_code == 200 else []
    except:
        policies = []
    
    return render_template('claims.html', policies=policies)


@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    try:
        response = requests.get(
            f'{API_BASE_URL}/api/user/me',
            headers=get_auth_headers()
        )
        
        if response.status_code == 200:
            user = response.json()
            return render_template('profile.html', user=user)
        else:
            flash('Unable to load profile.', 'error')
            return redirect(url_for('dashboard'))
    
    except requests.exceptions.RequestException as e:
        flash('Unable to connect to server. Please try again later.', 'error')
        return redirect(url_for('dashboard'))


@app.route('/chat')
def chat():
    """AI Chat interface - accessible to both authenticated and unauthenticated users"""
    # Get user info if authenticated
    user = None
    user_id = "guest"
    
    if 'access_token' in session:
        try:
            response = requests.get(
                f'{API_BASE_URL}/api/user/me',
                headers=get_auth_headers()
            )
            if response.status_code == 200:
                user = response.json()
                user_id = session.get('username', 'guest')
        except:
            pass  # If user lookup fails, use guest mode
    
    # Get AI Agent URL from environment
    ai_agent_url = os.getenv('AI_AGENT_URL', 'http://localhost:8002')
    
    return render_template('chat.html', user=user, user_id=user_id, ai_agent_url=ai_agent_url)


@app.context_processor
def inject_chat_widget_data():
    """Inject chat widget data into all templates"""
    user_id = "guest"
    policy_number = None
    
    if 'access_token' in session:
        user_id = session.get('username', 'guest')
        # Try to get user's policy number from backend
        try:
            user_response = requests.get(
                f'{API_BASE_URL}/api/user/me',
                headers=get_auth_headers(),
                timeout=2  # Short timeout to avoid blocking page load
            )
            if user_response.status_code == 200:
                user_data = user_response.json()
                policy_number = user_data.get('policy_number')
        except (requests.exceptions.RequestException, KeyError, AttributeError):
            # If we can't fetch it, continue without it
            pass
    
    ai_agent_url = os.getenv('AI_AGENT_URL', 'http://localhost:8002')
    
    return dict(
        user_id=user_id,
        policy_number=policy_number,
        ai_agent_url=ai_agent_url
    )


if __name__ == '__main__':
    # Only run in debug mode if FLASK_ENV is development
    debug_mode = os.getenv('FLASK_ENV', 'production') == 'development'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)


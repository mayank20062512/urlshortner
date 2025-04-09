# app.py

import os
import json
import string
import random
import qrcode # For QR code generation
from io import BytesIO # To handle image in memory before saving
from urllib.parse import urlparse # For basic URL validation

from flask import (Flask, render_template, request, redirect, url_for,
                   flash, send_from_directory, make_response)

# --- Configuration ---
app = Flask(__name__)
# Use a strong, random secret key in a real application
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'a_default_development_secret_key')
URL_FILE = 'urls.json'
SHORT_CODE_LENGTH = 6 # Length of the generated short codes
QR_CODE_DIR = os.path.join(app.static_folder, 'qrcodes')

# Ensure QR code directory exists
os.makedirs(QR_CODE_DIR, exist_ok=True)

# --- Helper Functions ---

def load_urls():
    """Loads URL mappings from the JSON file."""
    if not os.path.exists(URL_FILE):
        return {}
    try:
        with open(URL_FILE, 'r') as f:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading URLs: {e}")
        # In a real app, you might want more robust error handling here
        # Maybe backup the corrupted file and start fresh?
        return {}

def save_urls(urls):
    """Saves URL mappings to the JSON file."""
    try:
        with open(URL_FILE, 'w') as f:
            json.dump(urls, f, indent=4)
    except IOError as e:
        print(f"Error saving URLs: {e}")
        flash("Error saving URL data. Please try again later.", "error")

def generate_short_code(length=SHORT_CODE_LENGTH):
    """Generates a random, unique short code."""
    characters = string.ascii_letters + string.digits
    urls = load_urls()
    while True:
        short_code = ''.join(random.choice(characters) for _ in range(length))
        if short_code not in urls:
            return short_code

def is_valid_url(url_string):
    """Performs a basic check if a string looks like a valid URL."""
    try:
        result = urlparse(url_string)
        # Check if scheme (http/https) and netloc (domain name) are present
        return all([result.scheme in ['http', 'https'], result.netloc])
    except ValueError:
        return False

def generate_qr_code(data, filename):
    """Generates a QR code image and saves it."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image
    filepath = os.path.join(QR_CODE_DIR, filename)
    try:
        img.save(filepath)
        return filename # Return filename on success
    except IOError as e:
        print(f"Error saving QR code {filename}: {e}")
        return None # Return None on failure

# --- Flask Routes ---

@app.route('/', methods=['GET', 'POST'])
def index():
    """Handles the homepage: displays form and processes submissions."""
    short_url_display = None
    qr_code_url = None
    submitted_long_url = None # Keep track of the submitted URL for display

    if request.method == 'POST':
        long_url = request.form.get('long_url', '').strip() # Get and strip whitespace
        submitted_long_url = long_url # Store for display even if validation fails initially

        if not long_url:
            flash("Please enter a URL.", "error")
            return render_template('index.html', submitted_long_url=submitted_long_url)

        # Add http:// if scheme is missing (simple approach)
        if not (long_url.startswith('http://') or long_url.startswith('https://')):
            long_url = 'http://' + long_url
            submitted_long_url = long_url # Update submitted URL if modified

        # Basic Validation
        if not is_valid_url(long_url):
             flash("Please enter a valid URL (e.g., https://www.example.com).", "error")
             return render_template('index.html', submitted_long_url=submitted_long_url)

        urls = load_urls()

        # --- Check if long URL already exists ---
        existing_code = None
        for code, data in urls.items():
             if data.get('long') == long_url:
                 existing_code = code
                 break

        if existing_code:
            short_code = existing_code
            flash(f"This URL has already been shortened.", "info")
        else:
            # --- Generate new short code and save ---
            short_code = generate_short_code()
            # Store long URL and initialize click count
            urls[short_code] = {'long': long_url, 'clicks': 0}
            save_urls(urls)
            flash(f"URL shortened successfully!", "success")

        # --- Prepare display data (common for existing and new) ---
        short_url_display = url_for('redirect_to_url', short_code=short_code, _external=True)

        # --- Generate QR Code ---
        qr_filename = f"{short_code}.png"
        if generate_qr_code(short_url_display, qr_filename):
             qr_code_url = url_for('static', filename=f'qrcodes/{qr_filename}')
        else:
             flash("Could not generate QR code.", "warning")

    # For GET requests or after POST processing, render the template
    return render_template('index.html',
                           short_url_display=short_url_display,
                           qr_code_url=qr_code_url,
                           submitted_long_url=submitted_long_url)


@app.route('/<short_code>')
def redirect_to_url(short_code):
    """Redirects a short code to its corresponding long URL and tracks click."""
    urls = load_urls()
    url_data = urls.get(short_code)

    if url_data and 'long' in url_data:
        long_url = url_data['long']

        # --- Track Click ---
        urls[short_code]['clicks'] = url_data.get('clicks', 0) + 1 # Safely increment
        save_urls(urls) # Save updated click count

        print(f"Redirecting {short_code} to {long_url} (Clicks: {urls[short_code]['clicks']})")
        # Use 302 Found for temporary redirect as per common practice for shorteners
        return redirect(long_url, code=302)
    else:
        flash(f"Short URL code '{short_code}' not found.", "error")
        return redirect(url_for('index'))

@app.route('/list')
def list_urls():
    """Displays a list of all shortened URLs and their stats."""
    urls = load_urls()
    # Prepare data for template (add short_url for easy linking)
    url_list = []
    for code, data in urls.items():
        url_list.append({
            'short_code': code,
            'short_url': url_for('redirect_to_url', short_code=code, _external=True),
            'long_url': data.get('long', 'N/A'),
            'clicks': data.get('clicks', 0)
        })
    # Optional: Sort the list, e.g., by clicks or alphabetically by code
    # url_list.sort(key=lambda x: x['clicks'], reverse=True)
    return render_template('list.html', url_list=url_list)

# --- Serve Static QR Codes ---
# This route is technically handled by Flask's static file serving,
# but explicitly defining it can be clearer for understanding.
# If you have many static files, Flask's default handling is usually sufficient.
# @app.route('/static/qrcodes/<filename>')
# def serve_qr_code(filename):
#     return send_from_directory(QR_CODE_DIR, filename)

# --- Run the App ---
if __name__ == '__main__':
    # Set debug=False for any kind of deployment or sharing
    # Use environment variables for configuration in production
    app.run(debug=True, host='0.0.0.0', port=5000) # host='0.0.0.0' makes it accessible on your network

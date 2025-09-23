from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import PyPDF2
import openpyxl
from openpyxl import Workbook
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import json
import os.path

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = 'your-secret-key-here'  # Change this in production

# Dummy user credentials
USERS = {
    '101': '1234'
}

# Google Drive API Setup
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_google_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    return build('drive', 'v3', credentials=creds)

def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def screen_resume(resume_text, job_description):
    # Simple keyword matching for demo
    # In production, you might want to use NLP or more sophisticated matching
    keywords = job_description.lower().split()
    resume_words = resume_text.lower().split()
    
    # Simple scoring: percentage of keywords found in resume
    matched = sum(1 for word in keywords if word in resume_words)
    score = (matched / len(keywords)) * 100 if keywords else 0
    return min(100, round(score, 2))

def login_required(f):
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        if user_id in USERS and USERS[user_id] == password:
            session['user_id'] = user_id
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid ID or password. Please try again.', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/upload_jd', methods=['POST'])
@login_required
def upload_jd():
    if 'job_description' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['job_description']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'jd.pdf')
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file.save(filepath)
        return jsonify({'message': 'Job description uploaded successfully'})

@app.route('/screen_resumes', methods=['POST'])
@login_required
async def screen_resumes():
    try:
        # Get job description
        jd_path = os.path.join(app.config['UPLOAD_FOLDER'], 'jd.pdf')
        if not os.path.exists(jd_path):
            return jsonify({'error': 'Please upload a job description first'}), 400
            
        with open(jd_path, 'rb') as jd_file:
            job_description = extract_text_from_pdf(jd_file)
        
        # Get resumes from Google Drive (simplified for demo)
        # In production, you would connect to Google Drive API here
        # For now, we'll use a placeholder
        resumes = [
            {'name': 'John Doe', 'email': 'john@example.com', 'file_id': 'sample1'},
            {'name': 'Jane Smith', 'email': 'jane@example.com', 'file_id': 'sample2'},
        ]
        
        # Process resumes
        results = []
        for resume in resumes:
            # In production, download the file from Google Drive using file_id
            # For demo, we'll use a placeholder
            resume_text = f"Resume for {resume['name']}. {job_description[:100]}"  # Simplified for demo
            score = screen_resume(resume_text, job_description)
            
            results.append({
                'name': resume['name'],
                'email': resume['email'],
                'score': score
            })
        
        # Sort by score (descending)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        # Save to Excel
        wb = Workbook()
        ws = wb.active
        ws.title = "Screened Candidates"
        
        # Add headers
        headers = ['Name', 'Email', 'Score (%)']
        for col_num, header in enumerate(headers, 1):
            ws.cell(row=1, column=col_num, value=header)
        
        # Add data
        for row_num, result in enumerate(results, 2):
            ws.cell(row=row_num, column=1, value=result['name'])
            ws.cell(row=row_num, column=2, value=result['email'])
            ws.cell(row=row_num, column=3, value=result['score'])
        
        # Save the workbook
        excel_path = os.path.join(app.config['UPLOAD_FOLDER'], 'screened_candidates.xlsx')
        wb.save(excel_path)
        
        return jsonify({
            'message': 'Screening completed',
            'results': results,
            'excel_path': excel_path
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download_results')
@login_required
def download_results():
    excel_path = os.path.join(app.config['UPLOAD_FOLDER'], 'screened_candidates.xlsx')
    if not os.path.exists(excel_path):
        return jsonify({'error': 'No results available'}), 404
    
    return send_file(
        excel_path,
        as_attachment=True,
        download_name='screened_candidates.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)

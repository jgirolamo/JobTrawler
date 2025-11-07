#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web Interface for Job Trawler
Displays jobs posted within the last 24 hours
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import json
import os
import threading
import time
from job_trawler import JobTrawler

# Get the directory where this file is located
basedir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(basedir, 'templates')

app = Flask(__name__, template_folder=template_dir)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')  # For flash messages
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Allow iframe embedding (for WordPress integration)
@app.after_request
def set_xframe_options(response):
    """Allow iframe embedding by removing/setting permissive headers"""
    # Remove X-Frame-Options if it exists (some servers add it)
    response.headers.pop('X-Frame-Options', None)
    # Set to ALLOWALL to explicitly allow embedding
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    # Also set Content-Security-Policy to allow framing
    response.headers['Content-Security-Policy'] = "frame-ancestors *;"
    return response


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_jobs():
    """Load jobs from job_alerts.json"""
    jobs_file = 'job_alerts.json'
    if not os.path.exists(jobs_file):
        return []
    
    try:
        with open(jobs_file, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        return jobs
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return []

def load_cv():
    """Load current CV content"""
    # Check config.json for CV path
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        cv_file = config.get('cv_path', 'cv.txt')
    except:
        cv_file = 'cv.txt'
    
    # Check if file exists
    if not os.path.exists(cv_file):
        return None
    
    try:
        # Check if file is binary (PDF) by reading first few bytes
        with open(cv_file, 'rb') as f:
            header = f.read(4)
            f.seek(0)
            is_pdf = header.startswith(b'%PDF')
            is_docx = header == b'PK\x03\x04'  # DOCX files start with ZIP header
        
        if is_pdf:
            # It's a PDF, return a message instead of trying to read as text
            return "[PDF file uploaded successfully. Content will be used for job matching.]"
        
        if is_docx or cv_file.endswith(('.docx', '.doc')):
            # It's a DOCX/DOC file
            return "[DOCX/DOC file uploaded successfully. Content will be used for job matching.]"
        
        # Try to read as text with different encodings
        try:
            with open(cv_file, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(cv_file, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return "[Unable to read CV file - encoding issue]"
    except Exception as e:
        print(f"Error loading CV: {e}")
        return None


def filter_recent_jobs(jobs, hours=24):
    """Filter jobs posted within the last N hours"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_jobs = []
    
    for job in jobs:
        date_found_str = job.get('date_found', '')
        if not date_found_str:
            continue
        
        try:
            # Parse ISO format datetime
            job_date = datetime.fromisoformat(date_found_str.replace('Z', '+00:00'))
            # Handle timezone-aware datetime
            if job_date.tzinfo:
                job_date = job_date.replace(tzinfo=None)
            
            if job_date >= cutoff_time:
                # Calculate hours ago
                hours_ago = (datetime.now() - job_date).total_seconds() / 3600
                job['hours_ago'] = round(hours_ago, 1)
                recent_jobs.append(job)
        except Exception as e:
            print(f"Error parsing date for job: {e}")
            continue
    
    # Sort by most recent first
    recent_jobs.sort(key=lambda x: x.get('date_found', ''), reverse=True)
    return recent_jobs


@app.route('/')
def index():
    """Main page showing recent jobs - only from last search"""
    all_jobs = load_jobs()
    
    # Get last search start time
    search_session_file = 'last_search_start.json'
    cutoff_time = None
    
    try:
        if os.path.exists(search_session_file):
            with open(search_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                search_start_str = session_data.get('start_time', '')
                if search_start_str:
                    cutoff_time = datetime.fromisoformat(search_start_str.replace('Z', '+00:00'))
                    if cutoff_time.tzinfo:
                        cutoff_time = cutoff_time.replace(tzinfo=None)
    except Exception as e:
        print(f"Error loading search session: {e}")
    
    # If no search session found, show jobs from last 24 hours as fallback
    if cutoff_time is None:
        cutoff_time = datetime.now() - timedelta(hours=24)
    
    recent_jobs = []
    for job in all_jobs:
        date_found_str = job.get('date_found', '')
        if not date_found_str:
            continue
        
        try:
            job_date = datetime.fromisoformat(date_found_str.replace('Z', '+00:00'))
            if job_date.tzinfo:
                job_date = job_date.replace(tzinfo=None)
            
            # Only show jobs found after the last search started
            if job_date >= cutoff_time:
                hours_ago = (datetime.now() - job_date).total_seconds() / 3600
                job['hours_ago'] = round(hours_ago, 1)
                recent_jobs.append(job)
        except Exception as e:
            print(f"Error parsing date for job: {e}")
            continue
    
    recent_jobs.sort(key=lambda x: x.get('date_found', ''), reverse=True)
    
    # Sort all jobs by date and limit to last 999 most recent
    all_jobs_sorted = sorted(all_jobs, key=lambda x: x.get('date_found', ''), reverse=True)
    all_jobs_limited = all_jobs_sorted[:999]  # Limit to last 999 jobs
    
    # Get last update time
    jobs_file = 'job_alerts.json'
    last_updated = None
    if os.path.exists(jobs_file):
        last_updated = datetime.fromtimestamp(os.path.getmtime(jobs_file))
    
    # Load CV for display
    cv_content = load_cv()
    
    return render_template('jobs.html', 
                         jobs=recent_jobs, 
                         total_jobs=len(all_jobs),
                         recent_jobs_count=len(recent_jobs),
                         all_jobs=all_jobs_limited,  # Pass limited jobs (last 999) for toggle
                         last_updated=last_updated,
                         filter_type='last_search',  # Default to last search
                         cv_content=cv_content)


@app.route('/api/jobs')
def api_jobs():
    """API endpoint returning recent jobs as JSON - only from last search"""
    all_jobs = load_jobs()
    
    # Get last search start time
    search_session_file = 'last_search_start.json'
    cutoff_time = None
    
    try:
        if os.path.exists(search_session_file):
            with open(search_session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                search_start_str = session_data.get('start_time', '')
                if search_start_str:
                    cutoff_time = datetime.fromisoformat(search_start_str.replace('Z', '+00:00'))
                    if cutoff_time.tzinfo:
                        cutoff_time = cutoff_time.replace(tzinfo=None)
    except Exception as e:
        print(f"Error loading search session: {e}")
    
    # If no search session found, show jobs from last 24 hours as fallback
    if cutoff_time is None:
        cutoff_time = datetime.now() - timedelta(hours=24)
    
    recent_jobs = []
    for job in all_jobs:
        date_found_str = job.get('date_found', '')
        if not date_found_str:
            continue
        
        try:
            job_date = datetime.fromisoformat(date_found_str.replace('Z', '+00:00'))
            if job_date.tzinfo:
                job_date = job_date.replace(tzinfo=None)
            
            # Only show jobs found after the last search started
            if job_date >= cutoff_time:
                recent_jobs.append(job)
        except Exception:
            continue
    
    recent_jobs.sort(key=lambda x: x.get('date_found', ''), reverse=True)
    return jsonify({
        'total_jobs': len(all_jobs),
        'recent_jobs': len(recent_jobs),
        'jobs': recent_jobs
    })


@app.route('/api/refresh')
def api_refresh():
    """Force reload data from file"""
    all_jobs = load_jobs()
    recent_jobs = filter_recent_jobs(all_jobs, hours=72)
    return jsonify({
        'status': 'refreshed',
        'total_jobs': len(all_jobs),
        'recent_jobs': len(recent_jobs),
        'jobs': recent_jobs
    })

@app.route('/api/clear-cache')
def api_clear_cache():
    """Clear browser cache - just redirects to home"""
    return redirect('/?nocache=' + str(datetime.now().timestamp()))

@app.route('/upload-cv', methods=['GET', 'POST'])
def upload_cv():
    """Handle CV file upload"""
    if request.method == 'POST':
        # Check if this is an AJAX request
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Content-Type', '').startswith('application/json')
        
        # Check if file is present
        if 'cv_file' not in request.files:
            if is_ajax:
                return jsonify({'success': False, 'message': 'No file selected'}), 400
            flash('No file selected', 'error')
            return redirect('/')
        
        file = request.files['cv_file']
        
        # If no file selected
        if file.filename == '':
            if is_ajax:
                return jsonify({'success': False, 'message': 'No file selected'}), 400
            flash('No file selected', 'error')
            return redirect('/')
        
        # If file is allowed
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Read file content
            try:
                content = file.read()
                file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'txt'
                
                if file_ext == 'pdf':
                    # Save PDF as binary to cv.txt (keeps config.json simple)
                    # The parser will detect it's a PDF by checking the header
                    cv_file = 'cv.txt'
                    with open(cv_file, 'wb') as f:
                        f.write(content)
                    # Also update config.json to point to the uploaded CV
                    import json
                    try:
                        with open('config.json', 'r') as cfg:
                            config = json.load(cfg)
                        config['cv_path'] = cv_file
                        with open('config.json', 'w') as cfg:
                            json.dump(config, cfg, indent=2)
                    except:
                        pass
                    
                    message = 'PDF CV uploaded successfully! You can now click "Search Jobs" to start the trawler.'
                    if is_ajax:
                        return jsonify({'success': True, 'message': message})
                    flash(message, 'success')
                elif file_ext in ['docx', 'doc']:
                    # Save DOCX/DOC as binary - the parser will detect it's a DOCX by checking the header
                    # Use .docx extension to help parser identify it, but save as binary
                    cv_file = 'cv.docx' if file_ext == 'docx' else 'cv.doc'
                    with open(cv_file, 'wb') as f:
                        f.write(content)
                    # Also update config.json to point to the uploaded CV
                    import json
                    try:
                        with open('config.json', 'r') as cfg:
                            config = json.load(cfg)
                        config['cv_path'] = cv_file
                        with open('config.json', 'w') as cfg:
                            json.dump(config, cfg, indent=2)
                    except:
                        pass
                    
                    message = f'{file_ext.upper()} CV uploaded successfully! You can now click "Search Jobs" to start the trawler.'
                    if is_ajax:
                        return jsonify({'success': True, 'message': message})
                    flash(message, 'success')
                else:
                    # Try to decode as text (for .txt files)
                    try:
                        text_content = content.decode('utf-8')
                    except UnicodeDecodeError:
                        try:
                            text_content = content.decode('latin-1')
                        except:
                            error_msg = 'Error reading file. Please upload a text file (.txt)'
                            if is_ajax:
                                return jsonify({'success': False, 'message': error_msg}), 400
                            flash(error_msg, 'error')
                            return redirect('/')
                    
                    # Save to cv.txt
                    with open('cv.txt', 'w', encoding='utf-8') as f:
                        f.write(text_content)
                    
                    message = 'CV uploaded successfully! You can now click "Search Jobs" to start the trawler.'
                    if is_ajax:
                        return jsonify({'success': True, 'message': message})
                    flash(message, 'success')
            except Exception as e:
                error_msg = f'Error saving file: {str(e)}'
                if is_ajax:
                    return jsonify({'success': False, 'message': error_msg}), 500
                flash(error_msg, 'error')
        else:
            error_msg = 'Invalid file type. Please upload .txt, .pdf, .doc, or .docx files'
            if is_ajax:
                return jsonify({'success': False, 'message': error_msg}), 400
            flash(error_msg, 'error')
        
        # For non-AJAX requests, redirect
        if not is_ajax:
            return redirect('/')
        else:
            return jsonify({'success': True, 'message': 'CV uploaded successfully'})
    
    # GET request - show upload form (handled in template)
    return redirect('/')

@app.route('/view-cv')
def view_cv():
    """View current CV content"""
    # Check config.json for CV path
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        cv_file = config.get('cv_path', 'cv.txt')
    except:
        cv_file = 'cv.txt'
    
    # Check if file exists
    if not os.path.exists(cv_file):
        return '''
        <html>
        <head><title>View CV</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .error { color: #721c24; background: #f8d7da; padding: 15px; border-radius: 6px; border: 1px solid #f5c6cb; }
        </style>
        </head>
        <body>
        <div class="container">
            <h2>View CV</h2>
            <div class="error">No CV file found. Please upload one using the "Upload CV" button.</div>
        </div>
        </body>
        </html>
        '''
    
    # Check if it's a PDF
    try:
        with open(cv_file, 'rb') as f:
            header = f.read(4)
            is_pdf = header.startswith(b'%PDF')
            is_docx = header == b'PK\x03\x04'  # DOCX files start with ZIP header
    except:
        is_pdf = False
        is_docx = False
    
    if is_pdf:
        return '''
        <html>
        <head><title>View CV</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .info { color: #0c5460; background: #d1ecf1; padding: 15px; border-radius: 6px; border: 1px solid #bee5eb; }
        </style>
        </head>
        <body>
        <div class="container">
            <h2>View CV</h2>
            <div class="info">
                <strong>PDF File Detected</strong><br>
                Your CV has been uploaded as a PDF file. The content cannot be displayed in the browser, but it has been successfully saved and will be used for job matching.
            </div>
        </div>
        </body>
        </html>
        '''
    
    if is_docx or cv_file.endswith(('.docx', '.doc')):
        return '''
        <html>
        <head><title>View CV</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 8px; max-width: 800px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .info { color: #0c5460; background: #d1ecf1; padding: 15px; border-radius: 6px; border: 1px solid #bee5eb; }
        </style>
        </head>
        <body>
        <div class="container">
            <h2>View CV</h2>
            <div class="info">
                <strong>DOCX/DOC File Detected</strong><br>
                Your CV has been uploaded as a DOCX/DOC file. The content cannot be displayed in the browser, but it has been successfully saved and will be used for job matching.
            </div>
        </div>
        </body>
        </html>
        '''
    
    # Try to read as text
    try:
        with open(cv_file, 'r', encoding='utf-8') as f:
            cv_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(cv_file, 'r', encoding='latin-1') as f:
                cv_content = f.read()
        except:
            cv_content = "[Unable to read CV file - encoding issue]"
    except Exception as e:
        cv_content = f"[Error reading CV file: {str(e)}]"
    
    return f'''
    <html>
    <head><title>View CV</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
        .container {{ background: white; padding: 30px; border-radius: 8px; max-width: 900px; margin: 0 auto; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        pre {{ white-space: pre-wrap; font-family: 'Courier New', monospace; font-size: 14px; line-height: 1.6; background: #f8f9fa; padding: 20px; border-radius: 6px; border: 1px solid #dee2e6; overflow-x: auto; }}
        h2 {{ color: #333; margin-bottom: 20px; }}
    </style>
    </head>
    <body>
    <div class="container">
        <h2>Your CV</h2>
        <pre>{cv_content}</pre>
    </div>
    </body>
    </html>
    '''

# Global variable to track running trawler (thread-safe)
trawler_running = False
trawler_thread = None
trawler_lock = threading.Lock()  # Thread lock for thread-safe operations

def start_trawler(keywords=None, location=None, use_config_keywords=True):
    """Helper function to start the trawler in background (thread-safe)
    
    Args:
        keywords: Optional custom keywords. If None and use_config_keywords is True,
                 will use keywords from config.json
        location: Optional custom location. If None, will use location from config.json
        use_config_keywords: If True and keywords is None, load keywords from config
    
    Returns:
        tuple: (success: bool, message: str, error: str or None)
    """
    global trawler_running, trawler_thread
    
    # Thread-safe check and set
    with trawler_lock:
        if trawler_running:
            return (False, 'Trawler is already running', None)
    
    try:
        # Get keywords and location from config if not provided
        if (keywords is None or location is None) and use_config_keywords:
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
                if keywords is None:
                    keywords = config.get('search', {}).get('keywords', '')
                if location is None:
                    location = config.get('search', {}).get('location', '')
                if not keywords:
                    return (False, 'No keywords found in config.json', None)
            except Exception as e:
                return (False, f'Error loading config: {str(e)}', None)
        
        if not keywords:
            return (False, 'No keywords provided', None)
        
        # Import trawler here to avoid circular imports
        from job_trawler import JobTrawler
        
        # Create progress file path
        progress_file = 'trawler_progress.json'
        
        # Clear any old progress
        if os.path.exists(progress_file):
            os.remove(progress_file)
        
        # Create initial progress file immediately so API can see it
        try:
            initial_progress = {
                'stage': 'starting',
                'progress': 0,
                'total': 100,
                'percentage': 0,
                'message': 'Starting trawler...',
                'jobs_found': 0,
                'jobs_matched': 0,
                'timestamp': datetime.now().isoformat(),
                'running': True
            }
            with open(progress_file, 'w', encoding='utf-8') as f:
                json.dump(initial_progress, f)
        except Exception as e:
            print(f"Warning: Could not create initial progress file: {e}")
        
        def run_trawler():
            global trawler_running
            try:
                with trawler_lock:
                    trawler_running = True
                
                # Save search start time to track this search session
                search_start_time = datetime.now().isoformat()
                search_session_file = 'last_search_start.json'
                try:
                    with open(search_session_file, 'w', encoding='utf-8') as f:
                        json.dump({'start_time': search_start_time}, f)
                except Exception as e:
                    print(f"Warning: Could not save search start time: {e}", flush=True)
                
                # Clear old jobs before new search (optional - comment out if you want to keep history)
                # Uncomment the next 3 lines if you want to clear old jobs when new search starts
                # jobs_file = 'job_alerts.json'
                # if os.path.exists(jobs_file):
                #     os.remove(jobs_file)
                
                trawler = JobTrawler()
                # Temporarily update config with custom location if provided
                if location:
                    original_location = trawler.config.get('search', {}).get('location', '')
                    trawler.config.setdefault('search', {})['location'] = location
                trawler.process_jobs_with_keywords(keywords, progress_file)
                # Restore original location if we modified it
                if location:
                    if original_location:
                        trawler.config['search']['location'] = original_location
                    elif 'location' in trawler.config.get('search', {}):
                        del trawler.config['search']['location']
            except Exception as e:
                print(f"Error in trawler thread: {e}")
                import traceback
                traceback.print_exc()
            finally:
                with trawler_lock:
                    trawler_running = False
        
        # Start trawler in background thread
        trawler_thread = threading.Thread(target=run_trawler, daemon=True)
        trawler_thread.start()
        
        return (True, 'Trawler started successfully', None)
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error starting trawler: {error_msg}")
        print(traceback.format_exc())
        return (False, f'Error starting trawler: {error_msg}', error_msg)

@app.route('/search-positions', methods=['POST'])
def search_positions():
    """Run trawler with custom position keywords, location, and optional LinkedIn profile"""
    try:
        data = request.get_json()
        keywords = data.get('keywords', '').strip()
        location = data.get('location', '').strip()
        linkedin_url = data.get('linkedin_url', '').strip()
        use_config_keywords = data.get('use_config_keywords', False)  # Allow using config keywords
        
        # Either keywords OR LinkedIn URL must be provided, OR use_config_keywords flag
        if not keywords and not linkedin_url and not use_config_keywords:
            return jsonify({
                'success': False,
                'error': 'Please provide either keywords, a LinkedIn profile URL, or set use_config_keywords to true'
            }), 400
        
        # If LinkedIn URL provided, parse it and extract skills/keywords
        if linkedin_url:
            try:
                from linkedin_parser import LinkedInParser
                linkedin_parser = LinkedInParser(linkedin_url)
                if linkedin_parser.parse():
                    linkedin_skills = linkedin_parser.get_skills()
                    linkedin_keywords = linkedin_parser.get_keywords()
                    
                    # If no keywords provided, use LinkedIn skills/keywords
                    if not keywords:
                        if linkedin_skills:
                            keywords = ' OR '.join(list(linkedin_skills)[:15])  # Top 15 skills
                        elif linkedin_keywords:
                            keywords = ' OR '.join(list(linkedin_keywords)[:10])  # Top 10 keywords
                        else:
                            return jsonify({
                                'success': False,
                                'error': 'Could not extract skills/keywords from LinkedIn profile. Please provide keywords instead.'
                            }), 400
                    else:
                        # Merge LinkedIn skills/keywords with provided keywords
                        if linkedin_skills:
                            skills_str = ' OR '.join(list(linkedin_skills)[:10])  # Top 10 skills
                            keywords = f"({keywords}) AND ({skills_str})"
                        elif linkedin_keywords:
                            keywords_str = ' OR '.join(list(linkedin_keywords)[:5])  # Top 5 keywords
                            keywords = f"({keywords}) AND ({keywords_str})"
                    
                    print(f"LinkedIn profile parsed. Skills: {len(linkedin_skills)}, Keywords: {len(linkedin_keywords)}", flush=True)
                else:
                    if not keywords:
                        return jsonify({
                            'success': False,
                            'error': 'Could not parse LinkedIn profile. Please provide keywords instead.'
                        }), 400
                    print("Warning: Could not parse LinkedIn profile, using keywords only", flush=True)
            except Exception as e:
                print(f"Error parsing LinkedIn profile: {e}", flush=True)
                if not keywords:
                    return jsonify({
                        'success': False,
                        'error': f'Error parsing LinkedIn profile: {str(e)}. Please provide keywords instead.'
                    }), 400
                # Continue with original keywords if LinkedIn parsing fails
        
        # If use_config_keywords is True and no keywords provided, use config keywords
        if use_config_keywords and not keywords and not linkedin_url:
            success, message, error = start_trawler(keywords=None, location=location if location else None, use_config_keywords=True)
        else:
            success, message, error = start_trawler(keywords=keywords, location=location if location else None, use_config_keywords=False)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'progress_file': 'trawler_progress.json'
            })
        else:
            return jsonify({
                'success': False,
                'error': message
            }), 400 if 'already running' in message.lower() else 500
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"Error starting trawler: {error_msg}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': error_msg
        }), 500

@app.route('/api/progress')
def api_progress():
    """Get trawler progress"""
    progress_file = 'trawler_progress.json'
    
    # Thread-safe check if trawler is running
    with trawler_lock:
        is_running = trawler_running
    
    if not os.path.exists(progress_file):
        # If trawler is running but no file yet, return initial state
        if is_running:
            return jsonify({
                'running': True,
                'progress': 0,
                'total': 100,
                'percentage': 0,
                'message': 'Starting trawler...',
                'jobs_found': 0,
                'jobs_matched': 0,
                'stage': 'starting'
            })
        else:
            return jsonify({
                'running': False,
                'progress': 0,
                'message': 'No progress file found'
            })
    
    try:
        with open(progress_file, 'r', encoding='utf-8') as f:
            progress_data = json.load(f)
        
        # Thread-safe read of trawler_running
        progress_data['running'] = is_running or progress_data.get('stage') != 'complete'
        return jsonify(progress_data)
    except Exception as e:
        return jsonify({
            'running': False,
            'progress': 0,
            'error': str(e)
        })

@app.route('/api/test-board', methods=['POST'])
def api_test_board():
    """Test a single job board and return result"""
    try:
        board_method = request.json.get('board')
        keywords = request.json.get('keywords', 'Python Developer')
        location = request.json.get('location', 'London, UK')
        
        if not board_method:
            return jsonify({
                'success': False,
                'error': 'Board method not specified'
            }), 400
        
        trawler = JobTrawler()
        
        # Map method names to actual methods
        method_map = {
            'search_linkedin': trawler.search_linkedin,
            'search_indeed': trawler.search_indeed,
            'search_reed': trawler.search_reed,
            'search_monster': trawler.search_monster,
            'search_glassdoor': trawler.search_glassdoor,
            'search_totaljobs': trawler.search_totaljobs,
            'search_adzuna': trawler.search_adzuna,
            'search_jobserve': trawler.search_jobserve,
            'search_whatjobs': trawler.search_whatjobs,
            'search_stepstone': trawler.search_stepstone,
            'search_jobrapido': trawler.search_jobrapido,
            'search_jooble': trawler.search_jooble,
            'search_infojobs': trawler.search_infojobs,
            'search_eures': trawler.search_eures,
            'search_careerjet': trawler.search_careerjet,
        }
        
        if board_method not in method_map:
            return jsonify({
                'success': False,
                'error': f'Unknown board method: {board_method}'
            }), 400
        
        search_method = method_map[board_method]
        
        try:
            start_time = time.time()
            jobs = search_method(keywords, location, max_results=5)
            elapsed = time.time() - start_time
            
            return jsonify({
                'success': True,
                'jobs_found': len(jobs),
                'time': round(elapsed, 2),
                'sample_job': jobs[0] if jobs else None
            })
        except Exception as e:
            error_msg = str(e)
            return jsonify({
                'success': False,
                'error': error_msg[:200],
                'jobs_found': 0,
                'time': 0
            })
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-boards', methods=['POST'])
def api_test_boards():
    """Test all job boards and return results (legacy endpoint)"""
    try:
        keywords = request.json.get('keywords', 'Python Developer')
        location = request.json.get('location', 'London, UK')
        
        trawler = JobTrawler()
        results = {}
        
        # Test each board
        test_boards = [
            ('LinkedIn', trawler.search_linkedin),
            ('Indeed', trawler.search_indeed),
            ('Reed', trawler.search_reed),
            ('Monster', trawler.search_monster),
            ('Glassdoor', trawler.search_glassdoor),
            ('TotalJobs', trawler.search_totaljobs),
            ('Adzuna', trawler.search_adzuna),
            ('JobServe', trawler.search_jobserve),
            ('WhatJobs', trawler.search_whatjobs),
        ]
        
        for board_name, search_method in test_boards:
            try:
                start_time = time.time()
                jobs = search_method(keywords, location, max_results=5)
                elapsed = time.time() - start_time
                
                results[board_name] = {
                    'success': True,
                    'jobs_found': len(jobs),
                    'time': round(elapsed, 2),
                    'sample_job': jobs[0] if jobs else None
                }
            except Exception as e:
                error_msg = str(e)
                results[board_name] = {
                    'success': False,
                    'error': error_msg[:200],
                    'jobs_found': 0,
                    'time': 0
                }
            
            time.sleep(0.5)  # Small delay between tests
        
        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'working': [name for name, r in results.items() if r['success'] and r['jobs_found'] > 0],
                'no_jobs': [name for name, r in results.items() if r['success'] and r['jobs_found'] == 0],
                'failed': [name for name, r in results.items() if not r['success']]
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("\n" + "="*60)
    print("Job Trawler Web Interface")
    print("="*60)
    print("Starting web server...")
    print("Open your browser and go to: http://localhost:5000")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)



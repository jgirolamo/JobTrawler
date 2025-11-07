# PythonAnywhere Deployment Guide

## Step-by-Step Instructions

### Step 1: Prepare Your Files

Make sure you have these files ready:
- `web_app.py`
- `job_trawler.py` ⭐ (Updated with API support)
- `job_board_apis.py` ⭐ (NEW - API integrations)
- `cv_parser.py`
- `job_matcher.py`
- `alert_system.py`
- `linkedin_parser.py`
- `config.json` ⭐ (Updated with API configuration section)
- `requirements.txt`
- `templates/jobs.html`
- `cv.txt` (optional - can upload via web interface)

### Step 2: Upload Files to PythonAnywhere

1. **Log into PythonAnywhere**
2. **Go to "Files" tab** (top menu)
3. **Navigate to `/home/yourusername/`** (your home directory)
4. **Create a folder** called `JobTrawler` (or any name you prefer)
5. **Upload all files**:
   - Click "Upload a file"
   - Upload each `.py` file one by one
   - Upload `config.json`
   - Upload `requirements.txt`

6. **Create templates folder**:
   - Click "New directory"
   - Name it `templates`
   - Upload `jobs.html` into the `templates` folder

### Step 3: Install Dependencies

1. **Go to "Consoles" tab**
2. **Click "Bash"** (opens a new console)
3. **Navigate to your folder**:
   ```bash
   cd JobTrawler
   ```
4. **Install Python packages**:
   ```bash
   pip3.10 install --user -r requirements.txt
   ```
   (Or use `pip3.11` if you're using Python 3.11)

### Step 4: Configure Web App

1. **Go to "Web" tab** (top menu)
2. **Click "Add a new web app"** (if you don't have one yet)
   - OR click on existing web app if you have one
3. **Choose Flask**
4. **Select Python version** (3.10 or 3.11)
5. **Enter path to your Flask app**: `/home/yourusername/JobTrawler/web_app.py`
6. **Click "Next"**

### Step 5: Edit WSGI File

1. **Click on the WSGI configuration file link** (it will show something like `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
2. **Delete everything** in the file
3. **Replace with this code**:
   ```python
   import sys
   
   # Add your project directory to the path
   project_home = '/home/yourusername/JobTrawler'
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   
   # Import the Flask app
   from web_app import app as application
   
   # Optional: Set secret key from environment variable
   import os
   if 'SECRET_KEY' in os.environ:
       application.secret_key = os.environ['SECRET_KEY']
   ```
4. **Replace `yourusername`** with your actual PythonAnywhere username
5. **Save the file**

### Step 6: Set Working Directory (Important!)

1. **Still in "Web" tab**, scroll down to **"Static files"** section
2. **Add static file mapping** (optional, but helps with file paths):
   - URL: `/static/`
   - Directory: `/home/yourusername/JobTrawler/static/`
3. **Scroll to "Code" section**
4. **Set Working directory** to: `/home/yourusername/JobTrawler`

### Step 7: Set Environment Variables (Optional - Can Skip)

**Note:** Environment variables might not be visible in the free tier, or may be in a different location. This step is **optional** - the app will work without it.

**If you see the section:**
1. **In "Web" tab**, scroll down to find **"Environment variables"** section
2. **Add new variable**:
   - Key: `SECRET_KEY`
   - Value: `your-random-secret-key-here` (generate a random string)

**If you don't see it:**
- That's fine! The app has a default secret key
- You can skip this step
- The app will work perfectly without it
- (Environment variables are mainly for production security)

### Step 8: Reload Web App

1. **Click the green "Reload" button** (top of Web tab)
2. **Wait a few seconds**
3. **Your app should be live at**: `yourusername.pythonanywhere.com`

### Step 9: Test Your App

1. **Open your app URL** in a new tab
2. **You should see the Job Trawler interface**
3. **Test uploading a CV**
4. **Test searching for jobs**

### Step 10: Add to WordPress

1. **Copy your PythonAnywhere URL**: `https://yourusername.pythonanywhere.com`
2. **Log into WordPress**
3. **Create or edit a page**
4. **Add HTML block**:
   ```html
   <iframe src="https://yourusername.pythonanywhere.com" 
           style="width:100%; height:800px; border:none; min-height:600px;">
   </iframe>
   ```
5. **Publish the page**

## Troubleshooting

### App shows error 500
- Check the **Error log** in PythonAnywhere Web tab
- Make sure all files are uploaded correctly
- Check that `templates/jobs.html` is in the `templates` folder
- Verify the WSGI file path is correct

### Import errors
- Make sure you installed all requirements: `pip3.10 install --user -r requirements.txt`
- Check that all `.py` files are in the same directory

### Can't find templates
- Make sure `jobs.html` is in `/home/yourusername/JobTrawler/templates/`
- Check the folder name is exactly `templates` (lowercase)

### File upload doesn't work
- Check that `config.json` exists
- Make sure the web app has write permissions (usually automatic)
- The app will create `job_alerts.json` and `seen_jobs.json` automatically

### Trawler doesn't run
- Check the Error log in PythonAnywhere
- Some job boards may require Selenium (harder to set up on free tier)
- Try disabling some job boards in `config.json` if needed

## Free Tier Limitations

- **Web app sleeps** after inactivity (wakes up on first request)
- **No scheduled tasks** (can't run cron jobs on free tier)
- **Limited CPU time** (but usually enough for this app)
- **File size limits** (16MB max for uploads - already configured)

## Upgrading (Optional)

If you need:
- **Always-on web app** (no sleeping): Hacker plan ($5/month)
- **Scheduled tasks**: Hacker plan ($5/month)
- **Custom domain**: Hacker plan ($5/month)

## Quick Commands Reference

```bash
# Install dependencies
pip3.10 install --user -r requirements.txt

# Check Python version
python3.10 --version

# Test Flask app locally (in console)
cd /home/yourusername/JobTrawler
python3.10 web_app.py
```

## Next Steps

1. ✅ Deploy to PythonAnywhere
2. ✅ Test the app
3. ✅ Add iframe to WordPress
4. ✅ Share with users!

---

**Need help?** Check the Error log in PythonAnywhere Web tab - it shows detailed error messages!


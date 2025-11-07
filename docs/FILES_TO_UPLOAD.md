# Files to Upload for Deployment

## ✅ REQUIRED FILES (Must Upload)

### Core Python Files:
1. **web_app.py** - Main Flask application
2. **job_trawler.py** - Job board scraping logic (RECENTLY UPDATED - now includes API support)
3. **job_board_apis.py** - Job board API integrations (NEW - optional but recommended)
4. **cv_parser.py** - CV parsing functionality
5. **job_matcher.py** - Job matching algorithm
6. **alert_system.py** - Alert/notification system
7. **linkedin_parser.py** - LinkedIn profile parsing

### Configuration:
7. **config.json** - Application configuration (job boards, matching settings)

### Dependencies:
8. **requirements.txt** - Python package dependencies

### Templates:
9. **templates/jobs.html** - Web interface template
   - Upload this file into a `templates/` folder on the server

---

## ⚠️ OPTIONAL FILES (Not Required for Deployment)

### These are created at runtime or can be uploaded via web interface:
- **cv.txt** - CV content (can be uploaded via web interface)
- **trawler_progress.json** - Created automatically during trawler runs
- **test_job_boards.py** - Testing script (not needed for deployment)
- **Procfile** - Only needed for Heroku/Render
- **runtime.txt** - Only needed for Heroku/Render
- **PYTHONANYWHERE_DEPLOY.md** - Documentation (not needed on server)
- **README.md** - Documentation (not needed on server)

---

## 📁 Folder Structure on Server

After uploading, your server should have this structure:
```
/home/yourusername/JobTrawler/
├── web_app.py
├── job_trawler.py
├── job_board_apis.py  ⭐ NEW - API integrations
├── cv_parser.py
├── job_matcher.py
├── alert_system.py
├── linkedin_parser.py
├── config.json  ⭐ UPDATED - now includes API config section
├── requirements.txt
└── templates/
    └── jobs.html
```

---

## 📝 Quick Upload Checklist

- [ ] web_app.py
- [ ] job_trawler.py ⭐ **RECENTLY UPDATED** - includes API support
- [ ] job_board_apis.py ⭐ **NEW** - API integrations (optional but recommended)
- [ ] cv_parser.py
- [ ] job_matcher.py
- [ ] alert_system.py
- [ ] linkedin_parser.py
- [ ] config.json ⭐ **UPDATED** - now includes API configuration section
- [ ] requirements.txt
- [ ] templates/jobs.html (inside templates folder)

---

## 💡 Tips

1. **Upload `job_trawler.py` and `job_board_apis.py`** - These are the updated files with API support
2. **Upload `config.json`** - Make sure to upload the updated version with the API section (even if APIs are disabled)
3. **Create `templates` folder first**, then upload `jobs.html` into it
4. **Don't upload** `cv.txt` initially - you can upload your CV via the web interface after deployment
5. **Don't upload** `trawler_progress.json` - it will be created automatically
6. **Don't upload** setup scripts (`setup_api.py`, `quick_setup_adzuna.py`) - these are local tools only
7. After uploading, run: `pip3.10 install --user -r requirements.txt` (or `pip3.11` if using Python 3.11)

## ⚠️ Important Notes

- **`job_board_apis.py` is optional** - The system works without it (uses scraping only)
- **If you don't upload `job_board_apis.py`**, the system will work but APIs won't be available
- **The updated `config.json` includes API configuration** - Even if you don't use APIs, upload the updated config file
- **APIs are disabled by default** - Your existing setup will continue working exactly as before


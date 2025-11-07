# Project Structure

## Root Directory (Core Files)

### Python Application Files
- `web_app.py` - Main Flask web application
- `job_trawler.py` - Job board scraping and matching logic
- `job_board_apis.py` - API integrations for job boards
- `cv_parser.py` - CV/resume parsing
- `job_matcher.py` - Job matching algorithm
- `alert_system.py` - Alert/notification system
- `linkedin_parser.py` - LinkedIn profile parsing

### Configuration
- `config.json` - Application configuration
- `requirements.txt` - Python dependencies

### Deployment
- `Procfile` - For Heroku/Render deployment
- `runtime.txt` - Python version for deployment

### Templates
- `templates/jobs.html` - Web interface template

## Documentation (`docs/` folder)

- `README.md` - Main project documentation (in root)
- `API_SETUP.md` - API configuration guide
- `CUSTOM_DOMAIN_SETUP.md` - Custom domain setup guide
- `DEPLOYMENT_NOTES.md` - Deployment notes
- `FILES_TO_UPLOAD.md` - Files needed for deployment
- `IFRAME_FIX.md` - Iframe embedding fix
- `IFRAME_TROUBLESHOOTING.md` - Iframe troubleshooting
- `PYTHONANYWHERE_DEPLOY.md` - PythonAnywhere deployment guide
- `WORDPRESS_INTEGRATION.md` - WordPress integration guide
- `WORDPRESS_SUBPAGE_SETUP.md` - WordPress subpage setup

## Scripts (`scripts/` folder)

- `setup_api.py` - Interactive API setup wizard
- `quick_setup_adzuna.py` - Quick Adzuna API setup
- `test_job_boards.py` - Test job board connectivity

## WordPress Plugin (`wordpress-plugin/` folder)

- `jobtrawler-embed.php` - WordPress plugin for embedding
- `README.md` - Plugin documentation

## Files Not in Git (Generated/Runtime)

- `trawler_progress.json` - Runtime progress tracking
- `job_alerts.json` - Generated job alerts
- `seen_jobs.json` - Generated seen jobs cache
- `cv.txt` - Personal CV file (not in repo)
- `__pycache__/` - Python cache files

## Quick Reference

**For deployment:** See `docs/FILES_TO_UPLOAD.md`

**For API setup:** See `docs/API_SETUP.md`

**For WordPress:** See `docs/WORDPRESS_SUBPAGE_SETUP.md`

**For custom domain:** See `docs/CUSTOM_DOMAIN_SETUP.md`


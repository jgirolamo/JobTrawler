# Job Trawler

A Python-based job monitoring system that automatically searches job boards, matches postings with your CV, and alerts you when relevant opportunities are found.

## Features

- 🔍 **Multi-board Search**: Searches multiple UK and Europe job boards (Indeed, LinkedIn, Reed, Monster, Glassdoor, TotalJobs, Adzuna, JobServe, WhatJobs)
- 🎯 **Smart Matching**: Uses CV parsing and skill matching to find relevant jobs
- 📊 **Match Scoring**: Calculates relevance scores based on skills, keywords, and experience
- 📧 **Multiple Alerts**: Console output, email notifications, and JSON file logging
- 🌐 **Web Interface**: Beautiful web UI with progress tracking and real-time updates
- ⚙️ **Configurable**: Easy-to-customize search criteria and alert settings
- 🔄 **Custom Search**: Search for specific positions via web interface

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure

Edit `config.json`:
- Set your CV path
- Configure search keywords and location
- Enable/disable job boards
- Set matching thresholds

### 3. Add Your CV

- Place your CV PDF in the folder, OR
- Update `cv.txt` with your CV content
- Update `cv_path` in `config.json` to point to your CV

### 4. Run

**Web Interface (Recommended):**
```bash
python web_app.py
```
Then open http://localhost:5000 in your browser

**Command Line:**
```bash
python job_trawler.py
```

## File Structure

```
JobTrawler/
├── job_trawler.py      # Main trawler script
├── cv_parser.py        # CV/resume parser
├── job_matcher.py      # Job matching algorithm
├── alert_system.py     # Alert/notification system
├── web_app.py          # Web interface
├── config.json         # Configuration file
├── cv.txt              # Your CV/resume (text format)
├── CV JOAO GUSTAVO 2025.pdf  # Your CV (PDF format)
├── requirements.txt    # Python dependencies
├── templates/
│   └── jobs.html      # Web interface template
├── job_alerts.json    # Matched jobs (auto-generated)
├── seen_jobs.json     # Tracked jobs (auto-generated)
└── trawler_progress.json  # Progress tracking (auto-generated)
```

## Supported Job Boards

### General Job Boards
- ✅ Indeed (UK & US)
- ✅ LinkedIn
- ✅ Reed.co.uk
- ✅ Monster
- ✅ Glassdoor
- ✅ TotalJobs
- ✅ Adzuna
- ✅ JobServe
- ✅ WhatJobs
- ✅ StepStone
- ✅ JobRapido
- ✅ Jooble
- ✅ EURES
- ✅ CareerJet
- ❌ CV-Library (blocked, requires API)

### Charity & Nonprofit Job Boards
- ✅ CharityJob (UK charity and nonprofit jobs)
- ✅ Idealist (International nonprofit and social impact jobs)
- ✅ GlobalCharityJobs (International charity jobs)
- ✅ ThirdSector (UK charity, nonprofit, and voluntary sector jobs)
- ✅ GuardianJobs (Includes charity and nonprofit section)

### Environmental & Sustainability Jobs
- ✅ EnvironmentJobs (Environmental and sustainability jobs)

### Museums, Galleries & Arts Jobs
- ✅ Museums Association (UK museum and gallery jobs)
- ✅ ArtsJobs (UK arts, culture, heritage, and creative sector jobs)
- ✅ ArtsProfessional (UK arts and culture sector jobs)

## Web Interface Features

- **Real-time Progress Bar**: See trawler progress with job counts
- **Custom Search**: Search for specific positions
- **CV Upload**: Upload and update your CV
- **Job Display**: View matched jobs with match scores
- **Auto-refresh**: Automatically updates with new jobs

## Configuration

Edit `config.json` to customize:

- **Search Keywords**: Job titles/roles to search for
- **Location**: Job location preferences
- **Job Boards**: Enable/disable specific boards
- **Matching**: Minimum match score threshold
- **Alerts**: Email and notification settings

## How It Works

1. **CV Parsing**: Extracts skills, experience, and keywords from your CV
2. **Job Crawling**: Searches configured job boards using your keywords
3. **Job Matching**: Compares each job posting with your CV skills
4. **Scoring**: Calculates match score based on:
   - Skill matches (60% weight)
   - Keyword matches (30% weight)
   - Experience level (10% weight)
5. **Filtering**: Only jobs above the minimum score threshold
6. **Alerting**: Sends notifications for relevant jobs

## Notes

- The trawler respects rate limits and includes timeouts to prevent hanging
- Some job boards may require JavaScript rendering (Selenium)
- Progress is tracked in real-time for web interface
- Jobs are deduplicated automatically

## Deployment

### PythonAnywhere (Free Hosting)

See `PYTHONANYWHERE_DEPLOY.md` for detailed step-by-step instructions.

Quick steps:
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Upload all files via Files tab
3. Install dependencies: `pip3.10 install --user -r requirements.txt`
4. Configure WSGI file (see `PYTHONANYWHERE_DEPLOY.md`)
5. Reload web app

### WordPress Integration

Since WordPress runs on PHP and this app runs on Python, you need to:

1. **Deploy Flask app separately** (use PythonAnywhere or similar)
2. **Embed via iframe** in WordPress:
   ```html
   <iframe src="https://your-app.pythonanywhere.com" 
           width="100%" height="800px" frameborder="0"></iframe>
   ```
3. Or use WordPress plugins like "Advanced iFrame" for better integration

## Troubleshooting

**No jobs found?**
- Lower `min_score` in config.json
- Check that job boards are enabled
- Verify your CV has relevant skills
- Use the "Test Job Boards" button (bottom-left on web interface) to verify which boards are working

**Trawler stuck?**
- Check `trawler_progress.json` for current status
- Some jobs may timeout - this is normal
- Restart the trawler if needed

**Web interface not working?**
- Make sure port 5000 is available
- Check that Flask is installed
- View console output for errors

**Job boards not working?**
- Some boards may block requests (403 errors) - this is normal
- Test boards individually using the hidden test button (🧪 in bottom-left)
- Boards that work: LinkedIn, TotalJobs, Adzuna, JobServe

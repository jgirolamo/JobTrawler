# Deployment Notes - API Integration Update

## What's New

This update adds **optional API support** for job boards. The system is fully backward compatible - if you don't configure APIs, everything works exactly as before.

## Files to Upload

### Required Files (Must Upload):
1. ✅ `job_trawler.py` - **UPDATED** with API support
2. ✅ `job_board_apis.py` - **NEW** API integration module
3. ✅ `config.json` - **UPDATED** with API configuration section
4. ✅ All other existing files (web_app.py, cv_parser.py, etc.)

### Optional Files (Don't Need to Upload):
- ❌ `setup_api.py` - Local setup tool only
- ❌ `quick_setup_adzuna.py` - Local setup tool only
- ❌ `API_SETUP.md` - Documentation only
- ❌ `test_infojobs.py` - Testing script

## Quick Deployment Steps

1. **Upload the new/updated files:**
   - `job_trawler.py` (updated)
   - `job_board_apis.py` (new)
   - `config.json` (updated)

2. **No code changes needed** - The system automatically detects if APIs are available

3. **Test your deployment:**
   - Everything should work as before
   - APIs are disabled by default, so scraping continues to work

## What Happens After Deployment

- ✅ **If APIs are not configured:** System uses scraping (current behavior)
- ✅ **If APIs are configured:** System tries API first, falls back to scraping
- ✅ **No breaking changes** - Everything is backward compatible

## API Configuration (Optional)

If you want to enable APIs later:

1. Edit `config.json` on the server
2. Add your API credentials (see `API_SETUP.md`)
3. Set `"enabled": true` for the APIs you want to use
4. Restart the web app

## Verification

After deployment, check:
- [ ] Web app loads without errors
- [ ] Job trawler runs successfully
- [ ] Jobs are found (via scraping)
- [ ] No import errors in logs

If you see any warnings about API client, that's normal - it just means APIs aren't configured yet.


# Job Board API Setup Guide

This guide explains how to set up APIs for job boards to make your Job Trawler more reliable and faster.

## Why Use APIs?

- ✅ **More reliable** - No breaking when websites change their HTML
- ✅ **Faster** - Direct data access, no parsing needed
- ✅ **Structured data** - Better job information (salary, location, etc.)
- ✅ **Rate limits** - Clear limits, no blocking issues
- ✅ **Legal compliance** - Official APIs are allowed

## Available APIs

### 1. Adzuna API (Recommended - Free!)

**Coverage:** UK, Europe, US, Canada, Australia  
**Free tier:** 1,000 requests/month  
**Speed:** Fast and reliable

#### Setup Steps:

1. Go to https://developer.adzuna.com/
2. Click "Get Started" or "Sign Up"
3. Create a free account
4. Once logged in, you'll get:
   - `app_id` (Application ID)
   - `app_key` (Application Key)
5. Update `config.json`:
   ```json
   "apis": {
     "adzuna": {
       "enabled": true,
       "app_id": "YOUR_APP_ID_HERE",
       "app_key": "YOUR_APP_KEY_HERE",
       "use_api_instead_of_scraping": true
     }
   }
   ```

### 2. Infojobs API

**Coverage:** Spain (Spanish job board)  
**Free tier:** Available  
**Requires:** OAuth 2.0 setup

#### Setup Steps:

1. Go to https://developer.infojobs.net/
2. Register your application
3. Get your `client_id` and `client_secret`
4. Update `config.json`:
   ```json
   "apis": {
     "infojobs": {
       "enabled": true,
       "client_id": "YOUR_CLIENT_ID",
       "client_secret": "YOUR_CLIENT_SECRET",
       "use_api_instead_of_scraping": true
     }
   }
   ```

### 3. APIJobs (Aggregator - Paid)

**Coverage:** 4000+ job boards including LinkedIn, Indeed, Glassdoor  
**Pricing:** See https://apijobs.dev/pricing  
**Best for:** Replacing multiple job boards at once

#### Setup Steps:

1. Go to https://apijobs.dev/
2. Sign up and get your API key
3. Update `config.json`:
   ```json
   "apis": {
     "apijobs": {
       "enabled": true,
       "api_key": "YOUR_API_KEY_HERE"
     }
   }
   ```

**Note:** When APIJobs is enabled, it can replace searching individual boards since it aggregates from many sources.

### 4. JSearch API (Google for Jobs)

**Coverage:** Google for Jobs aggregator  
**Pricing:** See https://openwebninja.com/api/jsearch  
**Best for:** Comprehensive job search

#### Setup Steps:

1. Go to https://openwebninja.com/api/jsearch
2. Sign up and get your API key
3. Update `config.json`:
   ```json
   "apis": {
     "jsearch": {
       "enabled": true,
       "api_key": "YOUR_API_KEY_HERE"
     }
   }
   ```

## Configuration Example

Here's a complete `config.json` example with APIs configured:

```json
{
  "apis": {
    "adzuna": {
      "enabled": true,
      "app_id": "your_app_id_here",
      "app_key": "your_app_key_here",
      "use_api_instead_of_scraping": true
    },
    "infojobs": {
      "enabled": false,
      "client_id": "",
      "client_secret": "",
      "use_api_instead_of_scraping": false
    },
    "apijobs": {
      "enabled": false,
      "api_key": ""
    },
    "jsearch": {
      "enabled": false,
      "api_key": ""
    }
  }
}
```

## How It Works

1. **API First, Scraping Fallback:**
   - If an API is enabled and configured, it tries the API first
   - If the API fails or returns no results, it falls back to scraping
   - This ensures you always get results

2. **Aggregator APIs:**
   - APIJobs and JSearch can replace multiple individual board searches
   - They aggregate from many sources, so you get more comprehensive results
   - Enable them alongside or instead of individual boards

## Benefits by Board

| Board | API Available | Free Tier | Recommendation |
|-------|--------------|-----------|----------------|
| Adzuna | ✅ Yes | ✅ 1,000/month | **Highly Recommended** |
| Infojobs | ✅ Yes | ✅ Yes | Recommended for Spain |
| APIJobs | ✅ Yes | ❌ Paid | Good for aggregating multiple boards |
| JSearch | ✅ Yes | ❌ Paid | Good for comprehensive search |
| Indeed | ❌ No | N/A | Use scraping |
| LinkedIn | ❌ Limited | N/A | Use scraping |
| Reed | ❌ No | N/A | Use scraping |
| Monster | ❌ No | N/A | Use scraping |
| Glassdoor | ❌ No | N/A | Use scraping |
| TotalJobs | ❌ No | N/A | Use scraping |

## Testing APIs

After configuring APIs, test them:

1. **Via Web Interface:**
   - Go to the bottom-left corner
   - Click the test button (🧪)
   - Select a board to test

2. **Via Command Line:**
   ```bash
   python test_job_boards.py
   ```

## Troubleshooting

**API not working?**
- Check your API keys are correct
- Verify the API is enabled in config.json
- Check API rate limits (especially Adzuna's 1,000/month limit)
- Check API service status

**Falling back to scraping?**
- This is normal! The system automatically falls back if API fails
- Check console output for API error messages
- Verify your API credentials are valid

**API rate limits?**
- Adzuna: 1,000 requests/month (free tier)
- Consider upgrading to paid tiers if needed
- The system will fall back to scraping when limits are reached

## Security Notes

- **Never commit API keys to Git!**
- Add `config.json` to `.gitignore` if it contains API keys
- Consider using environment variables for production
- Rotate API keys if they're exposed

## Next Steps

1. Start with **Adzuna API** (free and easy)
2. Test it works
3. Consider aggregator APIs if you need broader coverage
4. Keep scraping as fallback for boards without APIs


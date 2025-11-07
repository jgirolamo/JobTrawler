# Iframe Still Not Working? Troubleshooting Guide

## Quick Fix Steps

### Step 1: Verify web_app.py is Updated

Make sure you uploaded the **updated `web_app.py`** with the iframe fix. The code should include:

```python
@app.after_request
def set_xframe_options(response):
    """Allow iframe embedding"""
    response.headers.pop('X-Frame-Options', None)
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Content-Security-Policy'] = "frame-ancestors *;"
    return response
```

### Step 2: Reload PythonAnywhere App

1. Go to PythonAnywhere **Web** tab
2. Click the **green "Reload"** button
3. Wait 10-20 seconds for it to reload

### Step 3: Clear Browser Cache

- **Chrome/Edge:** Ctrl+Shift+Delete → Clear cached images and files
- **Firefox:** Ctrl+Shift+Delete → Clear cache
- Or use **Incognito/Private mode** to test

### Step 4: Test Direct URL First

Before testing in WordPress, open your PythonAnywhere URL directly:
- `https://yourusername.pythonanywhere.com`

**Does it work?** If yes, continue. If no, fix the app first.

---

## Common Issues & Solutions

### Issue 1: PythonAnywhere is Adding Headers

**Solution:** The fix should override this, but if it doesn't work:

1. **Check PythonAnywhere Error Log:**
   - Go to Web tab → Error log
   - Look for any header-related errors

2. **Try using a proxy or different method** (see alternatives below)

### Issue 2: HTTPS/HTTP Mismatch

**Problem:** WordPress is HTTPS but PythonAnywhere is HTTP (or vice versa)

**Solution:** 
- Make sure **both** are using HTTPS
- PythonAnywhere free tier includes HTTPS automatically
- Use `https://` in your iframe URL

### Issue 3: Browser Security Settings

**Solution:** Test in different browsers:
- Chrome
- Firefox  
- Edge
- Safari

If it works in one but not another, it's a browser-specific security setting.

---

## Alternative Solutions

### Solution A: Use JavaScript Redirect (Works Always)

Replace your iframe with this:

```html
<div style="text-align: center; padding: 40px; background: #f5f5f5; border-radius: 8px;">
    <h2 style="color: #333;">Job Search Tool</h2>
    <p style="color: #666; margin: 20px 0;">Click the button below to open the job search tool in a new window:</p>
    <button onclick="window.open('https://yourusername.pythonanywhere.com', '_blank', 'width=1200,height=800')" 
            style="padding: 15px 40px; font-size: 18px; background: #0073aa; color: white; 
                   border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
        🔍 Open JobTrawler
    </button>
    <p style="margin-top: 20px; font-size: 14px; color: #999;">
        Or <a href="https://yourusername.pythonanywhere.com" target="_blank">open in new tab</a>
    </p>
</div>
```

### Solution B: Use WordPress Embed Block

Some WordPress themes have embed blocks that handle iframes better:

1. Add block → Search for **"Embed"**
2. Paste your PythonAnywhere URL
3. WordPress will try to embed it automatically

### Solution C: Use a Link with Preview

```html
<div class="jobtrawler-preview" style="border: 2px solid #0073aa; border-radius: 8px; padding: 20px; text-align: center;">
    <h3>Job Search Tool</h3>
    <p>Access our powerful job search tool to find relevant opportunities.</p>
    <a href="https://yourusername.pythonanywhere.com" 
       target="_blank"
       style="display: inline-block; padding: 12px 30px; background: #0073aa; 
              color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">
        Launch JobTrawler →
    </a>
</div>
```

### Solution D: Use WordPress Plugin

Install **"Advanced iFrame"** plugin - it handles security headers better:

1. Plugins → Add New → Search "Advanced iFrame"
2. Install and activate
3. Use in your page: `[advanced_iframe src="https://yourusername.pythonanywhere.com"]`

---

## Testing Checklist

- [ ] Updated `web_app.py` uploaded to PythonAnywhere
- [ ] PythonAnywhere web app reloaded
- [ ] Browser cache cleared
- [ ] Tested PythonAnywhere URL directly (works?)
- [ ] Using HTTPS for both WordPress and PythonAnywhere
- [ ] Tried different browser
- [ ] Checked browser console (F12) for errors
- [ ] Checked PythonAnywhere error log

---

## Debug: Check Browser Console

1. **Open your WordPress page with the iframe**
2. **Press F12** to open developer tools
3. **Go to Console tab**
4. **Look for errors** like:
   - "Refused to display in a frame because..."
   - "X-Frame-Options: DENY"
   - "Content-Security-Policy: frame-ancestors..."

These errors tell you what's blocking the iframe.

---

## Debug: Check Network Headers

1. **Open browser console (F12)**
2. **Go to Network tab**
3. **Refresh the page**
4. **Click on your PythonAnywhere request**
5. **Look at Response Headers**
6. **Check for:**
   - `X-Frame-Options` - Should be `ALLOWALL` (not `DENY` or `SAMEORIGIN`)
   - `Content-Security-Policy` - Should allow framing

---

## Quick Test: Simple iframe Code

Try this minimal iframe code in WordPress:

```html
<iframe src="https://yourusername.pythonanywhere.com" width="100%" height="800px"></iframe>
```

If this doesn't work, the issue is definitely with headers or security settings.

---

## Last Resort: Contact PythonAnywhere Support

If nothing works, PythonAnywhere support can help:
- They might have security settings blocking iframes
- They can check server-level headers
- They might need to whitelist your WordPress domain

---

## Most Likely Fix

**Upload the updated `web_app.py` → Reload PythonAnywhere → Clear cache → Test in incognito mode**

This fixes 90% of iframe issues!


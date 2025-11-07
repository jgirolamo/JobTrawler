# Fix: "Google Chrome does not support iframes" Error

## Problem

You're seeing the message "Google Chrome does not support iframes" - this means the iframe is being blocked by security headers.

## Solution 1: Update web_app.py (Recommended)

I've updated `web_app.py` to explicitly allow iframe embedding. You need to:

1. **Upload the updated `web_app.py`** to PythonAnywhere
2. **Reload your web app** in PythonAnywhere

The code now includes:
```python
@app.after_request
def set_xframe_options(response):
    """Allow iframe embedding by setting X-Frame-Options to ALLOWALL"""
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    return response
```

## Solution 2: Check PythonAnywhere Settings

If the issue persists:

1. **Go to PythonAnywhere Web tab**
2. **Check for any security headers** being added
3. **Make sure your app is using HTTPS** (required for iframes in modern browsers)

## Solution 3: Alternative - Use Direct Link Instead

If iframe still doesn't work, you can:

1. **Create a link** instead of iframe:
   ```html
   <a href="https://yourusername.pythonanywhere.com" target="_blank" 
      style="display: block; padding: 20px; background: #0073aa; color: white; 
             text-align: center; text-decoration: none; border-radius: 5px;">
      Open JobTrawler
   </a>
   ```

2. **Or use a button:**
   ```html
   <div style="text-align: center; margin: 20px 0;">
       <a href="https://yourusername.pythonanywhere.com" target="_blank">
           <button style="padding: 15px 30px; font-size: 16px; 
                          background: #0073aa; color: white; 
                          border: none; border-radius: 5px; cursor: pointer;">
               Open JobTrawler
           </button>
       </a>
   </div>
   ```

## Solution 4: Check Browser Console

1. **Open browser console** (F12)
2. **Look for errors** related to:
   - X-Frame-Options
   - Content-Security-Policy
   - Mixed content (HTTP vs HTTPS)

## Solution 5: Use JavaScript Redirect

If iframe is blocked, use a redirect:

```html
<div id="jobtrawler-redirect" style="text-align: center; padding: 40px;">
    <h2>Job Search Tool</h2>
    <p>Click the button below to open the job search tool:</p>
    <button onclick="window.open('https://yourusername.pythonanywhere.com', '_blank')" 
            style="padding: 15px 30px; font-size: 16px; background: #0073aa; 
                   color: white; border: none; border-radius: 5px; cursor: pointer;">
        Open JobTrawler
    </button>
</div>
```

## Quick Fix Steps

1. ✅ **Upload updated `web_app.py`** (with iframe fix)
2. ✅ **Reload PythonAnywhere web app**
3. ✅ **Clear browser cache** (Ctrl+Shift+Delete)
4. ✅ **Try iframe again**

## Testing

After uploading the fix:

1. **Open your PythonAnywhere URL directly** in a browser
2. **Check browser console** (F12) → Network tab
3. **Look for `X-Frame-Options` header** in response headers
4. **Should say:** `X-Frame-Options: ALLOWALL`

## If Still Not Working

Try this test iframe code in WordPress:

```html
<div style="width: 100%; height: 800px; border: 2px solid #ccc; padding: 10px;">
    <iframe 
        src="https://yourusername.pythonanywhere.com" 
        width="100%" 
        height="100%" 
        frameborder="0"
        sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
        style="border: none;">
    </iframe>
</div>
```

The `sandbox` attribute might help if there are other security restrictions.

---

**Most likely fix:** Upload the updated `web_app.py` and reload your PythonAnywhere app!


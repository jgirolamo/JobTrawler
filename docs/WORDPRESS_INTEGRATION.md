# WordPress Integration Guide for JobTrawler

## Overview

Since JobTrawler is a Python Flask app and WordPress runs on PHP, you have several integration options. This guide covers all methods from simple to advanced.

## Option 1: Simple iframe Embedding (Easiest)

### Steps:

1. **Deploy JobTrawler** on PythonAnywhere (or your custom domain `trawler.1jg.uk`)

2. **In WordPress:**
   - Go to **Pages** → **Add New** (or edit existing page)
   - Add a **Custom HTML** block or **HTML block**
   - Paste this code:

   ```html
   <div style="width: 100%; height: 800px; border: none;">
       <iframe 
           src="https://trawler.1jg.uk" 
           width="100%" 
           height="800px" 
           frameborder="0" 
           scrolling="auto"
           style="border: none; min-height: 600px;">
           <p>Your browser does not support iframes. 
           <a href="https://trawler.1jg.uk">Click here to open JobTrawler</a></p>
       </iframe>
   </div>
   ```

3. **Publish** the page

### Pros:
- ✅ Simple, no plugins needed
- ✅ Works immediately
- ✅ JobTrawler runs independently

### Cons:
- ❌ URL stays as PythonAnywhere domain in browser
- ❌ Doesn't feel fully integrated

---

## Option 2: Advanced iFrame Plugin (Recommended)

### Steps:

1. **Install Plugin:**
   - Go to **Plugins** → **Add New**
   - Search for **"Advanced iFrame"** or **"iframe"**
   - Install and activate **"Advanced iFrame"** by michaeldempfle

2. **Configure:**
   - Go to **Settings** → **Advanced iFrame**
   - Add your JobTrawler URL: `https://trawler.1jg.uk`
   - Configure options:
     - Auto height: ✅ Enabled
     - Auto width: ✅ Enabled
     - Hide scrollbars: Optional
     - Security: Enable XSS protection

3. **Use Shortcode:**
   - In any page/post, add:
   ```
   [advanced_iframe src="https://trawler.1jg.uk" width="100%" height="800px"]
   ```

### Pros:
- ✅ Better control over iframe behavior
- ✅ Auto-resizing
- ✅ Security features
- ✅ Easy to use shortcode

### Cons:
- ❌ Requires plugin installation
- ❌ Still uses iframe

---

## Option 3: WordPress Shortcode Plugin (Advanced)

Create a custom WordPress plugin that embeds JobTrawler with better integration.

### Create Plugin File:

1. **Create file:** `wp-content/plugins/jobtrawler-embed/jobtrawler-embed.php`

2. **Add this code:**

```php
<?php
/**
 * Plugin Name: JobTrawler Embed
 * Plugin URI: https://1jg.uk
 * Description: Embed JobTrawler job search tool
 * Version: 1.0
 * Author: Your Name
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Register shortcode
add_shortcode('jobtrawler', 'jobtrawler_embed_shortcode');

function jobtrawler_embed_shortcode($atts) {
    // Default attributes
    $atts = shortcode_atts(array(
        'url' => 'https://trawler.1jg.uk',
        'height' => '800px',
        'width' => '100%',
    ), $atts);
    
    // Generate iframe HTML
    $html = sprintf(
        '<div class="jobtrawler-container" style="width: %s; margin: 0 auto;">
            <iframe 
                src="%s" 
                width="%s" 
                height="%s" 
                frameborder="0" 
                scrolling="auto"
                style="border: none; display: block;"
                loading="lazy">
                <p>Your browser does not support iframes. 
                <a href="%s" target="_blank">Click here to open JobTrawler</a></p>
            </iframe>
        </div>',
        esc_attr($atts['width']),
        esc_url($atts['url']),
        esc_attr($atts['width']),
        esc_attr($atts['height']),
        esc_url($atts['url'])
    );
    
    return $html;
}

// Add CSS for responsive design
add_action('wp_head', 'jobtrawler_embed_styles');

function jobtrawler_embed_styles() {
    ?>
    <style>
        .jobtrawler-container {
            max-width: 100%;
            overflow: hidden;
        }
        .jobtrawler-container iframe {
            width: 100%;
            max-width: 100%;
        }
        @media (max-width: 768px) {
            .jobtrawler-container iframe {
                height: 600px !important;
            }
        }
    </style>
    <?php
}
```

3. **Activate Plugin:**
   - Go to **Plugins** → **Installed Plugins**
   - Find "JobTrawler Embed"
   - Click **Activate**

4. **Use Shortcode:**
   - In any page/post:
   ```
   [jobtrawler]
   ```
   - Or with custom options:
   ```
   [jobtrawler url="https://trawler.1jg.uk" height="900px"]
   ```

### Pros:
- ✅ Customizable
- ✅ Responsive design
- ✅ Easy to use shortcode
- ✅ No external plugin dependency

### Cons:
- ❌ Requires coding knowledge
- ❌ Still uses iframe

---

## Option 4: Full Integration via REST API (Most Advanced)

For full integration, you could create a WordPress plugin that:
1. Calls JobTrawler's API endpoints
2. Displays jobs in WordPress theme
3. Full control over styling

This requires:
- Exposing JobTrawler data via REST API (already available at `/api/jobs`)
- WordPress plugin to fetch and display data
- Custom styling

**Current API Endpoints:**
- `https://trawler.1jg.uk/api/jobs` - Returns job listings as JSON
- `https://trawler.1jg.uk/api/progress` - Returns trawler progress

---

## Option 5: Custom Domain Integration (Best User Experience)

If you use your custom domain `trawler.1jg.uk`:

1. **Set up custom domain** (see `CUSTOM_DOMAIN_SETUP.md`)
2. **Embed in WordPress** using any method above
3. **Users see consistent domain** (`1jg.uk`)

---

## Recommended Setup for 1jg.uk

### Step 1: Deploy JobTrawler
- Deploy to PythonAnywhere
- Set up subdomain: `trawler.1jg.uk`

### Step 2: Create WordPress Page
- Create page: **"Job Search"** or **"Find Jobs"**
- Use Option 2 (Advanced iFrame Plugin) or Option 3 (Custom Plugin)

### Step 3: Add to Menu
- Go to **Appearance** → **Menus**
- Add the "Job Search" page to your navigation menu

---

## Responsive Design Tips

### Mobile-Friendly iframe:

```html
<div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%;">
    <iframe 
        src="https://trawler.1jg.uk" 
        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: 0;"
        scrolling="auto">
    </iframe>
</div>
```

### CSS for Responsive:

```css
.jobtrawler-wrapper {
    position: relative;
    padding-bottom: 100%;
    height: 0;
    overflow: hidden;
    max-width: 100%;
}

.jobtrawler-wrapper iframe {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 0;
}

@media (max-width: 768px) {
    .jobtrawler-wrapper {
        padding-bottom: 150%;
    }
}
```

---

## Security Considerations

1. **X-Frame-Options:**
   - Make sure JobTrawler allows iframe embedding
   - Check `web_app.py` for any frame restrictions

2. **HTTPS:**
   - Always use HTTPS for both WordPress and JobTrawler
   - Prevents mixed content warnings

3. **Content Security Policy:**
   - If your WordPress has CSP headers, allow your JobTrawler domain

---

## Troubleshooting

### iframe not showing?
- Check browser console for errors
- Verify JobTrawler URL is correct
- Check if site allows iframe embedding
- Try opening URL directly in browser

### Styling issues?
- Add custom CSS to your WordPress theme
- Use browser inspector to debug
- Check responsive breakpoints

### Performance issues?
- Use lazy loading for iframe
- Consider caching JobTrawler responses
- Optimize WordPress page

---

## Quick Start (Easiest Method)

1. **Deploy JobTrawler** to `trawler.1jg.uk`
2. **In WordPress**, create a new page
3. **Add HTML block** with iframe code:
   ```html
   <iframe src="https://trawler.1jg.uk" width="100%" height="800px" frameborder="0"></iframe>
   ```
4. **Publish** and add to menu

**Done!** 🎉

---

**Need help?** Check the WordPress documentation or your hosting provider's support.


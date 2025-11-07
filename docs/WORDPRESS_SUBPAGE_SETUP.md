# WordPress Subpage Setup - JobTrawler Embed

## Quick Setup Guide

This guide shows you how to create a WordPress subpage that displays your JobTrawler running on PythonAnywhere.

## Step 1: Get Your PythonAnywhere URL

Your JobTrawler is running at one of these:
- `https://yourusername.pythonanywhere.com`
- `https://trawler.1jg.uk` (if you set up custom domain)

**Note this URL** - you'll need it in the next steps.

---

## Step 2: Create Subpage in WordPress

### Method A: Simple iframe (Easiest - No Plugins)

1. **Log into WordPress Admin**
   - Go to your WordPress site admin panel
   - Usually: `https://1jg.uk/wp-admin`

2. **Create New Page:**
   - Go to **Pages** → **Add New**
   - Or if you have a parent page already, go to that page and create a child page

3. **Set Page Title:**
   - Title: "Job Search" or "Find Jobs" or "Job Trawler"

4. **Add iframe:**
   - Click the **"+"** button to add a block
   - Search for **"Custom HTML"** or **"HTML"** block
   - Click to add it

5. **Paste this code:**
   ```html
   <div style="width: 100%; height: 800px; margin: 20px 0;">
       <iframe 
           src="https://yourusername.pythonanywhere.com" 
           width="100%" 
           height="800px" 
           frameborder="0" 
           scrolling="auto"
           style="border: none; display: block; width: 100%;">
           <p>Your browser does not support iframes. 
           <a href="https://yourusername.pythonanywhere.com" target="_blank">Click here to open JobTrawler</a></p>
       </iframe>
   </div>
   ```
   
   **⚠️ Replace `yourusername.pythonanywhere.com` with your actual PythonAnywhere URL!**

6. **Set as Subpage (if needed):**
   - In the right sidebar, find **"Page Attributes"**
   - Under **"Parent"**, select the parent page you want
   - This makes it a subpage

7. **Publish:**
   - Click **"Publish"** button (top right)
   - Your page is now live!

---

## Step 3: Add to Menu (Optional)

1. **Go to Appearance** → **Menus**
2. **Find your new page** in the left sidebar
3. **Check the box** next to it
4. **Click "Add to Menu"**
5. **Drag it** under the parent page to make it a submenu item
6. **Click "Save Menu"**

---

## Method B: Using Advanced iFrame Plugin (Better Control)

### Install Plugin:

1. **Go to Plugins** → **Add New**
2. **Search for:** "Advanced iFrame"
3. **Install:** "Advanced iFrame" by michaeldempfle
4. **Activate** the plugin

### Use Plugin:

1. **Create or edit your page**
2. **Add block** → Search for **"Advanced iFrame"**
3. **Configure:**
   - Source URL: `https://yourusername.pythonanywhere.com`
   - Width: 100%
   - Height: 800px
   - Auto height: Enabled (recommended)
4. **Publish**

---

## Method C: Using Shortcode (If You Installed Our Plugin)

If you uploaded the `jobtrawler-embed.php` plugin:

1. **Create or edit your page**
2. **Add shortcode block** or just type:
   ```
   [jobtrawler]
   ```
3. **Or with custom URL:**
   ```
   [jobtrawler url="https://yourusername.pythonanywhere.com" height="900px"]
   ```
4. **Publish**

---

## Step 4: Make it Responsive (Mobile-Friendly)

Add this CSS to make it work better on mobile:

1. **Go to Appearance** → **Customize** → **Additional CSS**
2. **Add this code:**
   ```css
   /* JobTrawler iframe responsive */
   .jobtrawler-wrapper {
       position: relative;
       width: 100%;
       padding-bottom: 100%;
       height: 0;
       overflow: hidden;
   }
   
   .jobtrawler-wrapper iframe {
       position: absolute;
       top: 0;
       left: 0;
       width: 100%;
       height: 100%;
       border: none;
   }
   
   @media (max-width: 768px) {
       .jobtrawler-wrapper {
           padding-bottom: 150%;
       }
   }
   ```
3. **Click "Publish"**

---

## Quick Example: Complete iframe Code

Here's a complete, ready-to-use iframe code:

```html
<div class="jobtrawler-wrapper" style="width: 100%; height: 800px; margin: 20px 0;">
    <iframe 
        src="https://yourusername.pythonanywhere.com" 
        width="100%" 
        height="800px" 
        frameborder="0" 
        scrolling="auto"
        style="border: none; display: block; width: 100%; min-height: 600px;"
        loading="lazy"
        title="JobTrawler - Job Search">
        <p>Your browser does not support iframes. 
        <a href="https://yourusername.pythonanywhere.com" target="_blank" rel="noopener">Open JobTrawler in a new window</a></p>
    </iframe>
</div>
```

**Just replace `yourusername.pythonanywhere.com` with your actual URL!**

---

## Troubleshooting

### iframe is blank?
- ✅ Check that your PythonAnywhere URL is correct
- ✅ Open the URL directly in a new browser tab to verify it works
- ✅ Check browser console (F12) for errors
- ✅ Make sure your PythonAnywhere app is running and not sleeping

### iframe too small/large?
- ✅ Adjust the `height` value in the iframe code
- ✅ Try `height="900px"` or `height="100vh"` for full viewport height

### Not showing on mobile?
- ✅ Add the responsive CSS (Step 4 above)
- ✅ Use a plugin like Advanced iFrame for better mobile support

### Page looks broken?
- ✅ Make sure you're using "Custom HTML" block, not regular text
- ✅ Check for any conflicting CSS in your theme
- ✅ Try deactivating other plugins temporarily to test

---

## Step-by-Step Checklist

- [ ] Get your PythonAnywhere URL
- [ ] Log into WordPress admin
- [ ] Create new page (or subpage)
- [ ] Add Custom HTML block
- [ ] Paste iframe code (replace URL!)
- [ ] Set parent page (if making subpage)
- [ ] Publish page
- [ ] Add to menu (optional)
- [ ] Test on desktop and mobile
- [ ] Add responsive CSS (optional but recommended)

---

## Example URLs

Replace these with your actual URLs:

- **PythonAnywhere:** `https://yourusername.pythonanywhere.com`
- **Custom domain:** `https://trawler.1jg.uk`
- **WordPress page:** `https://1jg.uk/job-search` (or whatever you named it)

---

## Quick Copy-Paste Code

**For WordPress Custom HTML block:**

```html
<iframe 
    src="YOUR_PYTHONANYWHERE_URL_HERE" 
    width="100%" 
    height="800px" 
    frameborder="0" 
    style="border: none; display: block;">
</iframe>
```

**Just replace `YOUR_PYTHONANYWHERE_URL_HERE` with your actual URL!**

---

**That's it!** Your JobTrawler should now be embedded in your WordPress subpage. 🎉


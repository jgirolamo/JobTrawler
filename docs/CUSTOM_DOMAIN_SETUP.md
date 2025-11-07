# Custom Domain Setup for 1jg.uk

## Current Domain Status

✅ **Domain `1jg.uk` is active and configured**
- Currently pointing to IPs: `3.33.152.147` and `15.197.142.173` (AWS)
- Domain is live and has DNS records
- You'll need to **change DNS records** to point to PythonAnywhere

## Prerequisites

✅ **You need a PythonAnywhere Hacker plan or higher** ($5/month minimum)
- Free tier doesn't support custom domains
- Hacker plan ($5/month) includes custom domain support

## Step 1: Upgrade to Hacker Plan (if needed)

1. Go to PythonAnywhere dashboard
2. Click "Account" → "Upgrade"
3. Select "Hacker" plan ($5/month)
4. Complete payment

## Step 2: Configure Domain in PythonAnywhere

1. **Go to "Web" tab** in PythonAnywhere
2. **Click on your web app** (or create one if you don't have it)
3. **Scroll down to "Static files" section**
4. **Find "Domains" section** (should be visible on Hacker plan)
5. **Add your domain:**
   - Enter: `1jg.uk`
   - Click "Add domain"
6. **Save changes**

## Step 3: Configure DNS Records

⚠️ **IMPORTANT:** Your domain `1jg.uk` is currently pointing to different IPs. You'll need to **change the DNS records** at your domain registrar.

Go to your domain registrar (where you bought 1jg.uk) and **update** the DNS records:

### Option A: Use Root Domain (1jg.uk)

**⚠️ IMPORTANT:** You'll need to **remove or update** the existing A records pointing to `3.33.152.147` and `15.197.142.173`

**Add/Update these DNS records:**

1. **CNAME Record** (Recommended - PythonAnywhere's preferred method):
   - Type: `CNAME`
   - Name: `@` or blank or `1jg.uk` (root domain)
   - Value: `yourusername.pythonanywhere.com` (replace with your actual PythonAnywhere username)
   - TTL: 3600 (or default)
   - **Note:** Some registrars don't allow CNAME on root domain - if so, use Option B (subdomain)

2. **Alternative - A Record** (if CNAME not allowed on root):
   - Type: `A`
   - Name: `@` or blank or `1jg.uk`
   - Value: `3.210.127.239` (PythonAnywhere's IP - **verify this is current in PythonAnywhere dashboard**)
   - TTL: 3600 (or default)

### Option B: Use Subdomain (Recommended - easier)

Use a subdomain like `trawler.1jg.uk` or `jobs.1jg.uk`:

1. **Add CNAME record:**
   - Type: `CNAME`
   - Name: `trawler` (or `jobs` or whatever you prefer)
   - Value: `yourusername.pythonanywhere.com`
   - TTL: 3600

2. **In PythonAnywhere**, add domain: `trawler.1jg.uk` (or whatever subdomain you chose)

## Step 4: Wait for DNS Propagation

- DNS changes can take **15 minutes to 48 hours** to propagate
- Usually takes about 1-2 hours
- Check DNS propagation: https://www.whatsmydns.net/

## Step 5: SSL Certificate (HTTPS)

1. **In PythonAnywhere Web tab**, scroll to your domain
2. **Click "Enable HTTPS"** or "SSL certificate"
3. PythonAnywhere will automatically provision a free Let's Encrypt certificate
4. Wait a few minutes for certificate to be issued

## Step 6: Reload Web App

1. **Click the green "Reload" button** in PythonAnywhere Web tab
2. Wait a few seconds
3. Your app should now be accessible at:
   - `https://1jg.uk` (if using root domain)
   - `https://trawler.1jg.uk` (if using subdomain)

## Step 7: Test Your Domain

1. Open `https://1jg.uk` (or your subdomain) in a browser
2. You should see your JobTrawler interface
3. If you see PythonAnywhere's "Hello" page, DNS hasn't propagated yet - wait longer

## Troubleshooting

### Domain not working?

1. **Check DNS propagation:**
   - Visit: https://www.whatsmydns.net/
   - Enter your domain: `1jg.uk`
   - Check if it points to PythonAnywhere

2. **Verify DNS records:**
   - Make sure CNAME points to `yourusername.pythonanywhere.com`
   - Make sure there are no conflicting A records

3. **Check PythonAnywhere:**
   - Make sure domain is added in Web tab
   - Make sure web app is reloaded
   - Check error logs for any issues

### SSL Certificate Issues?

- PythonAnywhere automatically provisions Let's Encrypt certificates
- Can take up to 24 hours for certificate to be issued
- Make sure DNS is fully propagated first

### Still having issues?

- Check PythonAnywhere's help docs: https://help.pythonanywhere.com/pages/CustomDomains/
- Check your domain registrar's DNS documentation
- Make sure you're on Hacker plan or higher

## Quick Checklist

- [ ] Upgraded to Hacker plan ($5/month)
- [ ] Added domain in PythonAnywhere Web tab
- [ ] Configured DNS records at domain registrar
- [ ] Waited for DNS propagation (1-2 hours)
- [ ] Enabled HTTPS/SSL certificate
- [ ] Reloaded web app
- [ ] Tested domain in browser

## Alternative: Use Subdomain

If root domain (`1jg.uk`) is tricky, use a subdomain:
- `trawler.1jg.uk`
- `jobs.1jg.uk`
- `app.1jg.uk`

Subdomains are easier to configure and often work better!

---

**Need help?** PythonAnywhere support is very helpful - contact them if you get stuck!


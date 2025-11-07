# JobTrawler WordPress Plugin

Simple WordPress plugin to embed JobTrawler into your WordPress site.

## Installation

### Method 1: Manual Installation

1. **Upload the plugin:**
   - Go to WordPress Admin → **Plugins** → **Add New**
   - Click **Upload Plugin**
   - Choose `jobtrawler-embed.php` file
   - Click **Install Now**

2. **Activate:**
   - Go to **Plugins** → **Installed Plugins**
   - Find "JobTrawler Embed"
   - Click **Activate**

### Method 2: FTP Upload

1. **Upload via FTP:**
   - Upload `jobtrawler-embed.php` to `/wp-content/plugins/jobtrawler-embed/`
   - Or create folder `jobtrawler-embed` in plugins directory
   - Upload the file there

2. **Activate:**
   - Go to **Plugins** → **Installed Plugins**
   - Find "JobTrawler Embed"
   - Click **Activate**

## Usage

### Basic Usage

In any WordPress page or post, add:

```
[jobtrawler]
```

### Custom URL

```
[jobtrawler url="https://trawler.1jg.uk"]
```

### Custom Height

```
[jobtrawler height="900px"]
```

### All Options

```
[jobtrawler url="https://trawler.1jg.uk" height="900px" width="100%"]
```

## Shortcode Parameters

- `url` - JobTrawler URL (default: `https://trawler.1jg.uk`)
- `height` - iframe height (default: `800px`)
- `width` - iframe width (default: `100%`)
- `class` - CSS class (default: `jobtrawler-embed`)

## Features

- ✅ Responsive design (mobile-friendly)
- ✅ Easy shortcode usage
- ✅ Customizable height and width
- ✅ Admin settings page
- ✅ No external dependencies
- ✅ SEO-friendly (lazy loading)

## Compatibility

- WordPress 5.0+
- All modern browsers
- Mobile responsive

## Support

For issues or questions, check:
- JobTrawler documentation
- WordPress support forums


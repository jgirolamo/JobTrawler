<?php
/**
 * Plugin Name: JobTrawler Embed
 * Plugin URI: https://1jg.uk
 * Description: Embed JobTrawler job search tool into WordPress pages/posts
 * Version: 1.0.0
 * Author: Your Name
 * License: GPL v2 or later
 * Text Domain: jobtrawler-embed
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Register shortcode: [jobtrawler]
add_shortcode('jobtrawler', 'jobtrawler_embed_shortcode');

/**
 * JobTrawler Embed Shortcode
 * 
 * Usage: [jobtrawler] or [jobtrawler url="https://trawler.1jg.uk" height="800px"]
 * 
 * @param array $atts Shortcode attributes
 * @return string HTML output
 */
function jobtrawler_embed_shortcode($atts) {
    // Default attributes
    $defaults = array(
        'url' => 'https://trawler.1jg.uk',
        'height' => '800px',
        'width' => '100%',
        'class' => 'jobtrawler-embed',
    );
    
    // Merge with user attributes
    $atts = shortcode_atts($defaults, $atts, 'jobtrawler');
    
    // Sanitize attributes
    $url = esc_url($atts['url']);
    $height = esc_attr($atts['height']);
    $width = esc_attr($atts['width']);
    $class = esc_attr($atts['class']);
    
    // Generate unique ID for this iframe
    $iframe_id = 'jobtrawler-' . uniqid();
    
    // Generate iframe HTML
    $html = sprintf(
        '<div class="%s-container" style="width: %s; margin: 0 auto;">
            <iframe 
                id="%s"
                src="%s" 
                width="%s" 
                height="%s" 
                frameborder="0" 
                scrolling="auto"
                style="border: none; display: block; width: 100%%;"
                loading="lazy"
                title="JobTrawler - Job Search Tool">
                <p>Your browser does not support iframes. 
                <a href="%s" target="_blank" rel="noopener">Click here to open JobTrawler in a new window</a></p>
            </iframe>
        </div>',
        $class,
        $width,
        $iframe_id,
        $url,
        $width,
        $height,
        $url
    );
    
    return $html;
}

// Add responsive CSS
add_action('wp_head', 'jobtrawler_embed_styles');

function jobtrawler_embed_styles() {
    ?>
    <style>
        .jobtrawler-embed-container {
            max-width: 100%;
            overflow: hidden;
            margin: 20px 0;
        }
        .jobtrawler-embed-container iframe {
            width: 100%;
            max-width: 100%;
            border: none;
        }
        /* Responsive design */
        @media (max-width: 768px) {
            .jobtrawler-embed-container {
                margin: 10px 0;
            }
            .jobtrawler-embed-container iframe {
                height: 600px !important;
            }
        }
        @media (max-width: 480px) {
            .jobtrawler-embed-container iframe {
                height: 500px !important;
            }
        }
    </style>
    <?php
}

// Optional: Add admin settings page
add_action('admin_menu', 'jobtrawler_embed_admin_menu');

function jobtrawler_embed_admin_menu() {
    add_options_page(
        'JobTrawler Embed Settings',
        'JobTrawler',
        'manage_options',
        'jobtrawler-embed',
        'jobtrawler_embed_settings_page'
    );
}

function jobtrawler_embed_settings_page() {
    ?>
    <div class="wrap">
        <h1>JobTrawler Embed Settings</h1>
        <p>Use the shortcode <code>[jobtrawler]</code> in any page or post to embed JobTrawler.</p>
        <h2>Usage Examples:</h2>
        <ul>
            <li><code>[jobtrawler]</code> - Default settings</li>
            <li><code>[jobtrawler url="https://trawler.1jg.uk"]</code> - Custom URL</li>
            <li><code>[jobtrawler height="900px"]</code> - Custom height</li>
            <li><code>[jobtrawler url="https://trawler.1jg.uk" height="900px" width="100%"]</code> - All options</li>
        </ul>
        <h2>Default Settings:</h2>
        <ul>
            <li><strong>URL:</strong> https://trawler.1jg.uk</li>
            <li><strong>Height:</strong> 800px</li>
            <li><strong>Width:</strong> 100%</li>
        </ul>
    </div>
    <?php
}


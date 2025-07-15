# Production Deployment Guide

## 📋 Pre-Deployment Checklist

✅ **Files Ready for Upload:**
- `app.py` - Main Flask application
- `wsgi.py` - WSGI entry point
- `.htaccess` - Apache configuration
- `requirements.txt` - Python dependencies
- `templates/` - HTML templates folder
- `static/` - CSS, JS, images folder
- `robots.txt` - SEO file
- `sitemap.xml` - SEO sitemap
- `ads.txt` - Advertising file
- `humans.txt` - Credits file
- `README.md` - Documentation
- `SEO_SUBMISSION_GUIDE.md` - SEO guide

## 🚀 Deployment Steps

### 1. Upload Files to Hosting Provider
1. Access your hosting control panel (cPanel)
2. Open **File Manager**
3. Navigate to `public_html` folder
4. Upload ALL project files to `public_html`
5. Extract if uploaded as ZIP

### 2. Set Up Python Environment
```bash
# In your hosting terminal or SSH:
pip3 install -r requirements.txt --user
```

### 3. Configure Permissions
Set these folder permissions:
- `downloads/` folder: **755** (writable)
- `static/` folder: **755** 
- `templates/` folder: **755**
- `wsgi.py` file: **755** (executable)

### 4. Python Path Configuration
Most shared hosting requires Python path setup in `.htaccess` or control panel:
```apache
AddHandler application/x-httpd-python3 .py
```

### 5. Database Setup (if needed)
No database setup required - app uses file storage.

## 🔧 Common Hosting Configurations

### cPanel/Shared Hosting:
1. Use **Python App** section in cPanel
2. Set application root to `public_html`
3. Set startup file to `wsgi.py`
4. Install dependencies via pip

### VPS/Dedicated Server:
```bash
# Install dependencies
pip3 install -r requirements.txt

# Run with Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:8000 wsgi:app

# Or use Apache/Nginx with mod_wsgi
```

## 🔒 Security Considerations

### Environment Variables (create .env file):
```bash
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=500000000
```

### File Permissions:
- Ensure `downloads/` folder is NOT publicly accessible
- Set proper file permissions (644 for files, 755 for directories)

## 🌐 Domain Configuration

### DNS Settings:
- Point A record to your server IP
- Set up SSL certificate (Let's Encrypt recommended)

### URL Structure:
- Main site: `https://yourdomain.com`
- Static files: `https://yourdomain.com/static/`
- Downloads: Handled by Flask (not direct access)

## 📊 Monitoring & Maintenance

### Log Files:
- Check server error logs regularly
- Monitor download folder size
- Set up log rotation

### Updates:
- Update `yt-dlp` regularly: `pip3 install --upgrade yt-dlp`
- Monitor for security updates

## 🐛 Troubleshooting

### Common Issues:

**500 Internal Server Error:**
- Check file permissions (wsgi.py should be 755)
- Verify Python path in .htaccess
- Check error logs

**Module Not Found:**
- Ensure requirements.txt dependencies are installed
- Check Python version compatibility

**Downloads Not Working:**
- Verify `downloads/` folder exists and is writable
- Check disk space
- Ensure yt-dlp is up to date

**Static Files Not Loading:**
- Check .htaccess rewrite rules
- Verify static folder permissions
- Clear browser cache

## 🎯 Performance Optimization

### For High Traffic:
1. Use CDN for static files
2. Implement caching headers
3. Use Gunicorn with multiple workers
4. Set up load balancing
5. Monitor server resources

### File Cleanup:
Set up automatic cleanup of old downloads:
```bash
# Add to cron job
find downloads/ -type f -mtime +1 -delete
```

## 📞 Support

If you encounter issues:
1. Check hosting provider documentation
2. Review error logs
3. Verify all files uploaded correctly
4. Test locally first before deploying

---

**🔥 Your YouTube Downloader is now ready for production!** 
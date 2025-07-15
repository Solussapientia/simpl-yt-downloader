# 🚄 Railway Deployment Guide for Simpl YT Downloader

## 📋 Pre-Deployment Checklist

✅ **Files Created/Updated:**
- `app.py` - Updated with Railway PORT environment variable
- `railway.toml` - Railway configuration
- `runtime.txt` - Python version specification
- `Procfile` - Alternative start command
- `.gitignore` - Exclude unnecessary files
- `downloads/.gitkeep` - Maintain directory structure
- `requirements.txt` - Already existed with all dependencies

## 🚀 Step-by-Step Deployment

### Step 1: Prepare Your Repository

1. **Initialize Git (if not already done)**
   ```bash
   git init
   git add .
   git commit -m "Initial commit - YouTube downloader ready for Railway"
   ```

2. **Push to GitHub**
   ```bash
   # Create a new repo on GitHub first, then:
   git remote add origin https://github.com/yourusername/your-repo-name.git
   git branch -M main
   git push -u origin main
   ```

### Step 2: Deploy to Railway

1. **Sign up for Railway**
   - Go to https://railway.app
   - Sign in with GitHub
   - Connect your GitHub account

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your YouTube downloader repository
   - Click "Deploy Now"

3. **Automatic Deployment**
   - Railway will automatically detect your Python app
   - It will install dependencies from `requirements.txt`
   - Use the configuration from `railway.toml`
   - Deploy using Gunicorn as specified in `Procfile`

### Step 3: Configure Your App

1. **Generate Domain**
   - In Railway dashboard, go to your project
   - Click "Settings" → "Domains"
   - Click "Generate Domain"
   - You'll get a URL like: `https://your-app.railway.app`

2. **Environment Variables (Optional)**
   - Go to "Variables" tab
   - Add any custom environment variables if needed
   - Railway automatically provides `PORT` variable

### Step 4: Monitor Deployment

1. **Check Build Logs**
   - Click "Deployments" tab
   - Monitor the build process
   - Look for any errors in the logs

2. **Expected Build Process**
   ```
   Building...
   ✅ Installing Python 3.9
   ✅ Installing dependencies from requirements.txt
   ✅ Starting with Gunicorn
   ✅ App running on Railway-provided port
   ```

### Step 5: Test Your App

1. **Visit Your App**
   - Open your Railway-provided URL
   - Should see your YouTube downloader interface

2. **Test Functionality**
   - Try downloading a YouTube video
   - Check if yt-dlp works correctly
   - Verify file downloads work

## 📊 Railway Configuration Details

### `railway.toml` Configuration

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn --bind 0.0.0.0:$PORT app:app"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[deploy.env]
PYTHONUNBUFFERED = "1"
PYTHONPATH = "/app"
```

### `Procfile` Alternative

```
web: gunicorn --bind 0.0.0.0:$PORT app:app
```

### App Configuration

```python
# app.py automatically detects Railway PORT
port = int(os.environ.get('PORT', 8000))
app.run(debug=False, host='0.0.0.0', port=port)
```

## 🔧 Troubleshooting

### Common Issues

1. **Build Fails**
   ```
   Error: Could not find requirements.txt
   Solution: Ensure requirements.txt is in root directory
   ```

2. **App Won't Start**
   ```
   Error: No module named 'yt_dlp'
   Solution: Check requirements.txt has yt-dlp==2024.12.13
   ```

3. **Port Issues**
   ```
   Error: App not responding
   Solution: Verify PORT environment variable usage in app.py
   ```

4. **yt-dlp Not Working**
   ```
   Error: yt-dlp command not found
   Solution: Railway automatically installs Python packages
   ```

### Debug Commands

```bash
# Check Railway logs
railway logs

# Connect to Railway shell
railway shell

# Check environment variables
railway variables
```

## 📈 Post-Deployment

### 1. Custom Domain (Optional)

```bash
# Add custom domain in Railway dashboard
# Settings → Domains → Add Custom Domain
# Configure DNS: CNAME record pointing to Railway
```

### 2. Environment Variables

```bash
# Add in Railway dashboard under Variables tab
DEBUG=False
FLASK_ENV=production
```

### 3. Monitoring

- Check Railway dashboard for:
  - CPU usage
  - Memory usage
  - Request metrics
  - Error logs

### 4. Scaling

- Railway automatically scales based on traffic
- Free tier: Sufficient for personal use
- Paid plans: Auto-scaling for high traffic

## 💰 Cost Estimation

### Free Tier
- $5 credit per month
- Sufficient for:
  - ~100-500 downloads per month
  - Personal use
  - Testing and development

### Paid Usage
- $0.000463 per GB-hour (CPU)
- $0.000231 per GB-hour (Memory)
- Typical cost: $2-5/month for moderate usage

## 🔄 Continuous Deployment

### Auto-Deploy Setup
1. Every GitHub push triggers automatic deployment
2. Railway rebuilds and redeploys your app
3. Zero downtime deployments
4. Rollback capability if needed

### Manual Deploy
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy manually
railway login
railway deploy
```

## ✅ Success Checklist

After deployment, verify:
- [ ] App loads at Railway URL
- [ ] YouTube URL input works
- [ ] Video info retrieval works
- [ ] Download functionality works
- [ ] Files are served correctly
- [ ] Error handling works
- [ ] Mobile responsiveness works

## 🎉 Your App is Live!

**Your YouTube downloader is now deployed on Railway!**

- **URL:** `https://your-app.railway.app`
- **Admin:** Railway dashboard
- **Logs:** Available in Railway dashboard
- **Scaling:** Automatic
- **Updates:** Push to GitHub to deploy

## 📞 Support

### Railway Support
- Documentation: https://docs.railway.app
- Discord: Railway Community
- GitHub: Railway Issues

### App Support
- Check Railway logs for errors
- Monitor resource usage
- Update dependencies regularly

**🚄 Enjoy your Railway-powered YouTube downloader!** 
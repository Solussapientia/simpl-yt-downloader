#!/usr/bin/env python3
"""
Deployment script for Simpl YT Downloader
Packages all necessary files for production deployment
"""

import os
import shutil
import zipfile
from datetime import datetime

def create_deployment_package():
    """Create a deployment package with all necessary files"""
    
    # Files and folders to include in deployment
    files_to_include = [
        'app.py',
        'wsgi.py',
        '.htaccess',
        'requirements.txt',
        'robots.txt',
        'sitemap.xml',
        'ads.txt',
        'humans.txt',
        'README.md',
        'SEO_SUBMISSION_GUIDE.md',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    folders_to_include = [
        'templates/',
        'static/',
        'downloads/'
    ]
    
    # Create deployment folder
    deployment_dir = 'deployment_package'
    if os.path.exists(deployment_dir):
        shutil.rmtree(deployment_dir)
    os.makedirs(deployment_dir)
    
    # Copy files
    print("📦 Packaging files for deployment...")
    for file in files_to_include:
        if os.path.exists(file):
            shutil.copy2(file, deployment_dir)
            print(f"✅ Added: {file}")
        else:
            print(f"⚠️  Missing: {file}")
    
    # Copy folders
    for folder in folders_to_include:
        if os.path.exists(folder):
            shutil.copytree(folder, os.path.join(deployment_dir, folder))
            print(f"✅ Added: {folder}")
        else:
            os.makedirs(os.path.join(deployment_dir, folder))
            print(f"📁 Created: {folder}")
    
    # Create zip file
    zip_name = f'simpl_yt_downloader_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(deployment_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, deployment_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n🎉 Deployment package created: {zip_name}")
    print(f"📁 Deployment folder: {deployment_dir}")
    
    # Cleanup
    shutil.rmtree(deployment_dir)
    
    return zip_name

def print_deployment_instructions():
    """Print deployment instructions"""
    print("\n" + "="*50)
    print("🚀 DEPLOYMENT INSTRUCTIONS")
    print("="*50)
    print("1. Upload the ZIP file to your hosting provider")
    print("2. Extract it in the public_html folder")
    print("3. Set file permissions:")
    print("   - wsgi.py: 755")
    print("   - downloads/ folder: 755")
    print("4. Install Python dependencies:")
    print("   pip3 install -r requirements.txt --user")
    print("5. Check DEPLOYMENT_GUIDE.md for detailed steps")
    print("="*50)

if __name__ == "__main__":
    print("🔧 Simpl YT Downloader - Deployment Script")
    print("-" * 40)
    
    zip_file = create_deployment_package()
    print_deployment_instructions()
    
    print(f"\n📄 Your deployment package is ready: {zip_file}")
    print("🌐 Ready to upload to your hosting provider!") 
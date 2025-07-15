#!/usr/bin/env python3
"""
Search Engine Ping Script for Simpl YT
This script helps accelerate indexing by notifying search engines about your sitemap.
Run this after hosting your site to speed up the indexing process.
"""

import requests
import urllib.parse
import time
from typing import List, Dict

class SearchEnginePinger:
    def __init__(self, site_url: str):
        self.site_url = site_url.rstrip('/')
        self.sitemap_url = f"{self.site_url}/sitemap.xml"
        
    def ping_google(self) -> Dict[str, str]:
        """Ping Google to notify about sitemap updates"""
        try:
            ping_url = f"https://www.google.com/ping?sitemap={urllib.parse.quote(self.sitemap_url)}"
            response = requests.get(ping_url, timeout=10)
            
            if response.status_code == 200:
                return {"status": "success", "message": "Google pinged successfully"}
            else:
                return {"status": "error", "message": f"Google ping failed with status {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Google ping failed: {str(e)}"}
    
    def ping_bing(self) -> Dict[str, str]:
        """Ping Bing to notify about sitemap updates"""
        try:
            ping_url = f"https://www.bing.com/ping?sitemap={urllib.parse.quote(self.sitemap_url)}"
            response = requests.get(ping_url, timeout=10)
            
            if response.status_code == 200:
                return {"status": "success", "message": "Bing pinged successfully"}
            else:
                return {"status": "error", "message": f"Bing ping failed with status {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Bing ping failed: {str(e)}"}
    
    def submit_to_indexnow(self) -> Dict[str, str]:
        """Submit to IndexNow (Microsoft/Yandex)"""
        try:
            # IndexNow endpoint
            indexnow_url = "https://api.indexnow.org/indexnow"
            
            # Key for IndexNow (you'll need to generate this)
            # Visit https://www.indexnow.org/ to get your key
            api_key = "your-indexnow-api-key-here"
            
            payload = {
                "host": self.site_url.replace('https://', '').replace('http://', ''),
                "key": api_key,
                "urlList": [
                    self.site_url,
                    f"{self.site_url}/about",
                    f"{self.site_url}/privacy",
                    f"{self.site_url}/terms"
                ]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(indexnow_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return {"status": "success", "message": "IndexNow submitted successfully"}
            else:
                return {"status": "error", "message": f"IndexNow submission failed with status {response.status_code}"}
                
        except Exception as e:
            return {"status": "error", "message": f"IndexNow submission failed: {str(e)}"}
    
    def ping_all_engines(self) -> List[Dict[str, str]]:
        """Ping all search engines"""
        results = []
        
        print(f"🚀 Starting search engine ping for: {self.site_url}")
        print(f"📍 Sitemap URL: {self.sitemap_url}")
        print("-" * 50)
        
        # Ping Google
        print("🔍 Pinging Google...")
        result = self.ping_google()
        results.append({"engine": "Google", **result})
        print(f"   {result['message']}")
        time.sleep(2)
        
        # Ping Bing
        print("🔍 Pinging Bing...")
        result = self.ping_bing()
        results.append({"engine": "Bing", **result})
        print(f"   {result['message']}")
        time.sleep(2)
        
        # Submit to IndexNow
        print("🔍 Submitting to IndexNow...")
        result = self.submit_to_indexnow()
        results.append({"engine": "IndexNow", **result})
        print(f"   {result['message']}")
        
        return results

def main():
    """Main function to run the ping script"""
    print("=" * 60)
    print("🎯 SIMPL YT - SEARCH ENGINE PING SCRIPT")
    print("=" * 60)
    
    # Replace with your actual domain after hosting
    site_url = input("Enter your site URL (e.g., https://simplyt.com): ").strip()
    
    if not site_url:
        print("❌ Error: Please provide a valid site URL")
        return
    
    if not site_url.startswith(('http://', 'https://')):
        site_url = f"https://{site_url}"
    
    pinger = SearchEnginePinger(site_url)
    results = pinger.ping_all_engines()
    
    print("\n" + "=" * 60)
    print("📊 PING RESULTS SUMMARY")
    print("=" * 60)
    
    success_count = 0
    for result in results:
        status_icon = "✅" if result['status'] == 'success' else "❌"
        print(f"{status_icon} {result['engine']}: {result['message']}")
        if result['status'] == 'success':
            success_count += 1
    
    print(f"\n🎉 Successfully pinged {success_count}/{len(results)} search engines")
    
    if success_count > 0:
        print("\n📈 Next Steps:")
        print("1. Monitor Google Search Console for indexing progress")
        print("2. Check Bing Webmaster Tools for crawl status")
        print("3. Run this script again after major site updates")
        print("4. Be patient - indexing can take 1-7 days")
    
    print("\n💡 Pro Tips:")
    print("• Submit your sitemap to Google Search Console")
    print("• Create quality backlinks to speed up indexing")
    print("• Share your site on social media")
    print("• Update your content regularly")

if __name__ == "__main__":
    main() 
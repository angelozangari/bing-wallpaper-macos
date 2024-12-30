import requests
import os
import subprocess
from datetime import datetime
import re
from bs4 import BeautifulSoup

def get_bing_wallpaper():
    """Fetch and download the Bing wallpaper of the day."""
    try:
        # Add headers to mimic a browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        # Get the Bing homepage
        print("Fetching Bing homepage...")
        response = requests.get("https://www.bing.com", headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for the background image URL in different possible locations
        image_url = None
        
        # Try to find image URL in the meta tags
        meta_tags = soup.find_all('meta', property='og:image')
        if meta_tags:
            image_url = meta_tags[0].get('content')
        
        # If not found in meta tags, try to find in background style
        if not image_url:
            bg_elements = soup.find_all(['div', 'style'], class_=lambda x: x and 'background' in x)
            for element in bg_elements:
                style = element.get('style', '')
                url_match = re.search(r'url\(["\']?(.*?)["\']?\)', style)
                if url_match:
                    image_url = url_match.group(1)
                    break
        
        if not image_url:
            raise ValueError("Could not find wallpaper URL in Bing homepage")
            
        # Ensure the URL is absolute
        if not image_url.startswith('http'):
            image_url = f"https://www.bing.com{image_url}"
        
        # Modify URL to get full resolution image
        image_url = image_url.replace('_tmb.jpg', '_UHD.jpg')
            
        print(f"Found image URL: {image_url}")
        
        # Download the image
        today = datetime.now().strftime("%Y-%m-%d")
        image_name = f"Bing_Wallpaper_{today}.jpg"
        
        wallpaper_dir = os.path.expanduser("~/Pictures/Bing")
        os.makedirs(wallpaper_dir, exist_ok=True)
        image_path = os.path.join(wallpaper_dir, image_name)
        
        print("Downloading image...")
        image_response = requests.get(image_url, headers=headers)
        image_response.raise_for_status()
        
        # Verify we got image data
        if 'image' not in image_response.headers.get('content-type', ''):
            raise ValueError("Received non-image response when downloading wallpaper")
        
        with open(image_path, "wb") as file:
            file.write(image_response.content)
            
        print(f"Successfully downloaded image to {image_path}")
        return os.path.abspath(image_path)  # Return absolute path
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Response status: {getattr(response, 'status_code', 'N/A')}")
        print(f"Response headers: {getattr(response, 'headers', {})}")
        print(f"Response content: {getattr(response, 'text', '')[:500]}")
        raise

def set_wallpaper(image_path):
    """Set the desktop wallpaper using AppleScript."""
    try:
        # Ensure we have an absolute path
        abs_path = os.path.abspath(image_path)
        
        # Escape any special characters in the path
        escaped_path = abs_path.replace('"', '\\"')
        
        script = f'''
        tell application "Finder"
            set desktop picture to POSIX file "{escaped_path}"
        end tell
        '''
        
        result = subprocess.run(["osascript", "-e", script], 
                              capture_output=True, 
                              text=True,
                              check=True)  # This will raise an exception if the command fails
        
        if result.stderr:
            print(f"AppleScript warning/error output: {result.stderr}")
            
    except subprocess.CalledProcessError as e:
        print(f"Error setting wallpaper: {e}")
        print(f"Script output: {e.output}")
        print(f"Script error: {e.stderr}")
        raise
    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        raise

def main():
    try:
        print("Starting Bing wallpaper download...")
        wallpaper_path = get_bing_wallpaper()
        print(f"Downloaded wallpaper to: {wallpaper_path}")
        
        print("Setting as desktop background...")
        set_wallpaper(wallpaper_path)
        print("Wallpaper set successfully!")
        
    except Exception as e:
        print(f"Failed to update wallpaper: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
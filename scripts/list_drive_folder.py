#!/usr/bin/env python3
"""Helper script to list file IDs from a public Google Drive folder.
Usage: python3 scripts/list_drive_folder.py FOLDER_ID
"""
import sys
import urllib.request
import re

def list_folder(folder_id):
    url = f"https://drive.google.com/embeddedfolderview?id={folder_id}"
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            # DEBUG: print(html[:2000]) # Uncomment if needed to see the start of the HTML
            
            # Google Drive's embedded folder view stores data in a JSON-like structure
            # We look for strings that look like Drive IDs (28-45 chars, alphanumeric/underscore/hyphen)
            # which are often prefixed with 'entry-' in this view.
            raw_matches = re.findall(r'"(?:entry-)?([a-zA-Z0-9_-]{28,45})"', html)
            
            # Filter out the folder ID itself and other common UI/junk strings
            ignore_list = [folder_id, 'flip-list-last-modified-header']
            ids = []
            for i in raw_matches:
                if i not in ignore_list and not i.startswith('entry-'):
                    ids.append(i)
            # De-duplicate while preserving order
            unique_ids = []
            for i in ids:
                if i not in unique_ids:
                    unique_ids.append(i)
            return unique_ids
    except Exception as e:
        print(f"Error: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/list_drive_folder.py FOLDER_ID")
        sys.exit(1)
    
    fid = sys.argv[1]
    print(f"→ Fetching IDs from folder: {fid}")
    found_ids = list_folder(fid)
    if found_ids:
        print("\nFound IDs (comma-separated for GitHub secret):")
        print(",".join(found_ids))
        print("\nIndividual IDs:")
        for i in found_ids:
            print(i)
    else:
        print("✗ No IDs found. Ensure the folder is shared as 'Anyone with the link can view'.")

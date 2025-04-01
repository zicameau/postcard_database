#!/usr/bin/env python3
"""
Script to check and optionally fix image URLs in the database.
This script identifies truncated UUIDs in image URLs and reports them.
"""
import re
import os
import sys
from supabase import create_client
from config import Config
from utils.db import PostcardDB

# Initialize Supabase client
supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def validate_uuid(uuid_str):
    """Validate if a string is a proper UUID"""
    # Full UUID pattern with hyphens (36 characters)
    pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(pattern, uuid_str))

def extract_uuid_from_url(url):
    """Extract UUID from image URL"""
    if not url:
        return None
    
    # Extract filename from URL
    filename = url.split('/')[-1]
    
    # Extract UUID part (before extension)
    uuid_part = filename.split('.')[0]
    
    return uuid_part

def check_all_postcards():
    """Check all postcards for problematic image URLs"""
    postcards = PostcardDB.get_all_postcards(limit=1000)  # Adjust limit if needed
    
    print(f"Checking {len(postcards)} postcards for image URL issues...")
    
    issues_found = 0
    
    for postcard in postcards:
        front_uuid = extract_uuid_from_url(postcard.get('front_image_url'))
        back_uuid = extract_uuid_from_url(postcard.get('back_image_url'))
        
        has_issues = False
        
        if front_uuid and not validate_uuid(front_uuid):
            print(f"- Postcard '{postcard['title']}' (ID: {postcard['id']}) has invalid front image UUID:")
            print(f"  URL: {postcard['front_image_url']}")
            print(f"  UUID: {front_uuid} (Length: {len(front_uuid)})")
            has_issues = True
        
        if back_uuid and not validate_uuid(back_uuid):
            print(f"- Postcard '{postcard['title']}' (ID: {postcard['id']}) has invalid back image UUID:")
            print(f"  URL: {postcard['back_image_url']}")
            print(f"  UUID: {back_uuid} (Length: {len(back_uuid)})")
            has_issues = True
        
        if has_issues:
            issues_found += 1
    
    print(f"\nFound {issues_found} postcards with image URL issues out of {len(postcards)} total.")
    
    if issues_found > 0:
        print("\nPossible solutions:")
        print("1. Re-upload the images for affected postcards")
        print("2. Check your Supabase configuration and ensure it matches what you had when uploading these images")
        print("3. Run this script with '--fix' to attempt automatic repair (NOT IMPLEMENTED YET - BACKUP FIRST!)")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        print("Auto-fixing is not implemented yet. This would require careful backup and verification.")
        print("For now, please manually re-upload the affected images.")
    else:
        check_all_postcards() 
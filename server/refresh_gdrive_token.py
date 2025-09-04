#!/usr/bin/env python3
"""
Script to refresh Google Drive OAuth tokens for MCP integration

Run this script when you get "invalid_request" errors from the MCP server.
This typically happens when the access token expires (every ~1 hour).
"""

import requests
import json
import time
import os

def refresh_gdrive_token():
    """Refresh the Google Drive access token for MCP server"""
    
    credentials_path = '/home/ramsha/Documents/smart-invoice-scheduler/mcp/gdrive_mcp/gdrive-mcp-server/credentials/.gdrive-server-credentials.json'
    oauth_keys_path = '/home/ramsha/Documents/smart-invoice-scheduler/mcp/gdrive_mcp/gdrive-mcp-server/credentials/gcp-oauth.keys.json'
    
    try:
        # Read current credentials
        with open(credentials_path) as f:
            creds = json.load(f)
        
        print('🔄 Current token expires:', time.ctime(creds['expiry_date'] / 1000))
        
        # Check if token is about to expire (within next 5 minutes)
        current_time = time.time() * 1000
        if creds['expiry_date'] > current_time + (5 * 60 * 1000):
            print('✅ Token is still valid, no refresh needed')
            return True
        
        print('🔄 Refreshing Google OAuth token...')
        
        # Read OAuth keys
        with open(oauth_keys_path) as f:
            oauth_keys = json.load(f)
        
        # Get client credentials
        if 'installed' in oauth_keys:
            client_id = oauth_keys['installed']['client_id']
            client_secret = oauth_keys['installed']['client_secret']
        elif 'web' in oauth_keys:
            client_id = oauth_keys['web']['client_id']
            client_secret = oauth_keys['web']['client_secret']
        else:
            raise ValueError('Could not find client credentials in OAuth keys')
        
        # Prepare refresh request
        refresh_data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'refresh_token': creds['refresh_token'],
            'grant_type': 'refresh_token'
        }
        
        # Make refresh request
        response = requests.post('https://oauth2.googleapis.com/token', data=refresh_data)
        
        if response.status_code == 200:
            new_token_data = response.json()
            
            # Update credentials with new access token
            creds['access_token'] = new_token_data['access_token']
            if 'expires_in' in new_token_data:
                creds['expiry_date'] = int((time.time() + new_token_data['expires_in']) * 1000)
            
            # Save updated credentials
            with open(credentials_path, 'w') as f:
                json.dump(creds, f)
            
            print('✅ Token refreshed successfully!')
            print('🕐 New expiry:', time.ctime(creds['expiry_date'] / 1000))
            return True
        else:
            print(f'❌ Token refresh failed: {response.status_code}')
            print(response.text)
            return False
            
    except Exception as e:
        print(f'❌ Error refreshing token: {e}')
        return False

if __name__ == "__main__":
    import sys
    success = refresh_gdrive_token()
    sys.exit(0 if success else 1)
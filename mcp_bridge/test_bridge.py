#!/usr/bin/env python3
"""Test the MCP bridge functionality"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_api_connection():
    """Test connection to the main app API"""
    try:
        # Get URL from environment
        main_app_url = os.getenv("MAIN_APP_URL", "http://localhost:9000")
        print(f"🔗 Testing connection to: {main_app_url}")
        
        async with httpx.AsyncClient() as client:
            # Test basic connection
            response = await client.get(f"{main_app_url}/api/users/")
            users = response.json()
            print(f"✅ API Connection successful! Found {len(users)} users:")
            for user in users:
                print(f"   - {user['display_name']} ({user['name']})")
            
            # Test adding a reading entry
            reading_data = {
                "user_id": 1,
                "title": "Test Book via Bridge",
                "author": "Test Author",
                "status": "in_progress",
                "notes": "Added via MCP bridge test"
            }
            
            response = await client.post(f"{main_app_url}/api/reading/", json=reading_data)
            result = response.json()
            print(f"✅ Reading entry created: {result['title']}")
            
            # Test adding a journal entry
            journal_data = {
                "user_id": 1,
                "date": "2024-08-27",
                "context": "Test journal entry for MCP bridge testing",
                "title": "Test Journal Entry",
                "tags": "test"
            }
            
            response = await client.post(f"{main_app_url}/api/journal/", json=journal_data)
            journal_result = response.json()
            journal_id = journal_result['id']
            print(f"✅ Journal entry created: {journal_result['title']}")
            
            # Test editing the journal entry with ai_analysis field only
            edit_data = {
                "ai_analysis": "**Test Analysis**\n\nThis is a test of editing journal entries with ai_analysis field only."
            }
            
            response = await client.put(f"{main_app_url}/api/journal/{journal_id}", json=edit_data)
            if response.status_code == 200:
                edit_result = response.json()
                print(f"✅ Journal entry edited with ai_analysis: Entry {journal_id}")
            else:
                print(f"❌ Journal entry edit failed: {response.status_code} - {response.text}")
                return False
            
            return True
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

async def main():
    print("🧪 Testing MCP Bridge...")
    main_app_url = os.getenv("MAIN_APP_URL", "http://localhost:9000")
    api_ok = await test_api_connection()
    
    if api_ok:
        print("\n🎉 All tests passed! The bridge should work with Claude Desktop.")
        print("\nTo use with Claude Desktop, add this to your config:")
        print('```json')
        print('{')
        print('  "mcpServers": {')
        print('    "progress-tracker": {')
        print('      "command": "python",')
        print(f'      "args": ["{__file__}/../server.py"],')
        print('      "env": {')
        print(f'        "MAIN_APP_URL": "{main_app_url}"')
        print('      }')
        print('    }')
        print('  }')
        print('}')
        print('```')
    else:
        print(f"❌ Tests failed. Make sure the main app is running on {main_app_url}")

if __name__ == "__main__":
    asyncio.run(main())
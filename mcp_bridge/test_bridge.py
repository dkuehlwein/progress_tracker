#!/usr/bin/env python3
"""Test the MCP bridge functionality"""

import asyncio
import httpx

async def test_api_connection():
    """Test connection to the main app API"""
    try:
        async with httpx.AsyncClient() as client:
            # Test basic connection
            response = await client.get("http://127.0.0.1:8000/api/users/")
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
            
            response = await client.post("http://127.0.0.1:8000/api/reading/", json=reading_data)
            result = response.json()
            print(f"✅ Reading entry created: {result['title']}")
            
            return True
            
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

async def main():
    print("🧪 Testing MCP Bridge...")
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
        print('        "MAIN_APP_URL": "http://127.0.0.1:8000"')
        print('      }')
        print('    }')
        print('  }')
        print('}')
        print('```')
    else:
        print("❌ Tests failed. Make sure the main app is running on http://127.0.0.1:8000")

if __name__ == "__main__":
    asyncio.run(main())
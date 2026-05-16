"""
Test script for Stage 2 API endpoint
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
ENDPOINT = f"{BASE_URL}/api/stage2/deduplicate"

# Test data
test_request = {
    "repo_url": "https://github.com/fastapi/fastapi",
    "idea": "Add support for WebSocket compression"
}

print("Testing Stage 2 - Idea Deduplication")
print("=" * 50)
print(f"\nEndpoint: {ENDPOINT}")
print(f"\nRequest:")
print(json.dumps(test_request, indent=2))
print("\n" + "=" * 50)

try:
    response = requests.post(ENDPOINT, json=test_request, timeout=30)
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\n[SUCCESS]")
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
    else:
        print(f"\n[ERROR]: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("\n[ERROR]: Could not connect to server")
    print("Make sure the server is running with: .venv\\Scripts\\python.exe -m uvicorn main:app --reload")
except Exception as e:
    print(f"\n[ERROR]: {str(e)}")

print("\n" + "=" * 50)

# Made with Bob

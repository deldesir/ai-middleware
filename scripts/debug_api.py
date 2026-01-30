import requests
import os

URL = "http://localhost/rp/api/v2/flows.json"
TOKEN = "GJ3ZQ8HZEWZQUENXBQ9R8Z9LKSLJFXUYU6EYWZUN" # User provided

def debug_api():
    print(f"GET {URL}")
    headers = {"Authorization": f"Token {TOKEN}"}
    try:
        res = requests.get(URL, headers=headers)
        print(f"Status: {res.status_code}")
        print(f"Headers: {res.headers}")
        print(f"Effective URL: {res.url}")
        print(f"Body: {res.text[:500]}") # First 500 chars
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_api()

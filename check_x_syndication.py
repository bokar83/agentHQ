import urllib.request
import json
import ssl

# Disable certificate verification just in case, or use default context
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

tweet_id = "2049836721752211703" # From your real live X post
url = f"https://syndication.twitter.com/widgets/tweet?id={tweet_id}"

req = urllib.request.Request(
    url,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
)

try:
    with urllib.request.urlopen(req, context=ctx) as response:
        data = json.loads(response.read().decode())
        print("Syndication Response:")
        # Let's print some key fields
        print(f"Created At: {data.get('created_at')}")
        print(f"Text: {data.get('text')}")
        user = data.get("user", {})
        print(f"User: {user.get('name')} (@{user.get('screen_name')})")
        
        # Look for engagement metrics!
        print("\nEngagement Metrics:")
        print(f"Favorite Count (Likes): {data.get('favorite_count')}")
        # Note: sometimes nested or called differently
        print(f"Conversation Count (Replies): {data.get('conversation_count')}")
        print(f"News Action Type: {data.get('news_action_type')}")
        
        # Let's print the entire raw dictionary to see all fields!
        print("\nFull JSON:")
        print(json.dumps(data, indent=2))
        
except Exception as e:
    print(f"Error: {e}")

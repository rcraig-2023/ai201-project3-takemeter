import requests
import pandas as pd
import html
import json
import time
import os
from groq import Groq

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# --- 1. Fetch 200 Comments from Hacker News ---
API_URL = "https://hn.algolia.com/api/v1/search_by_date"
comments_data = []
page = 0

print("Fetching 200 recent comments from Hacker News...")
while len(comments_data) < 200:
    params = {"tags": "comment", "hitsPerPage": 50, "page": page}
    response = requests.get(API_URL, params=params)
    
    if response.status_code != 200:
        print("Error fetching data")
        break
        
    for hit in response.json().get("hits", []):
        raw_text = hit.get("comment_text", "")
        text = html.unescape(raw_text).replace('<p>', '\n\n').replace('</p>', '').strip()
        
        # Filter for substantial comments
        if text and len(text) > 100:
            comments_data.append({"text": text, "label": "", "notes": ""})
            
        if len(comments_data) == 200:
            break
    page += 1

# --- 2. Pre-label with Groq ---
system_prompt = """
You are a data annotator classifying Hacker News comments. Output raw JSON with two keys: "label" and "notes". 
The "label" must be EXACTLY one of:
1. "technical_analysis": Structured argument about tech/engineering/business, backed by details.
2. "dismissive_take": Cynical, shallow, or reactionary criticism without substantive reasoning.
3. "clarifying_question": Asking for more information or clarification.

The "notes" should be empty unless the comment is genuinely ambiguous between two labels, in which case briefly explain why.
"""

print("Data fetched. Starting Groq pre-labeling process (this takes a few minutes)...")

for i, item in enumerate(comments_data):
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Classify this text:\n\n{item['text']}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0
        )
        
        result = json.loads(res.choices[0].message.content)
        comments_data[i]['label'] = result.get('label', '')
        comments_data[i]['notes'] = result.get('notes', '')
        
        # Print progress
        if (i + 1) % 20 == 0:
            print(f"Labeled {i + 1}/200 comments...")
            
        time.sleep(1) # Respect API rate limits
        
    except Exception as e:
        print(f"Error labeling row {i}: {e}")

# --- 3. Save to CSV ---
df = pd.DataFrame(comments_data)
df.to_csv("hackernews_dataset.csv", index=False)
print("Complete! Saved fully labeled dataset to hackernews_dataset.csv")
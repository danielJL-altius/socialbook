import requests
from bs4 import BeautifulSoup
import json

TAVILY_API_KEY = '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'

def tavily_search(query):
    url = 'https://api.tavily.com/search'
    headers = {'Authorization': f'Bearer {TAVILY_API_KEY}'}
    data = {
        'query': query,
        'search_depth': 'advanced',
        'include_answer': False,
        'include_domains': ['linkedin.com', 'crunchbase.com', 'company.com'],
        'max_results': 5
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()['results']

def extract_info_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Try meta tags
        bio = soup.find('meta', {'name': 'description'})
        if not bio:
            bio = soup.find('meta', {'property': 'og:description'})
        bio_text = bio['content'] if bio and bio.has_attr('content') else ''

        # Try og:image for headshot
        img = soup.find('meta', {'property': 'og:image'})
        img_url = img['content'] if img and img.has_attr('content') else ''

        return bio_text.strip(), img_url.strip(), url
    except Exception as e:
        return '', '', url

def find_person_profile(name, company=None):
    query = f"{name} {company} bio OR profile" if company else f"{name} bio OR profile"
    results = tavily_search(query)

    for r in results:
        bio, photo, url = extract_info_from_url(r['url'])
        if bio and photo:
            return {
                'name': name,
                'company': company,
                'bio': bio,
                'photo_url': photo,
                'source_url': url
            }

    return {
        'name': name,
        'company': company,
        'bio': None,
        'photo_url': None,
        'source_url': None
    }

# Example use
person = find_person_profile("Daniel Ek", "Spotify")
print(json.dumps(person, indent=2))
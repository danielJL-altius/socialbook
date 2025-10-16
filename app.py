from flask import Flask, render_template, request, jsonify
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
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

        bio = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        bio_text = bio['content'] if bio and bio.has_attr('content') else ''

        img = soup.find('meta', {'property': 'og:image'})
        img_url = img['content'] if img and img.has_attr('content') else ''

        return bio_text.strip(), img_url.strip(), url
    except:
        return '', '', url

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    name = request.form.get('name', '').strip()
    company = request.form.get('company', '').strip()
    query = f"{name} {company} bio OR profile" if company else f"{name} bio OR profile"

    results = tavily_search(query)

    for r in results:
        bio, photo, url = extract_info_from_url(r['url'])
        if bio and photo:
            return jsonify({
                'name': name,
                'company': company,
                'bio': bio,
                'photo_url': photo,
                'source_url': url
            })

    return jsonify({
        'name': name,
        'company': company,
        'bio': None,
        'photo_url': None,
        'source_url': None
    })

if __name__ == '__main__':
    app.run(debug=True)
import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

def tavily_search(query):
    url = 'https://api.tavily.com/search'
    headers = {'Authorization': f'Bearer {TAVILY_API_KEY}'}
    data = {
        'query': query,
        'search_depth': 'advanced',
        'include_answer': False,
        'include_domains': ['linkedin.com', 'crunchbase.com', 'net2phone.com', 'medium.com', 'twitter.com', 'x.com'],
        'max_results': 10  # Increased to get more candidates
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    results = response.json()['results']
    # Return both URL and content from Tavily
    return [(r['url'], r.get('content', '')) for r in results]

def search_person_images_google(name, company):
    """
    Use Tavily to specifically search for person images
    """
    url = 'https://api.tavily.com/search'
    headers = {'Authorization': f'Bearer {TAVILY_API_KEY}'}
    query = f"{name} {company} headshot photo profile picture" if company else f"{name} headshot photo"
    data = {
        'query': query,
        'search_depth': 'basic',
        'include_images': True,
        'max_results': 5
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        # Return image URLs if available
        return result.get('images', [])
    except:
        return []

def extract_text_and_image(url, name):
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        soup = BeautifulSoup(r.text, 'html.parser')

        # Extract text
        paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3'])
        text = ' '.join([p.get_text(strip=True) for p in paragraphs])

        image_url = ''

        # Strategy 1: LinkedIn-specific selectors
        if 'linkedin.com' in url.lower():
            # LinkedIn profile images have specific classes
            linkedin_img = soup.find('img', {'class': lambda c: c and any(x in str(c).lower() for x in ['profile', 'avatar', 'photo'])})
            if linkedin_img and linkedin_img.get('src'):
                image_url = linkedin_img.get('src')

        # Strategy 2: Look for structured data (JSON-LD)
        if not image_url:
            json_ld = soup.find_all('script', {'type': 'application/ld+json'})
            for script in json_ld:
                try:
                    import json
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        if data.get('@type') == 'Person' and data.get('image'):
                            image_url = data.get('image')
                            break
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'Person' and item.get('image'):
                                image_url = item.get('image')
                                break
                except:
                    continue

        # Strategy 3: Look for images with person-related attributes
        if not image_url:
            name_parts = [part.lower() for part in name.split()]
            imgs = soup.find_all('img')

            scored_images = []
            for img in imgs:
                src = img.get('src', '')
                alt = img.get('alt', '').lower()
                title = img.get('title', '').lower()
                img_class = ' '.join(img.get('class', [])).lower() if img.get('class') else ''

                # Skip obviously bad images
                if any(bad in src.lower() for bad in ['logo', 'icon', 'banner', 'cover', 'background', '.svg', 'illustration', 'cartoon', 'graphic', 'placeholder']):
                    continue
                if any(bad in alt for bad in ['illustration', 'cartoon', 'graphic', 'icon']):
                    continue
                if not src or src.startswith('data:'):
                    continue

                score = 0

                # High-value keywords
                if any(k in alt for k in ['headshot', 'portrait', 'professional photo']):
                    score += 10
                if any(k in img_class for k in ['profile', 'headshot', 'avatar', 'photo', 'portrait']):
                    score += 8
                if any(k in src.lower() for k in ['profile', 'headshot', 'avatar', 'portrait']):
                    score += 7

                # Name matching
                if all(part in alt or part in src.lower() or part in title for part in name_parts):
                    score += 15
                elif any(part in alt or part in src.lower() or part in title for part in name_parts):
                    score += 5

                # Size hints (bigger is more likely to be a headshot)
                width = img.get('width', '')
                height = img.get('height', '')
                if width and height:
                    try:
                        w, h = int(width), int(height)
                        if 150 <= w <= 800 and 150 <= h <= 800:
                            score += 3
                    except:
                        pass

                if score > 0:
                    scored_images.append((score, src))

            if scored_images:
                scored_images.sort(reverse=True, key=lambda x: x[0])
                image_url = scored_images[0][1]

        # Strategy 4: Fallback to og:image but with validation
        if not image_url:
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                og_url = og_image['content']
                # Only use og:image if it doesn't look like a generic asset
                if not any(bad in og_url.lower() for bad in ['logo', 'banner', 'cover', 'default', 'og-image']):
                    image_url = og_url

        # Ensure absolute URL
        if image_url and not image_url.startswith('http'):
            from urllib.parse import urljoin
            image_url = urljoin(url, image_url)

        return text, image_url
    except Exception:
        return '', ''

def validate_headshot(image_url, name):
    """
    Use OpenAI's vision API to validate if an image is actually a professional headshot
    Returns: (is_valid, confidence_score)
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"""Analyze this image and determine if it is a REAL PHOTOGRAPH of a professional headshot or portrait of a person named {name}.

Answer with a JSON object:
{{
  "is_headshot": true/false,
  "confidence": 0-100,
  "reasoning": "brief explanation"
}}

CRITICAL REQUIREMENTS - The image MUST be:
- An actual PHOTOGRAPH of a real person (not an illustration, cartoon, drawing, or graphic)
- Show a person's face clearly and prominently
- Be a professional headshot or portrait style photo
- Feature an individual person (not a group)

REJECT if the image is:
- An illustration, cartoon, drawing, or any non-photographic image
- A logo, icon, or graphic design
- A group photo or crowd scene
- A landscape, object, or scene without a clear face
- A stock photo illustration or clipart

Be very strict about rejecting illustrations and cartoons."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url}
                        }
                    ]
                }
            ],
            max_tokens=300
        )

        import json
        result_text = response.choices[0].message.content.strip()
        # Try to extract JSON from markdown code blocks if present
        if '```json' in result_text:
            result_text = result_text.split('```json')[1].split('```')[0].strip()
        elif '```' in result_text:
            result_text = result_text.split('```')[1].split('```')[0].strip()

        result = json.loads(result_text)
        return result.get('is_headshot', False), result.get('confidence', 0)
    except Exception as e:
        # If validation fails, reject the image (fail closed for better quality)
        return False, 0

def summarize_bio(name, company, texts):
    prompt = f"""
You are a helpful assistant. Based on the following web content, write a professional bio for {name} from {company}.
Focus on their roles, achievements, industries, and relevant history.
Remove emojis and informal language. Output a short paragraph in a LinkedIn-style tone.

Web content:
{texts}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def fallback_image(name):
    name_key = name.lower().replace(' ', '_')
    known_images = {
        'daniel_leubitz': 'https://www.example.com/images/daniel_leubitz_headshot.jpg'
    }
    return known_images.get(name_key, None)

@app.route('/')
def index():
    return render_template('index.html')

def extract_company_from_text(text, url):
    """Extract company name from page text or URL"""
    import re

    # Try LinkedIn structured data patterns
    if 'linkedin.com' in url.lower():
        # Pattern: "Job Title at Company | LinkedIn"
        match = re.search(r'at\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*[\|\-–•]|\s+on\s+LinkedIn|LinkedIn|$)', text[:600], re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            # Clean up artifacts
            company = re.sub(r'\s+(is|has|and|the|on|LinkedIn)$', '', company, flags=re.IGNORECASE)
            company = re.sub(r'\s+\|\s*.*$', '', company)  # Remove everything after |
            if len(company) > 2 and company != "Unknown":
                return company[:50]

    # Crunchbase pattern
    if 'crunchbase.com' in url.lower():
        match = re.search(r'crunchbase\.com/person/[^/]+', url)
        # Try to extract from title or content
        match = re.search(r'(?:Founder|CEO|CTO|President|VP|Director|COO|CFO|Chief)\s+(?:at|of|@)\s+([A-Z][A-Za-z0-9\s&,.\'-]+)', text[:500])
        if match:
            return match.group(1).strip()[:50]

    # Generic patterns - try multiple strategies
    if text:
        # Strategy 1: Job title patterns
        patterns = [
            r'(?:CEO|CTO|VP|President|Director|Head|Manager|Founder|Co-Founder|Chief)\s+(?:at|of|@)\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*[\|\-–•,.]|$)',
            r'(?:works?|working)\s+(?:at|for)\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*[\|\-–•,.]|$)',
            r'currently\s+(?:at|with)\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*[\|\-–•,.]|$)',
            r'employed\s+(?:at|by)\s+([A-Z][A-Za-z0-9\s&,.\'-]+?)(?:\s*[\|\-–•,.]|$)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text[:500], re.IGNORECASE)
            if match:
                company = match.group(1).strip()
                # Clean up
                company = re.sub(r'\s+(is|has|and|the|where|since|in)$', '', company, flags=re.IGNORECASE)
                company = re.sub(r'\s+\d{4}.*$', '', company)  # Remove years
                company = re.sub(r'\s*[\|\-–].*$', '', company)  # Remove text after separators
                if len(company) > 2 and not re.match(r'^(a|an|the)$', company, re.IGNORECASE):
                    return company[:50]

    return None  # Changed from "Unknown Company" to None

def create_person_profile(name, url, tavily_content=''):
    """Create a lightweight profile for a person from a URL"""
    try:
        print(f"Creating profile for {name} from {url}", flush=True)

        # Try to scrape the page
        text, img_url = extract_text_and_image(url, name)

        # If scraping failed, use Tavily's content
        if (not text or len(text.strip()) < 20) and tavily_content:
            print(f"  Using Tavily content (scraped text too short)", flush=True)
            text = tavily_content

        # Be more lenient - accept even if text is short
        if not text or len(text.strip()) < 10:
            print(f"  Skipping - insufficient text (len={len(text) if text else 0})", flush=True)
            return None

        # Extract company
        company = extract_company_from_text(text, url)

        # If no company found, try to extract from domain
        if not company:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Use domain as company for non-social sites
            if not any(social in domain for social in ['linkedin.com', 'twitter.com', 'facebook.com', 'instagram.com', 'crunchbase.com']):
                company = domain.replace('www.', '').split('.')[0].title()
            else:
                company = "Company Not Listed"

        # Get snippet bio (first 200 chars, prioritize sentences)
        if len(text) > 200:
            # Try to end at a sentence
            snippet = text[:200]
            last_period = snippet.rfind('.')
            if last_period > 100:  # If there's a period in reasonable range
                snippet = text[:last_period + 1]
            else:
                snippet = text[:200].strip() + "..."
        else:
            snippet = text.strip()

        # Clean up snippet
        import re
        snippet = re.sub(r'\s+', ' ', snippet)  # Normalize whitespace

        print(f"  Created profile: company={company}, has_photo={bool(img_url)}, snippet_len={len(snippet)}")

        return {
            'name': name,
            'company': company,
            'photo_url': img_url,
            'snippet': snippet,
            'source_url': url
        }
    except Exception as e:
        import traceback
        print(f"Error creating profile for {url}: {e}")
        print(traceback.format_exc())
        return None

@app.route('/search/candidates', methods=['POST'])
def search_candidates():
    """Step 1: Return multiple candidate profiles for disambiguation"""
    name = request.form.get('name', '').strip()
    company = request.form.get('company', '').strip()

    # If company is provided, do a targeted search
    if company:
        query = f"{name} {company} professional bio"
    else:
        query = f"{name} professional bio LinkedIn"

    try:
        url_content_pairs = tavily_search(query)
        print(f"\nSearching for '{name}' with query: {query}", flush=True)
        print(f"Found {len(url_content_pairs)} URLs to process", flush=True)

        # Create profiles for each candidate
        candidates = []
        seen_urls = set()
        company_groups = {}  # Track companies to identify unique people

        for url, tavily_content in url_content_pairs:
            # Skip duplicate URLs
            if url in seen_urls:
                continue
            seen_urls.add(url)

            profile = create_person_profile(name, url, tavily_content)
            if not profile:
                continue

            # Track by company to group same person
            company_key = profile['company'] if profile['company'] and profile['company'] != "Company Not Listed" else None

            if company_key:
                # If we've seen this company, it's likely the same person
                if company_key in company_groups:
                    # Update with better photo if available
                    existing = company_groups[company_key]
                    if profile['photo_url'] and not existing['photo_url']:
                        existing['photo_url'] = profile['photo_url']
                    # Keep the profile with more info
                    if len(profile['snippet']) > len(existing['snippet']):
                        existing['snippet'] = profile['snippet']
                        existing['source_url'] = profile['source_url']
                    continue
                else:
                    company_groups[company_key] = profile

            # Optional: Validate image if present (but don't reject profile)
            # Skip validation during candidate search for speed
            profile['image_confidence'] = 0

            candidates.append(profile)

            # Stop after finding 8 unique candidates
            if len(candidates) >= 8:
                break

        print(f"Total candidates found: {len(candidates)}")

        # If only one candidate found OR if company was specified, go straight to detail
        if len(candidates) == 1 or (company and len(candidates) > 0):
            # Return special flag to skip selection
            return jsonify({
                'candidates': candidates,
                'count': len(candidates),
                'skip_selection': True,
                'selected_candidate': candidates[0]
            })

        # Sort by: 1) has photo, 2) image confidence, 3) snippet length
        candidates.sort(key=lambda x: (
            1 if x.get('photo_url') else 0,
            x.get('image_confidence', 0),
            len(x.get('snippet', ''))
        ), reverse=True)

        return jsonify({
            'candidates': candidates,
            'count': len(candidates),
            'skip_selection': False
        })
    except Exception as e:
        import traceback
        print(f"Error in search_candidates: {e}")
        print(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/search/detail', methods=['POST'])
def search_detail():
    """Step 2: Get detailed bio for selected candidate"""
    name = request.form.get('name', '').strip()
    company = request.form.get('company', '').strip()
    source_url = request.form.get('source_url', '').strip()

    query = f"{name} {company} professional bio" if company else f"{name} professional bio"

    try:
        # Search for more detailed information
        url_content_pairs = tavily_search(query)
        urls = [url for url, _ in url_content_pairs]

        # If we have a source URL, prioritize it
        if source_url and source_url not in urls:
            urls.insert(0, source_url)
            url_content_pairs.insert(0, (source_url, ''))

        texts_images = []
        for url, tavily_content in url_content_pairs[:10]:
            text, img = extract_text_and_image(url, name)
            # Use Tavily content if scraping failed
            if not text or len(text.strip()) < 20:
                text = tavily_content
            texts_images.append((text, img))
        all_text = "\n\n".join([txt for txt, _ in texts_images])

        # Collect all candidate images
        candidate_images = []

        # Add images from scraped pages
        for _, img_url in texts_images:
            if img_url:
                candidate_images.append(img_url)

        # Also search for dedicated image results
        image_results = search_person_images_google(name, company)
        candidate_images.extend(image_results)

        # Find the best validated headshot
        photo_url = None
        best_confidence = 0

        for img_url in candidate_images:
            if img_url:
                is_valid, confidence = validate_headshot(img_url, name)
                print(f"Image: {img_url[:100]}... | Valid: {is_valid} | Confidence: {confidence}")

                if is_valid and confidence > best_confidence:
                    photo_url = img_url
                    best_confidence = confidence
                    # If we found a high-confidence match, stop searching
                    if confidence >= 85:
                        break

        # Fallback if no valid image found
        if not photo_url or best_confidence < 50:
            photo_url = fallback_image(name)
            if not photo_url:
                best_confidence = 0

        summary = summarize_bio(name, company, all_text)

        return jsonify({
            'name': name,
            'company': company,
            'bio': summary,
            'photo_url': photo_url,
            'source_urls': urls[:3],
            'image_confidence': best_confidence
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/search', methods=['POST'])
def search():
    """Legacy endpoint - redirects to candidate search"""
    return search_candidates()

if __name__ == '__main__':
    app.run(debug=True)
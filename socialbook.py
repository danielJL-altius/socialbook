import os
import requests
from bs4 import BeautifulSoup
from flask import Flask, request, render_template, jsonify, redirect, url_for
from dotenv import load_dotenv
from openai import OpenAI
import database as db

# Load environment variables
load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client
if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY not set. Please add it in Railway dashboard.")
    client = None
else:
    client = OpenAI(api_key=OPENAI_API_KEY)

app = Flask(__name__)

# Import all helper functions from ai_bio_scraper
from ai_bio_scraper import (
    tavily_search, extract_text_and_image, extract_company_from_text,
    validate_headshot, summarize_bio, search_person_images_google
)

@app.route('/')
def index():
    return render_template('socialbook.html')

@app.route('/browse')
def browse():
    """Browse all profiles in the social book"""
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    profiles = db.get_all_profiles(limit=per_page, offset=offset)
    total = db.get_profile_count()
    total_pages = (total + per_page - 1) // per_page

    return jsonify({
        'profiles': profiles,
        'page': page,
        'total_pages': total_pages,
        'total_count': total
    })

@app.route('/search', methods=['POST'])
def search():
    """Search for a person - check DB first, then web if not found"""
    name = request.form.get('name', '').strip()
    company = request.form.get('company', '').strip()

    if not name:
        return jsonify({'error': 'Name is required'}), 400

    print(f"\n=== Searching for: {name} (company: {company or 'any'}) ===", flush=True)

    # Step 1: Search database first
    db_results = db.search_profiles(name)
    print(f"Found {len(db_results)} profiles in database", flush=True)

    # Filter by company if specified
    if company and db_results:
        db_results = [p for p in db_results if company.lower() in (p.get('company') or '').lower()]

    # If exact match found in DB, return it
    if db_results:
        exact_matches = [p for p in db_results if p['name'].lower() == name.lower()]
        if exact_matches:
            if len(exact_matches) == 1:
                print(f"Exact match found in DB, returning profile", flush=True)
                return jsonify({
                    'source': 'database',
                    'profile': exact_matches[0],
                    'found_in_db': True
                })
            else:
                # Multiple matches - let user choose
                return jsonify({
                    'source': 'database',
                    'candidates': exact_matches,
                    'count': len(exact_matches),
                    'found_in_db': True
                })

    # Step 2: If not in DB, search the web
    print(f"Not found in DB, searching web...", flush=True)

    query = f"{name} {company} professional bio" if company else f"{name} professional bio LinkedIn"

    try:
        url_content_pairs = tavily_search(query)
        print(f"Found {len(url_content_pairs)} web results", flush=True)

        candidates = []
        seen_companies = set()

        for url, tavily_content in url_content_pairs[:10]:
            # Extract info
            text, img_url = extract_text_and_image(url, name)

            # Use Tavily content if scraping failed
            if not text or len(text.strip()) < 20:
                text = tavily_content

            if not text or len(text.strip()) < 10:
                continue

            # Extract company
            profile_company = extract_company_from_text(text, url)
            if not profile_company:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if not any(social in domain for social in ['linkedin.com', 'twitter.com', 'facebook.com']):
                    profile_company = domain.replace('www.', '').split('.')[0].title()
                else:
                    profile_company = "Company Not Listed"

            # Deduplicate by company
            if profile_company in seen_companies:
                continue
            seen_companies.add(profile_company)

            # Create snippet
            snippet = text[:200].strip()
            if len(text) > 200:
                snippet += "..."

            candidates.append({
                'name': name,
                'company': profile_company,
                'photo_url': img_url,
                'snippet': snippet,
                'source_url': url,
                'full_text': text
            })

            if len(candidates) >= 8:
                break

        if not candidates:
            return jsonify({'error': 'No profiles found on the web'}), 404

        # If only one candidate, auto-save and return
        if len(candidates) == 1:
            print(f"Only one candidate found, generating bio and saving...", flush=True)
            candidate = candidates[0]
            bio = summarize_bio(name, candidate['company'], candidate['full_text'])

            # Save to database
            profile_id = db.save_profile(
                name=name,
                company=candidate['company'],
                bio=bio,
                photo_url=candidate['photo_url'],
                snippet=candidate['snippet'],
                source_urls=[candidate['source_url']],
                image_confidence=0
            )

            saved_profile = db.get_profile_by_id(profile_id)
            return jsonify({
                'source': 'web',
                'profile': saved_profile,
                'found_in_db': False,
                'newly_added': True
            })

        # Multiple candidates - return for user selection
        return jsonify({
            'source': 'web',
            'candidates': candidates,
            'count': len(candidates),
            'found_in_db': False
        })

    except Exception as e:
        import traceback
        print(f"Error searching: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/save_profile', methods=['POST'])
def save_profile():
    """Save a selected candidate to the database"""
    data = request.json
    name = data.get('name')
    company = data.get('company')
    snippet = data.get('snippet')
    photo_url = data.get('photo_url')
    source_url = data.get('source_url')
    full_text = data.get('full_text', '')

    print(f"Saving profile for {name} at {company}", flush=True)

    try:
        # Generate full bio
        bio = summarize_bio(name, company, full_text)

        # Save to database
        profile_id = db.save_profile(
            name=name,
            company=company,
            bio=bio,
            photo_url=photo_url,
            snippet=snippet,
            source_urls=[source_url],
            image_confidence=0
        )

        saved_profile = db.get_profile_by_id(profile_id)
        return jsonify({
            'success': True,
            'profile': saved_profile
        })

    except Exception as e:
        import traceback
        print(f"Error saving profile: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
        return jsonify({'error': str(e)}), 500

@app.route('/stats')
def stats():
    """Get statistics about the social book"""
    total = db.get_profile_count()
    return jsonify({
        'total_profiles': total
    })

if __name__ == '__main__':
    print(f"Social Book initialized with {db.get_profile_count()} profiles")
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)

#!/usr/bin/env python3
"""
Bulk import profiles into Social Book
"""
import sys
import time
from socialbook import (
    tavily_search, extract_text_and_image, extract_company_from_text,
    summarize_bio
)
import database as db

def import_person(name):
    """Import a single person's profile"""
    print(f"\n{'='*60}")
    print(f"Importing: {name}")
    print('='*60)

    try:
        # Search the web
        query = f"{name} professional bio LinkedIn"
        url_content_pairs = tavily_search(query)

        if not url_content_pairs:
            print(f"  ❌ No results found for {name}")
            return False

        # Also search for images specifically
        print(f"  Searching for profile photo...")
        image_results = search_person_images_google(name, None)
        print(f"  Found {len(image_results)} potential images")

        # Try first few results
        for url, tavily_content in url_content_pairs[:5]:
            print(f"  Trying: {url}")

            text, img_url = extract_text_and_image(url, name)

            # Use Tavily content if scraping failed
            if not text or len(text.strip()) < 20:
                text = tavily_content

            if not text or len(text.strip()) < 10:
                print(f"    ⚠️  No text content")
                continue

            # If no image from scraping, try the image search results
            if not img_url and image_results:
                img_url = image_results[0]  # Use first image result
                print(f"    Using image search result")

            # Extract company
            company = extract_company_from_text(text, url)
            if not company:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                if not any(social in domain for social in ['linkedin.com', 'twitter.com', 'facebook.com']):
                    company = domain.replace('www.', '').split('.')[0].title()
                else:
                    company = "Company Not Listed"

            print(f"    ✓ Company: {company}")
            print(f"    ✓ Has photo: {bool(img_url)}")

            # Generate bio
            print(f"    Generating bio...")
            bio = summarize_bio(name, company, text)

            # Create snippet
            snippet = text[:200].strip()
            if len(text) > 200:
                snippet += "..."

            # Save to database
            profile_id = db.save_profile(
                name=name,
                company=company,
                bio=bio,
                photo_url=img_url,
                snippet=snippet,
                source_urls=[url],
                image_confidence=0
            )

            print(f"  ✅ Successfully imported {name} (ID: {profile_id})")
            return True

        print(f"  ❌ Could not extract valid data for {name}")
        return False

    except Exception as e:
        print(f"  ❌ Error importing {name}: {e}")
        import traceback
        traceback.print_exc()
        return False

def bulk_import(names):
    """Import multiple people"""
    print(f"\n🚀 Starting bulk import of {len(names)} profiles\n")

    success_count = 0
    fail_count = 0

    for i, name in enumerate(names, 1):
        print(f"\n[{i}/{len(names)}] ", end='')

        if import_person(name):
            success_count += 1
        else:
            fail_count += 1

        # Be polite to APIs - add delay
        if i < len(names):
            time.sleep(2)

    print(f"\n{'='*60}")
    print(f"✅ Import complete!")
    print(f"   Success: {success_count}")
    print(f"   Failed: {fail_count}")
    print(f"   Total in DB: {db.get_profile_count()}")
    print('='*60)

if __name__ == '__main__':
    # List of names to import
    names = [
        "David Barth",
        "Yishai Fox",
        "Elliot Julis",
        "Greg Kinross",
        "Jessica Vodowsky",
        "Matthew Winnick",
        "Daniel Klein",
        "Yoav Mor",
        "Avner Stepak"
    ]

    # If names provided as arguments, use those instead
    if len(sys.argv) > 1:
        names = sys.argv[1:]

    bulk_import(names)

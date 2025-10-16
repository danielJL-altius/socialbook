#!/usr/bin/env python3
"""
Initialize database with sample profiles
This runs automatically on Railway deployment
"""
import database as db

# Sample profiles to pre-populate
INITIAL_PROFILES = [
    {
        'name': 'David Barth',
        'company': 'University Health Network',
        'bio': 'Physician at University Health Network with experience in healthcare and medical practice. Located in Toronto with a strong professional network.',
        'snippet': 'Physician at University Health Network with medical expertise and healthcare experience.',
        'photo_url': None,
        'source_urls': ['https://ca.linkedin.com/in/david-barth-62354b6a']
    },
    {
        'name': 'Yishai Fox',
        'company': 'Financial Manager',
        'bio': 'Experienced Financial Manager with Global Expertise. Accomplished financial manager bringing wealth of knowledge and experience to the table.',
        'snippet': 'Experienced Financial Manager with Global Expertise bringing knowledge and experience.',
        'photo_url': None,
        'source_urls': ['https://il.linkedin.com/in/yishaifuchs']
    },
    {
        'name': 'Elliot Julis',
        'company': 'Company Not Listed',
        'bio': 'Professional with experience in various industries. Active on LinkedIn with connections across multiple sectors.',
        'snippet': 'View the profiles of professionals named Julius Elliott on LinkedIn.',
        'photo_url': None,
        'source_urls': ['https://www.linkedin.com/pub/dir/Julius/Elliott']
    },
    {
        'name': 'Greg Kinross',
        'company': 'Ceannas',
        'bio': 'Client Director at Ceannas with experience in education and business development. Located in Greater Edinburgh Area with 500+ connections on LinkedIn.',
        'snippet': 'Client Director at Ceannas with expertise in education and Preston Lodge location.',
        'photo_url': None,
        'source_urls': ['https://uk.linkedin.com/in/greg-kinross-4237b013']
    },
    {
        'name': 'Jessica Vodowsky',
        'company': 'Framework',
        'bio': 'Enthusiastic People Champion at Framework who is very interested in working to learn. Experience at UC Irvine with strong professional background.',
        'snippet': 'An enthusiastic People Champion at Framework who is very interested in working to learn.',
        'photo_url': None,
        'source_urls': ['https://www.linkedin.com/in/jessica-vo-839121161/']
    },
    {
        'name': 'Matthew Winnick',
        'company': 'True Classic',
        'bio': 'Co-Founder at True Classic, Partner at Luminous Solar & Kilowatt Capital Los Angeles, US with 500 connections and 6155 followers. Experienced entrepreneur and business leader.',
        'snippet': 'Matthew Winnick Co-Founder at True Classic, Partner at Luminous Solar & Kilowatt Capital.',
        'photo_url': None,
        'source_urls': ['https://www.linkedin.com/in/matthewwinnick']
    },
    {
        'name': 'Daniel Klein',
        'company': 'Formation Bio',
        'bio': 'Experience at Formation Bio with education from University of Alabama. Located in Auburn with 500+ connections on LinkedIn.',
        'snippet': 'Experience: Formation Bio. Education: University of Alabama. Location: Auburn.',
        'photo_url': None,
        'source_urls': ['https://www.linkedin.com/in/dmklein']
    },
    {
        'name': 'Yoav Mor',
        'company': 'Tel Aviv University',
        'bio': 'Professional based in Israel with connections to Tel Aviv University and CropX. Active on LinkedIn with strong professional network.',
        'snippet': 'מיקום: Israel-Tel Aviv University. חיבור: CropX. חיבור: +500 LinkedIn.',
        'photo_url': None,
        'source_urls': ['https://il.linkedin.com/in/yoavmor1']
    },
    {
        'name': 'Avner Stepak',
        'company': 'Investment Management',
        'bio': 'Accomplished professional based in the Tel Aviv District with robust background in investment management gained through tenure at Meitav. Holds academic pedigree from Kellogg-Recanati with essential skills in finance and business strategy. With over 500 connections on LinkedIn, has established strong professional network.',
        'snippet': 'חיבור: Meitav. חיבור: Kellogg-Recanati. מיקום: Tel Aviv District. חיבור: +500.',
        'photo_url': None,
        'source_urls': ['https://il.linkedin.com/in/avner-stepak-4b42981']
    }
]

def initialize_profiles():
    """Add initial profiles if database is empty"""
    current_count = db.get_profile_count()
    print(f"Current profile count: {current_count}")

    if current_count == 0:
        print("Initializing database with sample profiles...")
        for profile in INITIAL_PROFILES:
            try:
                profile_id = db.save_profile(
                    name=profile['name'],
                    company=profile['company'],
                    bio=profile['bio'],
                    photo_url=profile['photo_url'],
                    snippet=profile['snippet'],
                    source_urls=profile['source_urls'],
                    image_confidence=0
                )
                print(f"  ✓ Added {profile['name']} (ID: {profile_id})")
            except Exception as e:
                print(f"  ✗ Failed to add {profile['name']}: {e}")

        print(f"\n✅ Database initialized with {len(INITIAL_PROFILES)} profiles")
    else:
        print("Database already has profiles, skipping initialization")

if __name__ == '__main__':
    initialize_profiles()

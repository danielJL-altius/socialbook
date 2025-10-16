import sqlite3
from datetime import datetime
import json

DB_PATH = 'socialbook.db'

def init_db():
    """Initialize the database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            bio TEXT,
            photo_url TEXT,
            snippet TEXT,
            source_urls TEXT,
            image_confidence INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(name, company)
        )
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_name ON profiles(name)
    ''')

    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_company ON profiles(company)
    ''')

    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS profiles_fts USING fts5(
            name, company, bio, snippet, content=profiles, content_rowid=id
        )
    ''')

    # Trigger to keep FTS index updated
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS profiles_ai AFTER INSERT ON profiles BEGIN
            INSERT INTO profiles_fts(rowid, name, company, bio, snippet)
            VALUES (new.id, new.name, new.company, new.bio, new.snippet);
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS profiles_au AFTER UPDATE ON profiles BEGIN
            UPDATE profiles_fts SET name=new.name, company=new.company,
                bio=new.bio, snippet=new.snippet WHERE rowid=new.id;
        END
    ''')

    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS profiles_ad AFTER DELETE ON profiles BEGIN
            DELETE FROM profiles_fts WHERE rowid=old.id;
        END
    ''')

    conn.commit()
    conn.close()

def search_profiles(query):
    """Search profiles in database using full-text search"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Full-text search
    cursor.execute('''
        SELECT p.* FROM profiles p
        JOIN profiles_fts ON p.id = profiles_fts.rowid
        WHERE profiles_fts MATCH ?
        ORDER BY rank
        LIMIT 20
    ''', (query,))

    results = [dict(row) for row in cursor.fetchall()]

    # If no FTS results, try LIKE search
    if not results:
        cursor.execute('''
            SELECT * FROM profiles
            WHERE name LIKE ? OR company LIKE ?
            ORDER BY created_at DESC
            LIMIT 20
        ''', (f'%{query}%', f'%{query}%'))
        results = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Parse source_urls from JSON
    for result in results:
        if result.get('source_urls'):
            try:
                result['source_urls'] = json.loads(result['source_urls'])
            except:
                result['source_urls'] = []

    return results

def get_all_profiles(limit=50, offset=0):
    """Get all profiles for browsing"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM profiles
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    ''', (limit, offset))

    results = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Parse source_urls from JSON
    for result in results:
        if result.get('source_urls'):
            try:
                result['source_urls'] = json.loads(result['source_urls'])
            except:
                result['source_urls'] = []

    return results

def get_profile_count():
    """Get total number of profiles"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM profiles')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def save_profile(name, company, bio, photo_url, snippet, source_urls, image_confidence=0):
    """Save or update a profile"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Convert source_urls list to JSON
    source_urls_json = json.dumps(source_urls) if isinstance(source_urls, list) else json.dumps([])

    cursor.execute('''
        INSERT INTO profiles (name, company, bio, photo_url, snippet, source_urls, image_confidence)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name, company) DO UPDATE SET
            bio = excluded.bio,
            photo_url = excluded.photo_url,
            snippet = excluded.snippet,
            source_urls = excluded.source_urls,
            image_confidence = excluded.image_confidence,
            updated_at = CURRENT_TIMESTAMP
    ''', (name, company, bio, photo_url, snippet, source_urls_json, image_confidence))

    profile_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return profile_id

def get_profile_by_id(profile_id):
    """Get a specific profile by ID"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM profiles WHERE id = ?', (profile_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        result = dict(row)
        if result.get('source_urls'):
            try:
                result['source_urls'] = json.loads(result['source_urls'])
            except:
                result['source_urls'] = []
        return result
    return None

# Initialize database on import
init_db()

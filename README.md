# Social Book - Professional Directory

A smart professional directory that automatically builds and maintains profiles by searching the web.

## Features

- **Smart Search**: Search for anyone by name - checks database first, then searches the web
- **Auto-Add**: Profiles not in the directory are automatically found and added
- **Browse Directory**: View all profiles in a beautiful card-based interface
- **AI-Powered**: Uses AI to generate professional bios from multiple sources
- **Image Validation**: Ensures profile photos are actual headshots, not logos/illustrations
- **Full-Text Search**: Fast searching across names, companies, and bios

## How It Works

1. **Search**: Enter a person's name
2. **Database Check**: Searches local SQLite database first
3. **Web Search**: If not found, searches web using Tavily API
4. **AI Processing**: Extracts info and generates professional bio using OpenAI
5. **Auto-Save**: Adds profile to database for future searches
6. **Browse**: All profiles accessible in the Browse tab

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create `.env` file with your API keys:
```
TAVILY_API_KEY=your_tavily_key
OPENAI_API_KEY=your_openai_key
```

3. Run the application:
```bash
python socialbook.py
```

4. Open browser to: http://localhost:5001

## Bulk Import

To add multiple profiles at once:

```bash
python bulk_import.py "John Doe" "Jane Smith" "Bob Johnson"
```

Or edit the names list in `bulk_import.py` and run:

```bash
python bulk_import.py
```

## Database

- Uses SQLite with full-text search (FTS5)
- Automatically created on first run as `socialbook.db`
- Schema includes: name, company, bio, photo_url, snippet, source_urls
- Supports deduplication by (name + company)

## API Endpoints

### Search
`POST /search`
- Form data: `name`, `company` (optional)
- Returns profile or candidates

### Browse
`GET /browse?page=1`
- Returns paginated profiles

### Save Profile
`POST /save_profile`
- JSON data: candidate object
- Saves to database

### Stats
`GET /stats`
- Returns total profile count

## Files

- `socialbook.py` - Main Flask application
- `database.py` - SQLite database operations
- `ai_bio_scraper.py` - Web scraping and AI functions
- `bulk_import.py` - Bulk profile import script
- `templates/socialbook.html` - Frontend interface

## Technologies

- **Backend**: Flask, Python 3.12+
- **Database**: SQLite with FTS5
- **Web Scraping**: BeautifulSoup, Requests
- **Search API**: Tavily
- **AI**: OpenAI GPT-4o-mini
- **Frontend**: Vanilla JavaScript, CSS Grid

## Notes

- LinkedIn blocks direct scraping - uses Tavily's extracted content
- Rate limited to be respectful to APIs (2 second delay in bulk import)
- Images validated to reject logos/illustrations
- Profiles cached permanently in DB for instant access

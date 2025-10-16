# Deploy Social Book to the Web - FAST!

## Option 1: Railway.app (FASTEST - 2 minutes)

1. Go to https://railway.app
2. Click "Start a New Project"
3. Select "Deploy from GitHub repo"
4. Authorize GitHub and select this repository
5. Add environment variables:
   - `TAVILY_API_KEY` = your_tavily_key
   - `OPENAI_API_KEY` = your_openai_key
6. Click "Deploy"
7. Once deployed, click "Generate Domain" to get public URL

**URL will be**: `https://your-app.railway.app`

---

## Option 2: Render.com (FREE - 3 minutes)

1. Go to https://render.com
2. Click "New +" → "Web Service"
3. Connect GitHub repository
4. Settings:
   - Name: `socialbook`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn socialbook:app`
5. Add environment variables:
   - `TAVILY_API_KEY`
   - `OPENAI_API_KEY`
6. Click "Create Web Service"

**URL will be**: `https://socialbook.onrender.com`

---

## Option 3: Heroku (Classic - 5 minutes)

```bash
# Install Heroku CLI
# Then run:
heroku login
heroku create socialbook-app
heroku config:set TAVILY_API_KEY=your_key
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
heroku open
```

---

## Quick Push to GitHub

```bash
# Create new repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/socialbook.git
git branch -M main
git push -u origin main
```

Then use Railway or Render to deploy from GitHub!

---

## Environment Variables Needed

```
TAVILY_API_KEY=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
OPENAI_API_KEY=your_openai_key
```

---

## Notes

- Database (SQLite) will be created automatically on first run
- Profiles will persist in `/data` volume (configure in Railway/Render)
- Free tiers have enough resources for demo

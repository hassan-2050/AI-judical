# Pakistan Judiciary Case Database

A full-stack web application for scraping, storing, searching, and analyzing Pakistani court cases. Built with **Flask** (backend), **MongoDB** (database), **Next.js 14** (frontend), and real web scrapers targeting Pakistani judiciary websites.

---

## Features

### Backend
- **Real Web Scrapers** - Scrape cases from Supreme Court of Pakistan, Lahore High Court, and Pakistan Code
- **Scheduled Scraping** - APScheduler runs scrapers on configurable cron schedules
- **REST API** - Full CRUD for cases, advanced search with filters, analytics aggregations
- **Authentication** - JWT-based auth with bcrypt password hashing, role-based access (user / admin / scraper_admin)
- **Analytics** - Dashboard stats, timeline data, court breakdowns, top judges rankings

### Frontend
- **Dashboard** - Stats overview, recent cases, scraper status at a glance
- **Case Browser** - Paginated, filterable case database with card layout
- **Case Detail** - Full case view with parties, judges, cited references, tabs for summary / full text
- **Advanced Search** - Full-text search with court, judge, year range, type, and status filters
- **Analytics** - Interactive charts (pie, bar, line) for court distribution, timeline, judge rankings
- **Scraper Manager** - Run scrapers on-demand, view job history, real-time log viewer
- **Auth** - Login / Register pages with form validation

---

## Project Structure

```
judicary_backend/                # Flask backend
  app.py                         # Application factory
  config.py                      # Environment-based config
  requirements.txt               # Python dependencies
  .env.example                   # Environment variables template
  models/
    auth_model.py                # Auth (email, password, roles)
    user_model.py                # User profiles
    case_model.py                # Court cases with text indexes
    scrape_job.py                # Scrape job tracking + logs
  routes/
    auth_routes.py               # /api/auth/*
    case_routes.py               # /api/cases/*
    scraper_routes.py            # /api/scraper/*
    search_routes.py             # /api/search/*
    analytics_routes.py          # /api/analytics/*
  scrapers/
    base_scraper.py              # Abstract base with helpers
    supreme_court_scraper.py     # supremecourt.gov.pk
    lahore_hc_scraper.py         # lhc.gov.pk
    case_law_scraper.py          # pakistancode.gov.pk
    scheduler.py                 # APScheduler cron jobs

judiciary_frontend/              # Next.js 14 frontend
  src/app/
    page.tsx                     # Landing page
    dashboard/page.tsx           # Dashboard
    cases/page.tsx               # Case browser
    cases/[id]/page.tsx          # Case detail
    search/page.tsx              # Advanced search
    analytics/page.tsx           # Charts and stats
    scraper/page.tsx             # Scraper manager
    login/page.tsx               # Login
    register/page.tsx            # Registration
  src/components/                # Reusable components
  src/lib/api.ts                 # Axios API client
  src/types/index.ts             # TypeScript interfaces
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (local or MongoDB Atlas)

### 1. Backend Setup

```bash
cd judicary_backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env         # Windows

# Edit .env with your MongoDB URL and secrets
# Then run:
python app.py
```

Backend runs on http://localhost:5000

### 2. Frontend Setup

```bash
cd judiciary_frontend
npm install
npm run dev
```

Frontend runs on http://localhost:3000

---

## API Endpoints

### Auth
- POST /api/auth/register - Register new user
- POST /api/auth/login - Login, returns JWT
- GET  /api/auth/me - Get current user (auth required)
- PUT  /api/auth/me - Update profile (auth required)

### Cases
- GET    /api/cases - List cases (paginated, filterable)
- GET    /api/cases/:id - Get case details
- POST   /api/cases - Create case (auth required)
- PUT    /api/cases/:id - Update case (auth required)
- DELETE /api/cases/:id - Delete case (auth required)
- GET    /api/cases/stats - Case statistics

### Search
- GET /api/search - Advanced search with filters
- GET /api/search/filters - Available filter values
- GET /api/search/suggest - Autocomplete suggestions

### Scraper
- POST /api/scraper/run - Start a scraper
- GET  /api/scraper/status - Scheduler status
- GET  /api/scraper/jobs - Job history
- GET  /api/scraper/available - Available scrapers

### Analytics
- GET /api/analytics/dashboard - Dashboard stats
- GET /api/analytics/timeline?year=2024 - Monthly case counts
- GET /api/analytics/courts - Per-court breakdown
- GET /api/analytics/judges?limit=15 - Top judges

---

## Scrapers

| Scraper | Source | Schedule |
|---------|--------|----------|
| Supreme Court | supremecourt.gov.pk | Daily 2:00 AM |
| Lahore High Court | lhc.gov.pk | Daily 3:00 AM |
| Pakistan Code | pakistancode.gov.pk | Weekly Sunday 1:00 AM |

Scrapers can also be triggered manually from the Scraper page or via API.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, Flask 3.0, MongoEngine |
| Database | MongoDB |
| Auth | PyJWT, bcrypt |
| Scraping | BeautifulSoup4, lxml, Requests, Selenium |
| Scheduling | APScheduler |
| Frontend | Next.js 14, React 18, TypeScript |
| Styling | Tailwind CSS 3.4 |
| Charts | Recharts |

---

## Environment Variables

### Backend (.env)
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret
MONGODB_URL=mongodb://localhost:27017/judiciary_db
CORS_ORIGINS=http://localhost:3000
SCRAPER_ENABLED=true
SCRAPER_MAX_PAGES=50
```

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

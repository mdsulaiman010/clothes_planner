# Clothes Planner

A full-stack digital wardrobe app with AI-powered clothing classification, virtual try-on, and a context-aware fashion assistant.

---

## Features

- **Wardrobe Management** — Upload clothing photos; items are automatically classified by category (tops, bottoms, footwear, outerwear, accessories) using a vision AI model.
- **Virtual Try-On** — Upload a selfie and select a clothing item to see yourself wearing it, powered by Fashn.ai.
- **AI Fashion Assistant** — Chat with a Google Gemini-powered assistant that understands which page you're on and which items you've selected.
- **Authentication** — JWT-based login and registration with Supabase as the user store.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + TypeScript, Vite, React Router v6, Axios |
| Backend | Python, Flask, Flask-CORS |
| User Auth | Supabase |
| Image Storage | AWS S3 (presigned URLs) |
| Clothing DB | MongoDB |
| Image Classification | Moondream (vision model, custom endpoint) |
| Virtual Try-On | Fashn.ai API |
| AI Chat | Google Gemini 2.5 Flash |

---

## Project Structure

```
clothes_planner/
├── backend/
│   ├── app.py                      # Flask app factory & blueprint registration
│   ├── config.py                   # Loads env vars, exports settings
│   ├── requirements.txt
│   ├── auth/
│   │   ├── routes.py               # POST /auth/login, /register, /refresh
│   │   ├── utils.py                # Password hashing, JWT encode/decode
│   │   └── decorators.py          # @jwt_required decorator
│   ├── wardrobe/
│   │   ├── routes.py               # Upload, list, delete clothing items
│   │   └── services.py
│   ├── chat/
│   │   ├── routes.py               # Send message, get/clear history
│   │   ├── gemini_service.py       # Gemini API wrapper
│   │   └── context.py             # Builds context-aware system prompts
│   ├── tryon/
│   │   ├── routes.py               # Generate try-on, poll result
│   │   ├── factory.py             # Selects provider (fashn / local)
│   │   ├── fashn_provider.py       # Fashn.ai integration
│   │   └── local_provider.py      # Local fallback provider
│   ├── services/
│   │   ├── db_functions.py        # MongoDB + Supabase helpers
│   │   ├── genai_functions.py     # Moondream classification calls
│   │   └── s3_service.py          # S3 upload / presigned URL / delete
│   └── prompts/
│       ├── clothing_hierarchy.json # Taxonomy of clothing categories
│       ├── classification_prompt1.txt
│       └── classifier_sys_prompt.txt
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.tsx                 # Router + provider tree
    │   ├── api/
    │   │   ├── client.ts          # Axios instance with JWT interceptor
    │   │   ├── auth.ts
    │   │   ├── wardrobe.ts
    │   │   ├── tryon.ts
    │   │   └── chat.ts
    │   ├── context/
    │   │   ├── AuthContext.tsx
    │   │   ├── WardrobeContext.tsx
    │   │   └── ChatContext.tsx
    │   ├── components/
    │   │   ├── ImageUploader.tsx  # Drag-drop + camera capture
    │   │   ├── ClothingGrid.tsx
    │   │   ├── ClothingCard.tsx
    │   │   ├── CategoryFilter.tsx
    │   │   ├── ChatSidebar.tsx
    │   │   ├── TryOnPreview.tsx
    │   │   ├── Navbar.tsx
    │   │   └── Layout.tsx
    │   ├── pages/
    │   │   ├── LoginPage.tsx
    │   │   ├── RegisterPage.tsx
    │   │   ├── UploadPage.tsx
    │   │   ├── WardrobePage.tsx
    │   │   └── TryOnPage.tsx
    │   └── styles/
    │       └── index.css
```

---

## API Reference

### Auth — `/api/auth`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register `{ username, password, mobile_number }` |
| POST | `/auth/login` | — | Login `{ username, password }` → returns JWT |
| POST | `/auth/refresh` | ✓ | Refresh access token |

### Wardrobe — `/api/wardrobe`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/wardrobe/upload` | ✓ | Upload image files; returns classified items |
| GET | `/wardrobe/items` | ✓ | List items. Query: `category`, `skip`, `limit` |
| DELETE | `/wardrobe/items/<item_id>` | ✓ | Delete item and its S3 object |
| GET | `/wardrobe/categories` | — | Returns the full clothing taxonomy |

### Chat — `/api/chat`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/chat/message` | ✓ | Send `{ message, page_context }` → AI reply |
| GET | `/chat/history` | ✓ | Retrieve full conversation history |
| DELETE | `/chat/history` | ✓ | Clear conversation history |

`page_context` shape:
```json
{ "page": "wardrobe", "selectedItems": ["item_id"], "category": "tops" }
```

### Try-On — `/api/tryon`

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/tryon/generate` | ✓ | Submit job `{ selfie_image_b64, clothing_item_id, provider? }` → `job_id` |
| GET | `/tryon/result/<job_id>` | ✓ | Poll status. Query: `provider`. Returns image URL when done |

---

## Environment Variables

Create a `.env` file in the project root:

```env
# JWT
SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# MongoDB (clothing items + chat history)
MONGODB_ID=your-mongo-username
MONGODB_PW=your-mongo-password
MONGODB_LOOKBOOK_CLUSTER=mongodb+srv://<user>:<pw>@your-cluster.mongodb.net/

# Supabase (user accounts)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key

# AWS S3 (image storage)
S3_BUCKET_NAME=your-bucket-name
S3_BUCKET_REGION=ap-southeast-1
CREDENTIALS_DIR=/path/to/aws/credentials.xlsx

# Google Gemini (AI chat)
GEMINI_API_KEY=your-gemini-api-key

# Moondream (image classification)
MOONDREAM_ENDPOINT=https://your-moondream-endpoint.modal.run/v1

# Fashn.ai (virtual try-on)
FASHN_API_KEY=your-fashn-api-key
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- MongoDB Atlas cluster
- Supabase project
- AWS S3 bucket
- API keys for Gemini, Fashn.ai, and a Moondream endpoint

### 1 — Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Runs on `http://localhost:5000`.

### 2 — Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:5173`. API calls are proxied to `/api` — configure the target in `vite.config.ts` if needed.

### Production build

```bash
# Backend
gunicorn "app:create_app()" -w 4

# Frontend
npm run build   # outputs to dist/
```

---

## Database Schema

### MongoDB — `clothes` database

**`items` collection**
```
_id           ObjectId
uploadedBy    string        (username)
mainCategory  string        (tops | bottomwear | footwear | outerwear | accessories)
subCategory   string        (e.g. "t-shirt", "jeans")
format        string        (image MIME type)
s3_key        string        (S3 object key)
```

**`chat_sessions` collection**
```
username      string
messages      [{ role, content, timestamp }]
```

### Supabase — `users` table

```
username       text (unique)
password       text (SHA-256 hashed)
mobile_number  text
```

---

## How Classification Works

1. Image is uploaded to S3.
2. A presigned URL is passed to the Moondream vision model endpoint.
3. Moondream returns a category prediction matched against `prompts/clothing_hierarchy.json`.
4. The result is stored in MongoDB with `mainCategory` and `subCategory`.

## How Try-On Works

1. Client sends a base64 selfie and a `clothing_item_id`.
2. Backend fetches the item's S3 URL and submits a job to Fashn.ai.
3. A `job_id` is returned immediately.
4. Client polls `GET /tryon/result/<job_id>` until the status is `completed`.
5. The resulting image URL is displayed in `TryOnPreview`.

---

## Known Limitations

- Password hashing uses SHA-256 — consider migrating to bcrypt or argon2 for stronger security.
- No rate limiting on API endpoints.
- CORS is open to all origins (`*`) — restrict to your frontend domain in production.
- Try-on polling is client-driven; there is no webhook or server-sent event mechanism.

# Book Club Frontend

Next.js 14 application with CopilotKit integration for AI-powered book club assistance.

## Tech Stack

- **Next.js 14** (App Router)
- **TypeScript**
- **Tailwind CSS**
- **CopilotKit** (AI assistant framework)

## Development

### Local (outside Docker)

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Edit .env to use localhost:8010 for API
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8010

# Run dev server
npm run dev
```

Visit http://localhost:8000

### Docker Compose

The frontend is configured to run in Docker via `docker-compose.yml`:

```bash
# From project root
docker-compose up bookclub-app
```

The service will:
- Install dependencies on startup
- Run `next dev` on port 8000
- Connect to `bookclub-server` on port 8010

## Environment Variables

- `NEXT_PUBLIC_API_BASE_URL`: FastAPI backend URL
  - Docker: `http://bookclub-server:8010`
  - Local: `http://localhost:8010`

## CopilotKit Integration

The app includes:
- `CopilotProvider` wrapper in `components/CopilotProvider.tsx`
- `CopilotSidebar` for chat interface
- Runtime configured to call `/copilotkit` endpoint on FastAPI

**Note**: You need to implement the `/copilotkit` endpoint in the FastAPI backend to handle CopilotKit requests. See [CopilotKit docs](https://docs.copilotkit.ai/) for backend integration.

## Project Structure

```
src/book_club/app/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with CopilotProvider
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   └── CopilotProvider.tsx
├── package.json
├── tsconfig.json
├── next.config.js
├── tailwind.config.js
└── .env.example
```

## Next Steps

1. Implement `/copilotkit` endpoint in FastAPI backend
2. Add CopilotKit actions and hooks for book club features
3. Build UI for flashcard generation, SRS, and Anki export
4. Add authentication if needed

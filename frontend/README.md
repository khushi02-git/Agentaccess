# AgentAccess Frontend

Web dashboard for monitoring and controlling an AI agent that interacts with databases and system resources.

> **Status:** Phase 1 - static demo using dummy data shaped like the future API responses. Backend integration is next.

## Pages

- **Dashboard**: overview of agent activity and key stats
- **Agent**: agent state and active permission profile
- **System Monitor**: CPU, memory and resource usage
- **Logs**: query logs with search and filters
- **Audit Trail**: full event stream with event-type filter
- **Violations**: triage view with severity and status

## Tech stack

React, Vite, Tailwind CSS v4, React Router, Recharts, Lucide icons, Motion. Linting with Oxlint.

## Run locally

Requires Node.js.

    cd frontend
    npm install
    npm run dev

Open http://localhost:5173

## Project structure

    src/
      components/   reusable UI pieces
      data/         dummy data (replaced by FastAPI calls later)
      layout/       app shell and sidebar
      pages/        one file per page
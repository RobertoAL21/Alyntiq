# ADR 001 — Use React SPA for the Alyntiq Frontend

## Status

Accepted

## Context

Alyntiq requires an interactive dashboard for:

- portfolio monitoring
- trading activity
- strategy comparison
- model analysis
- financial charts
- real-time market information

The application does not currently require server-side rendering or SEO-oriented rendering.

## Options Considered

### Next.js

Provides React with server-side rendering, routing and full-stack capabilities.

### React + Vite

Provides a lightweight standalone frontend that communicates with the FastAPI backend.

## Decision

Use:

- React
- TypeScript
- Vite
- React Router
- Tailwind CSS

The frontend will be implemented as a Single Page Application.

FastAPI remains responsible for backend APIs and business logic.

## Reasons

Alyntiq is primarily an authenticated application/dashboard rather than a content-oriented website.

A standalone React SPA keeps a clear separation between:

Frontend → React

Backend → FastAPI

ML / Trading → Python

This also avoids introducing Next.js server-side functionality that Alyntiq does not currently require.

## Consequences

The frontend and backend are independent applications.

The frontend communicates with FastAPI through REST APIs and WebSockets.

Client-side routing is handled by React Router.

Deployment must support SPA routing correctly.

If SSR or other Next.js-specific capabilities become necessary in the future, this decision can be revisited through another ADR.
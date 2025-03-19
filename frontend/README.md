# Grafana Dashboard Generator - Frontend

This is the frontend component for the Grafana Dashboard Generator, built with Next.js using a hexagonal architecture. It provides an interactive interface for generating Grafana dashboards from natural language prompts.

## Features

- **Interactive Prompt Editor**: Compose natural language prompts to describe the desired dashboard
- **Multiple LLM Support**: Choose from available LLMs including OpenAI, Claude, and others
- **Visual Guidance**: On-screen tips and examples for creating effective dashboard prompts
- **JSON Preview**: View and validate generated dashboard JSON
- **Human-in-the-Loop**: Edit and correct dashboard JSON when validation fails
- **Responsive UI**: Modern, mobile-friendly interface

## Hexagonal Architecture

The project follows a hexagonal (ports and adapters) architecture:

- `app/adapters`: External adapters for APIs, storage, etc.
- `app/components`: Reusable UI components
- `app/domain`: Domain logic and services
- `app/hooks`: Custom React hooks
- `app/lib`: Utility functions and libraries
- `app/types`: TypeScript type definitions
- `app/ui/features`: Feature-specific UI components

## Getting Started

### Prerequisites

- Node.js 16+
- npm or yarn

### Installation

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create a `.env.local` file with the backend API URL:

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

3. Start the development server:

```bash
npm run dev
```

The application will be available at http://localhost:3000.

## Building for Production

To build the application for production:

```bash
npm run build
```

To start the production server:

```bash
npm start
```

## Development

- `npm run dev`: Start development server
- `npm run build`: Build for production
- `npm start`: Start production server
- `npm run lint`: Run ESLint

## Project Structure

- `app/`: Main application code
  - `adapters/`: External adapters (API clients, etc.)
  - `components/`: Reusable UI components
  - `domain/`: Domain logic and services
    - `services/`: Business logic services
    - `ports/`: Interface definitions
  - `hooks/`: Custom React hooks
  - `lib/`: Utility functions
  - `types/`: TypeScript type definitions
  - `ui/features/`: Feature-specific UI components
- `public/`: Static assets

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

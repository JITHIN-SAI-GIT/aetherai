# Nova AI — Premium AI Chatbot Frontend

A production-ready, futuristic AI assistant interface built with React 19, Vite, Tailwind CSS, TypeScript, and Framer Motion. Inspired by the best of ChatGPT, Claude, Perplexity, Apple, Linear, and Raycast — but entirely original in design.

> **Note:** This is a frontend-only demo. All AI responses are simulated with dummy data — no backend required.

## Features

- **Premium dark theme** with glassmorphism, soft gradients, and animated background
- **Floating glowing orbs** and particle effects that respond to mouse movement
- **Collapsible sidebar** with smooth animation, pinned chats, and search
- **Welcome screen** with time-based greeting and beautiful suggestion cards
- **Modern chat interface** with:
  - Right-aligned gradient user bubbles
  - Left-aligned assistant messages with avatar and timestamp
  - Markdown rendering with syntax-highlighted code blocks
  - Copy, regenerate, like, and dislike actions per message
  - Typing animation with streaming effect
- **Floating input bar** with auto-resize, attach, microphone, send/stop buttons, and focus glow
- **Settings dialog** with theme accent picker, language, temperature, model selector, memory toggle, export, and clear chat
- **Fully responsive** — desktop, tablet, and mobile with a slide-in drawer sidebar
- **60 FPS animations** powered by Framer Motion

## Tech Stack

| Category | Technology |
|----------|-----------|
| Framework | React 19 |
| Build Tool | Vite 5 |
| Styling | Tailwind CSS 3 |
| Language | TypeScript 5 |
| Animation | Framer Motion 11 |
| Icons | Lucide React |
| Markdown | react-markdown + remark-gfm + rehype-raw |
| Syntax Highlighting | react-syntax-highlighter (Prism) |

## Getting Started

### Prerequisites

- Node.js 18+ (recommended 20+)
- npm 9+

### Installation

```bash
# 1. Install dependencies
npm install

# 2. Start the development server
npm run dev
```

The app will be available at `http://localhost:5173`.

### Other Scripts

```bash
# Production build
npm run build

# Preview the production build
npm run preview

# Type checking
npm run typecheck

# Lint
npm run lint
```

## Project Structure

```
src/
├── components/
│   ├── ui/           # Reusable primitives (Button, Card, Dialog, Slider, Switch, etc.)
│   ├── layout/       # AppShell, AnimatedBackground, MobileTopBar
│   ├── chat/         # ChatArea, Message, ChatInput, CodeBlock, Markdown
│   ├── sidebar/      # Sidebar, SidebarHeader, SidebarFooter, ConversationList
│   ├── dialogs/      # SettingsDialog
│   └── pages/        # WelcomeScreen
├── hooks/            # useChat, useSettings, useGreeting, useMediaQuery, useMouseGlow, useAutoResize
├── services/         # dummyData (simulated AI responses & conversations)
├── utils/            # cn, time, id, accent
├── types/            # TypeScript type definitions
└── App.tsx           # Root with lazy-loaded AppShell
```

## Design Highlights

- **Color system:** Teal/cyan primary on deep charcoal background, with 5 switchable accent themes (Teal, Azure, Emerald, Amber, Rose) — no purple/indigo defaults
- **Glassmorphism:** Layered translucent panels with backdrop blur throughout
- **Typography:** Inter for UI, JetBrains Mono for code
- **Spacing:** Consistent 8px system
- **Micro-interactions:** Hover states, button ripples, scale transitions, and layout animations on every interactive element

## Customization

- **Accent color:** Open Settings and pick from 5 accent themes — the entire UI updates instantly via CSS variables
- **Temperature slider:** Adjust the simulated "creativity" (visual only in this demo)
- **Model selector:** Choose between Nova Pro, Air, Max, and Mini (visual only)
- **Memory toggle:** Simulated on/off switch

## Data Persistence

Chat history and settings are saved to `localStorage`, so your conversations persist across page reloads. No backend or database is used.

## License

MIT — Free to use for hackathons, portfolios, and learning.

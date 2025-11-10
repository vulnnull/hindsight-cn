# Memory Control Plane

Control plane UI for the temporal semantic memory system built with Next.js, React, TypeScript, Tailwind CSS, and Cytoscape.js.

## Overview

The control plane is a modern web application that provides a comprehensive UI for managing and visualizing temporal semantic memories. It acts as a proxy between the browser and the Python FastAPI dataplane, eliminating CORS issues and providing a clean separation of concerns.

## Architecture

```
Browser ←→ Control Plane (Next.js) ←→ Dataplane (Python FastAPI)
```

The control plane:
- Serves the React UI to the browser
- Provides Next.js API routes (`/api/*`) that proxy requests to the dataplane
- Handles client-side state management and visualization
- Eliminates CORS issues by serving both UI and API from the same origin

## Features

### 🔍 Search Debug (Most Important)
- **Multi-pane search interface**: Add multiple search panes for comparison
- **Interactive search controls**: Query, fact type, thinking budget, reranker selection, max tokens
- **Phase-based visualization**: Four phases of the retrieval pipeline
  - **1. Retrieval**: View results from each method (Semantic, BM25, Graph, Temporal) with ranks and scores
  - **2. RRF Merge**: See how Reciprocal Rank Fusion combines rankings from different methods
  - **3. Reranking**: Compare before/after reranking with rank changes highlighted (blue = improved)
  - **4. Final Results**: Detailed score breakdown with activation, similarity, recency, frequency ranks
- **Comprehensive stats**: Nodes visited, entry points, budget usage, results count, duration
- **Trace visualization**: See exactly how each retrieval method performs and contributes

### 📊 Data Visualization
- **World Facts**: View and explore general knowledge memories
- **Agent Facts**: Track agent actions and activities
- **Opinions**: Monitor agent beliefs and perspectives
- **Documents**: Manage source documents

Each fact type supports:
- Interactive graph visualization with Cytoscape.js (circle, grid, force-directed layouts)
- Searchable table view with filtering
- Real-time data loading

### 💭 Think Interface
- Ask questions to the AI agent
- View source facts used (world, agent, opinions)
- See newly formed opinions with confidence scores
- Configurable thinking budget

### ➕ Add Memory
- Submit new memories with context
- Support for event dates and document metadata
- Sync or async processing options
- Upsert capability for updates

### 📈 Statistics & Operations
- Real-time memory statistics (nodes, links, documents)
- Breakdown by fact type and link type
- Async operation monitoring (pending/failed)
- Auto-refresh every 5 seconds

## Getting Started

### Prerequisites

- Node.js 18.x or later
- A running dataplane API server (Python FastAPI)

### Installation

```bash
npm install
```

### Configuration

Configure the dataplane URL in `.env.local`:

```bash
cp .env.local.example .env.local
```

Edit `.env.local`:

```env
DATAPLANE_API_URL=http://localhost:8080
```

### Development

**Terminal 1 - Start Dataplane:**
```bash
# From project root
./scripts/start-server.sh
```

**Terminal 2 - Start Control Plane:**
```bash
cd control-plane
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Tech Stack

- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Visualization**: Cytoscape.js
- **State Management**: React Context API
- **API**: Next.js API Routes (proxy to dataplane)

## Project Structure

```
control-plane/
├── src/
│   ├── app/
│   │   ├── api/                    # API routes (proxy to dataplane)
│   │   │   ├── agents/            # GET /api/agents
│   │   │   ├── graph/             # GET /api/graph
│   │   │   ├── list/              # GET /api/list
│   │   │   ├── search/            # POST /api/search
│   │   │   ├── think/             # POST /api/think
│   │   │   ├── memories/
│   │   │   │   ├── batch/         # POST /api/memories/batch
│   │   │   │   └── batch_async/   # POST /api/memories/batch_async
│   │   │   ├── documents/
│   │   │   │   ├── route.ts       # GET /api/documents
│   │   │   │   └── [documentId]/  # GET /api/documents/:id
│   │   │   ├── stats/
│   │   │   │   └── [agentId]/     # GET /api/stats/:id
│   │   │   └── operations/
│   │   │       └── [agentId]/     # GET /api/operations/:id
│   │   ├── dashboard/
│   │   │   └── page.tsx           # Main dashboard
│   │   ├── layout.tsx             # Root layout
│   │   ├── page.tsx               # Home (redirects to dashboard)
│   │   └── globals.css            # Global styles
│   ├── components/
│   │   ├── agent-selector.tsx     # Agent dropdown
│   │   ├── data-view.tsx          # Graph/table visualization
│   │   ├── documents-view.tsx     # Document management
│   │   ├── think-view.tsx         # AI thinking interface
│   │   ├── add-memory-view.tsx    # Memory submission form
│   │   └── stats-view.tsx         # Statistics dashboard
│   └── lib/
│       ├── agent-context.tsx      # Global agent state
│       ├── api.ts                 # API client
│       └── utils.ts               # Utilities
├── .env.local                      # Environment config
└── package.json
```

## API Routes

All control plane API routes proxy to the dataplane:

| Route | Method | Description |
|-------|--------|-------------|
| `/api/agents` | GET | List all agents |
| `/api/graph` | GET | Get graph data for visualization |
| `/api/list` | GET | List memory units with search |
| `/api/search` | POST | Search memories |
| `/api/think` | POST | Generate AI answers |
| `/api/memories/batch` | POST | Store memories (sync) |
| `/api/memories/batch_async` | POST | Store memories (async) |
| `/api/documents` | GET | List documents |
| `/api/documents/:id` | GET | Get document details |
| `/api/stats/:agentId` | GET | Get agent statistics |
| `/api/operations/:agentId` | GET | List async operations |

## Usage

### Using Search Debug (Primary Feature)
1. Go to the **Search Debug** tab
2. Enter a search query
3. Select fact type (World, Agent, Opinion)
4. Adjust thinking budget, reranker (Heuristic/Cross-Encoder), and max tokens
5. Click **Search** to run the query
6. Use the phase radio buttons to explore the retrieval pipeline:
   - **1. Retrieval**: Switch between Semantic/BM25/Graph/Temporal tabs to see each method's results
   - **2. RRF Merge**: View how rankings from different methods are combined with source ranks
   - **3. Reranking**: See rank changes (↑ improved, ↓ declined) with score component breakdowns
   - **4. Final Results**: Detailed table with all score components and individual metric ranks
7. Monitor the status bar showing nodes visited, entry points, budget usage, and duration
8. Add more panes with **+ Add Search Pane** to compare different queries side-by-side
9. Each pane maintains independent state for query, settings, and current phase view

### Selecting an Agent
1. Use the dropdown in the top navigation bar
2. Select an agent to view their memories
3. All views will automatically filter by the selected agent

### Visualizing Memories
1. Go to the **Data** tab
2. Choose a fact type (World, Agent, Opinions, or Documents)
3. Click **Load** to fetch data
4. Toggle between **Graph** and **Table** views
5. Use search to filter results

### Asking Questions
1. Go to the **Think** tab
2. Enter your question
3. Adjust thinking budget if needed
4. Click **Think** to get an AI-generated answer
5. View source facts and new opinions formed

### Adding Memories
1. Go to the **Add Memory** tab
2. Enter memory content (required)
3. Optionally add context, date, document metadata
4. Choose sync or async processing
5. Click **Submit Memory**

### Monitoring Stats
1. Go to the **Stats & Operations** tab
2. View real-time statistics
3. Monitor pending/failed async operations
4. Stats auto-refresh every 5 seconds

## Development Notes

- The control plane uses client-side rendering for interactive features
- API routes run on the server and proxy to the dataplane
- No direct browser-to-dataplane communication (no CORS issues)
- Graph visualization uses Cytoscape.js with multiple layout options
- Tailwind CSS v4 for styling (simplified configuration)

## Troubleshooting

**CORS Errors**: The control plane should eliminate CORS issues. If you see them, ensure you're accessing the control plane at `http://localhost:3000` (not the dataplane directly).

**Connection Errors**: Verify the dataplane is running at the URL specified in `.env.local` (default: `http://localhost:8080`).

**Graph Not Rendering**: Check browser console for errors. Ensure data is loading correctly from `/api/graph`.

**Build Warnings**: The "workspace root" warning about lockfiles is harmless and can be ignored.

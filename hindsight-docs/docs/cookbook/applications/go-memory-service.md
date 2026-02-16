---
sidebar_position: 10
---

# Go Memory-Augmented API

:::info Complete Application
This is a complete, runnable Go application demonstrating Hindsight integration.
:::

A Go HTTP microservice that combines a domain API with Hindsight memory. Each API user gets a personal memory bank. The service remembers past interactions and uses them to provide personalized responses.

## Use Case

A **developer knowledge assistant** that remembers what technologies each user works with, what problems they've solved, and provides personalized recommendations.

## Features

- Per-user memory banks (created on first interaction)
- Conversation history stored via retain
- Context-aware responses via recall + reflect
- Structured output for programmatic consumption
- Health check and bank stats endpoints

## Project Structure

```
go-memory-service/
├── main.go          # HTTP server, routes, handlers
├── go.mod
└── go.sum
```

## The Code

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "os"
    "strings"
    "time"

    hindsight "github.com/vectorize-io/hindsight-client-go"
)

var client *hindsight.Client

func main() {
    apiURL := envOr("HINDSIGHT_API_URL", "http://localhost:8888")

    var err error
    client, err = hindsight.New(apiURL)
    if err != nil {
        log.Fatal(err)
    }

    mux := http.NewServeMux()
    mux.HandleFunc("POST /ask", handleAsk)
    mux.HandleFunc("POST /learn", handleLearn)
    mux.HandleFunc("GET /recall/{userID}", handleRecall)
    mux.HandleFunc("GET /health", handleHealth)

    addr := envOr("ADDR", ":8080")
    log.Printf("listening on %s (hindsight: %s)", addr, apiURL)
    log.Fatal(http.ListenAndServe(addr, mux))
}

// --- Request/Response types ---

type AskRequest struct {
    UserID string `json:"user_id"`
    Query  string `json:"query"`
}

type AskResponse struct {
    Answer string   `json:"answer"`
    Facts  []string `json:"facts,omitempty"`
}

type LearnRequest struct {
    UserID  string   `json:"user_id"`
    Content string   `json:"content"`
    Tags    []string `json:"tags,omitempty"`
}

type RecallResponse struct {
    Results []RecallFact `json:"results"`
}

type RecallFact struct {
    Text string `json:"text"`
    Type string `json:"type"`
}

// --- Handlers ---

// handleLearn stores new information for a user.
func handleLearn(w http.ResponseWriter, r *http.Request) {
    var req LearnRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid JSON", http.StatusBadRequest)
        return
    }

    ctx := r.Context()
    bankID := bankFor(req.UserID)

    // Ensure bank exists
    ensureBank(ctx, bankID, req.UserID)

    // Store the memory
    var opts []hindsight.RetainOption
    if len(req.Tags) > 0 {
        opts = append(opts, hindsight.WithTags(req.Tags))
    }

    resp, err := client.Retain(ctx, bankID, req.Content, opts...)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    writeJSON(w, map[string]any{
        "success": resp.Success,
        "bank_id": bankID,
    })
}

// handleAsk answers a question using the user's memories.
func handleAsk(w http.ResponseWriter, r *http.Request) {
    var req AskRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid JSON", http.StatusBadRequest)
        return
    }

    ctx := r.Context()
    bankID := bankFor(req.UserID)

    // Ensure bank exists
    ensureBank(ctx, bankID, req.UserID)

    // Recall relevant facts
    recallResp, err := client.Recall(ctx, bankID, req.Query,
        hindsight.WithBudget(hindsight.BudgetMid),
        hindsight.WithMaxTokens(2048),
    )
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    var facts []string
    for _, result := range recallResp.Results {
        facts = append(facts, result.Text)
    }

    // Reflect to generate an answer
    reflectResp, err := client.Reflect(ctx, bankID, req.Query,
        hindsight.WithReflectBudget(hindsight.BudgetMid),
    )
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    // Store this interaction as a new memory
    interaction := fmt.Sprintf("User asked: %q\nAssistant answered: %s", req.Query, reflectResp.Text)
    go func() {
        bgCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
        defer cancel()
        client.Retain(bgCtx, bankID, interaction,
            hindsight.WithContext("Q&A interaction"),
        )
    }()

    writeJSON(w, AskResponse{
        Answer: reflectResp.Text,
        Facts:  facts,
    })
}

// handleRecall returns raw memories for a user.
func handleRecall(w http.ResponseWriter, r *http.Request) {
    userID := r.PathValue("userID")
    query := r.URL.Query().Get("q")
    if query == "" {
        query = "What do you know?"
    }

    ctx := r.Context()
    bankID := bankFor(userID)

    resp, err := client.Recall(ctx, bankID, query,
        hindsight.WithBudget(hindsight.BudgetHigh),
    )
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }

    var results []RecallFact
    for _, result := range resp.Results {
        results = append(results, RecallFact{
            Text: result.Text,
            Type: result.Type.Or("unknown"),
        })
    }

    writeJSON(w, RecallResponse{Results: results})
}

func handleHealth(w http.ResponseWriter, _ *http.Request) {
    writeJSON(w, map[string]string{"status": "ok"})
}

// --- Helpers ---

func bankFor(userID string) string {
    return "user-" + strings.ToLower(userID)
}

func ensureBank(ctx context.Context, bankID, userID string) {
    client.CreateBank(ctx, bankID,
        hindsight.WithBankName(fmt.Sprintf("Memory for %s", userID)),
        hindsight.WithMission("Developer knowledge assistant. Remember technologies, problems solved, and preferences."),
    )
}

func writeJSON(w http.ResponseWriter, v any) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(v)
}

func envOr(key, fallback string) string {
    if v := os.Getenv(key); v != "" {
        return v
    }
    return fallback
}
```

## Running

### 1. Start Hindsight

```bash
export OPENAI_API_KEY=your-key

docker run --rm -it --pull always -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_LLM_MODEL=o3-mini \
  -v $HOME/.hindsight-docker:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

### 2. Start the service

```bash
go run main.go
```

### 3. Try it out

```bash
# Teach it something
curl -s localhost:8080/learn -d '{
  "user_id": "alice",
  "content": "I am building a Go microservice that uses gRPC and PostgreSQL",
  "tags": ["project"]
}' | jq .

# Teach it more
curl -s localhost:8080/learn -d '{
  "user_id": "alice",
  "content": "I solved a connection pooling issue by switching from pgx to pgxpool",
  "tags": ["debugging"]
}'

curl -s localhost:8080/learn -d '{
  "user_id": "alice",
  "content": "I prefer structured logging with slog over zerolog",
  "tags": ["preferences"]
}'

# Ask a question (uses recall + reflect)
curl -s localhost:8080/ask -d '{
  "user_id": "alice",
  "query": "What tech stack am I using?"
}' | jq .

# Raw recall
curl -s "localhost:8080/recall/alice?q=database" | jq .
```

## How It Works

1. **`/learn`** - Stores information using `Retain`. Each piece of info becomes searchable facts, entities, and relationships.

2. **`/ask`** - Two-phase retrieval:
   - **Recall**: Finds relevant facts from the user's memory bank
   - **Reflect**: Synthesizes a response using those facts plus disposition-aware reasoning
   - The Q&A interaction itself is stored as a new memory (fire-and-forget goroutine)

3. **`/recall/{userID}`** - Direct access to raw recalled facts for debugging or building custom UIs.

## Key Patterns

### Per-User Isolation

Each user gets their own bank (`user-alice`, `user-bob`). Banks are created lazily on first interaction via `CreateBank` (idempotent - safe to call repeatedly).

### Fire-and-Forget Memory

The `/ask` handler stores the interaction in a background goroutine so the response isn't delayed by the retain call:

```go
go func() {
    bgCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()
    client.Retain(bgCtx, bankID, interaction)
}()
```

### Tag-Based Scoping

Tags partition memories within a bank. Query only `debugging` memories, or only `preferences`:

```bash
# The /recall endpoint could be extended to support tag filtering:
curl "localhost:8080/recall/alice?q=issues&tags=debugging"
```

## Next Steps

- [Go Quickstart](/cookbook/recipes/go-quickstart) - Core operations walkthrough
- [Go Concurrent Pipeline](/cookbook/recipes/go-concurrent-pipeline) - Bulk data ingestion
- [Per-User Memory](/cookbook/recipes/per-user-memory) - The pattern in depth
- [Go SDK Reference](/sdks/go) - Full API documentation

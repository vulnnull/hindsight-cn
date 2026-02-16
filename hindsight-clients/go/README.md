# Hindsight Go Client

Go client for the [Hindsight](https://github.com/vectorize-io/hindsight) agent memory API.

## Installation

```bash
go get github.com/vectorize-io/hindsight-client-go
```

Requires Go 1.25+.

## Quick Start

```go
package main

import (
    "context"
    "fmt"
    "log"

    hindsight "github.com/vectorize-io/hindsight-client-go"
)

func main() {
    client, err := hindsight.New("http://localhost:8888")
    if err != nil {
        log.Fatal(err)
    }

    ctx := context.Background()

    // Store a memory
    _, err = client.Retain(ctx, "my-bank", "The user prefers dark mode")
    if err != nil {
        log.Fatal(err)
    }

    // Recall memories
    resp, err := client.Recall(ctx, "my-bank", "What are the user's preferences?")
    if err != nil {
        log.Fatal(err)
    }
    for _, r := range resp.Results {
        fmt.Println(r.Text)
    }

    // Reflect with reasoning
    ref, err := client.Reflect(ctx, "my-bank", "Summarize what you know about the user")
    if err != nil {
        log.Fatal(err)
    }
    fmt.Println(ref.Text)
}
```

## Authentication

```go
client, err := hindsight.New("http://localhost:8888", hindsight.WithAPIKey("your-key"))
```

## Core Operations

### Retain (Store Memories)

```go
// Single memory
_, err := client.Retain(ctx, "bank-id", "Alice loves Python",
    hindsight.WithContext("programming discussion"),
    hindsight.WithTags([]string{"tech"}),
    hindsight.WithDocumentID("conv-123"),
)

// Batch
items := []hindsight.MemoryItem{
    {Content: "First memory"},
    {Content: "Second memory"},
}
_, err := client.RetainBatch(ctx, "bank-id", items,
    hindsight.WithDocumentTags([]string{"import"}),
    hindsight.WithAsync(true),
)
```

### Recall (Retrieve Memories)

```go
resp, err := client.Recall(ctx, "bank-id", "What does Alice like?",
    hindsight.WithBudget(hindsight.BudgetHigh),
    hindsight.WithMaxTokens(4096),
    hindsight.WithTypes([]string{"world", "experience"}),
    hindsight.WithTrace(true),
    hindsight.WithRecallTags([]string{"tech"}),
)

for _, r := range resp.Results {
    fmt.Printf("[%s] %s\n", r.Type.Or("unknown"), r.Text)
}
```

### Reflect (Reason with Memories)

```go
resp, err := client.Reflect(ctx, "bank-id", "What are the user's interests?",
    hindsight.WithReflectBudget(hindsight.BudgetMid),
    hindsight.WithReflectMaxTokens(2048),
    hindsight.WithResponseSchema(map[string]any{
        "type": "object",
        "properties": map[string]any{
            "interests": map[string]any{"type": "array", "items": map[string]any{"type": "string"}},
        },
    }),
)

fmt.Println(resp.Text)
```

### Bank Management

```go
// Create bank with personality
_, err := client.CreateBank(ctx, "my-bank",
    hindsight.WithBankName("My Agent"),
    hindsight.WithMission("Help users with coding tasks"),
    hindsight.WithDisposition(hindsight.DispositionTraits{
        Skepticism: 3,
        Literalism: 2,
        Empathy:    4,
    }),
)

// Update mission
_, err = client.SetMission(ctx, "my-bank", "New mission statement")

// List all banks
banks, err := client.ListBanks(ctx)

// Delete bank
err = client.DeleteBank(ctx, "my-bank")
```

## Advanced Usage

For operations not covered by the high-level wrapper (documents, entities, operations, mental models, directives), access the ogen-generated client directly:

```go
ogen := client.OgenClient()

// List entities
resp, err := ogen.ListEntities(ctx, ogenapi.ListEntitiesParams{
    BankID: "my-bank",
})

// Create mental model
resp, err := ogen.CreateMentalModel(ctx, &ogenapi.CreateMentalModelRequest{
    Name:        "user-preferences",
    SourceQuery: "What are the user's preferences?",
}, ogenapi.CreateMentalModelParams{BankID: "my-bank"})
```

## Code Generation

The client is built on [ogen](https://github.com/ogen-go/ogen), generating strongly-typed Go code from the OpenAPI 3.1 spec. To regenerate after API changes:

```bash
cd hindsight-clients/go
go generate ./...
```

## Running Tests

Integration tests require a running Hindsight API server:

```bash
HINDSIGHT_API_URL=http://localhost:8888 go test -v -tags=integration ./...
```

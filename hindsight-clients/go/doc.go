// Package hindsight provides a Go client for the Hindsight agent memory API.
//
// Hindsight is a long-term memory system for AI agents. This client wraps the
// auto-generated ogen API client with a simpler, Go-idiomatic interface for the
// core operations: retain (store), recall (retrieve), and reflect (reason).
//
// # Quick Start
//
//	client, err := hindsight.New("http://localhost:8888")
//	if err != nil {
//	    log.Fatal(err)
//	}
//
//	// Store a memory
//	_, err = client.Retain(ctx, "my-bank", "The user prefers dark mode")
//
//	// Recall memories
//	resp, err := client.Recall(ctx, "my-bank", "What are the user's preferences?")
//	for _, r := range resp.Results {
//	    fmt.Println(r.Text)
//	}
//
//	// Reflect with reasoning
//	ref, err := client.Reflect(ctx, "my-bank", "Summarize what you know about the user")
//	fmt.Println(ref.Text)
//
// # Authentication
//
// For authenticated deployments, pass an API key:
//
//	client, err := hindsight.New("http://localhost:8888", hindsight.WithAPIKey("your-key"))
//
// # Advanced Usage
//
// For operations not covered by the high-level wrapper (documents, entities,
// operations, mental models, directives), access the ogen-generated client:
//
//	ogen := client.OgenClient()
//	resp, err := ogen.ListEntities(ctx, ogenapi.ListEntitiesParams{BankID: "my-bank"})
package hindsight

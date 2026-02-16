package hindsight_test

import (
	"context"
	"fmt"
	"log"

	hindsight "github.com/vectorize-io/hindsight-client-go"
)

func Example() {
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

func ExampleNew_withAPIKey() {
	_, err := hindsight.New(
		"http://localhost:8888",
		hindsight.WithAPIKey("your-api-key"),
	)
	if err != nil {
		log.Fatal(err)
	}
}

func ExampleClient_Retain() {
	client, _ := hindsight.New("http://localhost:8888")
	ctx := context.Background()

	// Simple retain
	_, _ = client.Retain(ctx, "my-bank", "Alice loves Python programming")

	// Retain with options
	_, _ = client.Retain(ctx, "my-bank", "Bob went hiking",
		hindsight.WithContext("outdoor activities"),
		hindsight.WithTags([]string{"hobbies"}),
		hindsight.WithDocumentID("conversation-123"),
	)
}

func ExampleClient_RetainBatch() {
	client, _ := hindsight.New("http://localhost:8888")
	ctx := context.Background()

	items := []hindsight.MemoryItem{
		{Content: "Alice completed the project"},
		{Content: "Bob started learning Go"},
		{Content: "Charlie presented at the conference"},
	}

	_, _ = client.RetainBatch(ctx, "my-bank", items,
		hindsight.WithDocumentTags([]string{"team-updates"}),
	)
}

func ExampleClient_Recall() {
	client, _ := hindsight.New("http://localhost:8888")
	ctx := context.Background()

	resp, _ := client.Recall(ctx, "my-bank", "What does Alice like?",
		hindsight.WithBudget(hindsight.BudgetHigh),
		hindsight.WithMaxTokens(4096),
		hindsight.WithTypes([]string{"world", "experience"}),
		hindsight.WithTrace(true),
	)

	for _, r := range resp.Results {
		fmt.Printf("[%s] %s\n", r.Type.Or("unknown"), r.Text)
	}
}

func ExampleClient_Reflect() {
	client, _ := hindsight.New("http://localhost:8888")
	ctx := context.Background()

	resp, _ := client.Reflect(ctx, "my-bank",
		"What are the user's professional interests?",
		hindsight.WithReflectBudget(hindsight.BudgetMid),
		hindsight.WithReflectMaxTokens(2048),
	)

	fmt.Println(resp.Text)
}

func ExampleClient_CreateBank() {
	client, _ := hindsight.New("http://localhost:8888")
	ctx := context.Background()

	_, _ = client.CreateBank(ctx, "my-bank",
		hindsight.WithBankName("My Agent"),
		hindsight.WithMission("Help users with programming tasks"),
		hindsight.WithDisposition(hindsight.DispositionTraits{
			Skepticism: 3,
			Literalism: 2,
			Empathy:    4,
		}),
	)
}

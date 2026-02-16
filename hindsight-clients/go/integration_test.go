//go:build integration

package hindsight_test

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	hindsight "github.com/vectorize-io/hindsight-client-go"
)

func apiURL(t *testing.T) string {
	t.Helper()
	u := os.Getenv("HINDSIGHT_API_URL")
	if u == "" {
		u = "http://localhost:8888"
	}
	return u
}

func newClient(t *testing.T) *hindsight.Client {
	t.Helper()
	c, err := hindsight.New(apiURL(t))
	if err != nil {
		t.Fatal(err)
	}
	return c
}

func uniqueBank(t *testing.T) string {
	t.Helper()
	return fmt.Sprintf("go_test_%d", time.Now().UnixNano())
}

// --- Retain tests ---

func TestRetainSingle(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	resp, err := c.Retain(ctx, uniqueBank(t), "Alice loves artificial intelligence and machine learning")
	if err != nil {
		t.Fatal(err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
}

func TestRetainWithContext(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	resp, err := c.Retain(ctx, uniqueBank(t), "Bob went hiking in the mountains",
		hindsight.WithTimestamp(time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)),
		hindsight.WithContext("outdoor activities"),
	)
	if err != nil {
		t.Fatal(err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
}

func TestRetainBatch(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	items := []hindsight.MemoryItem{
		{Content: "Charlie enjoys reading science fiction books"},
		{Content: "Diana is learning to play the guitar"},
		{Content: "Eve completed a marathon last month"},
	}

	resp, err := c.RetainBatch(ctx, uniqueBank(t), items)
	if err != nil {
		t.Fatal(err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
	if resp.ItemsCount != 3 {
		t.Errorf("expected items_count=3, got %d", resp.ItemsCount)
	}
}

func TestRetainWithTags(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	resp, err := c.Retain(ctx, uniqueBank(t), "New feature implementation for project Z",
		hindsight.WithTags([]string{"project_z", "features"}),
	)
	if err != nil {
		t.Fatal(err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
}

func TestRetainBatchWithDocumentTags(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	items := []hindsight.MemoryItem{
		{Content: "First item in batch"},
		{Content: "Second item in batch"},
	}

	resp, err := c.RetainBatch(ctx, uniqueBank(t), items,
		hindsight.WithDocumentTags([]string{"batch_import", "test_data"}),
	)
	if err != nil {
		t.Fatal(err)
	}
	if !resp.Success {
		t.Error("expected success=true")
	}
	if resp.ItemsCount != 2 {
		t.Errorf("expected items_count=2, got %d", resp.ItemsCount)
	}
}

// --- Recall tests ---

func setupRecallBank(t *testing.T, c *hindsight.Client, bankID string) {
	t.Helper()
	ctx := context.Background()

	items := []hindsight.MemoryItem{
		{Content: "Alice loves programming in Python"},
		{Content: "Bob enjoys hiking and outdoor adventures"},
		{Content: "Charlie is interested in quantum physics"},
		{Content: "Diana plays the violin beautifully"},
	}

	_, err := c.RetainBatch(ctx, bankID, items)
	if err != nil {
		t.Fatal(err)
	}
}

func TestRecallBasic(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)
	setupRecallBank(t, c, bankID)

	resp, err := c.Recall(ctx, bankID, "What does Alice like?")
	if err != nil {
		t.Fatal(err)
	}
	if len(resp.Results) == 0 {
		t.Error("expected at least one result")
	}

	found := false
	for _, r := range resp.Results {
		if contains(r.Text, "Alice") || contains(r.Text, "Python") || contains(r.Text, "programming") {
			found = true
			break
		}
	}
	if !found {
		t.Error("expected a result mentioning Alice or Python")
	}
}

func TestRecallWithMaxTokens(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)
	setupRecallBank(t, c, bankID)

	resp, err := c.Recall(ctx, bankID, "outdoor activities",
		hindsight.WithMaxTokens(1024),
	)
	if err != nil {
		t.Fatal(err)
	}
	if resp.Results == nil {
		t.Error("expected results, got nil")
	}
}

func TestRecallFullFeatured(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)
	setupRecallBank(t, c, bankID)

	resp, err := c.Recall(ctx, bankID, "What are people's hobbies?",
		hindsight.WithTypes([]string{"world"}),
		hindsight.WithMaxTokens(2048),
		hindsight.WithTrace(true),
	)
	if err != nil {
		t.Fatal(err)
	}
	if resp.Results == nil {
		t.Error("expected results, got nil")
	}
}

// --- Reflect tests ---

func setupReflectBank(t *testing.T, c *hindsight.Client, bankID string) {
	t.Helper()
	ctx := context.Background()

	_, err := c.CreateBank(ctx, bankID,
		hindsight.WithMission("I am a helpful AI assistant interested in technology and science."),
	)
	if err != nil {
		t.Fatal(err)
	}

	items := []hindsight.MemoryItem{
		{Content: "The Python programming language is great for data science"},
		{Content: "Machine learning models can recognize patterns in data"},
		{Content: "Neural networks are inspired by biological neurons"},
	}

	_, err = c.RetainBatch(ctx, bankID, items)
	if err != nil {
		t.Fatal(err)
	}
}

func TestReflectBasic(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)
	setupReflectBank(t, c, bankID)

	resp, err := c.Reflect(ctx, bankID, "What do you think about artificial intelligence?")
	if err != nil {
		t.Fatal(err)
	}
	if resp.Text == "" {
		t.Error("expected non-empty response text")
	}
}

func TestReflectWithMaxTokens(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)
	setupReflectBank(t, c, bankID)

	resp, err := c.Reflect(ctx, bankID, "What do you think about Python?",
		hindsight.WithReflectMaxTokens(500),
	)
	if err != nil {
		t.Fatal(err)
	}
	if resp.Text == "" {
		t.Error("expected non-empty response text")
	}
}

// --- Bank tests ---

func TestCreateBank(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	bankID := uniqueBank(t)
	resp, err := c.CreateBank(ctx, bankID,
		hindsight.WithBankName("Test Bank"),
		hindsight.WithMission("A test bank for Go client"),
	)
	if err != nil {
		t.Fatal(err)
	}
	if resp.BankID != bankID {
		t.Errorf("expected bank_id=%q, got %q", bankID, resp.BankID)
	}
}

func TestSetMission(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	bankID := uniqueBank(t)
	resp, err := c.SetMission(ctx, bankID, "Be a helpful PM tracking sprint progress")
	if err != nil {
		t.Fatal(err)
	}
	if resp.BankID != bankID {
		t.Errorf("expected bank_id=%q, got %q", bankID, resp.BankID)
	}
	if resp.Mission != "Be a helpful PM tracking sprint progress" {
		t.Errorf("expected mission=%q, got %q", "Be a helpful PM tracking sprint progress", resp.Mission)
	}
}

func TestListBanks(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	// Create a bank first
	bankID := uniqueBank(t)
	_, err := c.CreateBank(ctx, bankID)
	if err != nil {
		t.Fatal(err)
	}

	resp, err := c.ListBanks(ctx)
	if err != nil {
		t.Fatal(err)
	}
	if len(resp.Banks) == 0 {
		t.Error("expected at least one bank")
	}
}

func TestDeleteBank(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()

	bankID := uniqueBank(t)
	_, err := c.CreateBank(ctx, bankID, hindsight.WithMission("will be deleted"))
	if err != nil {
		t.Fatal(err)
	}

	err = c.DeleteBank(ctx, bankID)
	if err != nil {
		t.Fatal(err)
	}
}

// --- End-to-end workflow ---

func TestCompleteWorkflow(t *testing.T) {
	c := newClient(t)
	ctx := context.Background()
	bankID := uniqueBank(t)

	// 1. Create bank
	_, err := c.CreateBank(ctx, bankID,
		hindsight.WithMission("I am a software engineer who loves Python programming."),
	)
	if err != nil {
		t.Fatal(err)
	}

	// 2. Store memories
	items := []hindsight.MemoryItem{
		{Content: "I completed a project using FastAPI"},
		{Content: "I learned about async programming in Python"},
		{Content: "I enjoy working on open source projects"},
	}
	storeResp, err := c.RetainBatch(ctx, bankID, items)
	if err != nil {
		t.Fatal(err)
	}
	if !storeResp.Success {
		t.Error("expected retain success")
	}

	// 3. Search for relevant memories
	recallResp, err := c.Recall(ctx, bankID, "What programming technologies do I use?")
	if err != nil {
		t.Fatal(err)
	}
	if len(recallResp.Results) == 0 {
		t.Error("expected recall results")
	}

	// 4. Generate contextual answer
	reflectResp, err := c.Reflect(ctx, bankID, "What are my professional interests?")
	if err != nil {
		t.Fatal(err)
	}
	if reflectResp.Text == "" {
		t.Error("expected non-empty reflect response")
	}
}

// contains checks if s contains substr (case-sensitive).
func contains(s, substr string) bool {
	return len(s) >= len(substr) && searchString(s, substr)
}

func searchString(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

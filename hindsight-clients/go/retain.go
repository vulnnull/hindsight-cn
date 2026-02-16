package hindsight

import (
	"context"
	"fmt"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// Retain stores a single memory in the given bank.
// It wraps [Client.RetainBatch] for convenience.
func (c *Client) Retain(ctx context.Context, bankID, content string, opts ...RetainOption) (*RetainResponse, error) {
	var cfg retainConfig
	for _, o := range opts {
		o(&cfg)
	}

	item := ogenapi.MemoryItem{
		Content: content,
	}
	if cfg.timestamp != nil {
		item.Timestamp = ogenapi.NewOptDateTime(*cfg.timestamp)
	}
	if cfg.context != nil {
		item.Context = ogenapi.NewOptString(*cfg.context)
	}
	if cfg.documentID != nil {
		item.DocumentID = ogenapi.NewOptString(*cfg.documentID)
	}
	if cfg.metadata != nil {
		m := ogenapi.MemoryItemMetadata(cfg.metadata)
		item.Metadata = ogenapi.NewOptMemoryItemMetadata(m)
	}
	if cfg.entities != nil {
		item.Entities = cfg.entities
	}
	if cfg.tags != nil {
		item.Tags = cfg.tags
	}

	return c.RetainBatch(ctx, bankID, []MemoryItem{item})
}

// RetainBatch stores multiple memories in the given bank.
func (c *Client) RetainBatch(ctx context.Context, bankID string, items []MemoryItem, opts ...RetainBatchOption) (*RetainResponse, error) {
	var cfg retainBatchConfig
	for _, o := range opts {
		o(&cfg)
	}

	req := &ogenapi.RetainRequest{
		Items: items,
	}
	if cfg.async {
		req.Async = ogenapi.NewOptBool(true)
	}
	if cfg.documentTags != nil {
		req.DocumentTags = cfg.documentTags
	}

	res, err := c.api.RetainMemories(ctx, req, ogenapi.RetainMemoriesParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.RetainResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

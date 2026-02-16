package hindsight

import (
	"context"
	"fmt"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// Recall retrieves memories from the given bank that match the query.
func (c *Client) Recall(ctx context.Context, bankID, query string, opts ...RecallOption) (*RecallResponse, error) {
	var cfg recallConfig
	for _, o := range opts {
		o(&cfg)
	}

	req := &ogenapi.RecallRequest{
		Query: query,
	}
	if cfg.budget != nil {
		req.Budget = ogenapi.NewOptBudget(*cfg.budget)
	}
	if cfg.maxTokens != nil {
		req.MaxTokens = ogenapi.NewOptInt(*cfg.maxTokens)
	}
	if cfg.trace != nil {
		req.Trace = ogenapi.NewOptBool(*cfg.trace)
	}
	if cfg.queryTimestamp != nil {
		req.QueryTimestamp = ogenapi.NewOptString(*cfg.queryTimestamp)
	}
	if cfg.types != nil {
		req.Types = cfg.types
	}
	if cfg.includeOpts != nil {
		req.Include = ogenapi.NewOptIncludeOptions(*cfg.includeOpts)
	}
	if cfg.tags != nil {
		req.Tags = cfg.tags
	}
	if cfg.tagsMatch != nil {
		req.TagsMatch = ogenapi.NewOptRecallRequestTagsMatch(
			ogenapi.RecallRequestTagsMatch(*cfg.tagsMatch),
		)
	}

	res, err := c.api.RecallMemories(ctx, req, ogenapi.RecallMemoriesParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.RecallResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

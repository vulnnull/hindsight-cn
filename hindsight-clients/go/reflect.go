package hindsight

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/go-faster/jx"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// Reflect performs disposition-aware reasoning using the bank's memories and
// mental models. Returns a markdown-formatted response.
func (c *Client) Reflect(ctx context.Context, bankID, query string, opts ...ReflectOption) (*ReflectResponse, error) {
	var cfg reflectConfig
	for _, o := range opts {
		o(&cfg)
	}

	req := &ogenapi.ReflectRequest{
		Query: query,
	}
	if cfg.budget != nil {
		req.Budget = ogenapi.NewOptBudget(*cfg.budget)
	}
	if cfg.maxTokens != nil {
		req.MaxTokens = ogenapi.NewOptInt(*cfg.maxTokens)
	}
	if cfg.includeOpts != nil {
		req.Include = ogenapi.NewOptReflectIncludeOptions(*cfg.includeOpts)
	}
	if cfg.responseSchema != nil {
		schema, err := toResponseSchema(cfg.responseSchema)
		if err != nil {
			return nil, fmt.Errorf("hindsight: marshal response_schema: %w", err)
		}
		req.ResponseSchema = ogenapi.NewOptReflectRequestResponseSchema(schema)
	}
	if cfg.tags != nil {
		req.Tags = cfg.tags
	}
	if cfg.tagsMatch != nil {
		req.TagsMatch = ogenapi.NewOptReflectRequestTagsMatch(
			ogenapi.ReflectRequestTagsMatch(*cfg.tagsMatch),
		)
	}

	res, err := c.api.Reflect(ctx, req, ogenapi.ReflectParams{
		BankID: bankID,
	})
	if err != nil {
		return nil, err
	}

	resp, ok := res.(*ogenapi.ReflectResponse)
	if !ok {
		return nil, fmt.Errorf("hindsight: unexpected response type %T", res)
	}
	return resp, nil
}

// toResponseSchema converts a map[string]any JSON schema to the ogen type.
func toResponseSchema(schema map[string]any) (ogenapi.ReflectRequestResponseSchema, error) {
	out := make(ogenapi.ReflectRequestResponseSchema, len(schema))
	for k, v := range schema {
		data, err := json.Marshal(v)
		if err != nil {
			return nil, err
		}
		out[k] = jx.Raw(data)
	}
	return out, nil
}

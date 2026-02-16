package hindsight

import (
	"net/http"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// Client is the high-level Hindsight API client. It wraps the ogen-generated
// client with convenience methods for core operations.
type Client struct {
	api *ogenapi.Client
}

// New creates a new Hindsight client for the given base URL.
//
// By default, no authentication is configured. Use [WithAPIKey] to set a
// Bearer token, or [WithHTTPClient] for full control over the HTTP transport.
func New(baseURL string, opts ...Option) (*Client, error) {
	cfg := clientConfig{}
	for _, o := range opts {
		o(&cfg)
	}

	var httpClient http.Client
	if cfg.httpClient != nil {
		httpClient = *cfg.httpClient
	}

	if cfg.apiKey != "" {
		base := httpClient.Transport
		if base == nil {
			base = http.DefaultTransport
		}
		httpClient.Transport = &authTransport{
			base:  base,
			token: cfg.apiKey,
		}
	}

	api, err := ogenapi.NewClient(baseURL, ogenapi.WithClient(&httpClient))
	if err != nil {
		return nil, err
	}

	return &Client{api: api}, nil
}

// OgenClient returns the underlying ogen-generated client for advanced
// operations not covered by the high-level wrapper (documents, entities,
// operations, mental models, directives).
func (c *Client) OgenClient() *ogenapi.Client {
	return c.api
}

// authTransport injects a Bearer token into every request.
type authTransport struct {
	base  http.RoundTripper
	token string
}

func (t *authTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	r = r.Clone(r.Context())
	r.Header.Set("Authorization", "Bearer "+t.token)
	return t.base.RoundTrip(r)
}

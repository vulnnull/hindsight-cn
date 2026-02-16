package hindsight

import (
	"net/http"
	"time"

	"github.com/vectorize-io/hindsight-client-go/internal/ogenapi"
)

// --- Client options ---

type clientConfig struct {
	apiKey     string
	httpClient *http.Client
}

// Option configures a [Client].
type Option func(*clientConfig)

// WithAPIKey sets the Bearer token used for authentication.
func WithAPIKey(key string) Option {
	return func(c *clientConfig) { c.apiKey = key }
}

// WithHTTPClient sets a custom [http.Client] for all requests.
// If combined with [WithAPIKey], the API key transport wraps this client's transport.
func WithHTTPClient(hc *http.Client) Option {
	return func(c *clientConfig) { c.httpClient = hc }
}

// --- Re-exported types ---

// Budget controls the computation budget for recall and reflect operations.
type Budget = ogenapi.Budget

const (
	BudgetLow  = ogenapi.BudgetLow
	BudgetMid  = ogenapi.BudgetMid
	BudgetHigh = ogenapi.BudgetHigh
)

// TagsMatch controls how tag filtering works.
type TagsMatch string

const (
	TagsMatchAny       TagsMatch = "any"
	TagsMatchAll       TagsMatch = "all"
	TagsMatchAnyStrict TagsMatch = "any_strict"
	TagsMatchAllStrict TagsMatch = "all_strict"
)

type (
	// RetainResponse is the response from a retain operation.
	RetainResponse = ogenapi.RetainResponse

	// RecallResponse is the response from a recall operation.
	RecallResponse = ogenapi.RecallResponse

	// RecallResult is a single memory result from recall.
	RecallResult = ogenapi.RecallResult

	// ReflectResponse is the response from a reflect operation.
	ReflectResponse = ogenapi.ReflectResponse

	// MemoryItem is a single memory item for retain operations.
	MemoryItem = ogenapi.MemoryItem

	// EntityInput provides entity hints for retain.
	EntityInput = ogenapi.EntityInput

	// BankProfileResponse is the response for bank profile operations.
	BankProfileResponse = ogenapi.BankProfileResponse

	// BankListResponse is the response for listing banks.
	BankListResponse = ogenapi.BankListResponse

	// DispositionTraits configures personality traits for a bank.
	DispositionTraits = ogenapi.DispositionTraits

	// TokenUsage reports LLM token consumption.
	TokenUsage = ogenapi.TokenUsage

	// ReflectBasedOn contains the evidence used for a reflect response.
	ReflectBasedOn = ogenapi.ReflectBasedOn

	// IncludeOptions controls what extra data is returned from recall.
	IncludeOptions = ogenapi.IncludeOptions

	// ReflectIncludeOptions controls what extra data is returned from reflect.
	ReflectIncludeOptions = ogenapi.ReflectIncludeOptions
)

// --- Retain options ---

// RetainOption configures a [Client.Retain] call.
type RetainOption func(*retainConfig)

type retainConfig struct {
	timestamp  *time.Time
	context    *string
	documentID *string
	metadata   map[string]string
	entities   []EntityInput
	tags       []string
}

// WithTimestamp sets the timestamp for a retained memory.
func WithTimestamp(t time.Time) RetainOption {
	return func(c *retainConfig) { c.timestamp = &t }
}

// WithContext sets additional context for a retained memory.
func WithContext(ctx string) RetainOption {
	return func(c *retainConfig) { c.context = &ctx }
}

// WithDocumentID groups retained memories under a document.
func WithDocumentID(id string) RetainOption {
	return func(c *retainConfig) { c.documentID = &id }
}

// WithMetadata attaches key-value metadata to a retained memory.
func WithMetadata(m map[string]string) RetainOption {
	return func(c *retainConfig) { c.metadata = m }
}

// WithEntities provides entity hints for a retained memory.
func WithEntities(e []EntityInput) RetainOption {
	return func(c *retainConfig) { c.entities = e }
}

// WithTags attaches tags to a retained memory for filtering.
func WithTags(tags []string) RetainOption {
	return func(c *retainConfig) { c.tags = tags }
}

// RetainBatchOption configures a [Client.RetainBatch] call.
type RetainBatchOption func(*retainBatchConfig)

type retainBatchConfig struct {
	documentTags []string
	async        bool
}

// WithDocumentTags sets tags applied to all items in a batch retain.
func WithDocumentTags(tags []string) RetainBatchOption {
	return func(c *retainBatchConfig) { c.documentTags = tags }
}

// WithAsync processes the retain batch asynchronously.
func WithAsync(async bool) RetainBatchOption {
	return func(c *retainBatchConfig) { c.async = async }
}

// --- Recall options ---

// RecallOption configures a [Client.Recall] call.
type RecallOption func(*recallConfig)

type recallConfig struct {
	types          []string
	maxTokens      *int
	budget         *Budget
	trace          *bool
	queryTimestamp *string
	includeOpts    *IncludeOptions
	tags           []string
	tagsMatch      *TagsMatch
}

// WithTypes filters recalled memories by type (e.g., "world", "experience").
func WithTypes(types []string) RecallOption {
	return func(c *recallConfig) { c.types = types }
}

// WithMaxTokens sets the maximum tokens for recall results.
func WithMaxTokens(n int) RecallOption {
	return func(c *recallConfig) { c.maxTokens = &n }
}

// WithBudget sets the computation budget for recall.
func WithBudget(b Budget) RecallOption {
	return func(c *recallConfig) { c.budget = &b }
}

// WithTrace enables the execution trace in recall results.
func WithTrace(enabled bool) RecallOption {
	return func(c *recallConfig) { c.trace = &enabled }
}

// WithQueryTimestamp sets the temporal context for recall (ISO 8601 format).
func WithQueryTimestamp(ts string) RecallOption {
	return func(c *recallConfig) { c.queryTimestamp = &ts }
}

// WithInclude configures which additional data to include in recall results.
func WithInclude(opts IncludeOptions) RecallOption {
	return func(c *recallConfig) { c.includeOpts = &opts }
}

// WithRecallTags filters recalled memories by tags.
func WithRecallTags(tags []string) RecallOption {
	return func(c *recallConfig) { c.tags = tags }
}

// WithRecallTagsMatch sets how tags are matched during recall.
func WithRecallTagsMatch(m TagsMatch) RecallOption {
	return func(c *recallConfig) { c.tagsMatch = &m }
}

// --- Reflect options ---

// ReflectOption configures a [Client.Reflect] call.
type ReflectOption func(*reflectConfig)

type reflectConfig struct {
	budget         *Budget
	maxTokens      *int
	includeOpts    *ReflectIncludeOptions
	responseSchema map[string]any
	tags           []string
	tagsMatch      *TagsMatch
}

// WithReflectBudget sets the computation budget for reflect.
func WithReflectBudget(b Budget) ReflectOption {
	return func(c *reflectConfig) { c.budget = &b }
}

// WithReflectMaxTokens sets the maximum tokens for the reflect response.
func WithReflectMaxTokens(n int) ReflectOption {
	return func(c *reflectConfig) { c.maxTokens = &n }
}

// WithReflectInclude configures which additional data to include in reflect results.
func WithReflectInclude(opts ReflectIncludeOptions) ReflectOption {
	return func(c *reflectConfig) { c.includeOpts = &opts }
}

// WithResponseSchema sets a JSON Schema for structured output from reflect.
func WithResponseSchema(schema map[string]any) ReflectOption {
	return func(c *reflectConfig) { c.responseSchema = schema }
}

// WithReflectTags filters memories by tags during reflect.
func WithReflectTags(tags []string) ReflectOption {
	return func(c *reflectConfig) { c.tags = tags }
}

// WithReflectTagsMatch sets how tags are matched during reflect.
func WithReflectTagsMatch(m TagsMatch) ReflectOption {
	return func(c *reflectConfig) { c.tagsMatch = &m }
}

// --- Bank options ---

// CreateBankOption configures a [Client.CreateBank] call.
type CreateBankOption func(*createBankConfig)

type createBankConfig struct {
	name        *string
	mission     *string
	disposition *DispositionTraits
}

// WithBankName sets the display name for a bank.
func WithBankName(name string) CreateBankOption {
	return func(c *createBankConfig) { c.name = &name }
}

// WithMission sets the mission for a bank.
func WithMission(mission string) CreateBankOption {
	return func(c *createBankConfig) { c.mission = &mission }
}

// WithDisposition sets the personality traits for a bank.
func WithDisposition(d DispositionTraits) CreateBankOption {
	return func(c *createBankConfig) { c.disposition = &d }
}

// --- helpers ---

func optString(s string) ogenapi.OptString {
	return ogenapi.NewOptString(s)
}

func optStringPtr(s *string) ogenapi.OptString {
	if s == nil {
		return ogenapi.OptString{}
	}
	return ogenapi.NewOptString(*s)
}

func optInt(n int) ogenapi.OptInt {
	return ogenapi.NewOptInt(n)
}

func optIntPtr(n *int) ogenapi.OptInt {
	if n == nil {
		return ogenapi.OptInt{}
	}
	return ogenapi.NewOptInt(*n)
}

func optBool(b bool) ogenapi.OptBool {
	return ogenapi.NewOptBool(b)
}

func optBoolPtr(b *bool) ogenapi.OptBool {
	if b == nil {
		return ogenapi.OptBool{}
	}
	return ogenapi.NewOptBool(*b)
}

func optBudget(b *Budget) ogenapi.OptBudget {
	if b == nil {
		return ogenapi.OptBudget{}
	}
	return ogenapi.NewOptBudget(*b)
}

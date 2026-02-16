// Command preprocess converts an OpenAPI 3.1 spec to be ogen-compatible.
//
// Hindsight's OpenAPI spec uses anyOf: [{type: T}, {type: null}] for optional
// fields. ogen cannot handle the null type in header/query parameter schemas
// with style:simple. This tool rewrites such patterns to plain {type: T},
// making the spec consumable by ogen while preserving semantic meaning (the
// fields are already marked as required: false).
package main

import (
	"encoding/json"
	"fmt"
	"os"
)

func main() {
	if len(os.Args) != 3 {
		fmt.Fprintf(os.Stderr, "usage: preprocess <input.json> <output.json>\n")
		os.Exit(1)
	}

	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fmt.Fprintf(os.Stderr, "read: %v\n", err)
		os.Exit(1)
	}

	var spec map[string]any
	if err := json.Unmarshal(data, &spec); err != nil {
		fmt.Fprintf(os.Stderr, "parse: %v\n", err)
		os.Exit(1)
	}

	convertAnyOfNull(spec)

	out, err := json.MarshalIndent(spec, "", "  ")
	if err != nil {
		fmt.Fprintf(os.Stderr, "marshal: %v\n", err)
		os.Exit(1)
	}

	if err := os.WriteFile(os.Args[2], out, 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "write: %v\n", err)
		os.Exit(1)
	}
}

// convertAnyOfNull recursively walks the spec and converts
// anyOf: [{type: T}, {type: null}] → {type: T} (or just the non-null schema).
// For component schema properties, it also does the conversion but additionally
// handles cases where the non-null branch is a $ref.
func convertAnyOfNull(v any) {
	switch val := v.(type) {
	case map[string]any:
		// Check if this object has an "anyOf" with exactly a non-null + null pair.
		if tryConvertAnyOf(val) {
			// Converted in place; recurse into the result.
			convertAnyOfNull(val)
			return
		}
		// Recurse into all values.
		for _, child := range val {
			convertAnyOfNull(child)
		}
	case []any:
		for _, child := range val {
			convertAnyOfNull(child)
		}
	}
}

// tryConvertAnyOf checks if m has anyOf: [{...}, {type: null}] and converts
// it in-place. Returns true if conversion happened.
func tryConvertAnyOf(m map[string]any) bool {
	anyOf, ok := m["anyOf"].([]any)
	if !ok || len(anyOf) != 2 {
		return false
	}

	// Identify which branch is null and which is the real type.
	var realIdx int = -1
	for i, branch := range anyOf {
		branchMap, ok := branch.(map[string]any)
		if !ok {
			return false
		}
		if branchMap["type"] == "null" {
			continue
		}
		realIdx = i
	}

	if realIdx == -1 {
		return false // Both are null? Skip.
	}

	realBranch, ok := anyOf[realIdx].(map[string]any)
	if !ok {
		return false
	}

	// Remove the anyOf key.
	delete(m, "anyOf")

	// Copy all properties from the real branch into the parent.
	for k, v := range realBranch {
		m[k] = v
	}

	return true
}

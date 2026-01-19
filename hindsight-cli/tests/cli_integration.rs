//! Integration tests for the hindsight CLI commands.
//!
//! These tests require a running hindsight API server.
//! Set HINDSIGHT_API_URL environment variable to point to the server.
//! Tests will be skipped if the server is not available.

use std::env;
use std::process::Command;

/// Check if the API server is available
fn server_available() -> bool {
    let api_url = env::var("HINDSIGHT_API_URL").unwrap_or_else(|_| "http://localhost:8080".to_string());
    let health_url = format!("{}/health", api_url);

    match reqwest::blocking::get(&health_url) {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    }
}

/// Helper macro to skip tests when server is not available
macro_rules! skip_if_no_server {
    () => {
        if !server_available() {
            eprintln!("Skipping test: API server not available");
            return;
        }
    };
}

/// Get the path to the hindsight binary
fn hindsight_binary() -> String {
    env::var("CARGO_BIN_EXE_hindsight")
        .unwrap_or_else(|_| {
            // Try common locations
            let target_debug = "./target/debug/hindsight";
            let target_release = "./target/release/hindsight";
            if std::path::Path::new(target_debug).exists() {
                target_debug.to_string()
            } else if std::path::Path::new(target_release).exists() {
                target_release.to_string()
            } else {
                "hindsight".to_string()
            }
        })
}

/// Test bank ID for integration tests - each test needs a unique bank ID
/// to avoid parallel test interference
fn test_bank_id(test_name: &str) -> String {
    format!("cli-test-{}-{}", test_name, std::process::id())
}

/// Run a hindsight CLI command
fn run_hindsight(args: &[&str]) -> std::process::Output {
    let api_url = env::var("HINDSIGHT_API_URL").unwrap_or_else(|_| "http://localhost:8080".to_string());

    Command::new(hindsight_binary())
        .env("HINDSIGHT_API_URL", &api_url)
        .args(args)
        .output()
        .expect("Failed to execute hindsight command")
}

#[test]
fn test_health_check() {
    skip_if_no_server!();

    let output = run_hindsight(&["health"]);

    // Should succeed or fail gracefully
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Either succeeded with "healthy" output or has a reasonable error
    if output.status.success() {
        // Note: output may contain ANSI color codes, so check for key text
        assert!(
            stdout.contains("healthy") || stdout.contains("Health") || stdout.contains("status"),
            "Expected health check output, got: {} / {}",
            stdout,
            stderr
        );
    }
}

#[test]
fn test_health_check_json_output() {
    skip_if_no_server!();

    let output = run_hindsight(&["health", "-o", "json"]);

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        // Should be valid JSON
        let result: serde_json::Value = serde_json::from_str(&stdout)
            .expect(&format!("Expected valid JSON output, got: {}", stdout));

        // Should have status field
        assert!(result.get("status").is_some(), "Expected status field in health response");
    }
}

#[test]
fn test_bank_list() {
    skip_if_no_server!();

    let output = run_hindsight(&["bank", "list"]);

    // Should succeed (even if no banks exist)
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    assert!(
        output.status.success(),
        "Bank list command failed: {} / {}",
        stdout,
        stderr
    );
}

#[test]
fn test_bank_list_json_output() {
    skip_if_no_server!();

    let output = run_hindsight(&["bank", "list", "-o", "json"]);

    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        // Should be valid JSON array
        let _result: serde_json::Value = serde_json::from_str(&stdout)
            .expect(&format!("Expected valid JSON output, got: {}", stdout));
    }
}

#[test]
fn test_bank_create_and_delete() {
    skip_if_no_server!();

    let bank_id = test_bank_id("create-delete");

    // Create a bank
    let output = run_hindsight(&[
        "bank", "create",
        &bank_id,
        "--name", "Test Bank",
        "--mission", "A test bank for CLI integration tests",
    ]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Bank might already exist, which is OK
    let created = output.status.success();

    // Get bank disposition
    let output = run_hindsight(&["bank", "disposition", &bank_id]);
    if created {
        assert!(
            output.status.success(),
            "Bank disposition command failed: {} / {}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }

    // Clean up: delete the bank
    let output = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
    // Deletion should succeed
    if created {
        assert!(
            output.status.success(),
            "Bank delete command failed: {} / {}",
            String::from_utf8_lossy(&output.stdout),
            String::from_utf8_lossy(&output.stderr)
        );
    }
}

#[test]
fn test_memory_list() {
    skip_if_no_server!();

    let bank_id = test_bank_id("memory-list");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // List memories (should be empty for new bank)
    let output = run_hindsight(&["memory", "list", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed (even if empty)
    assert!(
        output.status.success(),
        "Memory list command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_mental_model_list() {
    skip_if_no_server!();

    let bank_id = test_bank_id("mm-list");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // List mental models
    let output = run_hindsight(&["mental-model", "list", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed
    assert!(
        output.status.success(),
        "Mental model list command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_mental_model_create_and_delete() {
    skip_if_no_server!();

    let bank_id = test_bank_id("mm-create");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // Create a mental model
    let output = run_hindsight(&[
        "mental-model", "create",
        &bank_id,
        "Test Model",
        "A test mental model",
    ]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // The create command should succeed
    assert!(
        output.status.success(),
        "Mental model create failed: stdout={}, stderr={}",
        stdout,
        stderr
    );

    // Verify it's in the list
    let output = run_hindsight(&["mental-model", "list", &bank_id, "-o", "json"]);
    let stdout = String::from_utf8_lossy(&output.stdout);

    assert!(
        output.status.success(),
        "Mental model list failed: {}",
        stdout
    );

    // Parse JSON and verify model exists
    if let Ok(result) = serde_json::from_str::<serde_json::Value>(&stdout) {
        if let Some(items) = result.get("items").and_then(|v| v.as_array()) {
            // Check if any model has the name "Test Model"
            let found = items.iter().any(|item| {
                item.get("name").and_then(|v| v.as_str()) == Some("Test Model")
            });
            assert!(found, "Expected to find 'Test Model' in mental models list: {}", stdout);
        }
    }

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_tag_list() {
    skip_if_no_server!();

    let bank_id = test_bank_id("tag-list");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // List tags
    let output = run_hindsight(&["tag", "list", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed (even if no tags)
    assert!(
        output.status.success(),
        "Tag list command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_entity_list() {
    skip_if_no_server!();

    let bank_id = test_bank_id("entity-list");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // List entities
    let output = run_hindsight(&["entity", "list", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed (even if no entities)
    assert!(
        output.status.success(),
        "Entity list command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_operation_list() {
    skip_if_no_server!();

    let bank_id = test_bank_id("op-list");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // List operations
    let output = run_hindsight(&["operation", "list", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed (even if no operations)
    assert!(
        output.status.success(),
        "Operation list command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_bank_stats() {
    skip_if_no_server!();

    let bank_id = test_bank_id("bank-stats");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // Get stats
    let output = run_hindsight(&["bank", "stats", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed
    assert!(
        output.status.success(),
        "Bank stats command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_bank_graph() {
    skip_if_no_server!();

    let bank_id = test_bank_id("bank-graph");

    // Create the bank first
    let _ = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    // Get graph
    let output = run_hindsight(&["bank", "graph", &bank_id]);

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    // Should succeed (even if empty graph)
    assert!(
        output.status.success(),
        "Bank graph command failed: {} / {}",
        stdout,
        stderr
    );

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_bank_update() {
    skip_if_no_server!();

    let bank_id = test_bank_id("bank-update");

    // Create the bank first
    let output = run_hindsight(&["bank", "create", &bank_id, "--name", "Test Bank"]);

    if output.status.success() {
        // Update the bank
        let output = run_hindsight(&[
            "bank", "update", &bank_id,
            "--name", "Updated Test Bank",
        ]);

        let stdout = String::from_utf8_lossy(&output.stdout);
        let stderr = String::from_utf8_lossy(&output.stderr);

        assert!(
            output.status.success(),
            "Bank update command failed: {} / {}",
            stdout,
            stderr
        );

        // Verify the update
        let output = run_hindsight(&["bank", "disposition", &bank_id, "-o", "json"]);
        if output.status.success() {
            let stdout = String::from_utf8_lossy(&output.stdout);
            let result: serde_json::Value = serde_json::from_str(&stdout).unwrap();
            assert_eq!(
                result.get("name").and_then(|v| v.as_str()),
                Some("Updated Test Bank")
            );
        }
    }

    // Clean up
    let _ = run_hindsight(&["bank", "delete", &bank_id, "-y"]);
}

#[test]
fn test_json_yaml_output_formats() {
    skip_if_no_server!();

    // Test JSON output for bank list
    let output = run_hindsight(&["bank", "list", "-o", "json"]);
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let _: serde_json::Value = serde_json::from_str(&stdout)
            .expect("Expected valid JSON for bank list");
    }

    // Test YAML output for bank list
    let output = run_hindsight(&["bank", "list", "-o", "yaml"]);
    if output.status.success() {
        let stdout = String::from_utf8_lossy(&output.stdout);
        let _: serde_yaml::Value = serde_yaml::from_str(&stdout)
            .expect("Expected valid YAML for bank list");
    }
}

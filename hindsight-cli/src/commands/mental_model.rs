//! Mental model commands for managing structured knowledge containers.

use anyhow::{Context, Result};
use std::fs;
use std::path::PathBuf;

use crate::api::ApiClient;
use crate::output::{self, OutputFormat};
use crate::ui;

use hindsight_client::types;
use serde::Deserialize;

// Local types for serde_json::Value deserialization
#[derive(Debug, Deserialize)]
struct VersionListResponse {
    versions: Vec<VersionItem>,
}

#[derive(Debug, Deserialize)]
struct VersionItem {
    version: i64,
    created_at: String,
    observations_count: Option<i64>,
}

#[derive(Debug, Deserialize)]
struct VersionDetailResponse {
    version: i64,
    created_at: String,
    observations: Option<Vec<ObservationData>>,
}

#[derive(Debug, Deserialize)]
struct ObservationData {
    title: String,
    content: String,
    trend: Option<String>,
    evidence: Option<Vec<EvidenceData>>,
}

#[derive(Debug, Deserialize)]
struct EvidenceData {
    quote: String,
}

/// List mental models for a bank
pub fn list(
    client: &ApiClient,
    bank_id: &str,
    subtype: Option<String>,
    tags: Option<Vec<String>>,
    tags_match: Option<String>,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching mental models..."))
    } else {
        None
    };

    let response = client.list_mental_models(
        bank_id,
        subtype.as_deref(),
        tags,
        tags_match.as_deref(),
        verbose,
    );

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                ui::print_section_header(&format!("Mental Models: {}", bank_id));

                if result.items.is_empty() {
                    println!("  {}", ui::dim("No mental models found."));
                } else {
                    for model in &result.items {
                        let subtype_str = &model.subtype;
                        let obs_count = model.observations.len();

                        println!(
                            "  {} {} {}",
                            ui::gradient_start(&model.id),
                            ui::dim(&format!("[{}]", subtype_str)),
                            model.name
                        );

                        if !model.description.is_empty() {
                            println!("    {}", ui::dim(&model.description));
                        }

                        println!(
                            "    {} observations, v{}",
                            obs_count,
                            model.version
                        );

                        // Show freshness status
                        if let Some(freshness) = &model.freshness {
                            let status = if freshness.is_up_to_date {
                                ui::gradient_start("up to date")
                            } else {
                                ui::gradient_end("needs refresh")
                            };
                            println!("    {}", status);
                        }

                        println!();
                    }
                }
            } else {
                output::print_output(&result, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Get a specific mental model
pub fn get(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching mental model..."))
    } else {
        None
    };

    let response = client.get_mental_model(bank_id, model_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(model) => {
            if output_format == OutputFormat::Pretty {
                print_mental_model_detail(&model);
            } else {
                output::print_output(&model, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Create a new mental model
pub fn create(
    client: &ApiClient,
    bank_id: &str,
    name: &str,
    description: &str,
    subtype: Option<String>,
    tags: Option<Vec<String>>,
    observations_file: Option<PathBuf>,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Creating mental model..."))
    } else {
        None
    };

    // Parse observations from file if provided
    let observations = if let Some(path) = observations_file {
        let content = fs::read_to_string(&path)
            .with_context(|| format!("Failed to read observations file: {}", path.display()))?;
        let obs: Vec<types::ObservationInput> = serde_json::from_str(&content)
            .with_context(|| format!("Failed to parse observations JSON from: {}", path.display()))?;
        Some(obs)
    } else {
        None
    };

    let request = types::CreateMentalModelRequest {
        name: name.to_string(),
        description: description.to_string(),
        subtype: subtype.unwrap_or_else(|| "pinned".to_string()),
        tags: tags.unwrap_or_default(),
        observations,
    };

    let response = client.create_mental_model(bank_id, &request, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(model) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Mental model '{}' created successfully", model.id));
                println!();
                print_mental_model_detail(&model);
            } else {
                output::print_output(&model, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Delete a mental model
pub fn delete(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    yes: bool,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    // Confirmation prompt unless -y flag is used
    if !yes && output_format == OutputFormat::Pretty {
        let message = format!(
            "Are you sure you want to delete mental model '{}'? This cannot be undone.",
            model_id
        );

        let confirmed = ui::prompt_confirmation(&message)?;

        if !confirmed {
            ui::print_info("Operation cancelled");
            return Ok(());
        }
    }

    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Deleting mental model..."))
    } else {
        None
    };

    let response = client.delete_mental_model(bank_id, model_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                if result.success {
                    ui::print_success(&format!("Mental model '{}' deleted successfully", model_id));
                } else {
                    ui::print_error("Failed to delete mental model");
                }
            } else {
                output::print_output(&result, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Update a mental model's name or description
pub fn update(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    name: Option<String>,
    description: Option<String>,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    if name.is_none() && description.is_none() {
        anyhow::bail!("At least one of --name or --description must be provided");
    }

    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Updating mental model..."))
    } else {
        None
    };

    let request = types::UpdateMentalModelRequest { name, description };

    let response = client.update_mental_model(bank_id, model_id, &request, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(model) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Mental model '{}' updated successfully", model_id));
                println!();
                print_mental_model_detail(&model);
            } else {
                output::print_output(&model, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Refresh all mental models (or filtered by subtype)
pub fn refresh_all(
    client: &ApiClient,
    bank_id: &str,
    subtype: Option<String>,
    tags: Option<Vec<String>>,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Submitting refresh request..."))
    } else {
        None
    };

    let response = client.refresh_mental_models(bank_id, subtype.as_deref(), tags, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success("Refresh operation submitted");
                println!("  Operation ID: {}", result.operation_id);
                println!("  Status: {}", result.status);
            } else {
                output::print_output(&result, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Refresh a specific mental model
pub fn refresh(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Submitting refresh request..."))
    } else {
        None
    };

    let response = client.refresh_mental_model(bank_id, model_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Refresh submitted for model '{}'", model_id));
                println!("  Operation ID: {}", result.operation_id);
                println!("  Status: {}", result.status);
            } else {
                output::print_output(&result, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// List version history for a mental model
pub fn versions(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching versions..."))
    } else {
        None
    };

    let response = client.list_mental_model_versions(bank_id, model_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(value) => {
            if output_format == OutputFormat::Pretty {
                let result: VersionListResponse = serde_json::from_value(value)
                    .with_context(|| "Failed to parse version list response")?;

                ui::print_section_header(&format!("Version History: {}", model_id));

                if result.versions.is_empty() {
                    println!("  {}", ui::dim("No versions found."));
                } else {
                    for version in &result.versions {
                        let obs_count = version.observations_count.unwrap_or(0);
                        println!(
                            "  {} v{} - {} observations",
                            ui::gradient_start(&format!("v{}", version.version)),
                            version.version,
                            obs_count
                        );
                        println!("    {}", ui::dim(&version.created_at));
                    }
                }
            } else {
                output::print_output(&value, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Get a specific version of a mental model
pub fn version(
    client: &ApiClient,
    bank_id: &str,
    model_id: &str,
    version_num: i64,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching version..."))
    } else {
        None
    };

    let response = client.get_mental_model_version(bank_id, model_id, version_num, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(value) => {
            if output_format == OutputFormat::Pretty {
                let result: VersionDetailResponse = serde_json::from_value(value)
                    .with_context(|| "Failed to parse version response")?;

                ui::print_section_header(&format!("{} v{}", model_id, version_num));

                println!("  {} {}", ui::dim("Created:"), result.created_at);
                println!();

                if let Some(observations) = &result.observations {
                    if observations.is_empty() {
                        println!("  {}", ui::dim("No observations in this version."));
                    } else {
                        for (i, obs) in observations.iter().enumerate() {
                            print_observation_data(i + 1, obs);
                        }
                    }
                }
            } else {
                output::print_output(&value, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

// Helper function to print mental model details
fn print_mental_model_detail(model: &types::MentalModelResponse) {
    ui::print_section_header(&model.name);

    let subtype_str = &model.subtype;
    println!("  {} {}", ui::dim("ID:"), ui::gradient_start(&model.id));
    println!("  {} {}", ui::dim("Subtype:"), subtype_str);
    println!("  {} v{}", ui::dim("Version:"), model.version);

    if !model.description.is_empty() {
        println!("  {} {}", ui::dim("Description:"), &model.description);
    }

    if !model.tags.is_empty() {
        println!("  {} {}", ui::dim("Tags:"), model.tags.join(", "));
    }

    // Freshness status
    if let Some(freshness) = &model.freshness {
        println!();
        println!("{}", ui::gradient_text("─── Freshness ───"));
        let status = if freshness.is_up_to_date {
            ui::gradient_start("Up to date")
        } else {
            ui::gradient_end("Needs refresh")
        };
        println!("  {} {}", ui::dim("Status:"), status);

        if let Some(last_refresh) = &freshness.last_refresh_at {
            println!("  {} {}", ui::dim("Last refresh:"), last_refresh);
        }

        if freshness.memories_since_refresh > 0 {
            println!("  {} {}", ui::dim("New memories:"), freshness.memories_since_refresh);
        }

        if !freshness.reasons.is_empty() {
            println!("  {} {}", ui::dim("Reasons:"), freshness.reasons.join(", "));
        }
    }

    // Observations
    println!();
    println!("{}", ui::gradient_text("─── Observations ───"));
    println!();

    if model.observations.is_empty() {
        println!("  {}", ui::dim("No observations yet."));
    } else {
        for (i, obs) in model.observations.iter().enumerate() {
            print_observation(i + 1, obs);
        }
    }

    println!();
}

fn print_observation(index: usize, obs: &types::MentalModelObservationResponse) {
    let trend_str = &obs.trend;
    let trend_colored = match trend_str.as_str() {
        "strengthening" => ui::gradient_start(trend_str),
        "stable" => ui::gradient_mid(trend_str),
        "weakening" | "stale" => ui::gradient_end(trend_str),
        _ => trend_str.to_string(),
    };

    println!("  {}. {} {}", index, ui::gradient_mid(&obs.title), ui::dim(&format!("[{}]", trend_colored)));
    println!("     {}", obs.content);

    // Show evidence if available
    if !obs.evidence.is_empty() {
        println!("     {} evidence items:", ui::dim(&obs.evidence.len().to_string()));
        for ev in obs.evidence.iter().take(2) {
            // Show first 2 evidence items
            let quote_preview: String = ev.quote.chars().take(60).collect();
            let ellipsis = if ev.quote.len() > 60 { "..." } else { "" };
            println!("       • \"{}{}\"", quote_preview, ellipsis);
        }
        if obs.evidence.len() > 2 {
            println!("       {} more...", ui::dim(&format!("+ {}", obs.evidence.len() - 2)));
        }
    }

    println!();
}

fn print_observation_data(index: usize, obs: &ObservationData) {
    let trend_str = obs.trend.as_deref().unwrap_or("unknown");
    let trend_colored = match trend_str {
        "strengthening" => ui::gradient_start(trend_str),
        "stable" => ui::gradient_mid(trend_str),
        "weakening" | "stale" => ui::gradient_end(trend_str),
        _ => trend_str.to_string(),
    };

    println!("  {}. {} {}", index, ui::gradient_mid(&obs.title), ui::dim(&format!("[{}]", trend_colored)));
    println!("     {}", obs.content);

    // Show evidence if available
    if let Some(evidence) = &obs.evidence {
        if !evidence.is_empty() {
            println!("     {} evidence items:", ui::dim(&evidence.len().to_string()));
            for ev in evidence.iter().take(2) {
                // Show first 2 evidence items
                let quote_preview: String = ev.quote.chars().take(60).collect();
                let ellipsis = if ev.quote.len() > 60 { "..." } else { "" };
                println!("       • \"{}{}\"", quote_preview, ellipsis);
            }
            if evidence.len() > 2 {
                println!("       {} more...", ui::dim(&format!("+ {}", evidence.len() - 2)));
            }
        }
    }

    println!();
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_observation_input_serialization() {
        let obs = types::ObservationInput {
            title: "Test observation".to_string(),
            content: "Test content".to_string(),
        };
        let json = serde_json::to_string(&obs).unwrap();
        assert!(json.contains("Test observation"));
        assert!(json.contains("Test content"));
    }

    #[test]
    fn test_version_list_response_deserialization() {
        let json = r#"{
            "versions": [
                {"version": 1, "created_at": "2024-01-10T10:00:00Z", "observations_count": 5},
                {"version": 2, "created_at": "2024-01-15T10:00:00Z", "observations_count": 8}
            ]
        }"#;

        let value: serde_json::Value = serde_json::from_str(json).unwrap();
        let result: VersionListResponse = serde_json::from_value(value).unwrap();

        assert_eq!(result.versions.len(), 2);
        assert_eq!(result.versions[0].version, 1);
        assert_eq!(result.versions[1].version, 2);
        assert_eq!(result.versions[1].observations_count, Some(8));
    }

    #[test]
    fn test_version_detail_response_deserialization() {
        let json = r#"{
            "version": 1,
            "created_at": "2024-01-10T10:00:00Z",
            "observations": [
                {
                    "title": "Test observation",
                    "content": "Test content",
                    "trend": "stable",
                    "evidence": [{"quote": "test evidence"}]
                }
            ]
        }"#;

        let value: serde_json::Value = serde_json::from_str(json).unwrap();
        let result: VersionDetailResponse = serde_json::from_value(value).unwrap();

        assert_eq!(result.created_at, "2024-01-10T10:00:00Z");
        let observations = result.observations.unwrap();
        assert_eq!(observations.len(), 1);
        assert_eq!(observations[0].title, "Test observation");
        assert_eq!(observations[0].trend, Some("stable".to_string()));
    }

    #[test]
    fn test_observation_data_deserialization() {
        let json = r#"{
            "title": "Test Title",
            "content": "Test Content",
            "trend": "strengthening",
            "evidence": [
                {"quote": "Evidence 1"},
                {"quote": "Evidence 2"}
            ]
        }"#;

        let result: ObservationData = serde_json::from_str(json).unwrap();

        assert_eq!(result.title, "Test Title");
        assert_eq!(result.content, "Test Content");
        assert_eq!(result.trend, Some("strengthening".to_string()));
        let evidence = result.evidence.unwrap();
        assert_eq!(evidence.len(), 2);
        assert_eq!(evidence[0].quote, "Evidence 1");
    }

    #[test]
    fn test_create_mental_model_request() {
        let request = types::CreateMentalModelRequest {
            name: "Test Model".to_string(),
            description: "A test model".to_string(),
            subtype: "pinned".to_string(),
            tags: vec!["test".to_string()],
            observations: None,
        };

        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("Test Model"));
        assert!(json.contains("pinned"));
        assert!(json.contains("test"));
    }

    #[test]
    fn test_update_mental_model_request() {
        let request = types::UpdateMentalModelRequest {
            name: Some("Updated Name".to_string()),
            description: None,
        };

        let json = serde_json::to_string(&request).unwrap();
        assert!(json.contains("Updated Name"));
    }

    #[test]
    fn test_async_operation_submit_response_deserialization() {
        let json = r#"{
            "operation_id": "op-123",
            "status": "pending"
        }"#;

        let result: types::AsyncOperationSubmitResponse = serde_json::from_str(json).unwrap();

        assert_eq!(result.operation_id, "op-123");
        assert_eq!(result.status, "pending");
    }
}

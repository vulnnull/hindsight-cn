//! Reflection commands for managing user-curated summaries.

use anyhow::Result;

use crate::api::ApiClient;
use crate::output::{self, OutputFormat};
use crate::ui;

use hindsight_client::types;

/// List reflections for a bank
pub fn list(
    client: &ApiClient,
    bank_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching reflections..."))
    } else {
        None
    };

    let response = client.list_reflections(bank_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                ui::print_section_header(&format!("Reflections: {}", bank_id));

                if result.items.is_empty() {
                    println!("  {}", ui::dim("No reflections found."));
                } else {
                    for reflection in &result.items {
                        println!(
                            "  {} {}",
                            ui::gradient_start(&reflection.id),
                            reflection.name
                        );

                        // Show content preview
                        let preview: String = reflection.content.chars().take(80).collect();
                        let ellipsis = if reflection.content.len() > 80 { "..." } else { "" };
                        println!("    {}{}", ui::dim(&preview), ellipsis);

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

/// Get a specific reflection
pub fn get(
    client: &ApiClient,
    bank_id: &str,
    reflection_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching reflection..."))
    } else {
        None
    };

    let response = client.get_reflection(bank_id, reflection_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(reflection) => {
            if output_format == OutputFormat::Pretty {
                print_reflection_detail(&reflection);
            } else {
                output::print_output(&reflection, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Create a new reflection
pub fn create(
    client: &ApiClient,
    bank_id: &str,
    name: &str,
    source_query: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Creating reflection..."))
    } else {
        None
    };

    let request = types::CreateReflectionRequest {
        name: name.to_string(),
        source_query: source_query.to_string(),
        max_tokens: 2048,
        tags: vec![],
    };

    let response = client.create_reflection(bank_id, &request, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(result) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Reflection created, operation_id: {}", result.operation_id));
            } else {
                output::print_output(&result, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Update a reflection
pub fn update(
    client: &ApiClient,
    bank_id: &str,
    reflection_id: &str,
    name: Option<String>,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    if name.is_none() {
        anyhow::bail!("--name must be provided");
    }

    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Updating reflection..."))
    } else {
        None
    };

    let request = types::UpdateReflectionRequest { name };

    let response = client.update_reflection(bank_id, reflection_id, &request, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(reflection) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Reflection '{}' updated successfully", reflection_id));
                println!();
                print_reflection_detail(&reflection);
            } else {
                output::print_output(&reflection, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Delete a reflection
pub fn delete(
    client: &ApiClient,
    bank_id: &str,
    reflection_id: &str,
    yes: bool,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    // Confirmation prompt unless -y flag is used
    if !yes && output_format == OutputFormat::Pretty {
        let message = format!(
            "Are you sure you want to delete reflection '{}'? This cannot be undone.",
            reflection_id
        );

        let confirmed = ui::prompt_confirmation(&message)?;

        if !confirmed {
            ui::print_info("Operation cancelled");
            return Ok(());
        }
    }

    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Deleting reflection..."))
    } else {
        None
    };

    let response = client.delete_reflection(bank_id, reflection_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(_) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Reflection '{}' deleted successfully", reflection_id));
            } else {
                println!("{{\"success\": true}}");
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

/// Refresh a reflection
pub fn refresh(
    client: &ApiClient,
    bank_id: &str,
    reflection_id: &str,
    verbose: bool,
    output_format: OutputFormat,
) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Submitting reflection refresh..."))
    } else {
        None
    };

    let response = client.refresh_reflection(bank_id, reflection_id, verbose);

    if let Some(mut sp) = spinner {
        sp.finish();
    }

    match response {
        Ok(operation) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!(
                    "Reflection refresh submitted. Operation ID: {}",
                    operation.operation_id
                ));
                println!("  {} {}", ui::dim("Status:"), operation.status);
                println!();
                println!("{}", ui::dim("Use 'hindsight operations get' to check the operation status."));
            } else {
                output::print_output(&operation, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e),
    }
}

// Helper function to print reflection details
fn print_reflection_detail(reflection: &types::ReflectionResponse) {
    ui::print_section_header(&reflection.name);

    println!("  {} {}", ui::dim("ID:"), ui::gradient_start(&reflection.id));
    println!("  {} {}", ui::dim("Source Query:"), &reflection.source_query);

    println!();
    println!("{}", ui::gradient_text("─── Content ───"));
    println!();
    println!("{}", &reflection.content);
    println!();
}

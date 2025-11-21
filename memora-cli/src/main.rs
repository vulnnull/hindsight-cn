mod api;
mod config;
mod errors;
mod output;
mod ui;

use anyhow::{Context, Result};
use api::{ApiClient, BatchMemoryRequest, MemoryItem, SearchRequest, ThinkRequest};
use clap::{Parser, Subcommand, ValueEnum};
use config::Config;
use output::OutputFormat;
use std::fs;
use std::path::PathBuf;
use walkdir::WalkDir;

#[derive(Debug, Clone, Copy, ValueEnum)]
enum Format {
    Pretty,
    Json,
    Yaml,
}

impl From<Format> for OutputFormat {
    fn from(f: Format) -> Self {
        match f {
            Format::Pretty => OutputFormat::Pretty,
            Format::Json => OutputFormat::Json,
            Format::Yaml => OutputFormat::Yaml,
        }
    }
}

#[derive(Parser)]
#[command(name = "memora")]
#[command(about = "Memora CLI - Semantic memory system", long_about = None)]
#[command(version)]
#[command(after_help = get_after_help())]
struct Cli {
    /// Output format (pretty, json, yaml)
    #[arg(short = 'o', long, global = true, default_value = "pretty")]
    output: Format,

    /// Show verbose output including full requests and responses
    #[arg(short = 'v', long, global = true)]
    verbose: bool,

    #[command(subcommand)]
    command: Commands,
}

fn get_after_help() -> String {
    let config = config::Config::load().ok();
    let (api_url, source) = match &config {
        Some(c) => (c.api_url.as_str(), c.source.to_string()),
        None => ("http://localhost:8080", "default".to_string()),
    };
    format!(
        "Current API URL: {} (from {})\n\nRun 'memora configure' to change the API URL.",
        api_url, source
    )
}

#[derive(Subcommand)]
enum Commands {
    /// Manage agents (list, profile, stats)
    #[command(subcommand)]
    Agent(AgentCommands),

    /// Manage memories (search, think, put, delete)
    #[command(subcommand)]
    Memory(MemoryCommands),

    /// Manage documents (list, get, delete)
    #[command(subcommand)]
    Document(DocumentCommands),

    /// Manage async operations (list, cancel)
    #[command(subcommand)]
    Operation(OperationCommands),

    /// Configure the CLI (API URL, etc.)
    #[command(after_help = "Configuration priority:\n  1. Environment variable (MEMORA_API_URL) - highest priority\n  2. Config file (~/.memora/config)\n  3. Default (http://localhost:8080)")]
    Configure {
        /// API URL to connect to (interactive prompt if not provided)
        #[arg(long)]
        api_url: Option<String>,
    },
}

#[derive(Subcommand)]
enum AgentCommands {
    /// List all agents
    List,

    /// Get agent profile (personality + background)
    Profile {
        /// Agent ID
        agent_id: String,
    },

    /// Get memory statistics for an agent
    Stats {
        /// Agent ID
        agent_id: String,
    },

    /// Set agent name
    Name {
        /// Agent ID
        agent_id: String,

        /// Agent name
        name: String,
    },

    /// Set or merge agent background
    Background {
        /// Agent ID
        agent_id: String,

        /// Background content
        content: String,

        /// Skip automatic personality inference
        #[arg(long)]
        no_update_personality: bool,
    },
}

#[derive(Subcommand)]
enum MemoryCommands {
    /// Search for memories using semantic search
    Search {
        /// Agent ID
        agent_id: String,

        /// Search query
        query: String,

        /// Fact types to search (world, agent, opinion)
        #[arg(short = 't', long, value_delimiter = ',', default_values = &["world", "agent", "opinion"])]
        fact_type: Vec<String>,

        /// Thinking budget
        #[arg(short = 'b', long, default_value = "100")]
        budget: i32,

        /// Maximum tokens for results
        #[arg(long, default_value = "4096")]
        max_tokens: i32,

        /// Show trace information
        #[arg(long)]
        trace: bool,
    },

    /// Generate answers using agent identity
    Think {
        /// Agent ID
        agent_id: String,

        /// Query to think about
        query: String,

        /// Thinking budget
        #[arg(short = 'b', long, default_value = "50")]
        budget: i32,

        /// Additional context
        #[arg(short = 'c', long)]
        context: Option<String>,
    },

    /// Store a single memory
    Put {
        /// Agent ID
        agent_id: String,

        /// Memory content
        content: String,

        /// Document ID (auto-generated if not provided)
        #[arg(short = 'd', long)]
        doc_id: Option<String>,

        /// Context for the memory
        #[arg(short = 'c', long)]
        context: Option<String>,

        /// Queue for background processing
        #[arg(long)]
        r#async: bool,
    },

    /// Bulk import memories from files
    PutFiles {
        /// Agent ID
        agent_id: String,

        /// Path to file or directory
        path: PathBuf,

        /// Search directories recursively
        #[arg(short = 'r', long, default_value = "true")]
        recursive: bool,

        /// Context for all memories
        #[arg(short = 'c', long)]
        context: Option<String>,

        /// Queue for background processing
        #[arg(long)]
        r#async: bool,
    },

    /// Delete a memory unit
    Delete {
        /// Agent ID
        agent_id: String,

        /// Memory unit ID
        unit_id: String,
    },

    /// Clear all memories for an agent
    Clear {
        /// Agent ID
        agent_id: String,

        /// Fact type to clear (world, agent, opinion). If not specified, clears all types.
        #[arg(short = 't', long, value_parser = ["world", "agent", "opinion"])]
        fact_type: Option<String>,

        /// Skip confirmation prompt
        #[arg(short = 'y', long)]
        yes: bool,
    },
}

#[derive(Subcommand)]
enum DocumentCommands {
    /// List documents for an agent
    List {
        /// Agent ID
        agent_id: String,

        /// Search query to filter documents
        #[arg(short = 'q', long)]
        query: Option<String>,

        /// Maximum number of results
        #[arg(short = 'l', long, default_value = "100")]
        limit: i32,

        /// Offset for pagination
        #[arg(short = 's', long, default_value = "0")]
        offset: i32,
    },

    /// Get a specific document by ID
    Get {
        /// Agent ID
        agent_id: String,

        /// Document ID
        document_id: String,
    },

    /// Delete a document and all its memory units
    Delete {
        /// Agent ID
        agent_id: String,

        /// Document ID
        document_id: String,
    },
}

#[derive(Subcommand)]
enum OperationCommands {
    /// List async operations for an agent
    List {
        /// Agent ID
        agent_id: String,
    },

    /// Cancel a pending async operation
    Cancel {
        /// Agent ID
        agent_id: String,

        /// Operation ID
        operation_id: String,
    },
}

fn main() {
    if let Err(e) = run() {
        std::process::exit(1);
    }
}

fn run() -> Result<()> {
    let cli = Cli::parse();

    let output_format: OutputFormat = cli.output.into();
    let verbose = cli.verbose;

    // Handle configure command before loading full config (it doesn't need API client)
    if let Commands::Configure { api_url } = cli.command {
        return handle_configure(api_url, output_format);
    }

    // Load configuration
    let config = Config::from_env().unwrap_or_else(|e| {
        ui::print_error(&format!("Configuration error: {}", e));
        errors::print_config_help();
        std::process::exit(1);
    });

    let api_url = config.api_url().to_string();

    // Create API client
    let client = ApiClient::new(api_url.clone()).unwrap_or_else(|e| {
        errors::handle_api_error(e, &api_url);
    });

    // Execute command and handle errors
    let result: Result<()> = match cli.command {
        Commands::Configure { .. } => unreachable!(), // Handled above
        Commands::Agent(agent_cmd) => match agent_cmd {
            AgentCommands::List => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching agents..."))
                } else {
                    None
                };

                let response = client.list_agents(verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(agents_list) => {
                        if output_format == OutputFormat::Pretty {
                            if agents_list.is_empty() {
                                ui::print_warning("No agents found");
                            } else {
                                ui::print_info(&format!("Found {} agent(s)", agents_list.len()));
                                for agent in &agents_list {
                                    println!("  - {}", agent.agent_id);
                                }
                            }
                        } else {
                            output::print_output(&agents_list, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            AgentCommands::Profile { agent_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching profile..."))
                } else {
                    None
                };

                let response = client.get_profile(&agent_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(profile) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_profile(&profile);
                        } else {
                            output::print_output(&profile, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            AgentCommands::Stats { agent_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching statistics..."))
                } else {
                    None
                };

                let response = client.get_stats(&agent_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(stats) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_info(&format!("Statistics for agent '{}'", agent_id));
                            println!();

                            println!("  📊 Overview");
                            println!("    Total Memory Units:  {}", stats.total_nodes);
                            println!("    Total Links:         {}", stats.total_links);
                            println!("    Total Documents:     {}", stats.total_documents);
                            println!();

                            println!("  🧠 Memory Units by Type");
                            let mut fact_types: Vec<_> = stats.nodes_by_fact_type.iter().collect();
                            fact_types.sort_by_key(|(k, _)| *k);
                            for (fact_type, count) in fact_types {
                                let icon = match fact_type.as_str() {
                                    "world" => "🌍",
                                    "agent" => "🤖",
                                    "opinion" => "💭",
                                    _ => "•"
                                };
                                println!("    {} {:<10} {}", icon, fact_type, count);
                            }
                            println!();

                            println!("  🔗 Links by Type");
                            let mut link_types: Vec<_> = stats.links_by_link_type.iter().collect();
                            link_types.sort_by_key(|(k, _)| *k);
                            for (link_type, count) in link_types {
                                let icon = match link_type.as_str() {
                                    "temporal" => "⏰",
                                    "semantic" => "🔤",
                                    "entity" => "🏷️",
                                    _ => "•"
                                };
                                println!("    {} {:<10} {}", icon, link_type, count);
                            }
                            println!();

                            println!("  🔗 Links by Fact Type");
                            let mut fact_type_links: Vec<_> = stats.links_by_fact_type.iter().collect();
                            fact_type_links.sort_by_key(|(k, _)| *k);
                            for (fact_type, count) in fact_type_links {
                                let icon = match fact_type.as_str() {
                                    "world" => "🌍",
                                    "agent" => "🤖",
                                    "opinion" => "💭",
                                    _ => "•"
                                };
                                println!("    {} {:<10} {}", icon, fact_type, count);
                            }
                            println!();

                            if !stats.links_breakdown.is_empty() {
                                println!("  📈 Detailed Link Breakdown");
                                let mut fact_types: Vec<_> = stats.links_breakdown.iter().collect();
                                fact_types.sort_by_key(|(k, _)| *k);
                                for (fact_type, link_types) in fact_types {
                                    let icon = match fact_type.as_str() {
                                        "world" => "🌍",
                                        "agent" => "🤖",
                                        "opinion" => "💭",
                                        _ => "•"
                                    };
                                    println!("    {} {}", icon, fact_type);
                                    let mut sorted_links: Vec<_> = link_types.iter().collect();
                                    sorted_links.sort_by_key(|(k, _)| *k);
                                    for (link_type, count) in sorted_links {
                                        println!("      - {:<10} {}", link_type, count);
                                    }
                                }
                                println!();
                            }

                            if stats.pending_operations > 0 || stats.failed_operations > 0 {
                                println!("  ⚙️  Operations");
                                if stats.pending_operations > 0 {
                                    println!("    ⏳ Pending:  {}", stats.pending_operations);
                                }
                                if stats.failed_operations > 0 {
                                    println!("    ❌ Failed:   {}", stats.failed_operations);
                                }
                            }
                        } else {
                            output::print_output(&stats, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            AgentCommands::Name {
                agent_id,
                name,
            } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Updating agent name..."))
                } else {
                    None
                };

                let response = client.update_agent_name(
                    &agent_id,
                    &name,
                    verbose,
                );

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(profile) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_success(&format!("Agent name updated to '{}'", profile.name));
                        } else {
                            output::print_output(&profile, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            AgentCommands::Background {
                agent_id,
                content,
                no_update_personality,
            } => {
                let current_profile = if !no_update_personality {
                    client.get_profile(&agent_id, verbose).ok()
                } else {
                    None
                };

                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Merging background..."))
                } else {
                    None
                };

                let response = client.add_background(
                    &agent_id,
                    &content,
                    !no_update_personality,
                    verbose,
                );

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(profile) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_success("Background updated successfully");
                            println!("\n{}", profile.background);

                            if !no_update_personality {
                                if let (Some(old_p), Some(new_p)) =
                                    (current_profile.as_ref().map(|p| p.personality), &profile.personality)
                                {
                                    println!("\nPersonality changes:");
                                    println!("  Openness:          {:.2} → {:.2}", old_p.openness, new_p.openness);
                                    println!("  Conscientiousness: {:.2} → {:.2}", old_p.conscientiousness, new_p.conscientiousness);
                                    println!("  Extraversion:      {:.2} → {:.2}", old_p.extraversion, new_p.extraversion);
                                    println!("  Agreeableness:     {:.2} → {:.2}", old_p.agreeableness, new_p.agreeableness);
                                    println!("  Neuroticism:       {:.2} → {:.2}", old_p.neuroticism, new_p.neuroticism);
                                }
                            }
                        } else {
                            output::print_output(&profile, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }
        },

        Commands::Memory(memory_cmd) => match memory_cmd {
            MemoryCommands::Search {
                agent_id,
                query,
                fact_type,
                budget,
                max_tokens,
                trace,
            } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Searching memories..."))
                } else {
                    None
                };

                let request = SearchRequest {
                    query,
                    fact_type,
                    thinking_budget: budget,
                    max_tokens,
                    trace,
                };

                let response = client.search(&agent_id, request, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_search_results(&result, trace);
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            MemoryCommands::Think {
                agent_id,
                query,
                budget,
                context,
            } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Thinking..."))
                } else {
                    None
                };

                let request = ThinkRequest {
                    query,
                    thinking_budget: budget,
                    context,
                };

                let response = client.think(&agent_id, request, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_think_response(&result);
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            MemoryCommands::Put {
                agent_id,
                content,
                doc_id,
                context,
                r#async,
            } => {
                let doc_id = doc_id.unwrap_or_else(config::generate_doc_id);

                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Storing memory..."))
                } else {
                    None
                };

                let item = MemoryItem {
                    content: content.clone(),
                    context,
                };

                let request = BatchMemoryRequest {
                    items: vec![item],
                    document_id: Some(doc_id.clone()),
                };

                let response = client.put_memories(&agent_id, request, r#async, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_success(&format!(
                                "Memory stored successfully (document: {})",
                                doc_id
                            ));
                            if let Some(op_id) = result.job_id {
                                println!("  Operation ID: {}", op_id);
                                println!("  Status: queued for background processing");
                            } else {
                                let count = result.stored_count.or(result.items_count).unwrap_or(0);
                                println!("  Stored count: {}", count);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            MemoryCommands::PutFiles {
                agent_id,
                path,
                recursive,
                context,
                r#async,
            } => {
                if !path.exists() {
                    anyhow::bail!("Path does not exist: {}", path.display());
                }

                let mut files = Vec::new();

                if path.is_file() {
                    files.push(path);
                } else if path.is_dir() {
                    if recursive {
                        for entry in WalkDir::new(&path)
                            .into_iter()
                            .filter_map(|e| e.ok())
                            .filter(|e| e.file_type().is_file())
                        {
                            let path = entry.path();
                            if let Some(ext) = path.extension() {
                                if ext == "txt" || ext == "md" {
                                    files.push(path.to_path_buf());
                                }
                            }
                        }
                    } else {
                        for entry in fs::read_dir(&path)? {
                            let entry = entry?;
                            let path = entry.path();
                            if path.is_file() {
                                if let Some(ext) = path.extension() {
                                    if ext == "txt" || ext == "md" {
                                        files.push(path);
                                    }
                                }
                            }
                        }
                    }
                }

                if files.is_empty() {
                    ui::print_warning("No .txt or .md files found");
                    return Ok(());
                }

                ui::print_info(&format!("Found {} files to import", files.len()));

                let pb = ui::create_progress_bar(files.len() as u64, "Processing files");

                let mut items = Vec::new();
                let mut document_id = None;

                for file_path in &files {
                    let content = fs::read_to_string(file_path)
                        .with_context(|| format!("Failed to read file: {}", file_path.display()))?;

                    let doc_id = file_path
                        .file_stem()
                        .and_then(|s| s.to_str())
                        .map(|s| s.to_string())
                        .unwrap_or_else(config::generate_doc_id);

                    if document_id.is_none() {
                        document_id = Some(doc_id);
                    }

                    items.push(MemoryItem {
                        content,
                        context: context.clone(),
                    });

                    pb.inc(1);
                }

                pb.finish_with_message("Files processed");

                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Uploading memories..."))
                } else {
                    None
                };

                let request = BatchMemoryRequest {
                    items,
                    document_id,
                };

                let response = client.put_memories(&agent_id, request, r#async, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_success("Files imported successfully");
                            if let Some(op_id) = result.job_id {
                                println!("  Operation ID: {}", op_id);
                                println!("  Status: queued for background processing");
                            } else {
                                let count = result.stored_count.or(result.items_count).unwrap_or(0);
                                println!("  Total units created: {}", count);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            MemoryCommands::Delete { agent_id, unit_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Deleting memory unit..."))
                } else {
                    None
                };

                let response = client.delete_memory(&agent_id, &unit_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            if result.success {
                                ui::print_success(&result.message);
                            } else {
                                ui::print_error(&result.message);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            MemoryCommands::Clear { agent_id, fact_type, yes } => {
                // Confirmation prompt unless -y flag is used
                if !yes && output_format == OutputFormat::Pretty {
                    let message = if let Some(ft) = &fact_type {
                        format!(
                            "Are you sure you want to clear all '{}' memories for agent '{}'? This cannot be undone.",
                            ft, agent_id
                        )
                    } else {
                        format!(
                            "Are you sure you want to clear ALL memories for agent '{}'? This cannot be undone.",
                            agent_id
                        )
                    };

                    let confirmed = ui::prompt_confirmation(&message)?;

                    if !confirmed {
                        ui::print_info("Operation cancelled");
                        return Ok(());
                    }
                }

                let spinner_msg = if let Some(ft) = &fact_type {
                    format!("Clearing {} memories...", ft)
                } else {
                    "Clearing all memories...".to_string()
                };

                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner(&spinner_msg))
                } else {
                    None
                };

                let response = client.clear_memories(&agent_id, fact_type.as_deref(), verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            if result.success {
                                ui::print_success(&result.message);
                            } else {
                                ui::print_error(&result.message);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }
        },

        Commands::Document(doc_cmd) => match doc_cmd {
            DocumentCommands::List {
                agent_id,
                query,
                limit,
                offset,
            } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching documents..."))
                } else {
                    None
                };

                let response = client.list_documents(&agent_id, query.as_deref(), Some(limit), Some(offset), verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(docs_response) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_info(&format!("Documents for agent '{}' (total: {})", agent_id, docs_response.total));
                            for doc in &docs_response.items {
                                println!("\n  Document ID: {}", doc.id);
                                println!("    Created: {}", doc.created_at);
                                println!("    Updated: {}", doc.updated_at);
                                println!("    Text Length: {}", doc.text_length);
                                println!("    Memory Units: {}", doc.memory_unit_count);
                            }
                        } else {
                            output::print_output(&docs_response, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            DocumentCommands::Get { agent_id, document_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching document..."))
                } else {
                    None
                };

                let response = client.get_document(&agent_id, &document_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(doc) => {
                        if output_format == OutputFormat::Pretty {
                            ui::print_info(&format!("Document: {}", doc.id));
                            println!("  Agent ID: {}", doc.agent_id);
                            println!("  Created: {}", doc.created_at);
                            println!("  Updated: {}", doc.updated_at);
                            println!("  Memory Units: {}", doc.memory_unit_count);
                            println!("\n  Text:\n{}", doc.original_text);
                        } else {
                            output::print_output(&doc, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            DocumentCommands::Delete { agent_id, document_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Deleting document..."))
                } else {
                    None
                };

                let response = client.delete_document(&agent_id, &document_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            if result.success {
                                ui::print_success(&result.message);
                            } else {
                                ui::print_error(&result.message);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }
        },

        Commands::Operation(op_cmd) => match op_cmd {
            OperationCommands::List { agent_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Fetching operations..."))
                } else {
                    None
                };

                let response = client.list_operations(&agent_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(ops_response) => {
                        if output_format == OutputFormat::Pretty {
                            if ops_response.operations.is_empty() {
                                ui::print_info("No operations found");
                            } else {
                                ui::print_info(&format!("Found {} operation(s)", ops_response.operations.len()));
                                for op in &ops_response.operations {
                                    println!("\n  Operation ID: {}", op.id);
                                    println!("    Type: {}", op.task_type);
                                    println!("    Status: {}", op.status);
                                    println!("    Items: {}", op.items_count);
                                    if let Some(doc_id) = &op.document_id {
                                        println!("    Document ID: {}", doc_id);
                                    }
                                }
                            }
                        } else {
                            output::print_output(&ops_response, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }

            OperationCommands::Cancel { agent_id, operation_id } => {
                let spinner = if output_format == OutputFormat::Pretty {
                    Some(ui::create_spinner("Cancelling operation..."))
                } else {
                    None
                };

                let response = client.cancel_operation(&agent_id, &operation_id, verbose);

                if let Some(sp) = spinner {
                    sp.finish_and_clear();
                }

                match response {
                    Ok(result) => {
                        if output_format == OutputFormat::Pretty {
                            if result.success {
                                ui::print_success(&result.message);
                            } else {
                                ui::print_error(&result.message);
                            }
                        } else {
                            output::print_output(&result, output_format)?;
                        }
                        Ok(())
                    }
                    Err(e) => Err(e)
                }
            }
        },
    };

    // Handle API errors with nice messages
    if let Err(e) = result {
        errors::handle_api_error(e, &api_url);
    }

    Ok(())
}

fn handle_configure(api_url: Option<String>, output_format: OutputFormat) -> Result<()> {
    // Load current config to show current state
    let current_config = Config::load().ok();

    if output_format == OutputFormat::Pretty {
        ui::print_info("Memora CLI Configuration");
        println!();

        // Show current configuration
        if let Some(ref config) = current_config {
            println!("  Current API URL: {}", config.api_url);
            println!("  Source: {}", config.source);
            println!();
        }
    }

    // Get the new API URL (from argument or prompt)
    let new_api_url = match api_url {
        Some(url) => url,
        None => {
            // Interactive prompt
            let current = current_config.as_ref().map(|c| c.api_url.as_str());
            config::prompt_api_url(current)?
        }
    };

    // Validate the URL
    if !new_api_url.starts_with("http://") && !new_api_url.starts_with("https://") {
        ui::print_error(&format!(
            "Invalid API URL: {}. Must start with http:// or https://",
            new_api_url
        ));
        return Ok(());
    }

    // Save to config file
    let config_path = Config::save_api_url(&new_api_url)?;

    if output_format == OutputFormat::Pretty {
        ui::print_success(&format!("Configuration saved to {}", config_path.display()));
        println!();
        println!("  API URL: {}", new_api_url);
        println!();
        println!("Note: Environment variable MEMORA_API_URL will override this setting.");
    } else {
        let result = serde_json::json!({
            "api_url": new_api_url,
            "config_path": config_path.display().to_string(),
        });
        output::print_output(&result, output_format)?;
    }

    Ok(())
}

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

#[derive(Subcommand)]
enum Commands {
    /// Search for memories using semantic search
    Search {
        /// Agent ID to search for
        agent_id: String,

        /// Search query
        query: String,

        /// Fact types to search (world, agent, opinion)
        #[arg(short = 't', long, value_delimiter = ',', default_values = &["world", "agent", "opinion"])]
        fact_type: Vec<String>,

        /// Thinking budget for search
        #[arg(short = 'b', long, default_value = "100")]
        budget: i32,

        /// Maximum tokens for results
        #[arg(long, default_value = "4096")]
        max_tokens: i32,

        /// Show trace information (timing, activation counts)
        #[arg(long)]
        trace: bool,
    },

    /// Generate answers using agent identity and memories
    Think {
        /// Agent ID to think as
        agent_id: String,

        /// Query to think about
        query: String,

        /// Thinking budget
        #[arg(short = 'b', long, default_value = "50")]
        budget: i32,
    },

    /// Store a single memory
    Put {
        /// Agent ID to store memory for
        agent_id: String,

        /// Memory content to store
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
        /// Agent ID to store memories for
        agent_id: String,

        /// Path to file or directory
        path: PathBuf,

        /// Search directories recursively
        #[arg(short = 'r', long, default_value = "true")]
        recursive: bool,

        /// Queue for background processing
        #[arg(long)]
        r#async: bool,
    },

    /// List all agents
    Agents,
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
        Commands::Search {
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
                agent_id,
                thinking_budget: budget,
                max_tokens,
                trace,
            };

            let response = client.search(request, verbose);

            if let Some(sp) = spinner {
                sp.finish_and_clear();
            }

            match response {
                Ok(resp) => {
                    if output_format == OutputFormat::Pretty {
                        ui::print_search_results(&resp, trace);
                    } else {
                        output::print_output(&resp, output_format)?;
                    }
                    Ok(())
                }
                Err(e) => Err(e)
            }
        }

        Commands::Think {
            agent_id,
            query,
            budget,
        } => {
            let spinner = if output_format == OutputFormat::Pretty {
                Some(ui::create_spinner("Thinking..."))
            } else {
                None
            };

            let request = ThinkRequest {
                query,
                agent_id,
                thinking_budget: budget,
            };

            let response = client.think(request, verbose);

            if let Some(sp) = spinner {
                sp.finish_and_clear();
            }

            match response {
                Ok(resp) => {
                    if output_format == OutputFormat::Pretty {
                        ui::print_think_response(&resp);
                    } else {
                        output::print_output(&resp, output_format)?;
                    }
                    Ok(())
                }
                Err(e) => Err(e)
            }
        }

        Commands::Put {
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
                agent_id,
                items: vec![item],
                document_id: Some(doc_id.clone()),
            };

            let response = client.put_memories(request, r#async, verbose);

            if let Some(sp) = spinner {
                sp.finish_and_clear();
            }

            match response {
                Ok(resp) => {
                    if output_format == OutputFormat::Pretty {
                        ui::print_stored_memory(&doc_id, &content, r#async);
                        if let Some(job_id) = resp.job_id {
                            ui::print_info(&format!("Job ID: {}", job_id));
                        }
                    } else {
                        output::print_output(&resp, output_format)?;
                    }
                    Ok(())
                }
                Err(e) => Err(e)
            }
        }

        Commands::PutFiles {
            agent_id,
            path,
            recursive,
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

                // Use the first file's stem as the document_id for the batch
                if document_id.is_none() {
                    document_id = Some(doc_id);
                }

                items.push(MemoryItem {
                    content,
                    context: None,
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
                agent_id,
                items,
                document_id,
            };
            let response = client.put_memories(request, r#async, verbose);

            if let Some(sp) = spinner {
                sp.finish_and_clear();
            }

            match response {
                Ok(resp) => {
                    if output_format == OutputFormat::Pretty {
                        if r#async {
                            ui::print_success(&format!(
                                "Queued {} files for background processing",
                                files.len()
                            ));
                            if let Some(job_id) = resp.job_id {
                                ui::print_info(&format!("Job ID: {}", job_id));
                            }
                        } else {
                            ui::print_success(&format!("Successfully stored {} memories", files.len()));
                        }
                    } else {
                        output::print_output(&resp, output_format)?;
                    }
                    Ok(())
                }
                Err(e) => Err(e)
            }
        }

        Commands::Agents => {
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
                Ok(agents) => {
                    if output_format == OutputFormat::Pretty {
                        ui::print_agents_table(&agents);
                    } else {
                        output::print_output(&agents, output_format)?;
                    }
                    Ok(())
                }
                Err(e) => Err(e)
            }
        }
    };

    // Handle API errors with nice messages
    if let Err(e) = result {
        errors::handle_api_error(e, &api_url);
    }

    Ok(())
}

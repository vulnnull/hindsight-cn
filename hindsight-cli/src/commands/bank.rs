use anyhow::Result;
use crate::api::ApiClient;
use crate::output::{self, OutputFormat};
use crate::ui;

pub fn list(client: &ApiClient, verbose: bool, output_format: OutputFormat) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching banks..."))
    } else {
        None
    };

    let response = client.list_agents(verbose);

    if let Some(sp) = spinner {
        sp.finish_and_clear();
    }

    match response {
        Ok(banks_list) => {
            if output_format == OutputFormat::Pretty {
                if banks_list.is_empty() {
                    ui::print_warning("No banks found");
                } else {
                    ui::print_info(&format!("Found {} bank(s)", banks_list.len()));
                    for bank in &banks_list {
                        println!("  - {}", bank.bank_id);
                    }
                }
            } else {
                output::print_output(&banks_list, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e)
    }
}

pub fn profile(client: &ApiClient, bank_id: &str, verbose: bool, output_format: OutputFormat) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching profile..."))
    } else {
        None
    };

    let response = client.get_profile(bank_id, verbose);

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

pub fn stats(client: &ApiClient, bank_id: &str, verbose: bool, output_format: OutputFormat) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Fetching statistics..."))
    } else {
        None
    };

    let response = client.get_stats(bank_id, verbose);

    if let Some(sp) = spinner {
        sp.finish_and_clear();
    }

    match response {
        Ok(stats) => {
            if output_format == OutputFormat::Pretty {
                ui::print_info(&format!("Statistics for bank '{}'", bank_id));
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

pub fn update_name(client: &ApiClient, bank_id: &str, name: &str, verbose: bool, output_format: OutputFormat) -> Result<()> {
    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Updating bank name..."))
    } else {
        None
    };

    let response = client.update_agent_name(bank_id, name, verbose);

    if let Some(sp) = spinner {
        sp.finish_and_clear();
    }

    match response {
        Ok(profile) => {
            if output_format == OutputFormat::Pretty {
                ui::print_success(&format!("Bank name updated to '{}'", profile.name));
            } else {
                output::print_output(&profile, output_format)?;
            }
            Ok(())
        }
        Err(e) => Err(e)
    }
}

pub fn update_background(
    client: &ApiClient,
    bank_id: &str,
    content: &str,
    no_update_personality: bool,
    verbose: bool,
    output_format: OutputFormat
) -> Result<()> {
    let current_profile = if !no_update_personality {
        client.get_profile(bank_id, verbose).ok()
    } else {
        None
    };

    let spinner = if output_format == OutputFormat::Pretty {
        Some(ui::create_spinner("Merging background..."))
    } else {
        None
    };

    let response = client.add_background(bank_id, content, !no_update_personality, verbose);

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
                        (current_profile.as_ref().map(|p| p.personality.clone()), &profile.personality)
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

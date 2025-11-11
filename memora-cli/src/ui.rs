use crate::api::{Agent, Fact, SearchResponse, ThinkResponse, TraceInfo};
use colored::*;
use indicatif::{ProgressBar, ProgressStyle};
use std::io::{self, Write};

pub fn print_banner() {
    println!("{}", "╔══════════════════════════════════════════════════╗".bright_cyan());
    println!("{}", "║            MEMORA - Memory CLI                   ║".bright_cyan());
    println!("{}", "╚══════════════════════════════════════════════════╝".bright_cyan());
    println!();
}

pub fn print_section_header(title: &str) {
    println!();
    println!("{}", format!("━━━ {} ━━━", title).bright_yellow().bold());
    println!();
}

pub fn print_fact(fact: &Fact, show_activation: bool) {
    let fact_type = fact.fact_type.as_deref().unwrap_or("unknown");

    let type_color = match fact_type {
        "world" => "cyan",
        "agent" => "magenta",
        "opinion" => "yellow",
        _ => "white",
    };

    let prefix = match fact_type {
        "world" => "🌍",
        "agent" => "🤖",
        "opinion" => "💭",
        _ => "📝",
    };

    print!("{} ", prefix);
    print!("{}", format!("[{}]", fact_type.to_uppercase()).color(type_color).bold());

    if show_activation {
        if let Some(activation) = fact.activation {
            print!(" {}", format!("({:.2})", activation).bright_black());
        }
    }

    println!();
    println!("  {}", fact.text);

    // Show context if available
    if let Some(context) = &fact.context {
        println!("  {}: {}", "Context".bright_black(), context.bright_black());
    }

    // Show event date if available
    if let Some(event_date) = &fact.event_date {
        println!("  {}: {}", "Date".bright_black(), event_date.bright_black());
    }

    println!();
}

pub fn print_search_results(response: &SearchResponse, show_trace: bool) {
    let results = &response.results;
    print_section_header(&format!("Search Results ({})", results.len()));

    if results.is_empty() {
        println!("{}", "  No results found.".bright_black());
    } else {
        for (i, fact) in results.iter().enumerate() {
            println!("{}", format!("  Result #{}", i + 1).bright_black());
            print_fact(fact, true);
        }
    }

    if show_trace {
        if let Some(trace) = &response.trace {
            print_trace_info(trace);
        }
    }
}

pub fn print_think_response(response: &ThinkResponse) {
    print_section_header("Answer");
    println!("{}", response.text.bright_white());
    println!();

    // Note: based_on facts are hidden in default output
    // Use -o json to see the complete response including based_on facts
    if !response.based_on.is_empty() {
        println!("  {}", format!("(Based on {} facts - use -o json to see details)", response.based_on.len()).bright_black());
        println!();
    }

    if !response.new_opinions.is_empty() {
        print_section_header(&format!("New opinions formed ({})", response.new_opinions.len()));
        for opinion in &response.new_opinions {
            println!("  💭 {}", opinion.bright_yellow());
        }
        println!();
    }
}

pub fn print_trace_info(trace: &TraceInfo) {
    print_section_header("Trace Information");

    if let Some(time) = trace.total_time {
        println!("  ⏱️  Total time: {}", format!("{:.2}ms", time).bright_green());
    }

    if let Some(count) = trace.activation_count {
        println!("  📊 Activation count: {}", count.to_string().bright_green());
    }

    println!();
}

pub fn print_agents_table(agents: &[Agent]) {
    print_section_header(&format!("Agents ({})", agents.len()));

    if agents.is_empty() {
        println!("{}", "  No agents found.".bright_black());
        return;
    }

    // Calculate column width
    let max_id_len = agents.iter().map(|a| a.agent_id.len()).max().unwrap_or(8);
    let id_width = max_id_len.max(8);

    // Print header
    println!("  ┌{}┐",
        "─".repeat(id_width + 2));

    println!("  │ {:<width$} │",
        "Agent ID".bright_cyan().bold(),
        width = id_width);

    println!("  ├{}┤",
        "─".repeat(id_width + 2));

    // Print rows
    for agent in agents {
        println!("  │ {:<width$} │",
            agent.agent_id,
            width = id_width);
    }

    println!("  └{}┘",
        "─".repeat(id_width + 2));

    println!();
}

pub fn print_success(message: &str) {
    println!("{} {}", "✓".bright_green().bold(), message.bright_white());
}

pub fn print_error(message: &str) {
    eprintln!("{} {}", "✗".bright_red().bold(), message.bright_red());
}

pub fn print_warning(message: &str) {
    println!("{} {}", "⚠".bright_yellow().bold(), message.bright_yellow());
}

pub fn print_info(message: &str) {
    println!("{} {}", "ℹ".bright_blue().bold(), message.bright_white());
}

pub fn create_spinner(message: &str) -> ProgressBar {
    let pb = ProgressBar::new_spinner();
    pb.set_style(
        ProgressStyle::default_spinner()
            .template("{spinner:.cyan} {msg}")
            .unwrap()
            .tick_strings(&["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]),
    );
    pb.set_message(message.to_string());
    pb.enable_steady_tick(std::time::Duration::from_millis(80));
    pb
}

pub fn create_progress_bar(total: u64, message: &str) -> ProgressBar {
    let pb = ProgressBar::new(total);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("{msg} [{bar:40.cyan/blue}] {pos}/{len} ({percent}%)")
            .unwrap()
            .progress_chars("█▓▒░ "),
    );
    pb.set_message(message.to_string());
    pb
}

pub fn print_stored_memory(doc_id: &str, content: &str, is_async: bool) {
    if is_async {
        println!("{} Queued for background processing", "⏳".bright_yellow());
    } else {
        println!("{} Stored successfully", "✓".bright_green());
    }
    println!("  Document ID: {}", doc_id.bright_cyan());
    let preview = if content.len() > 60 {
        format!("{}...", &content[..57])
    } else {
        content.to_string()
    };
    println!("  Content: {}", preview.bright_black());
    println!();
}

pub fn prompt_confirmation(message: &str) -> io::Result<bool> {
    print!("{} {} [y/N]: ", "?".bright_blue().bold(), message);
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    Ok(input.trim().eq_ignore_ascii_case("y") || input.trim().eq_ignore_ascii_case("yes"))
}

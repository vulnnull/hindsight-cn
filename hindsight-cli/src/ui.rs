use crate::api::{BankProfileResponse, RecallResult, RecallResponse, ReflectResponse};
use colored::*;
use indicatif::{ProgressBar, ProgressStyle};
use std::io::{self, Write};

pub fn print_section_header(title: &str) {
    println!();
    println!("{}", format!("━━━ {} ━━━", title).bright_yellow().bold());
    println!();
}

pub fn print_fact(fact: &RecallResult, show_activation: bool) {
    let fact_type = fact.type_.as_deref().unwrap_or("unknown");

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

    // Note: activation field not available in generated SearchResult
    // The API doesn't return it in the current schema
    if show_activation {
        // Placeholder for when activation is added to the API schema
    }

    println!();
    println!("  {}", fact.text);

    // Show context if available
    if let Some(context) = &fact.context {
        println!("  {}: {}", "Context".bright_black(), context.bright_black());
    }

    // Show temporal information
    if let Some(occurred_start) = &fact.occurred_start {
        if let Some(occurred_end) = &fact.occurred_end {
            println!("  {}: {} - {}", "Date".bright_black(), occurred_start.bright_black(), occurred_end.bright_black());
        } else {
            println!("  {}: {}", "Date".bright_black(), occurred_start.bright_black());
        }
    }

    // Show document ID if available
    if let Some(document_id) = &fact.document_id {
        println!("  {}: {}", "Document".bright_black(), document_id.bright_black());
    }

    println!();
}

pub fn print_search_results(response: &RecallResponse, show_trace: bool) {
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

pub fn print_think_response(response: &ReflectResponse) {
    println!();
    println!("{}", response.text.bright_white());
    println!();

    if !response.based_on.is_empty() {
        println!("{}", format!("Based on {} memory units", response.based_on.len()).bright_black());
    }
}

pub fn print_trace_info(trace: &serde_json::Map<String, serde_json::Value>) {
    print_section_header("Trace Information");

    if let Some(time) = trace.get("total_time").and_then(|v| v.as_f64()) {
        println!("  ⏱️  Total time: {}", format!("{:.2}ms", time).bright_green());
    }

    if let Some(count) = trace.get("activation_count").and_then(|v| v.as_i64()) {
        println!("  📊 Activation count: {}", count.to_string().bright_green());
    }

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

pub fn prompt_confirmation(message: &str) -> io::Result<bool> {
    print!("{} {} [y/N]: ", "?".bright_blue().bold(), message);
    io::stdout().flush()?;

    let mut input = String::new();
    io::stdin().read_line(&mut input)?;

    Ok(input.trim().eq_ignore_ascii_case("y") || input.trim().eq_ignore_ascii_case("yes"))
}

pub fn print_profile(profile: &BankProfileResponse) {
    print_section_header(&format!("Bank Profile: {}", profile.bank_id));

    // Print name
    println!("{} {}", "Name:".bright_cyan().bold(), profile.name.bright_white());
    println!();

    // Print background if available
    if !profile.background.is_empty() {
        println!("{}", "Background:".bright_yellow());
        for line in profile.background.lines() {
            println!("{}", line);
        }
        println!();
    }

    // Print personality traits
    println!("{}", "─── Personality Traits ───".bright_yellow());
    println!();

    let traits = [
        ("Openness", profile.personality.openness, "🔓", "green"),
        ("Conscientiousness", profile.personality.conscientiousness, "📋", "yellow"),
        ("Extraversion", profile.personality.extraversion, "🗣️", "cyan"),
        ("Agreeableness", profile.personality.agreeableness, "🤝", "magenta"),
        ("Neuroticism", profile.personality.neuroticism, "😰", "yellow"),
    ];

    for (name, value, emoji, color) in &traits {
        let bar_length = 40;
        let filled = (*value * bar_length as f64) as usize;
        let empty = bar_length - filled;

        let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));
        let colored_bar = match *color {
            "green" => bar.bright_green(),
            "yellow" => bar.bright_yellow(),
            "cyan" => bar.bright_cyan(),
            "magenta" => bar.bright_magenta(),
            _ => bar.bright_white(),
        };

        println!("  {} {:<20} [{}] {:.0}%",
            emoji,
            name,
            colored_bar,
            value * 100.0
        );
    }

    println!();
    println!("{}", "Bias Strength:".bright_yellow());
    let bias = profile.personality.bias_strength;
    let bar_length = 40;
    let filled = (bias * bar_length as f64) as usize;
    let empty = bar_length - filled;
    let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));

    println!("  💪 {:<20} [{}] {:.0}%",
        "Personality Influence",
        bar.bright_green(),
        bias * 100.0
    );
    println!("  {}", "(how much personality shapes opinions)".bright_black());
    println!();
}

use crate::api::{Agent, AgentProfile, Fact, PersonalityTraits, SearchResponse, ThinkResponse, TraceInfo};
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

pub fn print_profile(profile: &AgentProfile) {
    print_section_header(&format!("Agent Profile: {}", profile.agent_id));

    // Print personality traits
    println!("  {}", "Personality Traits (Big Five):".bright_cyan().bold());
    println!();

    let traits = [
        ("Openness", profile.personality.openness, "🔓"),
        ("Conscientiousness", profile.personality.conscientiousness, "📋"),
        ("Extraversion", profile.personality.extraversion, "🗣️"),
        ("Agreeableness", profile.personality.agreeableness, "🤝"),
        ("Neuroticism", profile.personality.neuroticism, "😰"),
    ];

    for (name, value, emoji) in &traits {
        let bar_length = 20;
        let filled = (*value * bar_length as f32) as usize;
        let empty = bar_length - filled;
        let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));

        let value_color = if *value >= 0.7 {
            bar.bright_green()
        } else if *value >= 0.4 {
            bar.bright_yellow()
        } else {
            bar.bright_red()
        };

        println!("    {} {:<20} [{}] {:.0}%",
            emoji,
            name,
            value_color,
            value * 100.0
        );
    }

    println!();
    println!("  {}", "Bias Strength:".bright_cyan().bold());
    let bias = profile.personality.bias_strength;
    let bar_length = 20;
    let filled = (bias * bar_length as f32) as usize;
    let empty = bar_length - filled;
    let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));

    let bias_color = if bias >= 0.7 {
        bar.bright_green()
    } else if bias >= 0.4 {
        bar.bright_yellow()
    } else {
        bar.bright_red()
    };

    println!("    💪 {:<20} [{}] {:.0}%",
        "Personality Influence",
        bias_color,
        bias * 100.0
    );
    println!("    {}", format!("(How much personality shapes opinions)").bright_black());
    println!();

    // Print background
    if !profile.background.is_empty() {
        println!("  {}", "Background:".bright_cyan().bold());
        println!();
        for line in profile.background.lines() {
            println!("    {}", line);
        }
        println!();
    } else {
        println!("  {}", "Background: (none)".bright_black());
        println!();
    }
}

pub fn print_personality_delta(old: &PersonalityTraits, new: &PersonalityTraits) {
    print_section_header("Personality Changes");

    let traits = [
        ("Openness", old.openness, new.openness, "🔓"),
        ("Conscientiousness", old.conscientiousness, new.conscientiousness, "📋"),
        ("Extraversion", old.extraversion, new.extraversion, "🗣️"),
        ("Agreeableness", old.agreeableness, new.agreeableness, "🤝"),
        ("Neuroticism", old.neuroticism, new.neuroticism, "😰"),
    ];

    for (name, old_value, new_value, emoji) in &traits {
        let bar_length = 20;
        let filled = (*new_value * bar_length as f32) as usize;
        let empty = bar_length - filled;
        let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));

        let value_color = if *new_value >= 0.7 {
            bar.bright_green()
        } else if *new_value >= 0.4 {
            bar.bright_yellow()
        } else {
            bar.bright_red()
        };

        let delta = new_value - old_value;
        let delta_pct = (delta * 100.0).abs();
        let delta_str = if delta.abs() < 0.01 {
            "".to_string()
        } else if delta > 0.0 {
            format!(" {} {:.0}%", "↗".bright_green(), delta_pct)
        } else {
            format!(" {} {:.0}%", "↘".bright_red(), delta_pct)
        };

        println!("    {} {:<20} [{}] {:.0}%{}",
            emoji,
            name,
            value_color,
            new_value * 100.0,
            delta_str
        );
    }

    println!();
    println!("  {}", "Bias Strength:".bright_cyan().bold());
    let old_bias = old.bias_strength;
    let new_bias = new.bias_strength;
    let bar_length = 20;
    let filled = (new_bias * bar_length as f32) as usize;
    let empty = bar_length - filled;
    let bar = format!("{}{}", "█".repeat(filled), "░".repeat(empty));

    let bias_color = if new_bias >= 0.7 {
        bar.bright_green()
    } else if new_bias >= 0.4 {
        bar.bright_yellow()
    } else {
        bar.bright_red()
    };

    let delta = new_bias - old_bias;
    let delta_pct = (delta * 100.0).abs();
    let delta_str = if delta.abs() < 0.01 {
        "".to_string()
    } else if delta > 0.0 {
        format!(" {} {:.0}%", "↗".bright_green(), delta_pct)
    } else {
        format!(" {} {:.0}%", "↘".bright_red(), delta_pct)
    };

    println!("    💪 {:<20} [{}] {:.0}%{}",
        "Personality Influence",
        bias_color,
        new_bias * 100.0,
        delta_str
    );
    println!("    {}", format!("(How much personality shapes opinions)").bright_black());
    println!();
}

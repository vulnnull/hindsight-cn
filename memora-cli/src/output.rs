use anyhow::Result;
use serde::Serialize;

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum OutputFormat {
    Pretty,
    Json,
    Yaml,
}

impl OutputFormat {
    pub fn from_str(s: &str) -> Option<Self> {
        match s.to_lowercase().as_str() {
            "pretty" | "default" => Some(OutputFormat::Pretty),
            "json" => Some(OutputFormat::Json),
            "yaml" | "yml" => Some(OutputFormat::Yaml),
            _ => None,
        }
    }
}

pub fn print_output<T: Serialize>(data: &T, format: OutputFormat) -> Result<()> {
    match format {
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(data)?);
        }
        OutputFormat::Yaml => {
            println!("{}", serde_yaml::to_string(data)?);
        }
        OutputFormat::Pretty => {
            // This should not be called - pretty printing is handled in ui.rs
            unreachable!("Pretty format should be handled separately")
        }
    }
    Ok(())
}

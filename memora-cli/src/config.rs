use anyhow::{Context, Result};
use std::env;

pub struct Config {
    pub api_url: String,
}

impl Config {
    pub fn from_env() -> Result<Self> {
        let api_url = env::var("MEMORA_API_URL")
            .unwrap_or_else(|_| "http://localhost:8080".to_string());

        // Validate URL format
        if !api_url.starts_with("http://") && !api_url.starts_with("https://") {
            anyhow::bail!(
                "Invalid API URL: {}. Must start with http:// or https://",
                api_url
            );
        }

        Ok(Config { api_url })
    }

    pub fn api_url(&self) -> &str {
        &self.api_url
    }
}

pub fn generate_doc_id() -> String {
    let now = chrono::Local::now();
    format!("cli_put_{}", now.format("%Y%m%d_%H%M%S"))
}

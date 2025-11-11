use anyhow::{Context, Result};
use reqwest::blocking::{Client, Response};
use serde::{Deserialize, Serialize};
use std::time::Duration;

pub struct ApiError {
    pub url: String,
    pub request_body: String,
    pub response_status: Option<u16>,
    pub response_body: Option<String>,
    pub error: anyhow::Error,
}

#[derive(Debug, Serialize)]
pub struct SearchRequest {
    pub query: String,
    pub fact_type: Vec<String>,
    pub agent_id: String,
    pub thinking_budget: i32,
    pub max_tokens: i32,
    pub trace: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct SearchResponse {
    pub results: Vec<Fact>,
    pub trace: Option<TraceInfo>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Fact {
    #[serde(default)]
    pub id: Option<String>,
    pub text: String,
    #[serde(rename = "type", default)]
    pub fact_type: Option<String>,
    pub activation: Option<f64>,
    #[serde(default)]
    pub context: Option<String>,
    #[serde(default)]
    pub event_date: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TraceInfo {
    pub total_time: Option<f64>,
    pub activation_count: Option<i32>,
}

#[derive(Debug, Serialize)]
pub struct ThinkRequest {
    pub query: String,
    pub agent_id: String,
    pub thinking_budget: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ThinkResponse {
    pub text: String,
    pub based_on: Vec<Fact>,
    pub new_opinions: Vec<String>,
}

#[derive(Debug, Serialize)]
pub struct MemoryItem {
    pub content: String,
    pub context: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct BatchMemoryRequest {
    pub agent_id: String,
    pub items: Vec<MemoryItem>,
    pub document_id: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BatchMemoryResponse {
    pub success: bool,
    pub stored_count: Option<i32>,
    pub error: Option<String>,
    pub job_id: Option<String>,
}

#[derive(Debug, Deserialize)]
#[serde(untagged)]
pub enum AgentsResponse {
    Success {
        agents: Vec<String>,
    },
    Error {
        error: String,
    },
}

#[derive(Debug, Serialize)]
pub struct Agent {
    pub agent_id: String,
}

pub struct ApiClient {
    client: Client,
    base_url: String,
}

impl ApiClient {
    pub fn new(base_url: String) -> Result<Self> {
        let client = Client::builder()
            .timeout(Duration::from_secs(60))
            .build()
            .context("Failed to create HTTP client")?;

        Ok(ApiClient { client, base_url })
    }

    pub fn search(&self, request: SearchRequest, verbose: bool) -> Result<SearchResponse> {
        let url = format!("{}/api/search", self.base_url);
        let request_body = serde_json::to_string_pretty(&request).unwrap_or_default();

        if verbose {
            eprintln!("Request URL: {}", url);
            eprintln!("Request body:\n{}", request_body);
        }

        let response = self
            .client
            .post(&url)
            .json(&request)
            .timeout(Duration::from_secs(120))
            .send()?;

        let status = response.status();
        if verbose {
            eprintln!("Response status: {}", status);
        }

        if !status.is_success() {
            let error_body = response.text().unwrap_or_default();
            if verbose {
                eprintln!("Error response body:\n{}", error_body);
            }
            anyhow::bail!("API returned error status {}: {}", status, error_body);
        }

        let response_text = response.text()?;
        if verbose {
            eprintln!("Response body:\n{}", response_text);
        }

        let result: SearchResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn think(&self, request: ThinkRequest, verbose: bool) -> Result<ThinkResponse> {
        let url = format!("{}/api/think", self.base_url);

        if verbose {
            eprintln!("Request URL: {}", url);
            eprintln!("Request body:\n{}", serde_json::to_string_pretty(&request).unwrap_or_default());
        }

        let response = self
            .client
            .post(&url)
            .json(&request)
            .timeout(Duration::from_secs(120))
            .send()?;

        let status = response.status();
        if verbose {
            eprintln!("Response status: {}", status);
        }

        if !status.is_success() {
            let error_body = response.text().unwrap_or_default();
            if verbose {
                eprintln!("Error response body:\n{}", error_body);
            }
            anyhow::bail!("API returned error status {}: {}", status, error_body);
        }

        let response_text = response.text()?;
        if verbose {
            eprintln!("Response body:\n{}", response_text);
        }

        let result: ThinkResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn put_memories(&self, request: BatchMemoryRequest, async_mode: bool, verbose: bool) -> Result<BatchMemoryResponse> {
        let endpoint = if async_mode {
            "batch_async"
        } else {
            "batch"
        };
        let url = format!("{}/api/memories/{}", self.base_url, endpoint);

        if verbose {
            eprintln!("Request URL: {}", url);
            eprintln!("Request body:\n{}", serde_json::to_string_pretty(&request).unwrap_or_default());
        }

        let response = self
            .client
            .post(&url)
            .json(&request)
            .timeout(Duration::from_secs(120))
            .send()?;

        let status = response.status();
        if verbose {
            eprintln!("Response status: {}", status);
        }

        if !status.is_success() {
            let error_body = response.text().unwrap_or_default();
            if verbose {
                eprintln!("Error response body:\n{}", error_body);
            }
            anyhow::bail!("API returned error status {}: {}", status, error_body);
        }

        let response_text = response.text()?;
        if verbose {
            eprintln!("Response body:\n{}", response_text);
        }

        let result: BatchMemoryResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn list_agents(&self, verbose: bool) -> Result<Vec<Agent>> {
        let url = format!("{}/api/agents", self.base_url);

        if verbose {
            eprintln!("Request URL: {}", url);
        }

        let response = self
            .client
            .get(&url)
            .timeout(Duration::from_secs(30))
            .send()?;

        let status = response.status();
        if verbose {
            eprintln!("Response status: {}", status);
        }

        if !status.is_success() {
            let error_body = response.text().unwrap_or_default();
            if verbose {
                eprintln!("Error response body:\n{}", error_body);
            }
            anyhow::bail!("API returned error status {}: {}", status, error_body);
        }

        let response_text = response.text()?;
        if verbose {
            eprintln!("Response body:\n{}", response_text);
        }

        let result: AgentsResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;

        match result {
            AgentsResponse::Success { agents } => {
                Ok(agents.into_iter().map(|agent_id| Agent { agent_id }).collect())
            }
            AgentsResponse::Error { error } => {
                anyhow::bail!("Failed to list agents: {}", error)
            }
        }
    }
}

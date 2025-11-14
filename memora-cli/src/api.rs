use anyhow::{Context, Result};
use reqwest::blocking::{Client, Response};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
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
    pub thinking_budget: i32,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub context: Option<String>,
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

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct PersonalityTraits {
    pub openness: f32,
    pub conscientiousness: f32,
    pub extraversion: f32,
    pub agreeableness: f32,
    pub neuroticism: f32,
    pub bias_strength: f32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AgentProfile {
    pub agent_id: String,
    pub name: String,
    pub personality: PersonalityTraits,
    pub background: String,
}

#[derive(Debug, Serialize)]
pub struct UpdatePersonalityRequest {
    pub personality: PersonalityTraits,
}

#[derive(Debug, Serialize)]
pub struct AddBackgroundRequest {
    pub content: String,
    pub update_personality: bool,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct BackgroundResponse {
    pub background: String,
    pub personality: Option<PersonalityTraits>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AgentStats {
    pub agent_id: String,
    pub total_nodes: i32,
    pub total_links: i32,
    pub total_documents: i32,
    pub nodes_by_fact_type: HashMap<String, i32>,
    pub links_by_link_type: HashMap<String, i32>,
    pub links_by_fact_type: HashMap<String, i32>,
    pub links_breakdown: HashMap<String, HashMap<String, i32>>,
    pub pending_operations: i32,
    pub failed_operations: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Document {
    pub id: String,
    pub agent_id: String,
    pub content_hash: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub text_length: i32,
    pub memory_unit_count: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DocumentDetails {
    pub id: String,
    pub agent_id: String,
    pub original_text: String,
    pub content_hash: Option<String>,
    pub created_at: String,
    pub updated_at: String,
    pub memory_unit_count: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DocumentsResponse {
    pub items: Vec<Document>,
    pub total: i32,
    pub limit: i32,
    pub offset: i32,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct Operation {
    pub id: String,
    pub task_type: String,
    pub items_count: i32,
    pub document_id: Option<String>,
    pub created_at: String,
    pub status: String,
    pub error_message: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct OperationsResponse {
    pub agent_id: String,
    pub operations: Vec<Operation>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct DeleteResponse {
    pub success: bool,
    pub message: String,
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

    pub fn search(&self, agent_id: &str, request: SearchRequest, verbose: bool) -> Result<SearchResponse> {
        let url = format!("{}/api/v1/agents/{}/memories/search", self.base_url, agent_id);
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

    pub fn think(&self, agent_id: &str, request: ThinkRequest, verbose: bool) -> Result<ThinkResponse> {
        let url = format!("{}/api/v1/agents/{}/think", self.base_url, agent_id);

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

    pub fn put_memories(&self, agent_id: &str, request: BatchMemoryRequest, async_mode: bool, verbose: bool) -> Result<BatchMemoryResponse> {
        let endpoint = if async_mode {
            "async"
        } else {
            ""
        };
        let url = if async_mode {
            format!("{}/api/v1/agents/{}/memories/{}", self.base_url, agent_id, endpoint)
        } else {
            format!("{}/api/v1/agents/{}/memories", self.base_url, agent_id)
        };

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
        let url = format!("{}/api/v1/agents", self.base_url);

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

    pub fn get_profile(&self, agent_id: &str, verbose: bool) -> Result<AgentProfile> {
        let url = format!("{}/api/v1/agents/{}/profile", self.base_url, agent_id);

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

        let result: AgentProfile = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn update_personality(
        &self,
        agent_id: &str,
        openness: f32,
        conscientiousness: f32,
        extraversion: f32,
        agreeableness: f32,
        neuroticism: f32,
        bias_strength: f32,
        verbose: bool,
    ) -> Result<AgentProfile> {
        let url = format!("{}/api/v1/agents/{}/profile", self.base_url, agent_id);
        let request = UpdatePersonalityRequest {
            personality: PersonalityTraits {
                openness,
                conscientiousness,
                extraversion,
                agreeableness,
                neuroticism,
                bias_strength,
            },
        };

        if verbose {
            eprintln!("Request URL: {}", url);
            eprintln!("Request body:\n{}", serde_json::to_string_pretty(&request).unwrap_or_default());
        }

        let response = self
            .client
            .put(&url)
            .json(&request)
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

        let result: AgentProfile = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn add_background(&self, agent_id: &str, content: &str, update_personality: bool, verbose: bool) -> Result<BackgroundResponse> {
        let url = format!("{}/api/v1/agents/{}/background", self.base_url, agent_id);
        let request = AddBackgroundRequest {
            content: content.to_string(),
            update_personality,
        };

        if verbose {
            eprintln!("Request URL: {}", url);
            eprintln!("Request body:\n{}", serde_json::to_string_pretty(&request).unwrap_or_default());
        }

        let response = self
            .client
            .post(&url)
            .json(&request)
            .timeout(Duration::from_secs(60))
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

        let result: BackgroundResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn get_stats(&self, agent_id: &str, verbose: bool) -> Result<AgentStats> {
        let url = format!("{}/api/v1/agents/{}/stats", self.base_url, agent_id);

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

        let result: AgentStats = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn list_documents(&self, agent_id: &str, q: Option<&str>, limit: Option<i32>, offset: Option<i32>, verbose: bool) -> Result<DocumentsResponse> {
        let mut url = format!("{}/api/v1/agents/{}/documents", self.base_url, agent_id);
        let mut params = vec![];

        if let Some(query) = q {
            params.push(format!("q={}", query));
        }
        if let Some(l) = limit {
            params.push(format!("limit={}", l));
        }
        if let Some(o) = offset {
            params.push(format!("offset={}", o));
        }

        if !params.is_empty() {
            url.push('?');
            url.push_str(&params.join("&"));
        }

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

        let result: DocumentsResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn get_document(&self, agent_id: &str, document_id: &str, verbose: bool) -> Result<DocumentDetails> {
        let url = format!("{}/api/v1/agents/{}/documents/{}", self.base_url, agent_id, document_id);

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

        let result: DocumentDetails = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn list_operations(&self, agent_id: &str, verbose: bool) -> Result<OperationsResponse> {
        let url = format!("{}/api/v1/agents/{}/operations", self.base_url, agent_id);

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

        let result: OperationsResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn cancel_operation(&self, agent_id: &str, operation_id: &str, verbose: bool) -> Result<DeleteResponse> {
        let url = format!("{}/api/v1/agents/{}/operations/{}", self.base_url, agent_id, operation_id);

        if verbose {
            eprintln!("Request URL: {}", url);
        }

        let response = self
            .client
            .delete(&url)
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

        let result: DeleteResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn delete_memory(&self, agent_id: &str, unit_id: &str, verbose: bool) -> Result<DeleteResponse> {
        let url = format!("{}/api/v1/agents/{}/memories/{}", self.base_url, agent_id, unit_id);

        if verbose {
            eprintln!("Request URL: {}", url);
        }

        let response = self
            .client
            .delete(&url)
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

        let result: DeleteResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }

    pub fn delete_document(&self, agent_id: &str, document_id: &str, verbose: bool) -> Result<DeleteResponse> {
        let url = format!("{}/api/v1/agents/{}/documents/{}", self.base_url, agent_id, document_id);

        if verbose {
            eprintln!("Request URL: {}", url);
        }

        let response = self
            .client
            .delete(&url)
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

        let result: DeleteResponse = serde_json::from_str(&response_text)
            .with_context(|| format!("Failed to parse API response. Response was: {}", response_text))?;
        Ok(result)
    }
}

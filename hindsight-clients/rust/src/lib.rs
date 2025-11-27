//! Hindsight API Client
//!
//! A Rust client library for the Hindsight semantic memory system API.
//!
//! # Example
//!
//! ```rust,no_run
//! use hindsight_client::Client;
//!
//! #[tokio::main]
//! async fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     let client = Client::new("http://localhost:8888");
//!
//!     // List agents
//!     let agents = client.agents_list().await?;
//!     println!("Found {} agents", agents.len());
//!
//!     Ok(())
//! }
//! ```

// Include the generated client code (which already exports Error and ResponseValue)
include!(concat!(env!("OUT_DIR"), "/hindsight_client_generated.rs"));

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_client_creation() {
        let client = Client::new("http://localhost:8888");
        // Just verify we can create a client
        assert!(true);
    }
}

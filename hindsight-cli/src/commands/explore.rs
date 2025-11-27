use crate::api::{ApiClient, RecallRequest, ReflectRequest};
use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen},
};
use hindsight_client::types::{BankListItem, RecallResult, EntityListItem, Budget};
use serde_json::{Map, Value};
use ratatui::{
    backend::{Backend, CrosstermBackend},
    layout::{Alignment, Constraint, Direction, Layout, Rect},
    style::{Color, Modifier, Style},
    text::{Line, Span},
    widgets::{Block, Borders, List, ListItem, ListState, Paragraph, Wrap},
    Frame, Terminal,
};
use std::io;
use std::time::{Duration, Instant};

/// Main view types (like k9s contexts)
#[derive(Debug, Clone, PartialEq)]
enum View {
    Banks,
    Memories(String),  // bank_id
    Entities(String),  // bank_id
    Documents(String), // bank_id
    Recall(String),    // bank_id
    Reflect(String),   // bank_id
}

impl View {
    fn title(&self) -> &str {
        match self {
            View::Banks => "Banks",
            View::Memories(_) => "Memories",
            View::Entities(_) => "Entities",
            View::Documents(_) => "Documents",
            View::Recall(_) => "Recall",
            View::Reflect(_) => "Reflect",
        }
    }

    fn bank_id(&self) -> Option<&str> {
        match self {
            View::Banks => None,
            View::Memories(id) | View::Entities(id) | View::Documents(id) | View::Recall(id) | View::Reflect(id) => Some(id),
        }
    }
}

/// Input mode for recall/reflect queries
#[derive(Debug, Clone, PartialEq)]
enum InputMode {
    Normal,
    Query,
}

/// Application state
struct App {
    client: ApiClient,
    view: View,
    view_history: Vec<View>,

    // List states
    banks: Vec<BankListItem>,
    banks_state: ListState,

    memories: Vec<Map<String, Value>>,
    memories_state: ListState,

    entities: Vec<EntityListItem>,
    entities_state: ListState,

    documents: Vec<Map<String, Value>>,
    documents_state: ListState,

    // Recall state
    recall_query: String,
    recall_results: Vec<RecallResult>,
    recall_results_state: ListState,

    // Reflect state
    reflect_query: String,
    reflect_response: String,

    // Input mode
    input_mode: InputMode,

    // Status messages
    status_message: String,
    error_message: String,

    // Help visibility
    show_help: bool,

    // Loading state
    loading: bool,

    // Auto-refresh
    auto_refresh_enabled: bool,
    last_refresh: Instant,
    refresh_interval: Duration,
}

impl App {
    fn new(client: ApiClient) -> Self {
        let mut app = Self {
            client,
            view: View::Banks,
            view_history: Vec::new(),

            banks: Vec::new(),
            banks_state: ListState::default(),

            memories: Vec::new(),
            memories_state: ListState::default(),

            entities: Vec::new(),
            entities_state: ListState::default(),

            documents: Vec::new(),
            documents_state: ListState::default(),

            recall_query: String::new(),
            recall_results: Vec::new(),
            recall_results_state: ListState::default(),

            reflect_query: String::new(),
            reflect_response: String::new(),

            input_mode: InputMode::Normal,
            status_message: String::from("Press ? for help"),
            error_message: String::new(),
            show_help: false,
            loading: false,

            auto_refresh_enabled: true,
            last_refresh: Instant::now(),
            refresh_interval: Duration::from_secs(5),
        };

        // Select first item by default
        app.banks_state.select(Some(0));
        app.memories_state.select(Some(0));
        app.entities_state.select(Some(0));
        app.recall_results_state.select(Some(0));

        app
    }

    fn refresh(&mut self) -> Result<()> {
        self.loading = true;
        self.error_message.clear();

        let result = match self.view.clone() {
            View::Banks => self.load_banks(),
            View::Memories(bank_id) => self.load_memories(&bank_id),
            View::Entities(bank_id) => self.load_entities(&bank_id),
            View::Documents(bank_id) => self.load_documents(&bank_id),
            View::Recall(_) => Ok(()), // Recall is query-driven
            View::Reflect(_) => Ok(()), // Reflect is query-driven
        };

        self.loading = false;

        if let Err(e) = result {
            self.error_message = format!("Error: {}", e);
        }

        Ok(())
    }

    fn toggle_auto_refresh(&mut self) {
        self.auto_refresh_enabled = !self.auto_refresh_enabled;
        if self.auto_refresh_enabled {
            self.status_message = "Auto-refresh enabled (5s)".to_string();
            self.last_refresh = Instant::now();
        } else {
            self.status_message = "Auto-refresh disabled".to_string();
        }
    }

    fn should_refresh(&self) -> bool {
        self.auto_refresh_enabled && self.last_refresh.elapsed() >= self.refresh_interval
    }

    fn do_auto_refresh(&mut self) -> Result<()> {
        if self.should_refresh() {
            self.last_refresh = Instant::now();
            self.refresh()?;
        }
        Ok(())
    }

    fn load_banks(&mut self) -> Result<()> {
        self.banks = self.client.list_agents(false)?;

        if !self.banks.is_empty() && self.banks_state.selected().is_none() {
            self.banks_state.select(Some(0));
        }

        self.status_message = format!("Loaded {} banks", self.banks.len());
        Ok(())
    }

    fn load_memories(&mut self, bank_id: &str) -> Result<()> {
        let response = self.client.list_memories(bank_id, None, None, Some(100), Some(0), false)?;
        self.memories = response.items;

        if !self.memories.is_empty() && self.memories_state.selected().is_none() {
            self.memories_state.select(Some(0));
        }

        self.status_message = format!("Loaded {} memories", self.memories.len());
        Ok(())
    }

    fn load_entities(&mut self, bank_id: &str) -> Result<()> {
        let response = self.client.list_entities(bank_id, Some(100), false)?;
        self.entities = response.entities;

        if !self.entities.is_empty() && self.entities_state.selected().is_none() {
            self.entities_state.select(Some(0));
        }

        self.status_message = format!("Loaded {} entities", self.entities.len());
        Ok(())
    }

    fn load_documents(&mut self, bank_id: &str) -> Result<()> {
        let response = self.client.list_documents(bank_id, None, Some(100), Some(0), false)?;
        self.documents = response.items;

        if !self.documents.is_empty() && self.documents_state.selected().is_none() {
            self.documents_state.select(Some(0));
        }

        self.status_message = format!("Loaded {} documents", self.documents.len());
        Ok(())
    }

    fn execute_recall(&mut self) -> Result<()> {
        if let View::Recall(bank_id) = &self.view {
            if self.recall_query.is_empty() {
                self.error_message = "Query cannot be empty".to_string();
                return Ok(());
            }

            self.loading = true;
            self.error_message.clear();

            let request = RecallRequest {
                query: self.recall_query.clone(),
                types: None,
                budget: Some(Budget::Mid),
                max_tokens: 4096,
                trace: false,
                query_timestamp: None,
                filters: None,
                include: None,
            };

            let response = self.client.recall(bank_id, &request, false)?;
            self.recall_results = response.results;

            if !self.recall_results.is_empty() {
                self.recall_results_state.select(Some(0));
            }

            self.loading = false;
            self.status_message = format!("Found {} results", self.recall_results.len());
            self.input_mode = InputMode::Normal;
        }

        Ok(())
    }

    fn execute_reflect(&mut self) -> Result<()> {
        if let View::Reflect(bank_id) = &self.view {
            if self.reflect_query.is_empty() {
                self.error_message = "Query cannot be empty".to_string();
                return Ok(());
            }

            self.loading = true;
            self.error_message.clear();

            let request = ReflectRequest {
                query: self.reflect_query.clone(),
                budget: Some(Budget::Mid),
                context: None,
                filters: None,
                include: None,
            };

            let response = self.client.reflect(bank_id, &request, false)?;
            self.reflect_response = response.text;

            self.loading = false;
            self.status_message = "Reflection complete".to_string();
            self.input_mode = InputMode::Normal;
        }

        Ok(())
    }

    fn next_item(&mut self) {
        match &self.view {
            View::Banks => {
                let i = match self.banks_state.selected() {
                    Some(i) => {
                        if i >= self.banks.len().saturating_sub(1) {
                            0
                        } else {
                            i + 1
                        }
                    }
                    None => 0,
                };
                self.banks_state.select(Some(i));
            }
            View::Memories(_) => {
                let i = match self.memories_state.selected() {
                    Some(i) => {
                        if i >= self.memories.len().saturating_sub(1) {
                            0
                        } else {
                            i + 1
                        }
                    }
                    None => 0,
                };
                self.memories_state.select(Some(i));
            }
            View::Entities(_) => {
                let i = match self.entities_state.selected() {
                    Some(i) => {
                        if i >= self.entities.len().saturating_sub(1) {
                            0
                        } else {
                            i + 1
                        }
                    }
                    None => 0,
                };
                self.entities_state.select(Some(i));
            }
            View::Documents(_) => {
                let i = match self.documents_state.selected() {
                    Some(i) => {
                        if i >= self.documents.len().saturating_sub(1) {
                            0
                        } else {
                            i + 1
                        }
                    }
                    None => 0,
                };
                self.documents_state.select(Some(i));
            }
            View::Recall(_) => {
                let i = match self.recall_results_state.selected() {
                    Some(i) => {
                        if i >= self.recall_results.len().saturating_sub(1) {
                            0
                        } else {
                            i + 1
                        }
                    }
                    None => 0,
                };
                self.recall_results_state.select(Some(i));
            }
            View::Reflect(_) => {} // No list to navigate
        }
    }

    fn previous_item(&mut self) {
        match &self.view {
            View::Banks => {
                let i = match self.banks_state.selected() {
                    Some(i) => {
                        if i == 0 {
                            self.banks.len().saturating_sub(1)
                        } else {
                            i - 1
                        }
                    }
                    None => 0,
                };
                self.banks_state.select(Some(i));
            }
            View::Memories(_) => {
                let i = match self.memories_state.selected() {
                    Some(i) => {
                        if i == 0 {
                            self.memories.len().saturating_sub(1)
                        } else {
                            i - 1
                        }
                    }
                    None => 0,
                };
                self.memories_state.select(Some(i));
            }
            View::Entities(_) => {
                let i = match self.entities_state.selected() {
                    Some(i) => {
                        if i == 0 {
                            self.entities.len().saturating_sub(1)
                        } else {
                            i - 1
                        }
                    }
                    None => 0,
                };
                self.entities_state.select(Some(i));
            }
            View::Documents(_) => {
                let i = match self.documents_state.selected() {
                    Some(i) => {
                        if i == 0 {
                            self.documents.len().saturating_sub(1)
                        } else {
                            i - 1
                        }
                    }
                    None => 0,
                };
                self.documents_state.select(Some(i));
            }
            View::Recall(_) => {
                let i = match self.recall_results_state.selected() {
                    Some(i) => {
                        if i == 0 {
                            self.recall_results.len().saturating_sub(1)
                        } else {
                            i - 1
                        }
                    }
                    None => 0,
                };
                self.recall_results_state.select(Some(i));
            }
            View::Reflect(_) => {} // No list to navigate
        }
    }

    fn enter_view(&mut self) -> Result<()> {
        match &self.view {
            View::Banks => {
                if let Some(i) = self.banks_state.selected() {
                    if let Some(bank) = self.banks.get(i) {
                        let bank_id = bank.bank_id.clone();
                        self.view_history.push(self.view.clone());
                        self.view = View::Memories(bank_id.clone());
                        self.load_memories(&bank_id)?;
                    }
                }
            }
            _ => {}
        }
        Ok(())
    }

    fn go_back(&mut self) {
        if let Some(prev_view) = self.view_history.pop() {
            self.view = prev_view;
            let _ = self.refresh();
        }
    }

    fn switch_to_view(&mut self, new_view: View) -> Result<()> {
        if self.view != new_view {
            self.view_history.push(self.view.clone());
            self.view = new_view;
            self.refresh()?;
        }
        Ok(())
    }
}

fn ui(f: &mut Frame, app: &mut App) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(5),  // Shortcuts bar (context + shortcuts, max 3 rows + 2 border)
            Constraint::Length(3),  // Header
            Constraint::Min(0),     // Main content
            Constraint::Length(1),  // Footer/status only (no border)
        ])
        .split(f.area());

    // Control bar
    render_control_bar(f, app, chunks[0]);

    // Header
    render_header(f, app, chunks[1]);

    // Main content
    if app.show_help {
        render_help(f, chunks[2]);
    } else {
        match &app.view {
            View::Banks => render_banks(f, app, chunks[2]),
            View::Memories(_) => render_memories(f, app, chunks[2]),
            View::Entities(_) => render_entities(f, app, chunks[2]),
            View::Documents(_) => render_documents(f, app, chunks[2]),
            View::Recall(_) => render_recall(f, app, chunks[2]),
            View::Reflect(_) => render_reflect(f, app, chunks[2]),
        }
    }

    // Footer
    render_footer(f, app, chunks[3]);
}

fn render_control_bar(f: &mut Frame, app: &App, area: Rect) {
    // Build contextual shortcuts based on view and input mode
    let shortcuts = match (&app.view, &app.input_mode) {
        (View::Banks, InputMode::Normal) => vec![
            ("Enter", "Select", Color::Cyan),
            ("m", "Mem", Color::Green),
            ("e", "Ent", Color::Green),
            ("d", "Docs", Color::Green),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Memories(_), InputMode::Normal) => vec![
            ("Enter", "View", Color::Cyan),
            ("Esc", "Back", Color::Yellow),
            ("r", "Recall", Color::Green),
            ("t", "Reflect", Color::Green),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Entities(_), InputMode::Normal) => vec![
            ("Enter", "View", Color::Cyan),
            ("Esc", "Back", Color::Yellow),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Documents(_), InputMode::Normal) => vec![
            ("Enter", "View", Color::Cyan),
            ("Del", "Delete", Color::Red),
            ("Esc", "Back", Color::Yellow),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Recall(_), InputMode::Normal) => vec![
            ("/", "Query", Color::Green),
            ("Esc", "Back", Color::Yellow),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Recall(_), InputMode::Query) => vec![
            ("Enter", "Search", Color::Green),
            ("Esc", "Cancel", Color::Red),
        ],
        (View::Reflect(_), InputMode::Normal) => vec![
            ("/", "Query", Color::Green),
            ("Esc", "Back", Color::Yellow),
            ("R", "Refresh", Color::Yellow),
            ("a", if app.auto_refresh_enabled { "Auto" } else { "Auto" },
             if app.auto_refresh_enabled { Color::Green } else { Color::DarkGray }),
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
        (View::Reflect(_), InputMode::Query) => vec![
            ("Enter", "Reflect", Color::Green),
            ("Esc", "Cancel", Color::Red),
        ],
        _ => vec![
            ("?", "Help", Color::Magenta),
            ("q", "Quit", Color::Red),
        ],
    };

    // Split into left (context) and right (shortcuts) sections
    let columns = Layout::default()
        .direction(Direction::Horizontal)
        .constraints([
            Constraint::Percentage(30),  // Context on left
            Constraint::Percentage(70),  // Shortcuts on right
        ])
        .split(area);

    // Left: Context info
    let context_info = match &app.view {
        View::Banks => "Context: Banks List".to_string(),
        View::Memories(bank_id) => format!("Context: Memories [{}]", bank_id),
        View::Entities(bank_id) => format!("Context: Entities [{}]", bank_id),
        View::Documents(bank_id) => format!("Context: Documents [{}]", bank_id),
        View::Recall(bank_id) => format!("Context: Recall [{}]", bank_id),
        View::Reflect(bank_id) => format!("Context: Reflect [{}]", bank_id),
    };

    let context_widget = Paragraph::new(context_info)
        .block(Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan))
            .title(" Context "))
        .style(Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Left);
    f.render_widget(context_widget, columns[0]);

    // Right: Shortcuts in columns if many
    // Calculate shortcuts per column (max 3 lines of shortcuts)
    let max_shortcuts_per_col = 3;
    let num_cols = (shortcuts.len() + max_shortcuts_per_col - 1) / max_shortcuts_per_col;

    let mut shortcut_lines = vec![];
    for row in 0..max_shortcuts_per_col {
        let mut line_spans = vec![];

        for col in 0..num_cols {
            let idx = col * max_shortcuts_per_col + row;
            if idx < shortcuts.len() {
                let (key, desc, color) = &shortcuts[idx];

                // Each shortcut gets fixed width: <key> desc = total 17 chars with spacing
                // Format: "<key> desc     " (padded to 17 for alignment)
                let shortcut_text = format!("<{:>6}> {:<9}", key, desc);

                line_spans.push(Span::styled(
                    shortcut_text,
                    Style::default().fg(*color).add_modifier(Modifier::BOLD)
                ));
            }
        }

        if !line_spans.is_empty() {
            shortcut_lines.push(Line::from(line_spans));
        }
    }

    let shortcuts_widget = Paragraph::new(shortcut_lines)
        .block(Block::default()
            .borders(Borders::ALL)
            .border_style(Style::default().fg(Color::Cyan))
            .title(" Shortcuts "))
        .alignment(Alignment::Left);

    f.render_widget(shortcuts_widget, columns[1]);
}

fn render_header(f: &mut Frame, app: &App, area: Rect) {
    let bank_info = if let Some(bank_id) = app.view.bank_id() {
        format!(" [{}]", bank_id)
    } else {
        String::new()
    };

    let title = format!("Hindsight Explorer - {}{}", app.view.title(), bank_info);

    let header = Paragraph::new(title)
        .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
        .alignment(Alignment::Center)
        .block(Block::default().borders(Borders::ALL));

    f.render_widget(header, area);
}

fn render_footer(f: &mut Frame, app: &App, area: Rect) {
    // Simple status line only (shortcuts are now at the top, no border)
    let status_line = if !app.error_message.is_empty() {
        Line::from(vec![
            Span::styled(" Error: ", Style::default().fg(Color::Red).add_modifier(Modifier::BOLD)),
            Span::raw(&app.error_message),
        ])
    } else if app.loading {
        Line::from(Span::styled(" Loading...", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)))
    } else if !app.status_message.is_empty() {
        Line::from(vec![
            Span::raw(" "),
            Span::styled(&app.status_message, Style::default().fg(Color::Green)),
        ])
    } else {
        Line::from("")
    };

    let footer = Paragraph::new(status_line).alignment(Alignment::Left);
    f.render_widget(footer, area);
}

fn render_banks(f: &mut Frame, app: &mut App, area: Rect) {
    let items: Vec<ListItem> = app
        .banks
        .iter()
        .map(|bank| {
            let name = if bank.name.is_empty() { "Unnamed" } else { &bank.name };
            let content = format!("{} - {}", bank.bank_id, name);
            ListItem::new(content).style(Style::default().fg(Color::White))
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Banks"))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol(">> ");

    f.render_stateful_widget(list, area, &mut app.banks_state);
}

fn render_memories(f: &mut Frame, app: &mut App, area: Rect) {
    // K9s-style table with columns
    let mut items = vec![
        // Header row
        ListItem::new(format!("{:<12} {:<20} {}", "TYPE", "CREATED", "TEXT"))
            .style(Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))
    ];

    // Data rows
    for memory in &app.memories {
        let mem_type = memory.get("type").and_then(|v| v.as_str()).unwrap_or("unknown");
        let created = memory.get("created_at")
            .and_then(|v| v.as_str())
            .and_then(|s| s.split('T').next())
            .unwrap_or("unknown");
        let text = memory.get("text").and_then(|v| v.as_str()).unwrap_or("");
        let preview = text.chars().take(60).collect::<String>();

        let content = format!("{:<12} {:<20} {}", mem_type, created, preview);
        items.push(ListItem::new(content).style(Style::default().fg(Color::White)));
    }

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Memories"))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol(">> ");

    f.render_stateful_widget(list, area, &mut app.memories_state);
}

fn render_entities(f: &mut Frame, app: &mut App, area: Rect) {
    let items: Vec<ListItem> = app
        .entities
        .iter()
        .map(|entity| {
            let content = format!("{} (mentioned {} times)", entity.canonical_name, entity.mention_count);
            ListItem::new(content).style(Style::default().fg(Color::White))
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Entities"))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol(">> ");

    f.render_stateful_widget(list, area, &mut app.entities_state);
}

fn render_documents(f: &mut Frame, app: &mut App, area: Rect) {
    let items: Vec<ListItem> = app
        .documents
        .iter()
        .map(|doc| {
            let id = doc.get("id")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            let content_type = doc.get("content_type")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown");
            let content = format!("{} ({})", id, content_type);
            ListItem::new(content).style(Style::default().fg(Color::White))
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title("Documents"))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol(">> ");

    f.render_stateful_widget(list, area, &mut app.documents_state);
}

fn render_recall(f: &mut Frame, app: &mut App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Query input
            Constraint::Min(0),     // Results
        ])
        .split(area);

    // Query input
    let query_style = if app.input_mode == InputMode::Query {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default()
    };

    let query = Paragraph::new(app.recall_query.as_str())
        .style(query_style)
        .block(Block::default().borders(Borders::ALL).title("Query (press / to edit)"));

    f.render_widget(query, chunks[0]);

    // Results
    let items: Vec<ListItem> = app
        .recall_results
        .iter()
        .map(|result| {
            let preview = result.text.chars().take(100).collect::<String>();
            let type_field = result.type_.as_deref().unwrap_or("unknown");
            let content = format!("[{}] {}", type_field, preview);
            ListItem::new(content).style(Style::default().fg(Color::White))
        })
        .collect();

    let list = List::new(items)
        .block(Block::default().borders(Borders::ALL).title(format!("Results ({})", app.recall_results.len())))
        .highlight_style(
            Style::default()
                .bg(Color::DarkGray)
                .add_modifier(Modifier::BOLD),
        )
        .highlight_symbol(">> ");

    f.render_stateful_widget(list, chunks[1], &mut app.recall_results_state);
}

fn render_reflect(f: &mut Frame, app: &mut App, area: Rect) {
    let chunks = Layout::default()
        .direction(Direction::Vertical)
        .constraints([
            Constraint::Length(3),  // Query input
            Constraint::Min(0),     // Response
        ])
        .split(area);

    // Query input
    let query_style = if app.input_mode == InputMode::Query {
        Style::default().fg(Color::Yellow)
    } else {
        Style::default()
    };

    let query = Paragraph::new(app.reflect_query.as_str())
        .style(query_style)
        .block(Block::default().borders(Borders::ALL).title("Query (press / to edit)"));

    f.render_widget(query, chunks[0]);

    // Response
    let response = Paragraph::new(app.reflect_response.as_str())
        .style(Style::default())
        .block(Block::default().borders(Borders::ALL).title("Response"))
        .wrap(Wrap { trim: false });

    f.render_widget(response, chunks[1]);
}

fn render_help(f: &mut Frame, area: Rect) {
    let help_text = vec![
        Line::from(Span::styled("Hindsight Explorer - Keyboard Shortcuts", Style::default().fg(Color::Cyan).add_modifier(Modifier::BOLD))),
        Line::from(""),
        Line::from(vec![
            Span::styled("Navigation", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ]),
        Line::from("  ↑/↓, j/k    - Navigate up/down in lists"),
        Line::from("  Enter       - Select item / drill down"),
        Line::from("  Esc         - Go back to previous view"),
        Line::from(""),
        Line::from(vec![
            Span::styled("Views (from Bank selection)", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ]),
        Line::from("  m           - View memories for selected bank"),
        Line::from("  e           - View entities for selected bank"),
        Line::from("  r           - Recall (search) in selected bank"),
        Line::from("  t           - Reflect (think) with selected bank"),
        Line::from(""),
        Line::from(vec![
            Span::styled("Actions", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ]),
        Line::from("  /           - Enter query (in Recall/Reflect views)"),
        Line::from("  Enter       - Execute query (when in query mode)"),
        Line::from("  R           - Refresh current view"),
        Line::from("  a           - Toggle auto-refresh (5s interval)"),
        Line::from(""),
        Line::from(vec![
            Span::styled("General", Style::default().fg(Color::Yellow).add_modifier(Modifier::BOLD)),
        ]),
        Line::from("  ?           - Toggle this help screen"),
        Line::from("  q           - Quit"),
        Line::from(""),
        Line::from(Span::styled("Press ? to close help", Style::default().fg(Color::DarkGray))),
    ];

    let help = Paragraph::new(help_text)
        .block(Block::default().borders(Borders::ALL).title("Help"))
        .alignment(Alignment::Left);

    f.render_widget(help, area);
}

fn run_app<B: Backend>(terminal: &mut Terminal<B>, mut app: App) -> Result<()> {
    // Initial load
    app.refresh()?;

    loop {
        terminal.draw(|f| ui(f, &mut app))?;

        if event::poll(Duration::from_millis(100))? {
            if let Event::Key(key) = event::read()? {
                // Handle Ctrl+C to exit
                if key.code == KeyCode::Char('c') && key.modifiers.contains(crossterm::event::KeyModifiers::CONTROL) {
                    return Ok(());
                }

                match app.input_mode {
                    InputMode::Normal => {
                        match key.code {
                            KeyCode::Char('q') => return Ok(()),
                            KeyCode::Char('?') => app.show_help = !app.show_help,

                            // Navigation
                            KeyCode::Down | KeyCode::Char('j') => app.next_item(),
                            KeyCode::Up | KeyCode::Char('k') => app.previous_item(),
                            KeyCode::Enter => app.enter_view()?,
                            KeyCode::Esc => app.go_back(),

                            // View switching (only from Banks view or same bank)
                            KeyCode::Char('m') => {
                                if let Some(i) = app.banks_state.selected() {
                                    if let Some(bank) = app.banks.get(i) {
                                        app.switch_to_view(View::Memories(bank.bank_id.clone()))?;
                                    }
                                }
                            }
                            KeyCode::Char('e') => {
                                if let Some(i) = app.banks_state.selected() {
                                    if let Some(bank) = app.banks.get(i) {
                                        app.switch_to_view(View::Entities(bank.bank_id.clone()))?;
                                    }
                                }
                            }
                            KeyCode::Char('d') => {
                                if let Some(i) = app.banks_state.selected() {
                                    if let Some(bank) = app.banks.get(i) {
                                        app.switch_to_view(View::Documents(bank.bank_id.clone()))?;
                                    }
                                }
                            }
                            KeyCode::Char('r') => {
                                if let Some(i) = app.banks_state.selected() {
                                    if let Some(bank) = app.banks.get(i) {
                                        app.switch_to_view(View::Recall(bank.bank_id.clone()))?;
                                    }
                                } else if let Some(bank_id) = app.view.bank_id() {
                                    app.switch_to_view(View::Recall(bank_id.to_string()))?;
                                }
                            }
                            KeyCode::Char('t') => {
                                if let Some(i) = app.banks_state.selected() {
                                    if let Some(bank) = app.banks.get(i) {
                                        app.switch_to_view(View::Reflect(bank.bank_id.clone()))?;
                                    }
                                } else if let Some(bank_id) = app.view.bank_id() {
                                    app.switch_to_view(View::Reflect(bank_id.to_string()))?;
                                }
                            }

                            // Refresh
                            KeyCode::Char('R') => {
                                app.refresh()?;
                            }

                            // Toggle auto-refresh
                            KeyCode::Char('a') => {
                                app.toggle_auto_refresh();
                            }

                            // Query input
                            KeyCode::Char('/') => {
                                if matches!(app.view, View::Recall(_) | View::Reflect(_)) {
                                    app.input_mode = InputMode::Query;
                                }
                            }

                            _ => {}
                        }
                    }
                    InputMode::Query => {
                        match key.code {
                            KeyCode::Enter => {
                                match &app.view {
                                    View::Recall(_) => app.execute_recall()?,
                                    View::Reflect(_) => app.execute_reflect()?,
                                    _ => {}
                                }
                            }
                            KeyCode::Esc => {
                                app.input_mode = InputMode::Normal;
                            }
                            KeyCode::Char(c) => {
                                match &app.view {
                                    View::Recall(_) => app.recall_query.push(c),
                                    View::Reflect(_) => app.reflect_query.push(c),
                                    _ => {}
                                }
                            }
                            KeyCode::Backspace => {
                                match &app.view {
                                    View::Recall(_) => { app.recall_query.pop(); }
                                    View::Reflect(_) => { app.reflect_query.pop(); }
                                    _ => {}
                                }
                            }
                            _ => {}
                        }
                    }
                }
            }
        }

        // Auto-refresh check
        app.do_auto_refresh()?;
    }
}

pub fn run(client: &ApiClient) -> Result<()> {
    // Setup terminal
    enable_raw_mode()?;
    let mut stdout = io::stdout();
    execute!(stdout, EnterAlternateScreen, EnableMouseCapture)?;
    let backend = CrosstermBackend::new(stdout);
    let mut terminal = Terminal::new(backend)?;

    // Create app and run it
    let app = App::new(client.clone());
    let res = run_app(&mut terminal, app);

    // Restore terminal
    disable_raw_mode()?;
    execute!(
        terminal.backend_mut(),
        LeaveAlternateScreen,
        DisableMouseCapture
    )?;
    terminal.show_cursor()?;

    if let Err(err) = res {
        println!("Error: {:?}", err);
    }

    Ok(())
}

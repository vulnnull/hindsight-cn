// Global state
let allGraphData = null;
let cy = null;
let debugPanes = [];
let debugPaneCounter = 0;
let currentAgentId = null; // Global agent context
let dataGraphs = {
    world: null,
    agent: null,
    opinions: null
};
let dataCache = {
    world: null,
    agent: null,
    opinions: null
};
let currentDataSubTab = 'world';

// Main tab switching (Data, Debug, Think, Benchmark)
window.switchMainTab = function(tabName) {
    // Remove active class from all main tabs and buttons
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });

    // Activate the selected tab
    const tabElement = document.getElementById(`${tabName}-tab`);
    if (tabElement) {
        tabElement.classList.add('active');
    }

    // Find and activate the corresponding button
    const buttons = document.querySelectorAll('.tab-button');
    buttons.forEach(btn => {
        const btnText = btn.textContent.toLowerCase();
        if (
            (tabName === 'data' && btnText.includes('data')) ||
            (tabName === 'debug' && btnText.includes('debug')) ||
            (tabName === 'think' && btnText.includes('think')) ||
            (tabName === 'benchmark' && btnText.includes('benchmark'))
        ) {
            btn.classList.add('active');
        }
    });

    // Tab-specific logic
    if (tabName === 'data') {
        // Resize current data graph if exists
        const factType = currentDataSubTab;
        if (dataGraphs[factType]) {
            setTimeout(() => dataGraphs[factType].resize(), 10);
        }
    } else if (tabName === 'debug') {
        if (debugPanes.length === 0) {
            addDebugPane();
        }
        debugPanes.forEach(pane => {
            if (pane.cy) {
                pane.cy.resize();
            }
        });
    } else if (tabName === 'think') {
        // Think tab uses global agent selector
    }
}

// Data subtab switching (World, Agent, Opinions)
window.switchDataSubTab = function(subTab) {
    currentDataSubTab = subTab;

    // Remove active class from all subtab buttons and content
    document.querySelectorAll('.data-sub-tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelectorAll('.data-subtab-content').forEach(content => {
        content.classList.remove('active');
    });

    // Activate selected subtab
    const buttons = document.querySelectorAll('.data-sub-tab-button');
    buttons.forEach(btn => {
        if (btn.textContent.toLowerCase().includes(subTab.toLowerCase())) {
            btn.classList.add('active');
        }
    });

    const subtabElement = document.getElementById(`${subTab}-subtab`);
    if (subtabElement) {
        subtabElement.classList.add('active');
    }

    // Resize graph if exists
    if (dataGraphs[subTab]) {
        setTimeout(() => dataGraphs[subTab].resize(), 10);
    }
}

// Switch between graph and table view for a fact type
window.switchDataView = function(factType, viewType) {
    const graphView = document.getElementById(`${factType}-graph-view`);
    const tableView = document.getElementById(`${factType}-table-view`);
    const buttons = document.querySelectorAll(`#${factType}-subtab .view-toggle-button`);

    // Update button states
    buttons.forEach(btn => {
        btn.classList.remove('active');
        if ((viewType === 'graph' && btn.textContent.includes('Graph')) ||
            (viewType === 'table' && btn.textContent.includes('Table'))) {
            btn.classList.add('active');
        }
    });

    // Show/hide views
    if (viewType === 'graph') {
        graphView.style.display = 'block';
        tableView.style.display = 'none';
        if (dataGraphs[factType]) {
            setTimeout(() => dataGraphs[factType].resize(), 10);
        }
    } else {
        graphView.style.display = 'none';
        tableView.style.display = 'block';
    }
}

// Load data for a specific fact type
window.loadDataView = async function(factType) {
    if (!currentAgentId) {
        alert('Please select an agent first');
        return;
    }

    try {
        // Build URL with agent filter and fact_type filter
        let url = `api/graph?agent_id=${encodeURIComponent(currentAgentId)}`;
        if (factType !== 'all') {
            url += `&fact_type=${factType}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        // Validate response structure
        if (!data || !data.nodes || !data.edges) {
            throw new Error('Invalid response format from server');
        }

        // Cache the data
        dataCache[factType] = data;

        // Update table
        updateDataTable(factType, data);

        // Update graph if in graph view
        const graphView = document.getElementById(`${factType}-graph-view`);
        if (graphView && graphView.style.display !== 'none') {
            reloadDataGraph(factType);
        }

        return data;
    } catch (e) {
        console.error(`Error loading ${factType} data:`, e);
        alert(`Error loading ${factType} data: ` + e.message);
    }
}

// Reload graph for a specific fact type
window.reloadDataGraph = function(factType) {
    const data = dataCache[factType];
    if (!data) return;

    const nodeLimit = parseInt(document.getElementById(`${factType}-node-limit`).value) || 50;
    const layoutName = document.getElementById(`${factType}-layout-select`).value;

    // Filter nodes to limit
    const limitedNodes = data.nodes.slice(0, nodeLimit);
    const nodeIds = new Set(limitedNodes.map(n => n.data.id));

    // Filter edges to only include those between visible nodes
    const limitedEdges = data.edges.filter(e =>
        nodeIds.has(e.data.source) && nodeIds.has(e.data.target)
    );

    // Update count display
    document.getElementById(`${factType}-node-count`).textContent =
        `Showing ${limitedNodes.length} of ${data.nodes.length} nodes`;

    // Destroy existing graph if any
    if (dataGraphs[factType]) {
        dataGraphs[factType].destroy();
    }

    // Layout configurations
    const layouts = {
        'circle': {
            name: 'circle',
            animate: false,
            radius: 300,
            spacingFactor: 1.5
        },
        'grid': {
            name: 'grid',
            animate: false,
            rows: Math.ceil(Math.sqrt(limitedNodes.length)),
            cols: Math.ceil(Math.sqrt(limitedNodes.length)),
            spacingFactor: 2
        },
        'cose': {
            name: 'cose',
            animate: false,
            nodeRepulsion: 15000,
            idealEdgeLength: 150,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        }
    };

    // Initialize Cytoscape
    dataGraphs[factType] = cytoscape({
        container: document.getElementById(`${factType}-cy`),

        elements: [
            ...limitedNodes.map(n => ({ data: n.data })),
            ...limitedEdges.map(e => ({ data: e.data }))
        ],

        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '10px',
                    'font-weight': 'bold',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'width': 40,
                    'height': 40,
                    'border-width': 2,
                    'border-color': '#333'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': 'data(color)',
                    'line-style': 'data(lineStyle)',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'data(color)',
                    'curve-style': 'bezier',
                    'opacity': 0.7
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#000'
                }
            }
        ],

        layout: layouts[layoutName] || layouts['circle']
    });

    // Add tooltip on hover
    let tooltip = null;
    dataGraphs[factType].on('mouseover', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        const renderedPosition = node.renderedPosition();

        tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.innerHTML = `
            <b>Text:</b> ${data.text}<br>
            <b>Context:</b> ${data.context}<br>
            <b>Date:</b> ${data.date}<br>
            <b>Entities:</b> ${data.entities}
        `;
        tooltip.style.left = renderedPosition.x + 20 + 'px';
        tooltip.style.top = renderedPosition.y + 'px';
        document.body.appendChild(tooltip);
    });

    dataGraphs[factType].on('mouseout', 'node', function(evt) {
        if (tooltip) {
            tooltip.remove();
            tooltip = null;
        }
    });
}

// Update table for a specific fact type
function updateDataTable(factType, data) {
    if (!data) return;

    const tbody = document.getElementById(`${factType}-table-body`);
    const countSpan = document.getElementById(`${factType}-table-count`);

    if (countSpan) {
        countSpan.textContent = `(${data.total_units})`;
    }

    if (tbody) {
        tbody.innerHTML = data.table_rows.map(row => `
            <tr>
                <td>${row.id}</td>
                <td>${row.text}</td>
                <td>${row.context}</td>
                <td>${row.date}</td>
                <td>${row.entities}</td>
                <td>
                    <button onclick="deleteRecord('${factType}', '${row.id}')"
                            class="delete-button"
                            title="Delete this record and all its links">
                        Delete
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Setup table filter
    const filterInput = document.getElementById(`${factType}-table-filter`);
    if (filterInput) {
        filterInput.removeEventListener('input', filterInput._filterHandler);
        filterInput._filterHandler = function() {
            const filterValue = this.value.toLowerCase();
            const rows = document.querySelectorAll(`#${factType}-table-body tr`);

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(filterValue)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        };
        filterInput.addEventListener('input', filterInput._filterHandler);
    }
}

// Delete a record and all its links
window.deleteRecord = async function(factType, recordId) {
    if (!confirm('Are you sure you want to delete this record and all its links? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`api/memory/${encodeURIComponent(recordId)}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        alert(result.message || 'Record deleted successfully');

        // Reload the table data
        await loadDataView(factType);
    } catch (e) {
        console.error('Error deleting record:', e);
        alert('Error deleting record: ' + e.message);
    }
}

// Load data from API (old function - kept for backward compatibility)
async function loadGraphData() {
    try {
        // Require agent selection
        if (!currentAgentId) {
            alert('Please select an agent first');
            return;
        }

        // Build URL with agent filter
        let url = `api/graph?agent_id=${encodeURIComponent(currentAgentId)}`;

        const response = await fetch(url);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        allGraphData = await response.json();

        // Validate response structure
        if (!allGraphData || !allGraphData.nodes || !allGraphData.edges) {
            throw new Error('Invalid response format from server');
        }

        // Update table
        updateTable();

        // Initialize graph
        if (document.getElementById('graph-tab').classList.contains('active')) {
            reloadGraph();
        }

        return allGraphData;
    } catch (e) {
        console.error('Error loading graph data:', e);
        alert('Error loading graph data: ' + e.message);

        // Show error in the UI
        const cyDiv = document.getElementById('cy');
        if (cyDiv) {
            cyDiv.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #d32f2f;">
                    <h3>Failed to load graph data</h3>
                    <p>${e.message}</p>
                    <button onclick="loadGraphData()" style="margin-top: 20px; padding: 10px 20px; background: #42a5f5; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        Retry
                    </button>
                </div>
            `;
        }
    }
}

// Refresh data from server
function refreshData() {
    loadGraphData();
}

// Update table with current data
function updateTable() {
    if (!allGraphData) return;

    const tbody = document.getElementById('table-body');
    const countSpan = document.getElementById('table-count');

    countSpan.textContent = `(${allGraphData.total_units})`;

    tbody.innerHTML = allGraphData.table_rows.map(row => `
        <tr>
            <td>${row.id}</td>
            <td>${row.text}</td>
            <td>${row.context}</td>
            <td>${row.date}</td>
            <td>${row.entities}</td>
        </tr>
    `).join('');
}

// Initialize graph with filtering
function initGraph(nodeLimit, layoutName) {
    if (!allGraphData) return;

    // Filter nodes to limit
    const limitedNodes = allGraphData.nodes.slice(0, nodeLimit);
    const nodeIds = new Set(limitedNodes.map(n => n.data.id));

    // Filter edges to only include those between visible nodes
    const limitedEdges = allGraphData.edges.filter(e =>
        nodeIds.has(e.data.source) && nodeIds.has(e.data.target)
    );

    // Update count display
    document.getElementById('node-count').textContent =
        `Showing ${limitedNodes.length} of ${allGraphData.nodes.length} nodes`;

    // Destroy existing graph if any
    if (cy) {
        cy.destroy();
    }

    // Layout configurations
    const layouts = {
        'circle': {
            name: 'circle',
            animate: false,
            radius: 300,
            spacingFactor: 1.5
        },
        'grid': {
            name: 'grid',
            animate: false,
            rows: Math.ceil(Math.sqrt(limitedNodes.length)),
            cols: Math.ceil(Math.sqrt(limitedNodes.length)),
            spacingFactor: 2
        },
        'cose': {
            name: 'cose',
            animate: false,
            nodeRepulsion: 15000,
            idealEdgeLength: 150,
            edgeElasticity: 100,
            nestingFactor: 1.2,
            gravity: 1,
            numIter: 1000,
            initialTemp: 200,
            coolingFactor: 0.95,
            minTemp: 1.0
        }
    };

    // Initialize Cytoscape
    cy = cytoscape({
        container: document.getElementById('cy'),

        elements: [
            ...limitedNodes.map(n => ({ data: n.data })),
            ...limitedEdges.map(e => ({ data: e.data }))
        ],

        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': '10px',
                    'font-weight': 'bold',
                    'text-wrap': 'wrap',
                    'text-max-width': '100px',
                    'width': 40,
                    'height': 40,
                    'border-width': 2,
                    'border-color': '#333'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 1,
                    'line-color': 'data(color)',
                    'line-style': 'data(lineStyle)',
                    'target-arrow-shape': 'triangle',
                    'target-arrow-color': 'data(color)',
                    'curve-style': 'bezier',
                    'opacity': 0.7
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#000'
                }
            }
        ],

        layout: layouts[layoutName] || layouts['circle']
    });

    // Simple tooltip on hover
    let tooltip = null;

    cy.on('mouseover', 'node', function(evt) {
        const node = evt.target;
        const data = node.data();
        const renderedPosition = node.renderedPosition();

        // Create tooltip
        tooltip = document.createElement('div');
        tooltip.className = 'tooltip';
        tooltip.innerHTML = `
            <b>Text:</b> ${data.text}<br>
            <b>Context:</b> ${data.context}<br>
            <b>Date:</b> ${data.date}<br>
            <b>Entities:</b> ${data.entities}
        `;
        tooltip.style.left = renderedPosition.x + 20 + 'px';
        tooltip.style.top = renderedPosition.y + 'px';
        document.body.appendChild(tooltip);
    });

    cy.on('mouseout', 'node', function(evt) {
        if (tooltip) {
            tooltip.remove();
            tooltip = null;
        }
    });
}

// Reload graph with current settings
function reloadGraph() {
    const nodeLimit = parseInt(document.getElementById('node-limit').value) || 50;
    const layoutName = document.getElementById('layout-select').value;
    initGraph(nodeLimit, layoutName);
}

// Load available agents
let agentsLoaded = false;
async function loadAgents() {
    if (agentsLoaded) return;

    try {
        const response = await fetch('api/agents');
        const data = await response.json();

        const select = document.getElementById('search-agent-id');
        select.innerHTML = '';

        if (data.agents && data.agents.length > 0) {
            data.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent;
                option.textContent = agent;
                select.appendChild(option);
            });
            agentsLoaded = true;
        } else {
            select.innerHTML = '<option value="default">default</option>';
        }
    } catch (e) {
        console.error('Error loading agents:', e);
        const select = document.getElementById('search-agent-id');
        select.innerHTML = '<option value="default">default</option>';
    }
}

// Debug pane management
function addDebugPane() {
    const paneId = debugPaneCounter++;
    const container = document.getElementById('debug-panes-container');

    const paneDiv = document.createElement('div');
    paneDiv.className = 'debug-pane';
    paneDiv.id = `debug-pane-${paneId}`;
    paneDiv.innerHTML = `
        <div class="debug-pane-header">
            Search Trace #${paneId + 1}
            <button onclick="removeSpecificDebugPane(${paneId})" style="float: right; padding: 4px 12px; background: #ef5350; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">✕ Remove</button>
        </div>
        <div class="debug-search-controls">
            <div style="display: flex; gap: 10px; align-items: flex-end; flex-wrap: wrap;">
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;">Query:</label>
                    <input type="text" id="search-query-${paneId}" placeholder="Enter search query..." style="width: 250px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                </div>
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;">Search Type:</label>
                    <select id="search-type-${paneId}" style="width: 120px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                        <option value="all">All Facts</option>
                        <option value="world">World Facts</option>
                        <option value="agent">Agent Facts</option>
                        <option value="opinion">Opinion Facts</option>
                    </select>
                </div>
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;">Agent:</label>
                    <select id="search-agent-${paneId}" style="width: 120px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                        <option value="">Loading...</option>
                    </select>
                </div>
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;">Budget:</label>
                    <input type="number" id="search-budget-${paneId}" value="100" min="10" max="1000" style="width: 70px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                </div>
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;">Top K:</label>
                    <input type="number" id="search-top-k-${paneId}" value="10" min="1" max="50" style="width: 60px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                </div>
                <div>
                    <label style="font-weight: bold; display: block; margin-bottom: 3px; font-size: 12px;" title="MMR Lambda: 0=max diversity, 1=no diversity">MMR λ:</label>
                    <input type="number" id="search-mmr-lambda-${paneId}" value="0.5" min="0" max="1" step="0.1" style="width: 60px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                </div>
                <button onclick="runSearchInPane(${paneId})" style="padding: 6px 16px; background: #42a5f5; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px;">🔍 Search</button>
            </div>
        </div>
        <div class="debug-status-bar" id="debug-status-${paneId}">
            <span style="color: #666;">Ready to search</span>
        </div>
        <div class="debug-controls">
            <label>
                <input type="radio" name="viz-mode-${paneId}" id="debug-mode-graph-${paneId}" checked> Graph View
            </label>
            <label>
                <input type="radio" name="viz-mode-${paneId}" id="debug-mode-log-${paneId}"> Decision Log
            </label>
            <label>
                <input type="radio" name="viz-mode-${paneId}" id="debug-mode-table-${paneId}"> Results Table
            </label>
            <span id="graph-controls-${paneId}" style="margin-left: 20px;">
                <label>
                    <input type="checkbox" id="debug-show-pruned-${paneId}"> Show pruned nodes
                </label>
                <label>
                    <input type="checkbox" id="debug-highlight-path-${paneId}"> Highlight top result path
                </label>
                <span style="margin-left: 15px;">
                    <input type="text" id="graph-search-${paneId}" placeholder="Find nodes..." style="width: 150px; padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px; font-size: 12px;">
                    <span id="graph-search-count-${paneId}" style="margin-left: 5px; font-size: 12px; color: #666;"></span>
                </span>
            </span>
        </div>
        <div class="debug-viz-container">
            <div class="debug-viz" id="debug-cy-${paneId}" style="display: block;"></div>
            <div class="decision-log" id="decision-log-${paneId}" style="display: none;"></div>
            <div class="results-table-container" id="results-table-${paneId}" style="display: none;"></div>
        </div>
    `;

    container.appendChild(paneDiv);

    // Add event listeners for view mode toggle
    document.getElementById(`debug-mode-graph-${paneId}`).addEventListener('change', function() {
        if (this.checked) {
            document.getElementById(`debug-cy-${paneId}`).style.display = 'block';
            document.getElementById(`decision-log-${paneId}`).style.display = 'none';
            document.getElementById(`results-table-${paneId}`).style.display = 'none';
            document.getElementById(`graph-controls-${paneId}`).style.display = 'inline';
            const pane = debugPanes.find(p => p.id === paneId);
            if (pane && pane.cy) {
                setTimeout(() => pane.cy.resize(), 10);
            }
        }
    });

    document.getElementById(`debug-mode-log-${paneId}`).addEventListener('change', function() {
        if (this.checked) {
            document.getElementById(`debug-cy-${paneId}`).style.display = 'none';
            document.getElementById(`decision-log-${paneId}`).style.display = 'block';
            document.getElementById(`results-table-${paneId}`).style.display = 'none';
            document.getElementById(`graph-controls-${paneId}`).style.display = 'none';
        }
    });

    document.getElementById(`debug-mode-table-${paneId}`).addEventListener('change', function() {
        if (this.checked) {
            document.getElementById(`debug-cy-${paneId}`).style.display = 'none';
            document.getElementById(`decision-log-${paneId}`).style.display = 'none';
            document.getElementById(`results-table-${paneId}`).style.display = 'block';
            document.getElementById(`graph-controls-${paneId}`).style.display = 'none';
        }
    });

    // Add event listeners for graph controls
    document.getElementById(`debug-show-pruned-${paneId}`).addEventListener('change', function() {
        const pane = debugPanes.find(p => p.id === paneId);
        if (pane && pane.trace) {
            visualizeTrace(paneId, pane.trace);
        }
    });

    document.getElementById(`debug-highlight-path-${paneId}`).addEventListener('change', function() {
        const pane = debugPanes.find(p => p.id === paneId);
        if (pane && pane.trace) {
            visualizeTrace(paneId, pane.trace);
        }
    });

    // Add search input listener for finding nodes
    document.getElementById(`graph-search-${paneId}`).addEventListener('input', function(e) {
        const pane = debugPanes.find(p => p.id === paneId);
        if (pane && pane.cy) {
            highlightMatchingNodes(paneId, e.target.value);
        }
    });

    debugPanes.push({
        id: paneId,
        element: paneDiv,
        cy: null,
        trace: null
    });

    // Load agents for this pane after DOM is ready
    setTimeout(() => loadAgentsForPane(paneId), 10);
}

async function loadAgentsForPane(paneId) {
    const select = document.getElementById(`search-agent-${paneId}`);
    if (!select) {
        console.error(`Could not find select element for pane ${paneId}`);
        return;
    }

    try {
        const response = await fetch('api/agents');
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        select.innerHTML = '';

        if (data.agents && data.agents.length > 0) {
            data.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent;
                option.textContent = agent;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="default">default</option>';
        }
    } catch (e) {
        console.error('Error loading agents for pane:', paneId, e);
        select.innerHTML = '<option value="default">default</option>';
    }
}

window.runSearchInPane = async function(paneId) {
    const pane = debugPanes.find(p => p.id === paneId);
    if (!pane) return;

    const query = document.getElementById(`search-query-${paneId}`).value;
    const searchType = document.getElementById(`search-type-${paneId}`).value;
    const agentId = document.getElementById(`search-agent-${paneId}`).value;
    const thinkingBudget = parseInt(document.getElementById(`search-budget-${paneId}`).value);
    const topK = parseInt(document.getElementById(`search-top-k-${paneId}`).value);
    const mmrLambda = parseFloat(document.getElementById(`search-mmr-lambda-${paneId}`).value);
    const statusBar = document.getElementById(`debug-status-${paneId}`);

    if (!query) {
        alert('Please enter a query');
        return;
    }

    try {
        // Prepare request body with optional fact_type
        const requestBody = {
            query: query,
            agent_id: agentId,
            thinking_budget: thinkingBudget,
            top_k: topK,
            mmr_lambda: mmrLambda,
            trace: true
        };

        // Add fact_type if not 'all'
        if (searchType !== 'all') {
            requestBody.fact_type = searchType;
        }

        statusBar.innerHTML = '<span style="color: #ff9800;">🔄 Searching...</span>';

        const response = await fetch('api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        });

        const data = await response.json();

        if (data.detail) {
            statusBar.innerHTML = `<span style="color: #d32f2f;">❌ Error: ${data.detail}</span>`;
            return;
        }

        // Update status bar with stats
        const summary = data.trace.summary;
        statusBar.innerHTML = `
            <span style="color: #43a047;">✓ Search complete</span>
            <span style="margin: 0 10px; color: #666;">|</span>
            <span><strong>Nodes visited:</strong> ${summary.total_nodes_visited}</span>
            <span style="margin: 0 10px; color: #666;">|</span>
            <span><strong>Entry points:</strong> ${summary.entry_points_found}</span>
            <span style="margin: 0 10px; color: #666;">|</span>
            <span><strong>Budget used:</strong> ${summary.budget_used} / ${summary.budget_used + summary.budget_remaining}</span>
            <span style="margin: 0 10px; color: #666;">|</span>
            <span><strong>Results:</strong> ${summary.results_returned}</span>
            <span style="margin: 0 10px; color: #666;">|</span>
            <span><strong>Duration:</strong> ${summary.total_duration_seconds.toFixed(2)}s</span>
        `;

        // Visualize the trace and results
        pane.trace = data.trace;
        pane.results = data.results;
        visualizeTrace(paneId, data.trace);
        renderDecisionLog(paneId, data.trace);
        renderResultsTable(paneId, data.results, data.trace);

    } catch (e) {
        statusBar.innerHTML = `<span style="color: #d32f2f;">❌ Error: ${e.message}</span>`;
        console.error('Error running search:', e);
    }
}

window.removeSpecificDebugPane = function(paneId) {
    const paneIndex = debugPanes.findIndex(p => p.id === paneId);
    if (paneIndex === -1) return;

    const pane = debugPanes[paneIndex];
    if (pane.cy) {
        pane.cy.destroy();
    }
    pane.element.remove();
    debugPanes.splice(paneIndex, 1);
}

function removeDebugPane() {
    if (debugPanes.length === 0) return;

    const pane = debugPanes.pop();
    if (pane.cy) {
        pane.cy.destroy();
    }
    pane.element.remove();
}

function renderResultsTable(paneId, results, trace) {
    const tableDiv = document.getElementById(`results-table-${paneId}`);
    if (!tableDiv) return;

    if (!results || results.length === 0) {
        tableDiv.innerHTML = '<div style="padding: 40px; text-align: center; color: #666;">No results returned</div>';
        return;
    }

    // Check if MMR was used
    const mmrUsed = results.some(r => r.mmr_score !== null && r.mmr_score !== undefined);

    let html = `
        <div style="padding: 20px; overflow: auto; height: 100%;">
            <h3>Search Results (${results.length} memories)</h3>
            <p style="color: #666; font-size: 13px; margin-bottom: 10px;">
                Query: "${trace.query.query_text}"
            </p>
            ${mmrUsed ? `
            <div style="background: #e3f2fd; padding: 10px; border-left: 4px solid #2196f3; margin-bottom: 15px; font-size: 12px;">
                <strong>MMR Diversification Active:</strong>
                🎯 = Diversified pick (selected for variety) |
                <span style="background: #fff3e0; padding: 2px 6px; border-radius: 3px;">Orange background</span> = Rank changed by MMR |
                <strong>Orig Rank</strong> shows position before MMR reranking
            </div>
            ` : ''}
            <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                    <tr style="background: #f0f0f0; border: 2px solid #333;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Rank</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Original rank before MMR">Orig Rank</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Text</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Context</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Final weighted score">Final Score</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Spreading activation value">Activation</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Semantic similarity to query">Similarity</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Recency boost">Recency</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Frequency boost">Frequency</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="MMR score (relevance - diversity penalty)">MMR Score</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Normalized relevance component">MMR Rel</th>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;" title="Max similarity to already selected">MMR Sim</th>
                    </tr>
                </thead>
                <tbody>
    `;

    results.forEach((result, idx) => {
        // Find corresponding visit in trace
        const visit = trace.visits.find(v => v.node_id === result.id);

        // Get scores from visit weights
        const finalScore = visit ? visit.weights.final_weight : (result.score || 0);
        const activation = visit ? visit.weights.activation : 0;
        const similarity = visit ? visit.weights.semantic_similarity : 0;
        const recency = visit ? (visit.weights.recency || 0) : 0;
        const frequency = visit ? (visit.weights.frequency || 0) : 0;

        // Get MMR information
        const originalRank = result.original_rank || (idx + 1);
        const mmrScore = result.mmr_score;
        const mmrRelevance = result.mmr_relevance;
        const mmrMaxSim = result.mmr_max_similarity;
        const isDiversified = result.mmr_diversified || false;

        // Highlight diversified results
        const rowBg = isDiversified ? '#fff3e0' : 'white';
        const rankDisplay = originalRank !== (idx + 1) ? `<span style="color: #ff9800;" title="Rank changed by MMR">↑${originalRank}</span>` : originalRank;

        html += `
            <tr style="border: 1px solid #ddd; background: ${rowBg};">
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold;">#${idx + 1}${isDiversified ? ' 🎯' : ''}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${rankDisplay}</td>
                <td style="padding: 8px; border: 1px solid #ddd; max-width: 300px;">${result.text}</td>
                <td style="padding: 8px; border: 1px solid #ddd; max-width: 150px;">${result.context || 'N/A'}</td>
                <td style="padding: 8px; border: 1px solid #ddd; white-space: nowrap;">${result.event_date ? new Date(result.event_date).toLocaleDateString() : 'N/A'}</td>
                <td style="padding: 8px; border: 1px solid #ddd;"><strong>${finalScore.toFixed(4)}</strong></td>
                <td style="padding: 8px; border: 1px solid #ddd;">${activation.toFixed(4)}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${similarity.toFixed(4)}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${recency.toFixed(4)}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${frequency.toFixed(4)}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${mmrScore !== null && mmrScore !== undefined ? mmrScore.toFixed(4) : '-'}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${mmrRelevance !== null && mmrRelevance !== undefined ? mmrRelevance.toFixed(4) : '-'}</td>
                <td style="padding: 8px; border: 1px solid #ddd;">${mmrMaxSim !== null && mmrMaxSim !== undefined ? mmrMaxSim.toFixed(4) : '-'}</td>
            </tr>
        `;
    });

    html += `
                </tbody>
            </table>
        </div>
    `;

    tableDiv.innerHTML = html;
}

function renderDecisionLog(paneId, trace) {
    const logDiv = document.getElementById(`decision-log-${paneId}`);
    if (!logDiv || !trace) return;

    // Group visits by step
    const stepGroups = {};
    trace.visits.forEach(visit => {
        if (!stepGroups[visit.step]) {
            stepGroups[visit.step] = [];
        }
        stepGroups[visit.step].push(visit);
    });

    // Build HTML for decision log
    let html = `
        <div class="log-header">
            <h3>Search Execution Trace</h3>
            <p><strong>Query:</strong> "${trace.query.query_text}"</p>
            <p class="log-explanation">
                This log shows the step-by-step decision process of the spreading activation search algorithm.
                The search starts from entry points (semantically similar memories) and spreads through connected memories,
                following temporal, semantic, and entity links to find relevant results.
            </p>
        </div>
    `;

    const maxStep = Math.max(...Object.keys(stepGroups).map(k => parseInt(k)));

    for (let step = 0; step <= maxStep; step++) {
        const visits = stepGroups[step] || [];
        if (visits.length === 0) continue;

        html += `<div class="log-step">`;
        html += `<div class="log-step-header">Step ${step}</div>`;

        if (step === 0) {
            html += `<div class="log-step-explanation">
                🎯 <strong>Finding Entry Points:</strong> Searching for memories semantically similar to the query.
                These are the starting points for spreading activation.
            </div>`;
        } else {
            html += `<div class="log-step-explanation">
                🔍 <strong>Spreading Activation:</strong> Following links from previously activated memories.
                The algorithm explores connected memories and calculates their relevance.
            </div>`;
        }

        visits.forEach((visit, idx) => {
            const isEntry = visit.is_entry_point;
            const isResult = visit.final_rank !== null;
            const hasParent = visit.parent_node_id !== null;

            let cardClass = 'log-card';
            if (isEntry) cardClass += ' log-card-entry';
            if (isResult) cardClass += ' log-card-result';

            html += `<div class="${cardClass}">`;

            // Header
            if (isEntry) {
                html += `<div class="log-card-header">
                    <span class="log-badge log-badge-entry">Entry Point</span>
                    ${isResult ? `<span class="log-badge log-badge-result">Rank #${visit.final_rank}</span>` : ''}
                </div>`;
            } else if (hasParent) {
                const linkTypeIcon = {
                    'temporal': '⏱️',
                    'semantic': '🔗',
                    'entity': '👤'
                };
                const icon = linkTypeIcon[visit.link_type] || '➡️';
                html += `<div class="log-card-header">
                    <span class="log-badge log-badge-${visit.link_type}">${icon} ${visit.link_type} link</span>
                    ${isResult ? `<span class="log-badge log-badge-result">Rank #${visit.final_rank}</span>` : ''}
                </div>`;
            }

            // Memory text
            html += `<div class="log-memory-text">"${visit.text}"</div>`;

            // Decision details
            html += `<div class="log-details">`;

            if (isEntry) {
                html += `
                    <div class="log-detail-row">
                        <span class="log-detail-label">Why selected:</span>
                        <span class="log-detail-value">Semantic similarity to query = ${visit.weights.semantic_similarity.toFixed(3)}</span>
                    </div>
                `;
            } else if (hasParent) {
                html += `
                    <div class="log-detail-row">
                        <span class="log-detail-label">Activated from:</span>
                        <span class="log-detail-value">Node ${visit.parent_node_id.substring(0, 8)}... via ${visit.link_type} link</span>
                    </div>
                    <div class="log-detail-row">
                        <span class="log-detail-label">Link weight:</span>
                        <span class="log-detail-value">${visit.link_weight.toFixed(3)}</span>
                    </div>
                `;
            }

            html += `
                <div class="log-detail-row">
                    <span class="log-detail-label">Activation:</span>
                    <span class="log-detail-value">${visit.weights.activation.toFixed(3)}</span>
                    <span class="log-detail-help" title="Combined score from parent activation and link weight">ℹ️</span>
                </div>
                <div class="log-detail-row">
                    <span class="log-detail-label">Semantic similarity:</span>
                    <span class="log-detail-value">${visit.weights.semantic_similarity.toFixed(3)}</span>
                    <span class="log-detail-help" title="How semantically similar this memory is to the original query">ℹ️</span>
                </div>
                <div class="log-detail-row">
                    <span class="log-detail-label">Final weight:</span>
                    <span class="log-detail-value"><strong>${visit.weights.final_weight.toFixed(3)}</strong></span>
                    <span class="log-detail-help" title="Final score = activation × semantic_similarity">ℹ️</span>
                </div>
            `;

            html += `</div>`; // log-details
            html += `</div>`; // log-card
        });

        html += `</div>`; // log-step
    }

    // Add pruned nodes section if any
    if (trace.pruned && trace.pruned.length > 0) {
        html += `<div class="log-step">`;
        html += `<div class="log-step-header">Pruned Nodes</div>`;
        html += `<div class="log-step-explanation">
            ✂️ <strong>Budget Limit Reached:</strong> These nodes were not explored to conserve computational resources.
        </div>`;

        trace.pruned.forEach(pruned => {
            html += `<div class="log-card log-card-pruned">`;
            html += `<div class="log-card-header">
                <span class="log-badge log-badge-pruned">Pruned</span>
            </div>`;
            html += `<div class="log-details">`;
            html += `<div class="log-detail-row">
                <span class="log-detail-label">Reason:</span>
                <span class="log-detail-value">${pruned.reason}</span>
            </div>`;
            html += `<div class="log-detail-row">
                <span class="log-detail-label">Activation:</span>
                <span class="log-detail-value">${pruned.activation.toFixed(3)}</span>
            </div>`;
            html += `</div></div>`;
        });

        html += `</div>`;
    }

    logDiv.innerHTML = html;
}

function visualizeTrace(paneId, trace) {
    const pane = debugPanes.find(p => p.id === paneId);
    if (!pane || !trace) return;

    const cyDiv = document.getElementById(`debug-cy-${paneId}`);
    if (!cyDiv) return;

    const showPruned = document.getElementById(`debug-show-pruned-${paneId}`).checked;
    const highlightPath = document.getElementById(`debug-highlight-path-${paneId}`).checked;

    try {
        // Build graph from trace
        const nodes = [];
        const edges = [];
        const visitedNodeIds = new Set();

        // Add all visited nodes
        trace.visits.forEach((visit, idx) => {
            visitedNodeIds.add(visit.node_id);

            // Determine node color based on properties
            let color = '#90caf9'; // default
            if (visit.is_entry_point) {
                color = '#66bb6a'; // green for entry points
            } else if (visit.final_rank !== null) {
                color = '#ffd54f'; // yellow for results
            }

            nodes.push({
                data: {
                    id: visit.node_id,
                    label: `${visit.text.substring(0, 30)}...`,
                    text: visit.text,
                    step: visit.step,
                    rank: visit.final_rank,
                    activation: visit.weights.activation.toFixed(3),
                    similarity: visit.weights.semantic_similarity.toFixed(3),
                    finalWeight: visit.weights.final_weight.toFixed(3),
                    isEntry: visit.is_entry_point,
                    color: color
                }
            });

            // Add edge from parent if exists
            if (visit.parent_node_id) {
                let edgeColor = '#999';
                if (visit.link_type === 'temporal') edgeColor = '#00bcd4';
                else if (visit.link_type === 'semantic') edgeColor = '#ff69b4';
                else if (visit.link_type === 'entity') edgeColor = '#ffd700';

                edges.push({
                    data: {
                        id: `${visit.parent_node_id}-${visit.node_id}`,
                        source: visit.parent_node_id,
                        target: visit.node_id,
                        linkType: visit.link_type,
                        linkWeight: visit.link_weight,
                        color: edgeColor
                    }
                });
            }
        });

        // Add pruned nodes if requested
        if (showPruned && trace.pruned) {
            trace.pruned.forEach(pruned => {
                if (!visitedNodeIds.has(pruned.node_id)) {
                    nodes.push({
                        data: {
                            id: pruned.node_id,
                            label: 'Pruned',
                            text: `Pruned: ${pruned.reason}`,
                            activation: pruned.activation.toFixed(3),
                            color: '#ef5350' // red for pruned
                        }
                    });
                }
            });
        }

        // Destroy existing graph
        if (pane.cy) {
            pane.cy.destroy();
        }

        // Add legend/explanation to the graph view
        const existingLegend = cyDiv.querySelector('.search-graph-legend');
        if (existingLegend) {
            existingLegend.remove();
        }

        const legend = document.createElement('div');
        legend.className = 'search-graph-legend';
        legend.innerHTML = `
            <h4 style="margin: 0 0 10px 0; border-bottom: 2px solid #333; padding-bottom: 5px;">🔍 Graph Legend</h4>
            <div style="font-size: 12px; line-height: 1.6;">
                <p style="margin: 5px 0 8px 0; font-weight: bold;">Node Colors:</p>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background: #66bb6a; border: 2px solid #333; border-radius: 50%; margin-right: 8px;"></div>
                    <span>Entry points - semantically similar to query</span>
                </div>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background: #ffd54f; border: 2px solid #333; border-radius: 50%; margin-right: 8px;"></div>
                    <span>Results - returned as answers</span>
                </div>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background: #90caf9; border: 2px solid #333; border-radius: 50%; margin-right: 8px;"></div>
                    <span>Visited - explored but not in results</span>
                </div>

                <p style="margin: 12px 0 8px 0; font-weight: bold;">Link Types:</p>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 30px; height: 3px; background: #00bcd4; margin-right: 8px;"></div>
                    <span><strong>Temporal</strong> - memories close in time</span>
                </div>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 30px; height: 3px; background: #ff69b4; margin-right: 8px;"></div>
                    <span><strong>Semantic</strong> - similar content/meaning</span>
                </div>
                <div style="margin: 5px 0; display: flex; align-items: center;">
                    <div style="width: 30px; height: 3px; background: #ffd700; margin-right: 8px;"></div>
                    <span><strong>Entity</strong> - same person/place/thing</span>
                </div>

                <p style="margin: 12px 0 5px 0; font-size: 11px; color: #666; font-style: italic;">
                    Layout: Rows represent search depth from entry points
                </p>
            </div>
        `;
        cyDiv.appendChild(legend);

        // Create new graph
        pane.cy = cytoscape({
            container: cyDiv,
            elements: [...nodes, ...edges],
            style: [
                {
                    selector: 'node',
                    style: {
                        'background-color': 'data(color)',
                        'label': 'data(label)',
                        'text-valign': 'center',
                        'text-halign': 'center',
                        'font-size': '10px',
                        'font-weight': 'bold',
                        'text-wrap': 'wrap',
                        'text-max-width': '100px',
                        'width': 50,
                        'height': 50,
                        'border-width': 2,
                        'border-color': '#333'
                    }
                },
                {
                    selector: 'edge',
                    style: {
                        'width': 2,
                        'line-color': 'data(color)',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': 'data(color)',
                        'curve-style': 'bezier',
                        'opacity': 0.8
                    }
                },
                {
                    selector: 'node:selected',
                    style: {
                        'border-width': 4,
                        'border-color': '#000'
                    }
                }
            ],
            layout: {
                name: 'breadthfirst',
                directed: true,
                spacingFactor: 1.5,
                animate: false
            }
        });

        // Highlight path to top result if requested
        if (highlightPath && trace.visits.length > 0) {
            const topResult = trace.visits.find(v => v.final_rank === 1);
            if (topResult) {
                const pathNodes = [];
                let current = topResult;
                while (current) {
                    pathNodes.push(current.node_id);
                    current = trace.visits.find(v => v.node_id === current.parent_node_id);
                }

                pathNodes.forEach(nodeId => {
                    pane.cy.$(`#${nodeId}`).style({
                        'border-width': 5,
                        'border-color': '#ff5722'
                    });
                });
            }
        }

        // Add tooltips
        let tooltip = null;
        pane.cy.on('mouseover', 'node', function(evt) {
            const node = evt.target;
            const data = node.data();
            const pos = node.renderedPosition();

            tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.innerHTML = `
                <b>Text:</b> ${data.text}<br>
                ${data.step ? `<b>Step:</b> ${data.step}<br>` : ''}
                ${data.rank !== null && data.rank !== undefined ? `<b>Rank:</b> ${data.rank}<br>` : ''}
                ${data.activation ? `<b>Activation:</b> ${data.activation}<br>` : ''}
                ${data.similarity ? `<b>Similarity:</b> ${data.similarity}<br>` : ''}
                ${data.finalWeight ? `<b>Final Weight:</b> ${data.finalWeight}` : ''}
            `;

            // Get container bounds
            const container = cyDiv.getBoundingClientRect();

            // Position tooltip relative to container
            let left = pos.x + 20;
            let top = pos.y;

            // Append to body temporarily to get dimensions
            document.body.appendChild(tooltip);
            const tooltipRect = tooltip.getBoundingClientRect();

            // Adjust if tooltip would go off right edge
            if (container.left + left + tooltipRect.width > window.innerWidth) {
                left = pos.x - tooltipRect.width - 20;
            }

            // Adjust if tooltip would go off bottom edge
            if (container.top + top + tooltipRect.height > window.innerHeight) {
                top = pos.y - tooltipRect.height;
            }

            // Adjust if tooltip would go off left edge
            if (container.left + left < 0) {
                left = 20;
            }

            // Adjust if tooltip would go off top edge
            if (container.top + top < 0) {
                top = 20;
            }

            tooltip.style.left = (container.left + left) + 'px';
            tooltip.style.top = (container.top + top) + 'px';
        });

        pane.cy.on('mouseout', 'node', function() {
            if (tooltip) {
                tooltip.remove();
                tooltip = null;
            }
        });

    } catch (e) {
        console.error('Error visualizing trace:', e);
        // Show error in status bar
        const statusBar = document.getElementById(`debug-status-${paneId}`);
        if (statusBar) {
            statusBar.innerHTML = `<span style="color: #d32f2f;">❌ Error visualizing trace: ${e.message}</span>`;
        }
    }
}

function highlightMatchingNodes(paneId, searchText) {
    const pane = debugPanes.find(p => p.id === paneId);
    if (!pane || !pane.cy) return;

    const countSpan = document.getElementById(`graph-search-count-${paneId}`);

    // If search is empty, reset all styles
    if (!searchText || searchText.trim() === '') {
        pane.cy.nodes().style({
            'opacity': 1,
            'border-width': 2,
            'border-color': '#333'
        });
        pane.cy.edges().style({
            'opacity': 0.8
        });
        if (countSpan) countSpan.textContent = '';
        return;
    }

    const searchLower = searchText.toLowerCase();
    let matchCount = 0;
    const totalNodes = pane.cy.nodes().length;

    // Check each node for matches
    pane.cy.nodes().forEach(node => {
        const data = node.data();
        const text = (data.text || '').toLowerCase();
        const label = (data.label || '').toLowerCase();

        const matches = text.includes(searchLower) || label.includes(searchLower);

        if (matches) {
            matchCount++;
            // Highlight matching nodes - full opacity with thicker orange border
            node.style({
                'opacity': 1,
                'border-width': 4,
                'border-color': '#ff6f00'
            });
        } else {
            // Dim non-matching nodes
            node.style({
                'opacity': 0.2,
                'border-width': 2,
                'border-color': '#333'
            });
        }
    });

    // Dim all edges
    pane.cy.edges().style({
        'opacity': 0.2
    });

    // Update counter
    if (countSpan) {
        if (matchCount === 0) {
            countSpan.textContent = '(no matches)';
            countSpan.style.color = '#d32f2f';
        } else {
            countSpan.textContent = `(${matchCount} of ${totalNodes})`;
            countSpan.style.color = '#43a047';
        }
    }
}

// Load agents into global selector
async function loadGlobalAgents() {
    try {
        console.log('Loading global agents...'); // Debug
        const select = document.getElementById('global-agent-selector');

        if (!select) {
            console.error('global-agent-selector element not found!');
            return;
        }

        console.log('Fetching api/agents...'); // Debug
        const response = await fetch('api/agents');

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('Agents data received:', data); // Debug

        // Start with placeholder
        select.innerHTML = '<option value="">Select an agent...</option>';

        if (data.agents && data.agents.length > 0) {
            console.log(`Adding ${data.agents.length} agents to dropdown`); // Debug
            data.agents.forEach(agent => {
                const option = document.createElement('option');
                option.value = agent;
                option.textContent = agent;
                select.appendChild(option);
            });

            // Auto-select first agent
            select.value = data.agents[0];
            currentAgentId = data.agents[0];
            console.log('Auto-selected agent:', currentAgentId); // Debug

            // Update UI to show agent is selected
            updateUIForAgentSelection();
        } else {
            console.warn('No agents found in response');
        }
    } catch (e) {
        console.error('Error loading global agents:', e);
        alert('Failed to load agents: ' + e.message);
    }
}

// Handle global agent selection change
function onGlobalAgentChange() {
    const select = document.getElementById('global-agent-selector');
    currentAgentId = select.value || null;

    // Show/hide UI elements based on agent selection
    updateUIForAgentSelection();

    // Refresh all tabs if agent is selected
    if (currentAgentId) {
        refreshAllTabs();
    }
}

// Update UI visibility based on agent selection
function updateUIForAgentSelection() {
    const hasAgent = !!currentAgentId;

    // Update each data subtab
    ['world', 'agent', 'opinions'].forEach(factType => {
        const noAgentMsg = document.getElementById(`${factType}-no-agent-message`);
        const graphView = document.getElementById(`${factType}-graph-view`);
        const tableView = document.getElementById(`${factType}-table-view`);

        if (noAgentMsg) noAgentMsg.style.display = hasAgent ? 'none' : 'block';
        if (graphView) graphView.style.display = hasAgent ? 'none' : 'none'; // Start hidden, load on demand
        if (tableView) tableView.style.display = hasAgent ? 'none' : 'none'; // Start hidden, load on demand
    });
}

// Refresh all tabs with new agent context
async function refreshAllTabs() {
    // Clear existing data
    dataCache = {
        world: null,
        agent: null,
        opinions: null
    };

    // Destroy existing graphs
    ['world', 'agent', 'opinions'].forEach(factType => {
        if (dataGraphs[factType]) {
            dataGraphs[factType].destroy();
            dataGraphs[factType] = null;
        }
    });

    // Update active debug panes with new agent
    debugPanes.forEach(pane => {
        const agentSelect = document.getElementById(`search-agent-${pane.id}`);
        if (agentSelect && currentAgentId) {
            agentSelect.value = currentAgentId;
        }
    });
}

// Run Think query
window.runThink = async function() {
    console.log('runThink called'); // Debug log

    const query = document.getElementById('think-query').value;
    const agentSelect = document.getElementById('global-agent-selector');
    const agentId = agentSelect ? agentSelect.value : null;
    const thinkingBudget = parseInt(document.getElementById('think-budget').value);
    const topK = parseInt(document.getElementById('think-top-k').value);

    console.log('Query:', query, 'Agent:', agentId); // Debug log

    if (!query || query.trim() === '') {
        alert('Please enter a question');
        return;
    }

    if (!agentId) {
        alert('Please select an agent from the breadcrumb');
        return;
    }

    const resultDiv = document.getElementById('think-result');
    const loadingDiv = document.getElementById('think-loading');

    if (!resultDiv || !loadingDiv) {
        console.error('Think result divs not found');
        return;
    }

    try {
        // Show loading
        resultDiv.style.display = 'none';
        loadingDiv.style.display = 'block';

        console.log('Calling api/think with', { query, agentId, thinkingBudget, topK }); // Debug log

        const response = await fetch('api/think', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: query,
                agent_id: agentId,
                thinking_budget: thinkingBudget,
                top_k: topK
            })
        });

        console.log('Response status:', response.status); // Debug log

        const data = await response.json();
        console.log('Response data:', data); // Debug log

        if (data.detail) {
            alert('Error: ' + data.detail);
            loadingDiv.style.display = 'none';
            return;
        }

        // Display answer
        document.getElementById('think-answer-text').textContent = data.text;

        // Display world facts
        const worldFactsDiv = document.getElementById('think-world-facts');
        if (data.based_on.world && data.based_on.world.length > 0) {
            worldFactsDiv.innerHTML = data.based_on.world.map((fact, idx) => `
                <div style="margin-bottom: 10px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #1976d2;">
                    <div style="font-size: 13px; color: #333; margin-bottom: 5px;">${fact.text}</div>
                    <div style="font-size: 11px; color: #666;">
                        Score: ${fact.score ? fact.score.toFixed(4) : 'N/A'} |
                        ${fact.context ? 'Context: ' + fact.context : ''}
                    </div>
                </div>
            `).join('');
        } else {
            worldFactsDiv.innerHTML = '<div style="color: #666; font-style: italic;">No world facts used</div>';
        }

        // Display agent facts
        const agentFactsDiv = document.getElementById('think-agent-facts');
        if (data.based_on.agent && data.based_on.agent.length > 0) {
            agentFactsDiv.innerHTML = data.based_on.agent.map((fact, idx) => `
                <div style="margin-bottom: 10px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #f57c00;">
                    <div style="font-size: 13px; color: #333; margin-bottom: 5px;">${fact.text}</div>
                    <div style="font-size: 11px; color: #666;">
                        Score: ${fact.score ? fact.score.toFixed(4) : 'N/A'} |
                        ${fact.context ? 'Context: ' + fact.context : ''}
                    </div>
                </div>
            `).join('');
        } else {
            agentFactsDiv.innerHTML = '<div style="color: #666; font-style: italic;">No agent facts used</div>';
        }

        // Display opinions
        const opinionsDiv = document.getElementById('think-opinions');
        if (data.based_on.opinion && data.based_on.opinion.length > 0) {
            opinionsDiv.innerHTML = data.based_on.opinion.map((fact, idx) => `
                <div style="margin-bottom: 10px; padding: 10px; background: white; border-radius: 4px; border-left: 3px solid #7b1fa2;">
                    <div style="font-size: 13px; color: #333; margin-bottom: 5px;">${fact.text}</div>
                    <div style="font-size: 11px; color: #666;">
                        Score: ${fact.score ? fact.score.toFixed(4) : 'N/A'} |
                        Confidence: ${fact.confidence_score ? (fact.confidence_score * 100).toFixed(1) + '%' : 'N/A'} |
                        ${fact.context ? 'Context: ' + fact.context : ''}
                    </div>
                </div>
            `).join('');
        } else {
            opinionsDiv.innerHTML = '<div style="color: #666; font-style: italic;">No opinions used</div>';
        }

        // Display new opinions
        const newOpinionsDiv = document.getElementById('think-new-opinions');
        const newOpinionsListDiv = document.getElementById('think-new-opinions-list');
        if (data.new_opinions && data.new_opinions.length > 0) {
            newOpinionsListDiv.innerHTML = data.new_opinions.map((opinion, idx) => `
                <div style="margin-bottom: 15px; padding: 15px; background: white; border-radius: 6px; border-left: 4px solid #4caf50; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center;">
                            <span style="background: #4caf50; color: white; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; margin-right: 10px;">NEW</span>
                            <span style="color: #666; font-size: 12px;">#${idx + 1}</span>
                        </div>
                        <span style="background: #e3f2fd; color: #1976d2; padding: 3px 8px; border-radius: 10px; font-size: 11px; font-weight: 600;">
                            ${(opinion.confidence * 100).toFixed(0)}% confidence
                        </span>
                    </div>
                    <div style="font-size: 14px; color: #333; line-height: 1.5;">${opinion.text}</div>
                </div>
            `).join('');
            newOpinionsDiv.style.display = 'block';
        } else {
            newOpinionsDiv.style.display = 'none';
        }

        // Show result
        loadingDiv.style.display = 'none';
        resultDiv.style.display = 'block';

    } catch (e) {
        console.error('Error running Think:', e);
        alert('Error: ' + e.message);
        loadingDiv.style.display = 'none';
    }
};

// Initialize global agent selector on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - initializing...'); // Debug

    // Add change listener to global agent selector
    const agentSelector = document.getElementById('global-agent-selector');
    if (agentSelector) {
        console.log('Found global-agent-selector, adding change listener'); // Debug
        agentSelector.addEventListener('change', onGlobalAgentChange);
    } else {
        console.error('global-agent-selector not found in DOM!'); // Debug
    }

    // Add Enter key listener for Think query input
    const thinkQuery = document.getElementById('think-query');
    if (thinkQuery) {
        thinkQuery.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                runThink();
            }
        });
    }

    // Initialize UI visibility
    updateUIForAgentSelection();

    // Load agents
    loadGlobalAgents();
});

// Don't auto-load data on page load - wait for user to click load button

// Benchmark Visualizer App

let currentBenchmark = null;
let benchmarkData = null;

function selectBenchmark() {
    const select = document.getElementById('benchmark-select');
    currentBenchmark = select.value;

    if (!currentBenchmark) {
        document.getElementById('benchmark-content').innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to Benchmark Visualizer</h2>
                <p>Select a benchmark from the dropdown above to view results.</p>
            </div>
        `;
        return;
    }

    // Load the selected benchmark
    if (currentBenchmark === 'locomo-search') {
        loadLocomoResults('search');
    } else if (currentBenchmark === 'locomo-think') {
        loadLocomoResults('think');
    } else if (currentBenchmark === 'longmemeval') {
        loadLongMemEvalResults();
    }
}

async function loadLocomoResults(mode = 'search') {
    try {
        const response = await fetch(`/api/locomo?mode=${mode}`);

        if (!response.ok) {
            const errorData = await response.json();
            const modeLabel = mode === 'think' ? 'think' : 'search';
            const runCommand = mode === 'think'
                ? 'uv run python locomo_benchmark.py --use-think'
                : 'uv run python locomo_benchmark.py';

            document.getElementById('benchmark-content').innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Benchmark Results Not Found</h3>
                    <p>${errorData.detail || 'The requested benchmark results are not available.'}</p>
                    <p><strong>To generate ${modeLabel} mode results:</strong></p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">cd benchmarks/locomo
${runCommand}</pre>
                    <p style="margin-top: 15px; font-size: 14px; color: #666;">
                        Once the benchmark completes, refresh this page and select "${mode === 'think' ? 'LoComo (think)' : 'LoComo (search)'}" again.
                    </p>
                </div>
            `;
            return;
        }

        benchmarkData = await response.json();
        console.log(`Loaded locomo data (${mode} mode):`, benchmarkData);
        renderLocomoResults(mode);
    } catch (e) {
        console.error('Error loading benchmark results:', e);
        document.getElementById('benchmark-content').innerHTML = `
            <div class="error-message">
                <h3>❌ Error Loading Results</h3>
                <p>${e.message}</p>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">Check the browser console for more details.</p>
            </div>
        `;
    }
}

function renderLocomoResults(mode = 'search') {
    if (!benchmarkData) return;

    const content = document.getElementById('benchmark-content');

    try {
        // Handle both old and new structure
        const results = benchmarkData.item_results || benchmarkData.conversation_results || [];
        const numItems = benchmarkData.num_items || results.length;

        console.log('Rendering results:', { resultsCount: results.length, numItems });

        // Calculate per-category statistics
        const categoryStats = {
            1: { name: 'Multi-hop', correct: 0, total: 0 },
            2: { name: 'Single-hop', correct: 0, total: 0 },
            3: { name: 'Temporal', correct: 0, total: 0 },
            4: { name: 'Open-domain', correct: 0, total: 0 }
        };

        // Aggregate across all items
        let totalInvalid = 0;
        results.forEach(item => {
            if (item.metrics && item.metrics.detailed_results) {
                item.metrics.detailed_results.forEach(result => {
                    const category = result.category;
                    if (categoryStats[category]) {
                        categoryStats[category].total++;
                        if (result.is_invalid) {
                            if (!categoryStats[category].invalid) categoryStats[category].invalid = 0;
                            categoryStats[category].invalid++;
                            totalInvalid++;
                        } else if (result.is_correct) {
                            categoryStats[category].correct++;
                        }
                    }
                });
            }
        });

        // Determine title based on mode
        const modeLabel = mode === 'think' ? ' (Think Mode)' : ' (Search Mode)';

        // Overall stats
        const totalInvalidDisplay = totalInvalid > 0
            ? `<div class="stat-item">
                <div class="stat-label">Invalid Questions</div>
                <div class="stat-value" style="color: #ff9800;">${totalInvalid}</div>
            </div>`
            : '';

        const overallHtml = `
            <div style="background: #f9f9f9; padding: 20px; border: 2px solid #333; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0;">LoComo Benchmark${modeLabel} - Overall Performance</h3>
                ${totalInvalid > 0 ? `<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>⚠️ Note:</strong> ${totalInvalid} question(s) marked as invalid due to errors (excluded from accuracy calculation)
                </div>` : ''}
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Overall Accuracy</div>
                        <div class="stat-value">${benchmarkData.overall_accuracy.toFixed(2)}%</div>
                        ${totalInvalid > 0 ? `<div style="font-size: 11px; color: #666; margin-top: 4px;">(${benchmarkData.total_correct} / ${benchmarkData.total_valid || (benchmarkData.total_questions - totalInvalid)})</div>` : ''}
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Correct Answers</div>
                        <div class="stat-value">${benchmarkData.total_correct} / ${benchmarkData.total_questions}</div>
                    </div>
                    ${totalInvalidDisplay}
                    <div class="stat-item">
                        <div class="stat-label">Items</div>
                        <div class="stat-value">${numItems}</div>
                    </div>
                </div>

                <h4 style="margin: 20px 0 10px 0; padding-top: 15px; border-top: 1px solid #ddd;">Accuracy by Category</h4>
                <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));">
                    ${Object.values(categoryStats).map(cat => {
                        const invalidCount = cat.invalid || 0;
                        const validTotal = cat.total - invalidCount;
                        const accuracy = validTotal > 0 ? ((cat.correct / validTotal) * 100).toFixed(1) : 0;
                        const color = accuracy >= 70 ? '#43a047' : accuracy >= 50 ? '#ff9800' : '#e53935';
                        const invalidNote = invalidCount > 0 ? ` <span style="color: #ff9800; font-size: 10px;">(${invalidCount} invalid)</span>` : '';
                        return `
                            <div class="stat-item">
                                <div class="stat-label">${cat.name}</div>
                                <div class="stat-value" style="color: ${color};">${accuracy}%</div>
                                <div style="font-size: 11px; color: #666; margin-top: 4px;">${cat.correct} / ${cat.total}${invalidNote}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        // Filter controls
        const filterHtml = `
            <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
                <label style="font-weight: bold;">Show:</label>
                <label><input type="radio" name="answer-filter" value="all" checked onchange="filterAnswers()"> All Answers</label>
                <label><input type="radio" name="answer-filter" value="incorrect" onchange="filterAnswers()"> ❌ Incorrect Only</label>
                <label><input type="radio" name="answer-filter" value="correct" onchange="filterAnswers()"> ✅ Correct Only</label>
                ${totalInvalid > 0 ? '<label><input type="radio" name="answer-filter" value="invalid" onchange="filterAnswers()"> ⚠️ Invalid Only</label>' : ''}
            </div>
        `;

        // Build item sections
        let itemsHtml = '';
        results.forEach((item, idx) => {
            const itemId = item.item_id || item.sample_id || `item-${idx}`;
            const accuracy = item.metrics.accuracy.toFixed(2);
            const correctCount = item.metrics.correct;
            const totalCount = item.metrics.total;

            itemsHtml += `
                <div style="margin-bottom: 30px; border: 2px solid #333; border-radius: 8px; overflow: hidden;">
                    <div style="background: #f0f0f0; padding: 15px; border-bottom: 2px solid #333; cursor: pointer;" onclick="toggleConversation(${idx})">
                        <h3 style="margin: 0; display: flex; justify-content: space-between; align-items: center;">
                            <span>📊 ${itemId}</span>
                            <span style="font-size: 18px; color: ${accuracy >= 70 ? '#43a047' : accuracy >= 50 ? '#ff9800' : '#e53935'};">
                                ${accuracy}% (${correctCount}/${totalCount})
                            </span>
                        </h3>
                    </div>
                    <div id="conv-${idx}" style="display: none; padding: 20px;">
                        ${renderConversationDetails(item)}
                    </div>
                </div>
            `;
        });

        content.innerHTML = overallHtml + filterHtml + itemsHtml;
    } catch (e) {
        console.error('Error rendering Locomo results:', e);
        content.innerHTML = `
            <div class="error-message">
                <strong>Error rendering results:</strong> ${e.message}<br>
                <pre style="margin-top: 10px; font-size: 11px; overflow: auto;">${e.stack}</pre>
            </div>
        `;
    }
}

function renderConversationDetails(conv) {
    if (!conv || !conv.metrics) {
        return '<div style="padding: 20px; color: #666;">No metrics available</div>';
    }

    const results = conv.metrics.detailed_results;
    if (!results || !Array.isArray(results) || results.length === 0) {
        return '<div style="padding: 20px; color: #666;">No detailed results available</div>';
    }

    let html = '<div class="qa-results">';

    results.forEach((result, idx) => {
        const isInvalid = result.is_invalid || false;
        const isCorrect = result.is_correct;
        const bgColor = isInvalid ? '#fff3cd' : (isCorrect ? '#e8f5e9' : '#ffebee');
        const icon = isInvalid ? '⚠️' : (isCorrect ? '✅' : '❌');
        const category = getCategoryName(result.category);

        html += `
            <div class="qa-item" data-correct="${isCorrect}" data-invalid="${isInvalid}" style="background: ${bgColor}; padding: 15px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">
                            ${icon} Question ${idx + 1} ${isInvalid ? '<span style="font-size: 12px; background: #ff9800; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">INVALID</span>' : ''} <span style="font-size: 12px; background: #666; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">${category}</span>
                        </div>
                        <div style="margin-bottom: 8px;">
                            <b>Q:</b> ${result.question}
                        </div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
                    <div>
                        <div style="font-weight: bold; color: #43a047; margin-bottom: 4px;">✓ Correct Answer:</div>
                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                            ${result.correct_answer}
                        </div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: ${isCorrect ? '#43a047' : '#e53935'}; margin-bottom: 4px;">
                            ${isCorrect ? '✓' : '✗'} Predicted Answer:
                        </div>
                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                            ${result.predicted_answer}
                        </div>
                    </div>
                </div>

                <details style="margin-top: 10px;" ${isInvalid ? 'open' : ''}>
                    <summary style="cursor: pointer; font-weight: bold; padding: 5px; background: rgba(255,255,255,0.5); border-radius: 4px;">
                        📝 Show Reasoning & Retrieved Memories
                    </summary>
                    <div style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px;">
                        ${isInvalid ? `<div style="margin-bottom: 10px; padding: 10px; background: #ffebee; border-left: 4px solid #e53935; border-radius: 4px;">
                            <b style="color: #c62828;">⚠️ Error:</b>
                            <div style="margin-top: 4px; color: #333;">${result.error || 'Question marked as invalid'}</div>
                        </div>` : ''}
                        <div style="margin-bottom: 10px;">
                            <b>System Reasoning:</b>
                            <div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-top: 4px;">
                                ${result.reasoning}
                            </div>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <b>Judge Reasoning:</b>
                            <div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-top: 4px;">
                                ${result.correctness_reasoning || 'N/A'}
                            </div>
                        </div>
                        <div>
                            <b>Retrieved Memories (${result.retrieved_memories ? result.retrieved_memories.length : 0}):</b>
                            ${renderRetrievedMemories(result.retrieved_memories)}
                        </div>
                    </div>
                </details>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

function renderRetrievedMemories(memories) {
    if (!memories || !Array.isArray(memories) || memories.length === 0) {
        return '<div style="padding: 8px; color: #999;">No memories retrieved</div>';
    }

    let html = '<div style="margin-top: 8px;">';
    memories.forEach((mem, idx) => {
        if (!mem) return;
        const eventDate = mem.event_date ? new Date(mem.event_date).toLocaleString() : 'N/A';

        // Determine border color based on fact type
        let borderColor = '#42a5f5'; // default blue
        let factTypeLabel = '';
        if (mem.fact_type) {
            factTypeLabel = `<span style="background: #666; color: white; padding: 2px 6px; border-radius: 3px; font-size: 10px; margin-left: 8px;">${mem.fact_type.toUpperCase()}</span>`;
            if (mem.fact_type === 'world') {
                borderColor = '#4caf50'; // green
            } else if (mem.fact_type === 'agent') {
                borderColor = '#ff9800'; // orange
            } else if (mem.fact_type === 'opinion') {
                borderColor = '#9c27b0'; // purple
            }
        }

        html += `
            <div style="padding: 8px; background: #f5f5f5; border-left: 3px solid ${borderColor}; margin-bottom: 8px;">
                <div style="font-size: 11px; color: #666; margin-bottom: 4px;">
                    Rank #${idx + 1} | Score: ${mem.score ? mem.score.toFixed(4) : 'N/A'} | Event Date: ${eventDate}${factTypeLabel}
                </div>
                <div style="font-size: 13px;">${mem.text}</div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function getCategoryName(category) {
    const categories = {
        1: 'Multi-hop',
        2: 'Single-hop',
        3: 'Temporal',
        4: 'Open-domain'
    };
    return categories[category] || 'Unknown';
}

function toggleConversation(idx) {
    const elem = document.getElementById(`conv-${idx}`);
    if (elem.style.display === 'none') {
        elem.style.display = 'block';
    } else {
        elem.style.display = 'none';
    }
}

function filterAnswers() {
    const filter = document.querySelector('input[name="answer-filter"]:checked').value;
    const items = document.querySelectorAll('.qa-item');

    items.forEach(item => {
        const isCorrect = item.dataset.correct === 'true';
        const isInvalid = item.dataset.invalid === 'true';

        if (filter === 'all') {
            item.style.display = 'block';
        } else if (filter === 'correct' && isCorrect && !isInvalid) {
            item.style.display = 'block';
        } else if (filter === 'incorrect' && !isCorrect && !isInvalid) {
            item.style.display = 'block';
        } else if (filter === 'invalid' && isInvalid) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// LongMemEval functions
async function loadLongMemEvalResults() {
    try {
        const response = await fetch('/api/longmemeval');

        if (!response.ok) {
            const errorData = await response.json();
            document.getElementById('benchmark-content').innerHTML = `
                <div class="error-message">
                    <h3>⚠️ Benchmark Results Not Found</h3>
                    <p>${errorData.detail || 'The requested benchmark results are not available.'}</p>
                    <p><strong>To generate results:</strong></p>
                    <pre style="background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto;">cd benchmarks/longmemeval
uv run python longmemeval_benchmark.py</pre>
                    <p style="margin-top: 15px; font-size: 14px; color: #666;">
                        Once the benchmark completes, refresh this page and select "LongMemEval" again.
                    </p>
                </div>
            `;
            return;
        }

        benchmarkData = await response.json();
        console.log('Loaded longmemeval data:', benchmarkData);
        renderLongMemEvalResults();
    } catch (e) {
        console.error('Error loading longmemeval results:', e);
        document.getElementById('benchmark-content').innerHTML = `
            <div class="error-message">
                <h3>❌ Error Loading Results</h3>
                <p>${e.message}</p>
                <p style="font-size: 12px; color: #666; margin-top: 10px;">Check the browser console for more details.</p>
            </div>
        `;
    }
}

function renderLongMemEvalResults() {
    if (!benchmarkData) return;

    const content = document.getElementById('benchmark-content');

    try {
        const results = benchmarkData.item_results || [];
        const numItems = benchmarkData.num_items || results.length;

        console.log('Rendering longmemeval results:', { resultsCount: results.length, numItems });

        // Calculate per-category statistics
        const categoryStats = {};

        // Aggregate across all items
        let totalInvalid = 0;
        results.forEach(item => {
            if (item.metrics && item.metrics.category_stats) {
                Object.entries(item.metrics.category_stats).forEach(([category, stats]) => {
                    if (!categoryStats[category]) {
                        categoryStats[category] = { name: category, correct: 0, total: 0, invalid: 0 };
                    }
                    categoryStats[category].correct += stats.correct || 0;
                    categoryStats[category].total += stats.total || 0;
                    categoryStats[category].invalid += stats.invalid || 0;
                });
            }
            if (item.metrics && item.metrics.detailed_results) {
                item.metrics.detailed_results.forEach(result => {
                    if (result.is_invalid) {
                        totalInvalid++;
                    }
                });
            }
        });

        // Overall stats
        const totalInvalidDisplay = totalInvalid > 0
            ? `<div class="stat-item">
                <div class="stat-label">Invalid Questions</div>
                <div class="stat-value" style="color: #ff9800;">${totalInvalid}</div>
            </div>`
            : '';

        const overallHtml = `
            <div style="background: #f9f9f9; padding: 20px; border: 2px solid #333; border-radius: 8px; margin-bottom: 20px;">
                <h3 style="margin-top: 0;">LongMemEval Benchmark - Overall Performance</h3>
                ${totalInvalid > 0 ? `<div style="background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 4px; margin-bottom: 15px;">
                    <strong>⚠️ Note:</strong> ${totalInvalid} question(s) marked as invalid due to errors (excluded from accuracy calculation)
                </div>` : ''}
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-label">Overall Accuracy</div>
                        <div class="stat-value">${benchmarkData.overall_accuracy.toFixed(2)}%</div>
                        ${totalInvalid > 0 ? `<div style="font-size: 11px; color: #666; margin-top: 4px;">(${benchmarkData.total_correct} / ${benchmarkData.total_valid || (benchmarkData.total_questions - totalInvalid)})</div>` : ''}
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Correct Answers</div>
                        <div class="stat-value">${benchmarkData.total_correct} / ${benchmarkData.total_questions}</div>
                    </div>
                    ${totalInvalidDisplay}
                    <div class="stat-item">
                        <div class="stat-label">Items</div>
                        <div class="stat-value">${numItems}</div>
                    </div>
                </div>

                <h4 style="margin: 20px 0 10px 0; padding-top: 15px; border-top: 1px solid #ddd;">Accuracy by Category</h4>
                <div class="stats-grid" style="grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));">
                    ${Object.values(categoryStats).map(cat => {
                        const invalidCount = cat.invalid || 0;
                        const validTotal = cat.total - invalidCount;
                        const accuracy = validTotal > 0 ? ((cat.correct / validTotal) * 100).toFixed(1) : 0;
                        const color = accuracy >= 70 ? '#43a047' : accuracy >= 50 ? '#ff9800' : '#e53935';
                        const invalidNote = invalidCount > 0 ? ` <span style="color: #ff9800; font-size: 10px;">(${invalidCount} invalid)</span>` : '';
                        return `
                            <div class="stat-item">
                                <div class="stat-label">${cat.name}</div>
                                <div class="stat-value" style="color: ${color};">${accuracy}%</div>
                                <div style="font-size: 11px; color: #666; margin-top: 4px;">${cat.correct} / ${cat.total}${invalidNote}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;

        // Filter controls
        const filterHtml = `
            <div style="margin-bottom: 20px; display: flex; gap: 10px; align-items: center;">
                <label style="font-weight: bold;">Show:</label>
                <label><input type="radio" name="answer-filter" value="all" checked onchange="filterAnswers()"> All Answers</label>
                <label><input type="radio" name="answer-filter" value="incorrect" onchange="filterAnswers()"> ❌ Incorrect Only</label>
                <label><input type="radio" name="answer-filter" value="correct" onchange="filterAnswers()"> ✅ Correct Only</label>
                ${totalInvalid > 0 ? '<label><input type="radio" name="answer-filter" value="invalid" onchange="filterAnswers()"> ⚠️ Invalid Only</label>' : ''}
            </div>
        `;

        // Build item sections
        let itemsHtml = '';
        results.forEach((item, idx) => {
            const itemId = item.item_id || `item-${idx}`;
            const accuracy = item.metrics.accuracy.toFixed(2);
            const correctCount = item.metrics.correct;
            const totalCount = item.metrics.total;

            itemsHtml += `
                <div style="margin-bottom: 30px; border: 2px solid #333; border-radius: 8px; overflow: hidden;">
                    <div style="background: #f0f0f0; padding: 15px; border-bottom: 2px solid #333; cursor: pointer;" onclick="toggleConversation(${idx})">
                        <h3 style="margin: 0; display: flex; justify-content: space-between; align-items: center;">
                            <span>📊 ${itemId}</span>
                            <span style="font-size: 18px; color: ${accuracy >= 70 ? '#43a047' : accuracy >= 50 ? '#ff9800' : '#e53935'};">
                                ${accuracy}% (${correctCount}/${totalCount})
                            </span>
                        </h3>
                    </div>
                    <div id="conv-${idx}" style="display: none; padding: 20px;">
                        ${renderLongMemEvalItemDetails(item)}
                    </div>
                </div>
            `;
        });

        content.innerHTML = overallHtml + filterHtml + itemsHtml;
    } catch (e) {
        console.error('Error rendering LongMemEval results:', e);
        content.innerHTML = `
            <div class="error-message">
                <strong>Error rendering results:</strong> ${e.message}<br>
                <pre style="margin-top: 10px; font-size: 11px; overflow: auto;">${e.stack}</pre>
            </div>
        `;
    }
}

function renderLongMemEvalItemDetails(item) {
    if (!item || !item.metrics) {
        return '<div style="padding: 20px; color: #666;">No metrics available</div>';
    }

    const results = item.metrics.detailed_results;
    if (!results || !Array.isArray(results) || results.length === 0) {
        return '<div style="padding: 20px; color: #666;">No detailed results available</div>';
    }

    let html = '<div class="qa-results">';

    results.forEach((result, idx) => {
        const isInvalid = result.is_invalid || false;
        const isCorrect = result.is_correct;
        const bgColor = isInvalid ? '#fff3cd' : (isCorrect ? '#e8f5e9' : '#ffebee');
        const icon = isInvalid ? '⚠️' : (isCorrect ? '✅' : '❌');
        const category = result.category || 'Unknown';

        html += `
            <div class="qa-item" data-correct="${isCorrect}" data-invalid="${isInvalid}" style="background: ${bgColor}; padding: 15px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px;">
                    <div style="flex: 1;">
                        <div style="font-weight: bold; font-size: 16px; margin-bottom: 8px;">
                            ${icon} Question ${idx + 1} ${isInvalid ? '<span style="font-size: 12px; background: #ff9800; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">INVALID</span>' : ''} <span style="font-size: 12px; background: #666; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 8px;">${category}</span>
                        </div>
                        <div style="margin-bottom: 8px;">
                            <b>Q:</b> ${result.question}
                        </div>
                    </div>
                </div>

                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 10px;">
                    <div>
                        <div style="font-weight: bold; color: #43a047; margin-bottom: 4px;">✓ Correct Answer:</div>
                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                            ${result.correct_answer}
                        </div>
                    </div>
                    <div>
                        <div style="font-weight: bold; color: ${isCorrect ? '#43a047' : '#e53935'}; margin-bottom: 4px;">
                            ${isCorrect ? '✓' : '✗'} Predicted Answer:
                        </div>
                        <div style="background: white; padding: 8px; border-radius: 4px; border: 1px solid #ccc;">
                            ${result.predicted_answer}
                        </div>
                    </div>
                </div>

                <details style="margin-top: 10px;" ${isInvalid ? 'open' : ''}>
                    <summary style="cursor: pointer; font-weight: bold; padding: 5px; background: rgba(255,255,255,0.5); border-radius: 4px;">
                        📝 Show Reasoning & Retrieved Memories
                    </summary>
                    <div style="margin-top: 10px; padding: 10px; background: white; border-radius: 4px;">
                        ${isInvalid ? `<div style="margin-bottom: 10px; padding: 10px; background: #ffebee; border-left: 4px solid #e53935; border-radius: 4px;">
                            <b style="color: #c62828;">⚠️ Error:</b>
                            <div style="margin-top: 4px; color: #333;">${result.error || 'Question marked as invalid'}</div>
                        </div>` : ''}
                        <div style="margin-bottom: 10px;">
                            <b>System Reasoning:</b>
                            <div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-top: 4px;">
                                ${result.reasoning || 'N/A'}
                            </div>
                        </div>
                        <div style="margin-bottom: 10px;">
                            <b>Judge Reasoning:</b>
                            <div style="padding: 8px; background: #f5f5f5; border-radius: 4px; margin-top: 4px;">
                                ${result.correctness_reasoning || 'N/A'}
                            </div>
                        </div>
                        <div>
                            <b>Retrieved Memories (${result.retrieved_memories ? result.retrieved_memories.length : 0}):</b>
                            ${renderRetrievedMemories(result.retrieved_memories)}
                        </div>
                    </div>
                </details>
            </div>
        `;
    });

    html += '</div>';
    return html;
}

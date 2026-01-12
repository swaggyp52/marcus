/**
 * Marcus v0.46 - Mission Operations Panels
 *
 * Box-specific operation panels:
 * - Inbox Panel: Artifact picker with search/filter
 * - Ask Panel: Question input + citations display
 * - Practice Panel: Session creation + item list + answers
 * - Checker Panel: Answer verification + feedback
 * - Citations Panel: Report generation + display
 */

let currentMissionId = null;
let currentBoxData = {};
let currentPracticeSession = null;

// ============================================================================
// INBOX PANEL
// ============================================================================

async function renderInboxPanel(missionId, boxId, missionDetail) {
    currentMissionId = missionId;

    const panel = document.getElementById('inboxPanel');
    if (!panel) return;

    // Get linked artifacts
    const linkedArtifacts = missionDetail.artifacts.filter(a => a.type === 'document') || [];

    panel.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Linked Artifacts (${linkedArtifacts.length})</h4>
            ${linkedArtifacts.length > 0 ? linkedArtifacts.map(art => `
                <div style="background: #1a1a1a; border: 1px solid #2ecc71; padding: 10px; margin-bottom: 8px; border-radius: 6px;">
                    <div><strong>${art.title}</strong></div>
                    <div style="color: #888; font-size: 0.85em;">Type: ${art.type}</div>
                </div>
            `).join('') : '<p style="color: #888;">No artifacts linked yet</p>'}
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Add Artifacts</h4>
            <input type="text" id="artifactSearchInput" placeholder="Search by filename..."
                oninput="searchArtifacts()"
                style="width: 100%; padding: 8px; margin-bottom: 10px; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; border-radius: 4px;">

            ${missionDetail.mission.class_id ? `
                <div style="margin-bottom: 10px; color: #888; font-size: 0.9em;">
                    Filtering by class: ${missionDetail.mission.class_id}
                </div>
            ` : ''}

            <div id="availableArtifactsList" style="max-height: 300px; overflow-y: auto; margin-bottom: 10px;">
                <p style="color: #888;">Loading artifacts...</p>
            </div>

            <button class="btn" onclick="linkSelectedArtifacts()" id="linkArtifactsBtn" disabled>
                Link Selected Artifacts
            </button>
        </div>
    `;

    // Load available artifacts
    await loadAvailableArtifacts(missionDetail.mission.class_id, missionDetail.mission.assignment_id);
}

let availableArtifacts = [];
let selectedArtifactIds = new Set();

async function loadAvailableArtifacts(classId, assignmentId) {
    try {
        // Build query params
        const params = new URLSearchParams();
        if (classId) params.append('class_id', classId);
        if (assignmentId) params.append('assignment_id', assignmentId);

        const response = await fetch(`/api/artifacts?${params.toString()}`);
        if (!response.ok) throw new Error('Failed to load artifacts');

        availableArtifacts = await response.json();
        renderAvailableArtifacts();
    } catch (error) {
        console.error('[Inbox Panel] Error loading artifacts:', error);
        document.getElementById('availableArtifactsList').innerHTML =
            '<p style="color: #e74c3c;">Failed to load artifacts. Endpoint may not exist yet.</p>';
    }
}

function renderAvailableArtifacts(searchTerm = '') {
    const container = document.getElementById('availableArtifactsList');
    if (!container) return;

    const filtered = searchTerm
        ? availableArtifacts.filter(art =>
            art.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (art.original_filename && art.original_filename.toLowerCase().includes(searchTerm.toLowerCase()))
          )
        : availableArtifacts;

    if (filtered.length === 0) {
        container.innerHTML = '<p style="color: #888;">No artifacts found</p>';
        return;
    }

    container.innerHTML = filtered.map(art => `
        <div style="background: #1a1a1a; border: 1px solid #333; padding: 10px; margin-bottom: 8px; border-radius: 6px; display: flex; align-items: center;">
            <input type="checkbox"
                id="artifact_${art.id}"
                onchange="toggleArtifactSelection(${art.id})"
                ${selectedArtifactIds.has(art.id) ? 'checked' : ''}
                style="margin-right: 10px;">
            <label for="artifact_${art.id}" style="flex: 1; cursor: pointer;">
                <div><strong>${art.filename}</strong></div>
                <div style="color: #888; font-size: 0.85em;">
                    Type: ${art.file_type || 'unknown'} •
                    Size: ${(art.file_size / 1024).toFixed(1)} KB
                </div>
            </label>
        </div>
    `).join('');

    updateLinkButtonState();
}

function searchArtifacts() {
    const searchTerm = document.getElementById('artifactSearchInput')?.value || '';
    renderAvailableArtifacts(searchTerm);
}

function toggleArtifactSelection(artifactId) {
    if (selectedArtifactIds.has(artifactId)) {
        selectedArtifactIds.delete(artifactId);
    } else {
        selectedArtifactIds.add(artifactId);
    }
    updateLinkButtonState();
}

function updateLinkButtonState() {
    const btn = document.getElementById('linkArtifactsBtn');
    if (btn) {
        btn.disabled = selectedArtifactIds.size === 0;
    }
}

async function linkSelectedArtifacts() {
    if (selectedArtifactIds.size === 0) {
        showError('Please select at least one artifact');
        return;
    }

    try {
        const response = await fetch(`/api/missions/${currentMissionId}/inbox/link`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ artifact_ids: Array.from(selectedArtifactIds) })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to link artifacts');
        }

        showSuccess(`Linked ${selectedArtifactIds.size} artifact(s) successfully`);
        selectedArtifactIds.clear();

        // Refresh mission detail
        await openMissionDetail(currentMissionId);
    } catch (error) {
        console.error('[Inbox Panel] Error linking artifacts:', error);
        showError(error.message);
    }
}

// ============================================================================
// ASK PANEL
// ============================================================================

async function renderAskPanel(missionId, boxId, missionDetail) {
    currentMissionId = missionId;

    const panel = document.getElementById('askPanel');
    if (!panel) return;

    // Get previous QA artifacts
    const qaArtifacts = missionDetail.artifacts.filter(a => a.type === 'qa' || a.type === 'note') || [];

    panel.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Ask a Question</h4>
            <textarea id="askQuestionInput"
                placeholder="Enter your question about the course material..."
                style="width: 100%; min-height: 100px; padding: 10px; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; border-radius: 4px; resize: vertical; font-family: inherit;"></textarea>

            <div style="margin: 10px 0;">
                <label style="display: flex; align-items: center; cursor: pointer;">
                    <input type="checkbox" id="useSourcesCheckbox" checked style="margin-right: 8px;">
                    <span>Use mission sources (recommended)</span>
                </label>
            </div>

            <button class="btn" onclick="submitQuestion()">Ask Question</button>
        </div>

        <div id="askAnswerDisplay" style="margin-top: 20px;">
            ${qaArtifacts.length > 0 ? `
                <h4 style="color: #667eea; margin-bottom: 10px;">Previous Q&A (${qaArtifacts.length})</h4>
                ${qaArtifacts.slice(0, 5).map(qa => `
                    <div style="background: #1a1a1a; border: 1px solid #333; padding: 10px; margin-bottom: 8px; border-radius: 6px;">
                        <div><strong>${qa.title}</strong></div>
                        <div style="color: #888; font-size: 0.85em;">
                            ${new Date(qa.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('')}
            ` : '<p style="color: #888;">No questions asked yet</p>'}
        </div>
    `;
}

async function submitQuestion() {
    const question = document.getElementById('askQuestionInput')?.value.trim();
    const useSources = document.getElementById('useSourcesCheckbox')?.checked ?? true;

    if (!question) {
        showError('Please enter a question');
        return;
    }

    try {
        const response = await fetch(`/api/missions/${currentMissionId}/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                use_search: useSources
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to ask question');
        }

        const result = await response.json();
        displayAnswer(result, question);

        // Clear input
        document.getElementById('askQuestionInput').value = '';

        showSuccess('Question answered successfully');
    } catch (error) {
        console.error('[Ask Panel] Error asking question:', error);
        showError(error.message);
    }
}

function displayAnswer(result, question) {
    const display = document.getElementById('askAnswerDisplay');
    if (!display) return;

    // Extract answer from result
    const answer = result.output?.answer_md || result.answer_md || 'No answer provided';
    const citations = result.output?.citations || result.citations || [];
    const confidence = result.output?.confidence || 'unknown';
    const method = result.output?.method || 'unknown';

    display.innerHTML = `
        <div style="background: #1a1a1a; border: 1px solid #667eea; padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <div style="margin-bottom: 10px;">
                <strong style="color: #667eea;">Question:</strong>
                <p style="margin: 5px 0; color: #e0e0e0;">${question}</p>
            </div>

            <div style="margin-bottom: 10px;">
                <strong style="color: #667eea;">Answer:</strong>
                <div style="margin: 5px 0; color: #e0e0e0; line-height: 1.6;">
                    ${answer.split('\n').map(line => `<p>${line}</p>`).join('')}
                </div>
            </div>

            <div style="display: flex; gap: 10px; margin-bottom: 10px;">
                <span style="background: #2ecc71; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                    Confidence: ${confidence}
                </span>
                <span style="background: #3498db; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em;">
                    Method: ${method}
                </span>
            </div>

            ${citations.length > 0 ? `
                <div style="margin-top: 15px;">
                    <strong style="color: #667eea;">Citations:</strong>
                    <div style="margin-top: 5px;">
                        ${citations.map(cit => `
                            <div style="background: #252525; padding: 8px; margin: 5px 0; border-radius: 4px; font-size: 0.85em;">
                                <div style="color: #aaa;">${cit.source || cit.chunk_id || 'Unknown source'}</div>
                                ${cit.text ? `<div style="color: #888; margin-top: 3px; font-size: 0.9em;">"${cit.text.substring(0, 150)}..."</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                    <button class="btn btn-secondary" onclick="copyCitations(${JSON.stringify(citations).replace(/"/g, '&quot;')})" style="margin-top: 10px;">
                        Copy Citations
                    </button>
                </div>
            ` : ''}

            <button class="btn btn-secondary" onclick="pinAsNote('${question.replace(/'/g, "\\'")}', '${answer.replace(/'/g, "\\'")}')" style="margin-top: 10px;">
                Pin as Note
            </button>
        </div>
    `;
}

function copyCitations(citations) {
    const text = citations.map((cit, idx) =>
        `[${idx + 1}] ${cit.source || cit.chunk_id || 'Unknown'}: ${cit.text || ''}`
    ).join('\n\n');

    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Citations copied to clipboard');
    }).catch(err => {
        showError('Failed to copy citations');
    });
}

async function pinAsNote(question, answer) {
    try {
        const response = await fetch(`/api/missions/${currentMissionId}/artifacts/create-note`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: question.substring(0, 100),
                content: `Q: ${question}\n\nA: ${answer}`
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create note');
        }

        showSuccess('Pinned as note successfully');
        await openMissionDetail(currentMissionId);
    } catch (error) {
        console.error('[Ask Panel] Error pinning note:', error);
        showError(error.message);
    }
}

// ============================================================================
// PRACTICE PANEL
// ============================================================================

async function renderPracticePanel(missionId, boxId, missionDetail) {
    currentMissionId = missionId;

    const panel = document.getElementById('practicePanel');
    if (!panel) return;

    // Get practice sessions
    const sessions = missionDetail.practice_sessions || [];

    panel.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Create Practice Session</h4>
            <input type="number" id="questionCountInput"
                placeholder="Number of questions"
                value="10"
                min="1"
                max="50"
                style="width: 200px; padding: 8px; background: #1a1a1a; border: 1px solid #333; color: #e0e0e0; border-radius: 4px; margin-right: 10px;">
            <button class="btn" onclick="createPracticeSession()">Create Session</button>
        </div>

        <div id="practiceSessionsList">
            ${sessions.length > 0 ? `
                <h4 style="color: #667eea; margin-bottom: 10px;">Practice Sessions (${sessions.length})</h4>
                ${sessions.map(session => `
                    <div style="background: #1a1a1a; border: 1px solid #333; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div>
                                <strong>Session #${session.id}</strong>
                                <span style="margin-left: 10px; color: #888;">${session.item_count} questions</span>
                            </div>
                            <button class="btn btn-secondary" onclick="loadPracticeSession(${session.id})">
                                Open Session
                            </button>
                        </div>
                        <div style="color: #888; font-size: 0.85em;">
                            State: ${session.state} •
                            Created: ${new Date(session.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('')}
            ` : '<p style="color: #888;">No practice sessions yet</p>'}
        </div>

        <div id="practiceItemsContainer" style="margin-top: 20px;"></div>
    `;
}

async function createPracticeSession() {
    const questionCount = parseInt(document.getElementById('questionCountInput')?.value || '10');

    try {
        const response = await fetch(`/api/missions/${currentMissionId}/practice/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_count: questionCount,
                topic_keywords: null
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create practice session');
        }

        showSuccess('Practice session created successfully');
        await openMissionDetail(currentMissionId);
    } catch (error) {
        console.error('[Practice Panel] Error creating session:', error);
        showError(error.message);
    }
}

async function loadPracticeSession(sessionId) {
    currentPracticeSession = sessionId;

    try {
        const response = await fetch(`/api/practice/${sessionId}`);
        if (!response.ok) throw new Error('Failed to load practice session');

        const data = await response.json();
        renderPracticeItems(data);
    } catch (error) {
        console.error('[Practice Panel] Error loading session:', error);
        showError('Failed to load practice session');
    }
}

function renderPracticeItems(data) {
    const container = document.getElementById('practiceItemsContainer');
    if (!container) return;

    const session = data.session;
    const items = data.items;

    container.innerHTML = `
        <h4 style="color: #667eea; margin-bottom: 10px;">Session #${session.id} - Questions</h4>
        <div style="background: #1a1a1a; border: 1px solid #667eea; padding: 10px; border-radius: 6px; margin-bottom: 15px;">
            <strong>Score:</strong>
            Correct: ${session.score?.correct || 0} /
            Attempted: ${session.score?.attempted || 0} /
            Total: ${items.length}
        </div>

        ${items.map((item, idx) => renderPracticeItem(item, idx)).join('')}
    `;
}

function renderPracticeItem(item, index) {
    const isAnswered = item.state === 'answered' || item.state === 'checked';

    return `
        <div id="practiceItem_${item.id}" style="background: #1a1a1a; border: 1px solid #333; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
            <div style="margin-bottom: 10px;">
                <strong style="color: #667eea;">Question ${index + 1}:</strong>
            </div>
            <div style="margin-bottom: 15px; line-height: 1.6;">
                ${item.prompt_md}
            </div>

            <textarea id="answerInput_${item.id}"
                placeholder="Enter your answer..."
                ${isAnswered ? 'disabled' : ''}
                style="width: 100%; min-height: 80px; padding: 10px; background: #252525; border: 1px solid #333; color: #e0e0e0; border-radius: 4px; resize: vertical; font-family: inherit; margin-bottom: 10px;">
${item.user_answer || ''}</textarea>

            <div style="display: flex; gap: 10px;">
                <button class="btn btn-secondary" onclick="submitPracticeAnswer(${currentPracticeSession}, ${item.id})" ${isAnswered ? 'disabled' : ''}>
                    ${isAnswered ? 'Answer Submitted' : 'Submit Answer'}
                </button>

                ${item.state === 'answered' || item.state === 'checked' ? `
                    <button class="btn" onclick="checkPracticeAnswer(${currentPracticeSession}, ${item.id})">
                        ${item.state === 'checked' ? 'View Results' : 'Check Answer'}
                    </button>
                ` : ''}
            </div>

            <div id="checkResult_${item.id}" style="margin-top: 15px;"></div>
        </div>
    `;
}

async function submitPracticeAnswer(sessionId, itemId) {
    const userAnswer = document.getElementById(`answerInput_${itemId}`)?.value.trim();

    if (!userAnswer) {
        showError('Please enter an answer');
        return;
    }

    try {
        const response = await fetch(`/api/practice/${sessionId}/items/${itemId}/answer`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_answer: userAnswer })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to submit answer');
        }

        showSuccess('Answer submitted. Click "Check Answer" to verify.');
        await loadPracticeSession(sessionId);
    } catch (error) {
        console.error('[Practice Panel] Error submitting answer:', error);
        showError(error.message);
    }
}

async function checkPracticeAnswer(sessionId, itemId) {
    try {
        const response = await fetch(`/api/practice/${sessionId}/items/${itemId}/check`, {
            method: 'POST'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to check answer');
        }

        const result = await response.json();
        displayCheckResult(itemId, result);

        showSuccess('Answer checked successfully');
    } catch (error) {
        console.error('[Practice Panel] Error checking answer:', error);
        showError(error.message);
    }
}

function displayCheckResult(itemId, result) {
    const container = document.getElementById(`checkResult_${itemId}`);
    if (!container) return;

    const output = result.output || {};
    const isCorrect = output.is_correct || false;
    const explanation = output.explanation || 'No explanation provided';
    const citations = output.citations || [];
    const claims = output.claims || [];

    container.innerHTML = `
        <div style="background: ${isCorrect ? '#2ecc71' : '#e74c3c'}; padding: 15px; border-radius: 6px;">
            <div style="font-weight: 600; margin-bottom: 10px; color: white;">
                ${isCorrect ? '✓ Correct!' : '✗ Incorrect'}
            </div>

            <div style="color: white; margin-bottom: 10px;">
                <strong>Explanation:</strong>
                <p style="margin: 5px 0; line-height: 1.6;">${explanation}</p>
            </div>

            ${citations.length > 0 ? `
                <div style="margin-top: 10px; color: white;">
                    <strong>Sources:</strong>
                    ${citations.map(cit => `
                        <div style="background: rgba(0,0,0,0.2); padding: 5px; margin: 3px 0; border-radius: 3px; font-size: 0.85em;">
                            ${cit.source || cit.chunk_id || 'Unknown'}
                        </div>
                    `).join('')}
                </div>
            ` : ''}

            ${claims.length > 0 ? `
                <div style="margin-top: 10px; color: white;">
                    <strong>Claims created:</strong> ${claims.join(', ')}
                </div>
            ` : ''}

            <div style="margin-top: 15px; display: flex; gap: 10px;">
                <button class="btn btn-secondary" onclick="markClaimVerified(${itemId}, true)" style="background: #2ecc71;">
                    ✓ Mark Verified
                </button>
                <button class="btn btn-secondary" onclick="markClaimVerified(${itemId}, false)" style="background: #e74c3c;">
                    ✗ Disagree
                </button>
            </div>
        </div>
    `;
}

async function markClaimVerified(itemId, verified) {
    // This would call a claim verification endpoint if it exists
    // For now, just show feedback
    showSuccess(verified ? 'Marked as verified' : 'Marked as disputed');
}

// ============================================================================
// CITATIONS PANEL
// ============================================================================

async function renderCitationsPanel(missionId, boxId, missionDetail) {
    currentMissionId = missionId;

    const panel = document.getElementById('citationsPanel');
    if (!panel) return;

    // Get citations artifacts
    const citationsArtifacts = missionDetail.artifacts.filter(a => a.type === 'citations_report') || [];

    panel.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Generate Citation Snapshot</h4>
            <p style="color: #888; margin-bottom: 10px;">
                Creates a comprehensive report of all sources used in this mission.
            </p>
            <button class="btn" onclick="generateCitationSnapshot()">Generate Snapshot</button>
        </div>

        <div id="citationsReportDisplay">
            ${citationsArtifacts.length > 0 ? `
                <h4 style="color: #667eea; margin-bottom: 10px;">Previous Reports (${citationsArtifacts.length})</h4>
                ${citationsArtifacts.map(report => `
                    <div style="background: #1a1a1a; border: 1px solid #333; padding: 10px; margin-bottom: 8px; border-radius: 6px;">
                        <div><strong>${report.title}</strong></div>
                        <div style="color: #888; font-size: 0.85em;">
                            ${new Date(report.created_at).toLocaleString()}
                        </div>
                    </div>
                `).join('')}
            ` : '<p style="color: #888;">No citation reports generated yet</p>'}
        </div>
    `;
}

async function generateCitationSnapshot() {
    try {
        // Find citations box
        const response = await fetch(`/api/missions/${currentMissionId}`);
        if (!response.ok) throw new Error('Failed to load mission');

        const detail = await response.json();
        const citationsBox = detail.boxes.find(b => b.type === 'citations');

        if (!citationsBox) {
            throw new Error('Citations box not found');
        }

        // Run citations box
        const runResponse = await fetch(`/api/missions/${currentMissionId}/boxes/${citationsBox.id}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_payload: {} })
        });

        if (!runResponse.ok) {
            const error = await runResponse.json();
            throw new Error(error.detail || 'Failed to generate citations');
        }

        const result = await runResponse.json();
        displayCitationsReport(result);

        showSuccess('Citations report generated successfully');
    } catch (error) {
        console.error('[Citations Panel] Error generating report:', error);
        showError(error.message);
    }
}

function displayCitationsReport(result) {
    const display = document.getElementById('citationsReportDisplay');
    if (!display) return;

    const output = result.output || {};
    const topSources = output.top_sources || [];
    const chunkStats = output.chunk_usage || {};
    const totalCitations = output.total_citations || 0;

    const reportText = `
MARCUS CITATION REPORT
Generated: ${new Date().toLocaleString()}
Total Citations: ${totalCitations}

TOP SOURCES:
${topSources.map((src, idx) => `${idx + 1}. ${src.source} (${src.count} citations)`).join('\n')}

CHUNK USAGE STATISTICS:
${Object.entries(chunkStats).map(([key, value]) => `${key}: ${value}`).join('\n')}
    `.trim();

    display.innerHTML = `
        <div style="background: #1a1a1a; border: 1px solid #667eea; padding: 15px; border-radius: 6px; margin-top: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Latest Citation Report</h4>

            ${topSources.length > 0 ? `
                <div style="margin-bottom: 15px;">
                    <strong>Top Sources:</strong>
                    <div style="margin-top: 5px;">
                        ${topSources.slice(0, 10).map((src, idx) => `
                            <div style="background: #252525; padding: 8px; margin: 5px 0; border-radius: 4px;">
                                <span style="color: #667eea; font-weight: 600;">${idx + 1}.</span>
                                <span style="color: #e0e0e0;">${src.source}</span>
                                <span style="color: #888; margin-left: 10px;">${src.count} citations</span>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}

            <div style="margin-top: 15px;">
                <strong>Total Citations:</strong> ${totalCitations}
            </div>

            <button class="btn btn-secondary" onclick="copyReport(\`${reportText.replace(/`/g, '\\`')}\`)" style="margin-top: 15px;">
                Copy Report
            </button>
        </div>
    `;
}

function copyReport(text) {
    navigator.clipboard.writeText(text).then(() => {
        showSuccess('Report copied to clipboard');
    }).catch(err => {
        showError('Failed to copy report');
    });
}

// ============================================================================
// PANEL SWITCHING
// ============================================================================

function switchBoxPanel(boxType) {
    // Hide all panels
    const panels = ['inboxPanel', 'extractPanel', 'askPanel', 'practicePanel', 'checkerPanel', 'citationsPanel', 'artifactsPanel'];
    panels.forEach(panelId => {
        const panel = document.getElementById(panelId);
        if (panel) panel.style.display = 'none';
    });

    // Show selected panel
    const selectedPanel = document.getElementById(`${boxType}Panel`);
    if (selectedPanel) {
        selectedPanel.style.display = 'block';
    }

    // Update tab buttons
    document.querySelectorAll('.box-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const activeTab = document.querySelector(`.box-tab[data-box="${boxType}"]`);
    if (activeTab) {
        activeTab.classList.add('active');
    }
}

// Export for global access
if (typeof window !== 'undefined') {
    window.missionOperationsAPI = {
        renderInboxPanel,
        renderAskPanel,
        renderPracticePanel,
        renderCitationsPanel,
        switchBoxPanel,
        linkSelectedArtifacts,
        submitQuestion,
        createPracticeSession,
        loadPracticeSession,
        submitPracticeAnswer,
        checkPracticeAnswer,
        generateCitationSnapshot
    };
}

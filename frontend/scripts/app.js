const API_BASE = '';

const AGENT_CATEGORIES = {
    'image_gen': 'Creative',
    'presentation_gen': 'Creative',
    'video_gen': 'Creative',
    'email_gen': 'Creative',
    'quiz_gen': 'Education',
    'roadmap_gen': 'Education',
    'student_gen': 'Education',
    'nacle': 'Research',
    'scholar': 'Research',
    'quanta': 'Research',
    'nexus': 'Development',
    'security_recon': 'Security',
    'resume_opt': 'Career',
    'debate_coach': 'Career',
    'travel_plan': 'Lifestyle'
};

const AGENT_LABELS = {
    'image_gen': { label: 'Description', placeholder: 'Describe the scene, style, and lighting...' },
    'presentation_gen': { label: 'Topic & Context', placeholder: 'e.g., Q4 Business Review for Executives...' },
    'quiz_gen': { label: 'Subject Matter', placeholder: 'e.g., Advanced Python Programming...' },
    'roadmap_gen': { label: 'Career Goal', placeholder: 'e.g., Becoming a Senior DevOps Engineer...' },
    'student_gen': { label: 'Student Context', placeholder: 'e.g., High school student struggling with calculus...' },
    'nacle': { label: 'Concept to Map', placeholder: 'e.g., Neural Networks architecture...' },
    'scholar': { label: 'Research Question', placeholder: 'e.g., Impact of climate change on urban planning...' },
    'quanta': { label: 'Research Topic', placeholder: 'e.g., Quantum error correction codes...' },
    'nexus': { label: 'Code or System', placeholder: 'Paste code snippet or describe system requirements...' },
    'security_recon': { label: 'Target Domain', placeholder: 'e.g., example.com (Authorized testing only)...' },
    'resume_opt': { label: 'Resume Text', placeholder: 'Paste your resume content here...' },
    'debate_coach': { label: 'Debate Topic', placeholder: 'e.g., Universal Basic Income...' },
    'travel_plan': { label: 'Destination', placeholder: 'e.g., Tokyo, Japan...' }
};

const AGENT_ICONS = {
    'image_gen': 'ph-paint-brush',
    'presentation_gen': 'ph-presentation-chart',
    'video_gen': 'ph-film-strip',
    'email_gen': 'ph-envelope',
    'quiz_gen': 'ph-exam',
    'roadmap_gen': 'ph-map-trifold',
    'student_gen': 'ph-student',
    'nacle': 'ph-graph',
    'scholar': 'ph-graduation-cap',
    'quanta': 'ph-atom',
    'nexus': 'ph-code',
    'security_recon': 'ph-shield-warning',
    'resume_opt': 'ph-file-text',
    'debate_coach': 'ph-scales',
    'travel_plan': 'ph-airplane-tilt'
};

const state = {
    agents: [],
    currentAgent: null,
    progressInterval: null
};

// DOM Elements
const elements = {
    grid: document.getElementById('agents-grid'),
    count: document.getElementById('agent-count'),
    modalOverlay: document.getElementById('modal-overlay'),
    modalClose: document.getElementById('modal-close'),
    modalTitle: document.getElementById('modal-title'),
    modalDesc: document.getElementById('modal-description'),
    modalIcon: document.getElementById('modal-icon'),
    modalCategory: document.getElementById('modal-category'),
    form: document.getElementById('agent-form'),
    inputLabel: document.getElementById('input-label'),
    input: document.getElementById('topic-input'),
    options: document.getElementById('options-container'),
    submitBtn: document.getElementById('submit-btn'),
    resultArea: document.getElementById('modal-result'),
    resultDisplay: document.getElementById('result-display'),
    downloadBtn: document.getElementById('download-btn'),
    progressContainer: document.getElementById('progress-container'),
    progressBar: document.getElementById('progress-bar'),
    progressStatus: document.getElementById('progress-status'),
    progressDetail: document.getElementById('progress-detail'),
    navLinks: document.querySelectorAll('.nav-link')
};

// --- SPA Routing ---
function handleRouting() {
    const hash = window.location.hash || '#home';
    const pageId = hash.substring(1);

    // Hide all views
    document.querySelectorAll('.view-section').forEach(el => {
        el.classList.remove('active');
    });

    // Show active view
    const activeView = document.getElementById(`view-${pageId}`);
    if (activeView) {
        activeView.classList.add('active');
    } else {
        // Fallback to home
        document.getElementById('view-home').classList.add('active');
    }

    // Update Nav
    elements.navLinks.forEach(link => {
        if (link.getAttribute('href') === hash) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });

    // Scroll to top
    window.scrollTo(0, 0);

    // Load agents if on agents page
    if (pageId === 'agents' && state.agents.length === 0) {
        fetchAgents();
    }
}

window.addEventListener('hashchange', handleRouting);
window.addEventListener('load', handleRouting);

// --- Agent Logic ---
async function fetchAgents() {
    try {
        const res = await fetch(`${API_BASE}/api/agents`);
        const data = await res.json();
        state.agents = data.agents;
        renderGrid();
        if (elements.count) elements.count.textContent = `${state.agents.length} Active Agents`;
    } catch (e) {
        console.error(e);
        elements.grid.innerHTML = `<div class="loading-state" style="border-color: #ef4444; color: #ef4444;">
            <i class="ph ph-warning-circle"></i> Connection Failed. check backend.
        </div>`;
    }
}

function renderGrid() {
    elements.grid.innerHTML = state.agents.map((agent, index) => {
        const cat = AGENT_CATEGORIES[agent.id] || 'General';
        const icon = AGENT_ICONS[agent.id] || 'ph-robot';

        return `
        <div class="agent-card" data-id="${agent.id}" data-category="${cat}" onclick="openAgent('${agent.id}')" style="animation-delay: ${index * 50}ms">
            <div class="agent-header">
                <div class="agent-title">
                    <h3>${formatName(agent.name)}</h3>
                    <div class="tags-wrapper">
                        <span class="tag">${cat}</span>
                    </div>
                </div>
                <div class="agent-icon">
                    <i class="ph ${icon}"></i>
                </div>
            </div>
            <p class="agent-desc">${agent.description}</p>
            <div class="agent-action">
                <span>Configure Agent</span>
                <i class="ph ph-sliders"></i>
            </div>
        </div>
        `;
    }).join('');
}

function openAgent(id) {
    const agent = state.agents.find(a => a.id === id);
    if (!agent) return;

    state.currentAgent = agent;
    const cat = AGENT_CATEGORIES[id] || 'General';
    const labels = AGENT_LABELS[id] || { label: 'Input', placeholder: 'Enter details...' };
    const icon = AGENT_ICONS[id] || 'ph-robot';

    // Update Modal Content
    elements.modalTitle.textContent = formatName(agent.name);
    elements.modalDesc.textContent = agent.description;
    // Updated to use innerHTML for icon wrapper
    const iconWrapper = document.getElementById('modal-icon');
    if (iconWrapper) {
        iconWrapper.innerHTML = `<i class="ph ${icon}"></i>`;
        // Apply category styling dynamically to modal icon if needed, but CSS handles it via parent context usually.
        // For simplicity, just reset classes
        iconWrapper.className = `agent-icon`;
        // We could add category class to modal content to theme it
        const content = document.getElementById('agent-modal');
        if (content) {
            content.setAttribute('data-category', cat);
        }
    }

    if (elements.modalCategory) elements.modalCategory.textContent = cat;

    // Update Form
    if (elements.inputLabel) elements.inputLabel.textContent = labels.label;
    if (elements.input) {
        elements.input.placeholder = labels.placeholder;
        elements.input.value = '';
    }

    renderOptions(id);

    // Reset State
    elements.resultArea.style.display = 'none';
    elements.resultArea.classList.remove('active');
    elements.progressContainer.style.display = 'none';
    elements.progressContainer.classList.remove('active');

    elements.submitBtn.disabled = false;
    elements.submitBtn.innerHTML = `<span>Execute Agent</span><i class="ph ph-lightning-fill"></i>`;

    // Show Modal
    elements.modalOverlay.classList.add('active');
}

function renderOptions(id) {
    const AGENT_OPTIONS = {
        'presentation_gen': [
            { name: 'num_slides', label: 'Slides', type: 'number', default: 5 }
        ],
        'quiz_gen': [
            { name: 'difficulty', label: 'Difficulty', type: 'select', options: ['easy', 'medium', 'hard'], default: 'medium' }
        ],
        'student_gen': [
            { name: 'command', label: 'Task', type: 'select', options: ['notes', 'roadmap', 'quiz', 'dsa', 'debug', 'interview'], default: 'notes' }
        ],
        'nexus': [
            { name: 'module', label: 'Module', type: 'select', options: ['codex', 'sherlock', 'aria', 'atlas'], default: 'codex' },
            { name: 'command', label: 'Action', type: 'select', options: ['review', 'debug', 'research', 'design'], default: 'review' }
        ],
        'quanta': [
            { name: 'module', label: 'Domain', type: 'select', options: ['quantum', 'medica'], default: 'quantum' },
            { name: 'command', label: 'Analysis', type: 'select', options: ['algorithm', 'hardware', 'interactions'], default: 'algorithm' }
        ],
        'resume_opt': [
            { name: 'job_description', label: 'Job Description (Optional)', type: 'text', default: '' }
        ],
        'debate_coach': [
            { name: 'user_argument', label: 'Your Argument', type: 'text', default: '' }
        ],
        'travel_plan': [
            { name: 'duration', label: 'Duration', type: 'text', default: '3 days' },
            { name: 'budget', label: 'Budget', type: 'select', options: ['Low', 'Medium', 'High', 'Luxury'], default: 'Medium' },
            { name: 'interests', label: 'Interests', type: 'text', default: 'Sightseeing, Food, History' }
        ]
    };

    const options = AGENT_OPTIONS[id] || [];

    elements.options.innerHTML = options.map(opt => {
        if (opt.type === 'select') {
            return `
            <div class="input-group">
                <label class="input-label">${opt.label}</label>
                <select name="${opt.name}" class="input-field">
                    ${opt.options.map(o => `<option value="${o}" ${o === opt.default ? 'selected' : ''}>${formatName(o)}</option>`).join('')}
                </select>
            </div>`;
        } else {
            return `
            <div class="input-group">
                <label class="input-label">${opt.label}</label>
                <input type="${opt.type}" name="${opt.name}" value="${opt.default}" class="input-field" min="1" max="50">
            </div>`;
        }
    }).join('');
}

function closeAgent() {
    elements.modalOverlay.classList.remove('active');
    setTimeout(() => {
        state.currentAgent = null;
    }, 300);
}

// Form Handling
if (elements.submitBtn) {
    elements.submitBtn.onclick = async (e) => {
        e.preventDefault();
        if (!state.currentAgent) return;

        const topic = elements.input.value.trim();
        if (!topic) return elements.input.focus();

        // Gather options
        const options = {};
        elements.options.querySelectorAll('input, select').forEach(el => {
            options[el.name] = el.type === 'number' ? parseInt(el.value) : el.value;
        });

        // Start UI Logic
        elements.submitBtn.disabled = true;
        elements.submitBtn.innerHTML = `<i class="ph ph-spinner ph-spin"></i> Processing...`;

        startProgress(state.currentAgent.id);

        try {
            const res = await fetch(`${API_BASE}/api/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent: state.currentAgent.id,
                    topic,
                    options
                })
            });

            const data = await res.json();

            if (data.success) {
                renderResult(state.currentAgent.id, data.result);
            } else {
                console.error(data);
                showError(data.detail || 'Execution failed');
            }

        } catch (err) {
            console.error(err);
            showError(err.message);
        } finally {
            elements.submitBtn.disabled = false;
            elements.submitBtn.innerHTML = `<span>Execute Agent</span><i class="ph ph-lightning-fill"></i>`;
            stopProgress();
        }
    };
}

// Helpers
function formatName(str) {
    if (!str) return '';
    return str.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

function startProgress(id) {
    elements.progressContainer.style.display = 'block';
    elements.progressContainer.classList.add('active');
    elements.resultArea.style.display = 'none';
    elements.resultArea.classList.remove('active');

    if (elements.progressStatus) elements.progressStatus.textContent = "Initializing Agents...";
    if (elements.progressBar) elements.progressBar.style.width = "0%";

    let width = 0;
    const interval = setInterval(() => {
        if (width >= 90) clearInterval(interval);
        width += Math.random() * 10;
        if (elements.progressBar) elements.progressBar.style.width = Math.min(width, 90) + "%";
        if (elements.progressDetail) {
            const steps = ['Analyzing intent...', 'Loading external tools...', 'Generating solution...', 'Formatting output...'];
            elements.progressDetail.textContent = steps[Math.floor((width / 100) * steps.length)] || 'Processing...';
        }
    }, 800);

    state.progressInterval = interval;
}

function stopProgress() {
    clearInterval(state.progressInterval);
    if (elements.progressBar) elements.progressBar.style.width = "100%";
    if (elements.progressDetail) elements.progressDetail.textContent = 'Complete';
    setTimeout(() => {
        // Don't hide immediately, let the user see 100%
        // elements.progressContainer.classList.remove('active');
    }, 500);
}

function renderResult(id, result) {
    let displayHtml = '';

    if (result.pdf) {
        displayHtml += `<div class="result-summary" style="background: rgba(16, 185, 129, 0.1); padding: 1rem; border-radius: 8px; border: 1px solid rgba(16, 185, 129, 0.2); margin-bottom: 1rem;">
            <div style="display: flex; gap: 0.5rem; align-items: center;">
                <i class="ph ph-file-pdf" style="color: #10b981; font-size: 1.5rem;"></i>
                <div>
                    <strong style="color: #10b981;">Report Generated Successfully</strong>
                    <p style="font-size: 0.85rem; margin: 0; opacity: 0.8;">Your document is ready for download.</p>
                </div>
            </div>
        </div>`;
    }

    displayHtml += `<div class="result-content" style="background: rgba(0,0,0,0.3); padding: 1rem; border-radius: 8px; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; overflow: auto; max-height: 400px; color: #e2e8f0;">
        <pre>${JSON.stringify(result, null, 2)}</pre>
    </div>`;

    if (elements.resultDisplay) elements.resultDisplay.innerHTML = displayHtml;

    // Handle Download
    const file = findOutputFile(result);
    if (file && elements.downloadBtn) {
        const name = file.split(/[/\\]/).pop();
        elements.downloadBtn.href = `/files/${name}`;
        elements.downloadBtn.download = name;
        elements.downloadBtn.style.display = 'inline-flex';
    } else if (elements.downloadBtn) {
        elements.downloadBtn.style.display = 'none';
    }

    if (elements.resultArea) {
        elements.resultArea.style.display = 'block';
        elements.resultArea.classList.add('active');
    }
}

function findOutputFile(obj) {
    if (!obj || typeof obj !== 'object') return null;
    if (obj.pdf) return obj.pdf;
    if (obj.output_file) return obj.output_file;
    if (obj.image_path) return obj.image_path;

    for (const key in obj) {
        const found = findOutputFile(obj[key]);
        if (found) return found;
    }
    return null;
}

function showError(msg) {
    if (elements.resultDisplay) {
        elements.resultDisplay.innerHTML = `<div style="color: #ef4444; padding: 1rem; background: rgba(239, 68, 68, 0.1); border-radius: 8px; border: 1px solid rgba(239, 68, 68, 0.2); display: flex; align-items: center; gap: 0.5rem;">
            <i class="ph ph-warning"></i>
            <div><strong>Execution Error</strong><br>${msg}</div>
        </div>`;
    }
    if (elements.resultArea) {
        elements.resultArea.style.display = 'block';
        elements.resultArea.classList.add('active');
    }
}

// Event Listeners
if (elements.modalClose) elements.modalClose.onclick = closeAgent;
if (elements.modalOverlay) elements.modalOverlay.onclick = (e) => { if (e.target === elements.modalOverlay) closeAgent(); };
document.onkeydown = (e) => { if (e.key === 'Escape') closeAgent(); };

// State init (triggered by load/hashchange listener)
// init() is removed in favor of handleRouting()

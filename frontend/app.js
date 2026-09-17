const API_BASE = 'https://ngi7d95uh8.execute-api.eu-north-1.amazonaws.com';
let currentRepoId = null;
let currentRepoUrl = null;
let indexingInterval = null;

const ingestBtn = document.getElementById('ingest-btn');
const urlInput = document.getElementById('repo-url-input');
const statusBox = document.getElementById('status-display');
const statusText = document.getElementById('status-text');
const statusIndicator = document.querySelector('.status-indicator');
const repoBadge = document.getElementById('current-repo-badge');

const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const sendBtn = document.getElementById('send-btn');
const chatHistory = document.getElementById('chat-history');

// Configure marked to render markdown safely
marked.setOptions({
    breaks: true,
    gfm: true
});

function appendMessage(role, content) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${role}-message`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (role === 'agent') {
        contentDiv.innerHTML = marked.parse(content);
    } else {
        contentDiv.textContent = content;
    }
    
    msgDiv.appendChild(contentDiv);
    chatHistory.appendChild(msgDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Handle Ingestion
ingestBtn.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    if (!url) return;
    
    ingestBtn.disabled = true;
    urlInput.disabled = true;
    statusBox.classList.remove('hidden');
    statusIndicator.className = 'status-indicator pulsing';
    statusText.textContent = 'Starting pipeline...';
    
    try {
        const res = await fetch(`${API_BASE}/ingest`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_url: url })
        });
        
        const data = await res.json();
        if (res.ok) {
            currentRepoId = data.repo_id;
            currentRepoUrl = url;
            pollStatus(currentRepoId);
        } else {
            throw new Error(data.detail || data.error || 'Failed to start index');
        }
    } catch (e) {
        statusIndicator.className = 'status-indicator error';
        statusText.textContent = `Error: ${e.message}`;
        ingestBtn.disabled = false;
        urlInput.disabled = false;
    }
});

function pollStatus(repoId) {
    if (indexingInterval) clearInterval(indexingInterval);
    
    indexingInterval = setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/status?repo=${repoId}`);
            const data = await res.json();
            
            if (data.status === 'completed') {
                clearInterval(indexingInterval);
                statusIndicator.className = 'status-indicator success';
                statusText.textContent = `Indexed successfully!`;
                
                repoBadge.textContent = repoId;
                chatInput.disabled = false;
                sendBtn.disabled = false;
                
                appendMessage('system', 'Repository successfully indexed. You can now chat with the agent.');
                
                ingestBtn.disabled = false;
                urlInput.disabled = false;
            } else if (data.status === 'failed') {
                clearInterval(indexingInterval);
                statusIndicator.className = 'status-indicator error';
                statusText.textContent = `Failed: ${data.error}`;
                ingestBtn.disabled = false;
                urlInput.disabled = false;
            } else {
                statusText.textContent = `Status: ${data.status}...`;
            }
        } catch (e) {
            console.error(e);
        }
    }, 2000);
}

// Handle Chat
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!currentRepoId) return;
    
    const query = chatInput.value.trim();
    if (!query) return;
    
    // Add user message
    appendMessage('user', query);
    chatInput.value = '';
    
    // Add temporary loading message
    const loadingId = 'loading-' + Date.now();
    const loadingHtml = `<div id="${loadingId}" class="message agent-message"><div class="message-content"><em>Agent is searching and thinking...</em></div></div>`;
    chatHistory.insertAdjacentHTML('beforeend', loadingHtml);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    
    chatInput.disabled = true;
    sendBtn.disabled = true;
    
    try {
        const res = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                repo_url: currentRepoUrl,
                message: query,
                history: []
            })
        });
        
        const data = await res.json();
        
        if (document.getElementById(loadingId)) {
            document.getElementById(loadingId).remove();
        }
        
        if (!res.ok) {
            appendMessage('system', `Error: ${data.error || data.detail || 'Failed to get answer'}`);
            throw new Error("Chat request failed");
        }
        
        if (data.response) {
            appendMessage('agent', data.response);
        } else {
            appendMessage('system', `Agent Error: Unexpected response format.`);
        }
        
    } catch (e) {
        if(document.getElementById(loadingId)) {
            document.getElementById(loadingId).remove();
        }
        appendMessage('system', `Connection Error: ${e.message}`);
    } finally {
        chatInput.disabled = false;
        sendBtn.disabled = false;
        chatInput.focus();
    }
});

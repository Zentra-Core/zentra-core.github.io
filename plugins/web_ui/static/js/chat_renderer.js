// chat_renderer.js
// Handles DOM manipulation, Markdown parsing, and UI Bubble logic

window.currentAudio = null;

function addBubble(role, text, id) {
  const isUser = role === 'user';
  const msg = document.createElement('div');
  msg.className = `msg ${isUser?'user':'ai'}`;
  if(id) msg.id = id;
  const avatar = document.createElement('div');
  avatar.className = 'msg-avatar';
  if (isUser) {
    avatar.textContent = '👤';
  } else {
    avatar.innerHTML = `<img src="/assets/Zentra_Core_Logo_NBG.png" style="width:24px; height:24px; filter:drop-shadow(0 0 5px rgba(108,140,255,0.4));">`;
  }
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  if(text) bubble.innerHTML = renderMarkdown(text);
  msg.appendChild(avatar);
  msg.appendChild(bubble);
  
  const chatArea = document.getElementById('chat-area');
  if (chatArea) {
      chatArea.appendChild(msg);
      chatArea.scrollTop = chatArea.scrollHeight;
  }
  
  const hIdx = (window.historyList) ? window.historyList.length : -1;
  if (typeof window.attachMessageActions === 'function') {
    window.attachMessageActions(msg, isUser ? 'user' : 'ai', hIdx);
  }
  return { msg, bubble };
}

function renderMarkdown(text) {
  let html = text
    .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>');
    
  if (typeof window.processAiImages === 'function') {
    html = window.processAiImages(html);
  }
  return html;
}

async function tryLoadAudio(bubble) {
  const url = '/api/audio?t=' + Date.now();
  console.log("[Audio] Creating element for URL:", url);
  
  const badge = document.createElement('div');
  badge.className='audio-badge';
  badge.innerHTML = '🔊 ';
  
  const audio = document.createElement('audio');
  audio.controls = true;
  audio.src = url;
  window.currentAudio = audio;
  badge.appendChild(audio);
  bubble.appendChild(badge);
  showStopVoiceBtn(true);
  
  audio.oncanplaythrough = () => {
    console.log("[Audio] Can play through, starting...");
    audio.play().catch(err => {
      console.warn("[Audio] Autoplay blocked:", err);
      const hint = document.createElement('span');
      hint.style.fontSize = '10px';
      hint.style.color = 'var(--accent)';
      hint.textContent = ' (Clicca Play)';
      badge.appendChild(hint);
    });
  };

  audio.onended  = () => { window.currentAudio = null; showStopVoiceBtn(false); };
  audio.onerror = () => {
    console.error("[Audio] Element error code:", audio.error ? audio.error.code : 'unknown');
    window.currentAudio = null; showStopVoiceBtn(false);
  };
}

function showStopVoiceBtn(visible) {
  const btn1 = document.getElementById('sidebar-stop-voice-btn');
  const btn2 = document.getElementById('topbar-stop-voice-btn');
  const display = visible ? 'inline-flex' : 'none';
  if (btn1) btn1.style.display = display;
  if (btn2) btn2.style.display = display;
}

// Global Exports
window.addBubble = addBubble;
window.renderMarkdown = renderMarkdown;
window.tryLoadAudio = tryLoadAudio;
window.showStopVoiceBtn = showStopVoiceBtn;

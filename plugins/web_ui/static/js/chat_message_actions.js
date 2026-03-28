/**
 * MODULE: chat_message_actions.js
 * PURPOSE: Logic for inline message actions (copy, edit, regenerate, delete)
 * Loaded by chat.html. Depends on: addBubble(), sendMessage(), history[], chatArea
 */

// ── Toast Notification ───────────────────────────────────────────
function showToast(msg, duration = 2000) {
  const el = document.getElementById('chat-toast');
  if (!el) return;
  el.textContent = msg;
  el.classList.add('show');
  setTimeout(() => el.classList.remove('show'), duration);
}

// ── Build the action bar DOM for a message bubble ────────────────
function buildMessageActions(msgEl, role, historyIndex) {
  const bar = document.createElement('div');
  bar.className = 'msg-actions';

  // Copy button (all messages)
  const copyBtn = document.createElement('button');
  copyBtn.className = 'msg-action-btn';
  copyBtn.innerHTML = '📋 Copia';
  copyBtn.title = 'Copia il testo';
  copyBtn.onclick = () => {
    const bubble = msgEl.querySelector('.msg-bubble');
    navigator.clipboard.writeText(bubble.innerText || bubble.textContent)
      .then(() => showToast('✅ Copiato!'))
      .catch(() => showToast('❌ Copia fallita'));
  };
  bar.appendChild(copyBtn);

  // Edit button (all messages)
  const editBtn = document.createElement('button');
  editBtn.className = 'msg-action-btn';
  editBtn.innerHTML = '✏️ Modifica';
  editBtn.title = 'Modifica il messaggio';
  editBtn.onclick = () => toggleEditMode(msgEl, historyIndex);
  bar.appendChild(editBtn);

  // Regenerate (AI messages only)
  if (role === 'ai') {
    const regenBtn = document.createElement('button');
    regenBtn.className = 'msg-action-btn';
    regenBtn.innerHTML = '🔁 Rigenera';
    regenBtn.title = 'Genera una nuova risposta';
    regenBtn.onclick = () => regenerateLastResponse(historyIndex);
    bar.appendChild(regenBtn);
  }

  // Delete button (all messages)
  const delBtn = document.createElement('button');
  delBtn.className = 'msg-action-btn danger';
  delBtn.innerHTML = '🗑';
  delBtn.title = 'Elimina messaggio';
  delBtn.onclick = () => deleteMessage(msgEl, historyIndex);
  bar.appendChild(delBtn);

  return bar;
}

// Build the edit mode textarea area for a bubble
function buildEditArea(msgEl, historyIndex) {
  const wrap = document.createElement('div');
  wrap.className = 'msg-edit-wrap';

  const bubble = msgEl.querySelector('.msg-bubble');
  const textarea = document.createElement('textarea');
  textarea.className = 'msg-edit-textarea';
  textarea.value = bubble.innerText || bubble.textContent;
  textarea.rows = 3;
  wrap.appendChild(textarea);

  const controls = document.createElement('div');
  controls.className = 'msg-edit-controls';

  const cancelBtn = document.createElement('button');
  cancelBtn.className = 'msg-edit-cancel';
  cancelBtn.textContent = 'Annulla';
  cancelBtn.onclick = () => wrap.classList.remove('active');

  const confirmBtn = document.createElement('button');
  confirmBtn.className = 'msg-edit-confirm';
  confirmBtn.textContent = '✓ Salva';
  confirmBtn.onclick = () => {
    const newText = textarea.value.trim();
    if (!newText) return;
    bubble.innerHTML = window.renderMarkdown ? renderMarkdown(newText) : newText;
    // Update history if index is valid
    if (typeof historyIndex === 'number' && history && history[historyIndex]) {
      history[historyIndex].content = newText;
    }
    wrap.classList.remove('active');
    showToast('✅ Messaggio modificato');
  };

  controls.appendChild(cancelBtn);
  controls.appendChild(confirmBtn);
  wrap.appendChild(controls);

  return wrap;
}

// Toggle edit mode on a message
function toggleEditMode(msgEl, historyIndex) {
  let wrap = msgEl.querySelector('.msg-edit-wrap');
  if (!wrap) {
    wrap = buildEditArea(msgEl, historyIndex);
    msgEl.querySelector('.msg-bubble').parentNode.appendChild(wrap);
  }
  wrap.classList.toggle('active');
  if (wrap.classList.contains('active')) {
    wrap.querySelector('textarea').focus();
  }
}

// Delete a message from the chat (visual + history)
function deleteMessage(msgEl, historyIndex) {
  msgEl.style.opacity = '0';
  msgEl.style.transform = 'translateY(-8px)';
  msgEl.style.transition = 'all .25s';
  setTimeout(() => {
    msgEl.remove();
    if (typeof historyIndex === 'number' && history && history[historyIndex]) {
      history.splice(historyIndex, 1);
    }
    showToast('🗑 Messaggio eliminato');
  }, 250);
}

// Regenerate the last AI response (remove it and re-send the previous user message)
async function regenerateLastResponse(historyIndex) {
  if (!history || history.length < 2) {
    showToast('⚠️ Nessun messaggio precedente da rigenerare');
    return;
  }
  // Remove visual AI message
  const aiMsgEl = document.querySelector(`[data-history="${historyIndex}"]`);
  if (aiMsgEl) aiMsgEl.remove();
  // Remove AI from history
  history.splice(historyIndex, 1);
  // Re-send
  showToast('🔁 Rigenerazione in corso...');
  if (typeof window.sendMessage === 'function') {
    await window.sendMessage(null, true); // pass regen flag
  }
}

// ── Attach action bars to all rendered messages ─────────────────
// Called after each bubble is added. Exposed globally.
window.attachMessageActions = function(msgEl, role, historyIndex) {
  const actionBar = buildMessageActions(msgEl, role, historyIndex);
  // Append after the bubble
  const bubble = msgEl.querySelector('.msg-bubble');
  if (bubble && bubble.parentNode) {
    bubble.parentNode.insertBefore(actionBar, bubble.nextSibling);
  }
};

// atlas-chat.js -- Atlas M9b native chat panel
// All DOM writes use createElement/textContent/appendChild.
// Artifact content goes into srcdoc of a sandboxed iframe only.

var atlasChat = (function() {
  var SESSION_STORAGE_KEY = 'agentsHQ_session_id';
  var SHARED_SESSION_KEY = 'browser:7792432594';
  var _sessionKey = null;
  var _messages = [];
  var _pollTimer = null;

  function _getSessionKey() {
    if (_sessionKey) return _sessionKey;
    // Always use the shared session key so /atlas and /chat share history.
    localStorage.setItem(SESSION_STORAGE_KEY, SHARED_SESSION_KEY);
    _sessionKey = SHARED_SESSION_KEY;
    return _sessionKey;
  }

  // Build a DocumentFragment from model output using only DOM APIs.
  // User text never enters this function -- user bubbles use textContent directly.
  function _mdFragment(text) {
    var frag = document.createDocumentFragment();
    if (!text) return frag;
    var codeFenceRe = /(```[\s\S]*?```)/g;
    var parts = text.split(codeFenceRe);
    parts.forEach(function(part) {
      if (part.indexOf('```') === 0) {
        var inner = part.replace(/^```[^\n]*\n?/, '').replace(/```$/, '');
        var pre = document.createElement('pre');
        var codeEl = document.createElement('code');
        codeEl.textContent = inner;
        pre.appendChild(codeEl);
        frag.appendChild(pre);
        return;
      }
      part.split(/\n\n+/).forEach(function(block) {
        block = block.trim();
        if (!block) return;
        var lines = block.split('\n');
        // Unordered list
        var hasDash = lines.some(function(l) { return l.indexOf('- ') === 0; });
        var allDash = lines.every(function(l) { return !l.trim() || l.indexOf('- ') === 0; });
        if (hasDash && allDash) {
          var ul = document.createElement('ul');
          lines.forEach(function(l) {
            if (!l.trim()) return;
            var li = document.createElement('li');
            li.textContent = l.slice(2);
            ul.appendChild(li);
          });
          frag.appendChild(ul);
          return;
        }
        // Numbered list
        var numRe = /^\d+\. /;
        var hasNum = lines.some(function(l) { return numRe.test(l); });
        var allNum = lines.every(function(l) { return !l.trim() || numRe.test(l); });
        if (hasNum && allNum) {
          var ol = document.createElement('ol');
          lines.forEach(function(l) {
            if (!l.trim()) return;
            var li = document.createElement('li');
            li.textContent = l.replace(numRe, '');
            ol.appendChild(li);
          });
          frag.appendChild(ol);
          return;
        }
        // Header
        var hm = block.match(/^(#{1,3}) (.+)/);
        if (hm) {
          var hdr = document.createElement('h' + Math.min(hm[1].length, 3));
          hdr.textContent = hm[2];
          frag.appendChild(hdr);
          return;
        }
        // Paragraph with inline formatting
        var p = document.createElement('p');
        _appendInline(p, block);
        frag.appendChild(p);
      });
    });
    return frag;
  }

  function _appendInline(parent, text) {
    var re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
    var last = 0;
    var m;
    while ((m = re.exec(text)) !== null) {
      if (m.index > last) {
        parent.appendChild(document.createTextNode(text.slice(last, m.index).replace(/\n/g, ' ')));
      }
      var t = m[0];
      var n;
      if (t.indexOf('**') === 0) { n = document.createElement('strong'); n.textContent = t.slice(2,-2); }
      else if (t.indexOf('*') === 0) { n = document.createElement('em'); n.textContent = t.slice(1,-1); }
      else { n = document.createElement('code'); n.textContent = t.slice(1,-1); }
      parent.appendChild(n);
      last = m.index + t.length;
    }
    if (last < text.length) {
      parent.appendChild(document.createTextNode(text.slice(last).replace(/\n/g, ' ')));
    }
  }

  function _appendMessage(role, text, actions, artifact) {
    var panel = document.getElementById('chat-messages');
    if (!panel) return;
    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble chat-bubble-' + (role === 'user' ? 'user' : 'assistant');
    var body = document.createElement('div');
    body.className = 'chat-bubble-body';
    if (role === 'user') { body.textContent = text; }
    else { body.appendChild(_mdFragment(text)); }
    bubble.appendChild(body);
    if (actions && actions.length) {
      var row = document.createElement('div');
      row.className = 'chat-action-row';
      actions.forEach(function(a) {
        var btn = document.createElement('button');
        btn.className = 'btn btn-chat-action';
        btn.textContent = a.label || '';
        btn.addEventListener('click', function() { _handleAction(a, btn, row); });
        row.appendChild(btn);
      });
      bubble.appendChild(row);
    }
    panel.appendChild(bubble);
    panel.scrollTop = panel.scrollHeight;
    if (artifact && artifact.content) { _renderArtifact(artifact); }
  }

  function _renderArtifact(artifact) {
    var wrap = document.getElementById('chat-artifact-wrap');
    var frame = document.getElementById('chat-artifact-frame');
    if (!wrap || !frame) return;
    var c = artifact.content || '';
    frame.srcdoc = (artifact.type === 'html')
      ? c
      : '<!DOCTYPE html><html><body style="margin:8px;font-family:sans-serif">' + c + '</body></html>';
    wrap.style.display = 'block';
  }

  function _typing(show) {
    if (show) {
      var panel = document.getElementById('chat-messages');
      if (!panel) return;
      var b = document.createElement('div');
      b.className = 'chat-bubble chat-bubble-assistant chat-typing';
      b.id = 'chat-typing-indicator';
      b.textContent = 'Atlas is thinking...';
      panel.appendChild(b);
      panel.scrollTop = panel.scrollHeight;
    } else {
      var ind = document.getElementById('chat-typing-indicator');
      if (ind) ind.remove();
    }
  }

  function _pollJob(jobId) {
    if (_pollTimer) clearInterval(_pollTimer);
    _pollTimer = setInterval(function() {
      apiFetch('/atlas/job/' + jobId)
        .then(function(d) {
          if (d.status === 'completed' || d.status === 'failed') {
            clearInterval(_pollTimer); _pollTimer = null;
            _appendMessage('assistant',
              d.status === 'completed' ? (d.result || 'Done.') : ('Failed: ' + (d.error || 'unknown')),
              [], null);
          }
        }).catch(function() {});
    }, 3000);
  }

  function _handleAction(action, btn, row) {
    var cb = action.callback_data || '';
    btn.disabled = true;
    if (cb.indexOf('confirm:') === 0) {
      apiFetch('/atlas/confirm/' + cb.slice('confirm:'.length), { method: 'POST', body: '{}' })
        .then(function(d) {
          row.replaceChildren();
          if (d.job_id) { _appendMessage('assistant', 'Running. Will update you when done.', [], null); _pollJob(d.job_id); }
          else { _appendMessage('assistant', d.message || 'Done.', [], null); }
        }).catch(function(e) { btn.disabled = false; _appendMessage('assistant', 'Failed: ' + e.message, [], null); });
    } else if (cb.indexOf('cancel:') === 0) {
      apiFetch('/atlas/confirm/' + cb.slice('cancel:'.length) + '/cancel', { method: 'POST', body: '{}' }).catch(function(){});
      row.replaceChildren();
      _appendMessage('assistant', 'Cancelled.', [], null);
    } else { btn.disabled = false; }
  }

  function sendMessage(text) {
    if (!text || !text.trim()) return;
    text = text.trim();
    var sendBtn = document.getElementById('chat-send');
    var inputEl = document.getElementById('chat-input');
    if (sendBtn) sendBtn.disabled = true;
    if (inputEl) inputEl.disabled = true;
    _messages.push({ role: 'user', content: text });
    _appendMessage('user', text, [], null);
    _typing(true);
    apiFetch('/atlas/chat', {
      method: 'POST',
      body: JSON.stringify({ messages: _messages, session_key: _getSessionKey() }),
    }).then(function(r) {
      _typing(false);
      _messages.push({ role: 'assistant', content: r.reply || '' });
      _appendMessage('assistant', r.reply || '', r.actions || [], r.artifact || null);
      if (r.job_id) { _pollJob(r.job_id); }
      try { refreshQueue(); } catch (_) {}
    }).catch(function(e) {
      _typing(false);
      _appendMessage('assistant', 'Error: ' + e.message, [], null);
      _messages.pop();
    }).finally(function() {
      if (sendBtn) sendBtn.disabled = false;
      if (inputEl) { inputEl.disabled = false; inputEl.focus(); }
    });
  }

  function init() {
    var sendBtn = document.getElementById('chat-send');
    var inputEl = document.getElementById('chat-input');
    if (!sendBtn || !inputEl) return;
    sendBtn.addEventListener('click', function() { var t = inputEl.value; inputEl.value = ''; sendMessage(t); });
    inputEl.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        var t = inputEl.value; inputEl.value = '';
        sendMessage(t);
      }
    });
    _appendMessage('assistant', 'Atlas ready. Ask me anything about your content pipeline, agents, or spend.', [], null);
  }

  return { init: init, sendMessage: sendMessage };
})();

var _origShowDashboard = showDashboard;
showDashboard = function() { _origShowDashboard(); atlasChat.init(); };

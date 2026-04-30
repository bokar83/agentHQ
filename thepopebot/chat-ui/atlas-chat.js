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

  // Attachment state — per-message, cleared after each send.
  // Each entry: { name, size, mime, kind: 'image'|'pdf'|'text'|'unsupported',
  //               dataUrl?, text?, errorMsg? }
  var _attachments = [];
  var MAX_FILES = 4;
  var MAX_FILE_BYTES = 10 * 1024 * 1024;  // 10 MB
  var TEXT_LIKE_MIMES = /^(text\/|application\/(json|xml|x-yaml|toml))/i;
  var TEXT_LIKE_EXT = /\.(txt|md|markdown|csv|tsv|json|log|py|js|ts|tsx|jsx|html|css|yml|yaml|toml|sh|sql|env|conf|ini|xml)$/i;

  function _classifyFile(file) {
    var mime = (file.type || '').toLowerCase();
    var name = file.name || '';
    if (mime.indexOf('image/') === 0) return 'image';
    if (mime === 'application/pdf') return 'pdf';
    if (TEXT_LIKE_MIMES.test(mime) || TEXT_LIKE_EXT.test(name)) return 'text';
    return 'unsupported';
  }

  function _formatBytes(n) {
    if (n < 1024) return n + ' B';
    if (n < 1024 * 1024) return Math.round(n / 1024) + ' KB';
    return (n / (1024 * 1024)).toFixed(1) + ' MB';
  }

  function _readFileAsDataURL(file) {
    return new Promise(function(resolve, reject) {
      var r = new FileReader();
      r.onload = function() { resolve(r.result); };
      r.onerror = function() { reject(r.error || new Error('read failed')); };
      r.readAsDataURL(file);
    });
  }

  function _readFileAsText(file) {
    return new Promise(function(resolve, reject) {
      var r = new FileReader();
      r.onload = function() { resolve(r.result); };
      r.onerror = function() { reject(r.error || new Error('read failed')); };
      r.readAsText(file);
    });
  }

  function _renderChips() {
    var strip = document.getElementById('chat-attachment-strip');
    if (!strip) return;
    while (strip.firstChild) strip.removeChild(strip.firstChild);
    _attachments.forEach(function(att, idx) {
      var chip = document.createElement('span');
      chip.className = 'chat-chip' + (att.errorMsg ? ' chat-chip-error' : '');
      if (att.kind === 'image' && att.dataUrl) {
        var img = document.createElement('img');
        img.className = 'chat-chip-thumb';
        img.src = att.dataUrl;
        img.alt = '';
        chip.appendChild(img);
      }
      var name = document.createElement('span');
      name.className = 'chat-chip-name';
      name.textContent = att.name;
      chip.appendChild(name);
      var size = document.createElement('span');
      size.className = 'chat-chip-size';
      size.textContent = att.errorMsg ? att.errorMsg : _formatBytes(att.size);
      chip.appendChild(size);
      var rm = document.createElement('button');
      rm.type = 'button';
      rm.className = 'chat-chip-remove';
      rm.setAttribute('aria-label', 'Remove ' + att.name);
      rm.textContent = '×';
      rm.addEventListener('click', function() {
        _attachments.splice(idx, 1);
        _renderChips();
      });
      chip.appendChild(rm);
      strip.appendChild(chip);
    });
  }

  function _addFiles(fileList) {
    if (!fileList || !fileList.length) return;
    var files = Array.prototype.slice.call(fileList);
    var pending = [];
    files.forEach(function(file) {
      if (_attachments.length + pending.length >= MAX_FILES) {
        pending.push({
          name: file.name || 'file', size: file.size, mime: file.type, kind: 'unsupported',
          errorMsg: 'max ' + MAX_FILES + ' attachments',
        });
        return;
      }
      var kind = _classifyFile(file);
      if (file.size > MAX_FILE_BYTES) {
        pending.push({
          name: file.name || 'file', size: file.size, mime: file.type, kind: kind,
          errorMsg: 'too large (' + _formatBytes(file.size) + ' > 10MB)',
        });
        return;
      }
      if (kind === 'unsupported') {
        pending.push({
          name: file.name || 'file', size: file.size, mime: file.type, kind: kind,
          errorMsg: 'unsupported type',
        });
        return;
      }
      pending.push({ name: file.name || 'file', size: file.size, mime: file.type, kind: kind, _file: file });
    });
    _attachments = _attachments.concat(pending);
    _renderChips();
    pending.forEach(function(att) {
      if (!att._file) return;
      var promise = (att.kind === 'text') ? _readFileAsText(att._file) : _readFileAsDataURL(att._file);
      promise.then(function(value) {
        if (att.kind === 'text') att.text = value;
        else att.dataUrl = value;
        delete att._file;
        _renderChips();
      }).catch(function(e) {
        att.errorMsg = 'read failed';
        _renderChips();
      });
    });
  }

  function _buildContent(text) {
    // Returns either a plain string (no attachments) or an OpenRouter
    // structured-content array (text + image_url + file blocks, plus inlined
    // text for text-like files).
    var valid = _attachments.filter(function(a) { return !a.errorMsg && (a.dataUrl || a.text); });
    if (!valid.length) return text;
    var blocks = [];
    var textBody = text;
    valid.forEach(function(a) {
      if (a.kind === 'text' && a.text) {
        var snippet = a.text.length > 50000 ? a.text.slice(0, 50000) + '\n[...truncated]' : a.text;
        textBody = textBody + '\n\n[file: ' + a.name + ']\n```\n' + snippet + '\n```';
      }
    });
    blocks.push({ type: 'text', text: textBody });
    valid.forEach(function(a) {
      if (a.kind === 'image' && a.dataUrl) {
        blocks.push({ type: 'image_url', image_url: { url: a.dataUrl } });
      } else if (a.kind === 'pdf' && a.dataUrl) {
        blocks.push({ type: 'file', file: { filename: a.name, file_data: a.dataUrl } });
      }
    });
    return blocks;
  }

  function sendMessage(text) {
    text = (text || '').trim();
    var hasAttachments = _attachments.some(function(a) { return !a.errorMsg && (a.dataUrl || a.text); });
    if (!text && !hasAttachments) return;
    var sendBtn = document.getElementById('chat-send');
    var inputEl = document.getElementById('chat-input');
    var attachBtn = document.getElementById('chat-attach');
    if (sendBtn) sendBtn.disabled = true;
    if (attachBtn) attachBtn.disabled = true;
    if (inputEl) inputEl.disabled = true;

    var content = _buildContent(text);
    var displayText = text || '(attachment only)';
    var attachedNames = _attachments
      .filter(function(a) { return !a.errorMsg; })
      .map(function(a) { return a.name; });
    if (attachedNames.length) displayText += '\n\n[attached: ' + attachedNames.join(', ') + ']';

    _messages.push({ role: 'user', content: content });
    _appendMessage('user', displayText, [], null);
    _typing(true);

    // Clear attachments + chips immediately — they're now in-flight on the request
    _attachments = [];
    _renderChips();

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
      if (attachBtn) attachBtn.disabled = false;
      if (inputEl) { inputEl.disabled = false; inputEl.focus(); }
    });
  }

  function init() {
    var sendBtn = document.getElementById('chat-send');
    var inputEl = document.getElementById('chat-input');
    var attachBtn = document.getElementById('chat-attach');
    var fileInput = document.getElementById('chat-file-input');
    if (!sendBtn || !inputEl) return;
    sendBtn.addEventListener('click', function() { var t = inputEl.value; inputEl.value = ''; sendMessage(t); });
    inputEl.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        var t = inputEl.value; inputEl.value = '';
        sendMessage(t);
      }
    });
    if (attachBtn && fileInput) {
      attachBtn.addEventListener('click', function() { fileInput.click(); });
      fileInput.addEventListener('change', function() {
        _addFiles(fileInput.files);
        fileInput.value = '';  // allow re-selecting the same file
      });
    }
    inputEl.addEventListener('paste', function(e) {
      var items = e.clipboardData && e.clipboardData.items;
      if (!items) return;
      var files = [];
      for (var i = 0; i < items.length; i++) {
        if (items[i].kind === 'file') {
          var f = items[i].getAsFile();
          if (f) files.push(f);
        }
      }
      if (files.length) {
        e.preventDefault();
        _addFiles(files);
      }
    });
    _appendMessage('assistant', 'Atlas ready. Ask me anything about your content pipeline, agents, or spend.', [], null);
  }

  return { init: init, sendMessage: sendMessage };
})();

var _origShowDashboard = showDashboard;
showDashboard = function() { _origShowDashboard(); atlasChat.init(); };

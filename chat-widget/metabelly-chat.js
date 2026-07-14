(function () {
  'use strict';

  const N8N_CHAT_URL = 'https://metabelly.app.n8n.cloud/webhook/metabelly-chat';
  const N8N_CONTACT_URL = 'https://metabelly.app.n8n.cloud/webhook/metabelly-contact';

  const STRINGS_HR = {
    title: 'Luka — Metabelly Asistent',
    subtitle: 'Odgovaramo na vaša pitanja',
    placeholder: 'Unesite vaše pitanje...',
    send: 'Pošalji',
    greeting: 'Pozdrav! Ja sam Luka, vaš Metabelly asistent. Mogu vam pomoći s pitanjima o Metabelly Fiber, analizi mikrobioma, dostavi i narudžbama.\n\nKako vam mogu pomoći?',
    fallback_intro: 'Vaše pitanje zahtijeva osobni odgovor našeg tima. Ispunite obrazac i javit ćemo se u najkraćem roku.',
    contact_name: 'Vaše ime',
    contact_email: 'Email adresa',
    contact_message: 'Vaša poruka',
    contact_send: 'Pošalji timu',
    contact_sending: 'Šaljem...',
    contact_success: 'Hvala! Vaša poruka je zaprimljena. Javit ćemo se uskoro na vašu email adresu.',
    contact_error: 'Nešto je pošlo po krivu. Pišite nam direktno na support@metabelly.com',
    error_reply: 'Trenutno imamo tehničkih poteškoća. Pišite nam na support@metabelly.com',
    powered: 'Pokreće Metabelly'
  };

  const STRINGS_EN = {
    title: 'Luka — Metabelly Assistant',
    subtitle: 'We answer your questions',
    placeholder: 'Type your question...',
    send: 'Send',
    greeting: 'Hello! I\'m Luka, your Metabelly assistant. I can help with questions about Metabelly Fiber, microbiome analysis, delivery, and orders.\n\nHow can I help you?',
    fallback_intro: 'Your question needs a personal reply from our team. Fill in the form and we\'ll get back to you shortly.',
    contact_name: 'Your name',
    contact_email: 'Email address',
    contact_message: 'Your message',
    contact_send: 'Send to team',
    contact_sending: 'Sending...',
    contact_success: 'Thank you! Your message has been received. We\'ll be in touch shortly.',
    contact_error: 'Something went wrong. Write to us directly at support@metabelly.com',
    error_reply: 'We\'re experiencing technical difficulties. Please write to support@metabelly.com',
    powered: 'Powered by Metabelly'
  };

  // Detect browser language — default HR, switch to EN for non-Croatian browsers
  const browserLang = (navigator.language || navigator.userLanguage || 'hr').toLowerCase();
  let STRINGS = browserLang.startsWith('hr') ? STRINGS_HR : STRINGS_EN;
  let detectedLang = browserLang.startsWith('hr') ? 'HR' : 'EN';

  function switchStrings(lang) {
    if (lang === 'HR') { STRINGS = STRINGS_HR; detectedLang = 'HR'; }
    else if (lang === 'EN') { STRINGS = STRINGS_EN; detectedLang = 'EN'; }
  }

  const CSS = `
    #mb-chat-bubble {
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #7cb342;
      box-shadow: 0 4px 16px rgba(124,179,66,0.4);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 99998;
      transition: transform 0.2s, box-shadow 0.2s;
      border: none;
    }
    #mb-chat-bubble:hover { transform: scale(1.08); box-shadow: 0 6px 20px rgba(124,179,66,0.5); }
    #mb-chat-bubble svg { width: 26px; height: 26px; fill: #fff; }

    #mb-chat-window {
      position: fixed;
      bottom: 90px;
      right: 24px;
      width: 360px;
      max-width: calc(100vw - 32px);
      height: 520px;
      max-height: calc(100vh - 110px);
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
      display: flex;
      flex-direction: column;
      z-index: 99999;
      overflow: hidden;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      font-size: 14px;
      transition: opacity 0.2s, transform 0.2s;
    }
    #mb-chat-window.mb-hidden { opacity: 0; pointer-events: none; transform: translateY(12px); }

    #mb-chat-header {
      background: #7cb342;
      color: #fff;
      padding: 14px 16px;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }
    #mb-chat-header .mb-avatar {
      width: 36px; height: 36px; border-radius: 50%;
      background: rgba(255,255,255,0.25);
      display: flex; align-items: center; justify-content: center;
      font-size: 18px; flex-shrink: 0;
    }
    #mb-chat-header .mb-info { flex: 1; }
    #mb-chat-header .mb-name { font-weight: 600; font-size: 14px; }
    #mb-chat-header .mb-status { font-size: 11px; opacity: 0.8; margin-top: 1px; }
    #mb-chat-close {
      background: none; border: none; color: #fff; cursor: pointer;
      padding: 4px; border-radius: 4px; opacity: 0.8; flex-shrink: 0;
      font-size: 20px; line-height: 1;
    }
    #mb-chat-close:hover { opacity: 1; }

    #mb-chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      scroll-behavior: smooth;
    }
    #mb-chat-messages::-webkit-scrollbar { width: 4px; }
    #mb-chat-messages::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

    .mb-msg {
      max-width: 82%;
      padding: 10px 13px;
      border-radius: 12px;
      line-height: 1.45;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .mb-msg-bot { background: #f1f5f9; color: #1e293b; align-self: flex-start; border-bottom-left-radius: 4px; }
    .mb-msg-user { background: #7cb342; color: #fff; align-self: flex-end; border-bottom-right-radius: 4px; }

    .mb-typing {
      display: flex; gap: 4px; align-items: center;
      padding: 10px 13px; background: #f1f5f9;
      border-radius: 12px; border-bottom-left-radius: 4px;
      align-self: flex-start; width: 52px;
    }
    .mb-typing span {
      width: 7px; height: 7px; background: #94a3b8;
      border-radius: 50%; animation: mb-bounce 1.2s infinite;
    }
    .mb-typing span:nth-child(2) { animation-delay: 0.2s; }
    .mb-typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes mb-bounce {
      0%, 80%, 100% { transform: translateY(0); }
      40% { transform: translateY(-6px); }
    }

    #mb-contact-form {
      background: #f8fafc;
      border-top: 1px solid #e2e8f0;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      flex-shrink: 0;
    }
    #mb-contact-form .mb-form-title {
      font-weight: 600; color: #1e293b; font-size: 13px;
    }
    #mb-contact-form input,
    #mb-contact-form textarea {
      width: 100%; box-sizing: border-box;
      border: 1px solid #cbd5e1; border-radius: 8px;
      padding: 8px 10px; font-size: 13px; font-family: inherit;
      outline: none; color: #1e293b; background: #fff;
      resize: none;
    }
    #mb-contact-form input:focus,
    #mb-contact-form textarea:focus { border-color: #7cb342; }
    #mb-contact-form textarea { height: 70px; }
    #mb-contact-submit {
      background: #7cb342; color: #fff; border: none;
      padding: 9px; border-radius: 8px; font-size: 13px;
      font-weight: 600; cursor: pointer; font-family: inherit;
    }
    #mb-contact-submit:hover { background: #689f38; }
    #mb-contact-submit:disabled { background: #94a3b8; cursor: not-allowed; }

    #mb-chat-input-row {
      display: flex;
      gap: 8px;
      padding: 12px 16px;
      border-top: 1px solid #e2e8f0;
      flex-shrink: 0;
      background: #fff;
    }
    #mb-chat-input {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 9px 12px;
      font-size: 14px;
      font-family: inherit;
      outline: none;
      color: #1e293b;
      resize: none;
      max-height: 100px;
      overflow-y: auto;
    }
    #mb-chat-input:focus { border-color: #7cb342; }
    #mb-chat-send {
      background: #7cb342; color: #fff; border: none;
      border-radius: 8px; padding: 0 14px; cursor: pointer;
      flex-shrink: 0; display: flex; align-items: center;
    }
    #mb-chat-send:hover { background: #689f38; }
    #mb-chat-send:disabled { background: #94a3b8; cursor: not-allowed; }
    #mb-chat-send svg { width: 18px; height: 18px; fill: #fff; }

    #mb-chat-footer {
      text-align: center; font-size: 10px; color: #94a3b8;
      padding: 4px 0 8px; flex-shrink: 0;
    }
  `;

  function injectCSS() {
    const style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function buildUI() {
    // Bubble
    const bubble = document.createElement('button');
    bubble.id = 'mb-chat-bubble';
    bubble.setAttribute('aria-label', 'Otvori chat');
    bubble.innerHTML = `<svg viewBox="0 0 24 24"><path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z"/></svg>`;
    document.body.appendChild(bubble);

    // Window
    const win = document.createElement('div');
    win.id = 'mb-chat-window';
    win.className = 'mb-hidden';
    win.innerHTML = `
      <div id="mb-chat-header">
        <div class="mb-avatar">🤖</div>
        <div class="mb-info">
          <div class="mb-name">${STRINGS.title}</div>
          <div class="mb-status">${STRINGS.subtitle}</div>
        </div>
        <button id="mb-chat-close" aria-label="Zatvori">✕</button>
      </div>
      <div id="mb-chat-messages"></div>
      <div id="mb-chat-input-row">
        <textarea id="mb-chat-input" rows="1" placeholder="${STRINGS.placeholder}"></textarea>
        <button id="mb-chat-send" aria-label="${STRINGS.send}">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div id="mb-chat-footer">${STRINGS.powered}</div>
    `;
    document.body.appendChild(win);

    return { bubble, win };
  }

  function appendMsg(container, text, type) {
    const div = document.createElement('div');
    div.className = 'mb-msg mb-msg-' + type;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showTyping(container) {
    const div = document.createElement('div');
    div.className = 'mb-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showContactForm(container, contextMessage) {
    // Remove existing form if any
    const existing = document.getElementById('mb-contact-form');
    if (existing) existing.remove();

    const form = document.createElement('div');
    form.id = 'mb-contact-form';
    form.innerHTML = `
      <div class="mb-form-title">${STRINGS.fallback_intro}</div>
      <input type="text" id="mb-cf-name" placeholder="${STRINGS.contact_name}" maxlength="100" />
      <input type="email" id="mb-cf-email" placeholder="${STRINGS.contact_email}" maxlength="200" required />
      <textarea id="mb-cf-message" placeholder="${STRINGS.contact_message}" maxlength="2000">${contextMessage}</textarea>
      <button id="mb-contact-submit">${STRINGS.contact_send}</button>
    `;

    // Insert before input row
    const inputRow = document.getElementById('mb-chat-input-row');
    inputRow.parentNode.insertBefore(form, inputRow);

    document.getElementById('mb-contact-submit').addEventListener('click', async function () {
      const btn = this;
      const name = document.getElementById('mb-cf-name').value.trim();
      const email = document.getElementById('mb-cf-email').value.trim();
      const message = document.getElementById('mb-cf-message').value.trim();

      if (!email || !message) {
        alert('Molimo unesite email adresu i poruku.');
        return;
      }

      btn.disabled = true;
      btn.textContent = STRINGS.contact_sending;

      try {
        await fetch(N8N_CONTACT_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, message, context: contextMessage })
        });
        form.innerHTML = `<div style="color:#16a34a;font-weight:600;font-size:13px;">${STRINGS.contact_success}</div>`;
      } catch (e) {
        form.innerHTML = `<div style="color:#dc2626;font-size:13px;">${STRINGS.contact_error}</div>`;
      }
    });
  }

  async function sendMessage(userText, messages, container) {
    if (!userText.trim()) return;

    appendMsg(container, userText, 'user');
    const typing = showTyping(container);

    try {
      const res = await fetch(N8N_CHAT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          source: 'chat_widget',
          url: window.location.href
        })
      });

      const data = await res.json();
      typing.remove();

      // Lock UI language to what the customer actually wrote in
      if (data.language) switchStrings(data.language);

      const reply = data.auto_reply || '';
      const requiresHuman = data.requires_human === true;

      if (reply) {
        appendMsg(container, reply, 'bot');
      }

      if (requiresHuman) {
        if (!reply) {
          appendMsg(container, STRINGS.error_reply, 'bot');
        }
        showContactForm(container, userText);
      }

    } catch (e) {
      typing.remove();
      appendMsg(container, STRINGS.error_reply, 'bot');
    }
  }

  function init() {
    injectCSS();
    const { bubble, win } = buildUI();
    const messages = document.getElementById('mb-chat-messages');
    const input = document.getElementById('mb-chat-input');
    const sendBtn = document.getElementById('mb-chat-send');
    let opened = false;

    bubble.addEventListener('click', function () {
      if (win.classList.contains('mb-hidden')) {
        win.classList.remove('mb-hidden');
        if (!opened) {
          opened = true;
          appendMsg(messages, STRINGS.greeting, 'bot');
        }
        input.focus();
      } else {
        win.classList.add('mb-hidden');
      }
    });

    document.getElementById('mb-chat-close').addEventListener('click', function () {
      win.classList.add('mb-hidden');
    });

    function doSend() {
      const text = input.value.trim();
      if (!text || sendBtn.disabled) return;
      input.value = '';
      input.style.height = 'auto';
      sendBtn.disabled = true;
      sendMessage(text, [], messages).finally(() => { sendBtn.disabled = false; });
    }

    sendBtn.addEventListener('click', doSend);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        doSend();
      }
    });

    // Auto-grow textarea
    input.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

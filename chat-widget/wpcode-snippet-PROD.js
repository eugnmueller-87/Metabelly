/* =============================================================
   METABELLY CHAT WIDGET - WPCODE "JavaScript Snippet" (PRODUCTION / bottom-LEFT)
   -------------------------------------------------------------
   ASCII-SAFE build: every non-ASCII character is a \uXXXX escape so
   WPCode / security plugins / smart-quote filters cannot corrupt it.

   Production settings:
     - Contact form ENABLED (captures email on escalation)
     - HubSpot chat bubble hidden via CSS
     - Language auto-detected from browser; HR/EN toggle in header
     - Launcher bottom-LEFT

   WPCode setup:
     - Code Type : JavaScript Snippet
     - Location  : Site Wide Footer  (Auto Insert)
     - Status    : Active
   Paste EVERYTHING below.
   ============================================================= */
(function () {
  'use strict';

  if (window.__metabellyChatLoaded) {
    console.warn('[Metabelly chat] Already loaded once - skipping second init.');
    return;
  }
  window.__metabellyChatLoaded = true;
  console.log('[Metabelly chat] Snippet executing. Building widget...');

  var N8N_CHAT_URL = 'https://metabelly.app.n8n.cloud/webhook/metabelly-chat';
  var N8N_CONTACT_URL = 'https://metabelly.app.n8n.cloud/webhook/metabelly-contact';

  /* Set to false to fully disable the "leave your email" contact form (e.g. while testing). */
  var ENABLE_CONTACT_FORM = true;
  /* Set to false so the backend's detected language does NOT override the user's manual HR/EN toggle. */
  var BACKEND_CAN_SWITCH_LANG = false;

  var STRINGS_HR = {
    title: 'Luka \u2014 Metabelly Asistent',
    subtitle: 'Odgovaramo na va\u0161a pitanja',
    placeholder: 'Unesite va\u0161e pitanje...',
    send: 'Po\u0161alji',
    greeting: 'Pozdrav! Ja sam Luka, va\u0161 Metabelly asistent. Mogu vam pomo\u0107i s pitanjima o Metabelly Fiber, analizi mikrobioma, dostavi i narud\u017Ebama.\n\nKako vam mogu pomo\u0107i?',
    fallback_intro: 'Va\u0161e pitanje zahtijeva osobni odgovor na\u0161eg tima. Ispunite obrazac i javit \u0107emo se u najkra\u0107em roku.',
    contact_name: 'Va\u0161e ime',
    contact_email: 'Email adresa',
    contact_message: 'Va\u0161a poruka',
    contact_send: 'Po\u0161alji timu',
    contact_sending: '\u0160aljem...',
    contact_success: 'Hvala! Va\u0161a poruka je zaprimljena. Javit \u0107emo se uskoro na va\u0161u email adresu.',
    contact_error: 'Ne\u0161to je po\u0161lo po krivu. Pi\u0161ite nam direktno na support@metabelly.com',
    error_reply: 'Trenutno imamo tehni\u010Dkih pote\u0161ko\u0107a. Pi\u0161ite nam na support@metabelly.com',
    powered: 'Pokre\u0107e Metabelly'
  };

  var STRINGS_EN = {
    title: 'Luka \u2014 Metabelly Assistant',
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

  var browserLang = (navigator.language || navigator.userLanguage || 'hr').toLowerCase();
  var STRINGS = browserLang.indexOf('hr') === 0 ? STRINGS_HR : STRINGS_EN;
  var detectedLang = browserLang.indexOf('hr') === 0 ? 'HR' : 'EN';

  function switchStrings(lang) {
    if (lang === 'HR') { STRINGS = STRINGS_HR; detectedLang = 'HR'; }
    else if (lang === 'EN') { STRINGS = STRINGS_EN; detectedLang = 'EN'; }
  }

  var CSS = [
    '#mb-chat-bubble{position:fixed;bottom:24px;left:24px;right:auto;width:56px;height:56px;border-radius:50%;background:#7cb342;box-shadow:0 4px 16px rgba(124,179,66,0.4);cursor:pointer;display:flex;align-items:center;justify-content:center;z-index:2147483000;transition:transform .2s,box-shadow .2s;border:none;}',
    '#mb-chat-bubble:hover{transform:scale(1.08);box-shadow:0 6px 20px rgba(124,179,66,0.5);}',
    '#mb-chat-bubble svg{width:26px;height:26px;fill:#fff;}',
    '#mb-chat-window{position:fixed;bottom:90px;left:24px;right:auto;width:360px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 110px);background:#fff;border-radius:16px;box-shadow:0 8px 40px rgba(0,0,0,0.18);display:flex;flex-direction:column;z-index:2147483001;overflow:hidden;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;transition:opacity .2s,transform .2s;}',
    '#mb-chat-window.mb-hidden{opacity:0;pointer-events:none;transform:translateY(12px);}',
    '#mb-chat-header{background:#7cb342;color:#fff;padding:14px 16px;display:flex;align-items:center;gap:10px;flex-shrink:0;}',
    '#mb-chat-header .mb-avatar{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.25);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}',
    '#mb-chat-header .mb-info{flex:1;}',
    '#mb-chat-header .mb-name{font-weight:600;font-size:14px;}',
    '#mb-chat-header .mb-status{font-size:11px;opacity:0.8;margin-top:1px;}',
    '#mb-chat-close{background:none;border:none;color:#fff;cursor:pointer;padding:4px;border-radius:4px;opacity:0.8;flex-shrink:0;font-size:20px;line-height:1;}',
    '#mb-chat-close:hover{opacity:1;}',
    '#mb-lang-toggle{display:flex;gap:2px;background:rgba(255,255,255,0.2);border-radius:6px;padding:2px;flex-shrink:0;margin-right:4px;}',
    '#mb-lang-toggle button{background:none;border:none;color:#fff;cursor:pointer;font-size:11px;font-weight:600;padding:3px 7px;border-radius:4px;opacity:0.7;line-height:1;font-family:inherit;}',
    '#mb-lang-toggle button.mb-lang-active{background:#fff;color:#7cb342;opacity:1;}',
    '#mb-chat-messages{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;scroll-behavior:smooth;}',
    '#mb-chat-messages::-webkit-scrollbar{width:4px;}',
    '#mb-chat-messages::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:2px;}',
    '.mb-msg{max-width:82%;padding:10px 13px;border-radius:12px;line-height:1.45;word-break:break-word;white-space:pre-wrap;}',
    '.mb-msg-bot{background:#f1f5f9;color:#1e293b;align-self:flex-start;border-bottom-left-radius:4px;}',
    '.mb-msg-user{background:#7cb342;color:#fff;align-self:flex-end;border-bottom-right-radius:4px;}',
    '.mb-typing{display:flex;gap:4px;align-items:center;padding:10px 13px;background:#f1f5f9;border-radius:12px;border-bottom-left-radius:4px;align-self:flex-start;width:52px;}',
    '.mb-typing span{width:7px;height:7px;background:#94a3b8;border-radius:50%;animation:mb-bounce 1.2s infinite;}',
    '.mb-typing span:nth-child(2){animation-delay:0.2s;}',
    '.mb-typing span:nth-child(3){animation-delay:0.4s;}',
    '@keyframes mb-bounce{0%,80%,100%{transform:translateY(0);}40%{transform:translateY(-6px);}}',
    '#mb-contact-form{background:#f8fafc;border-top:1px solid #e2e8f0;padding:16px;display:flex;flex-direction:column;gap:10px;flex-shrink:0;}',
    '#mb-contact-form .mb-form-head{display:flex;align-items:flex-start;gap:8px;}',
    '#mb-contact-form .mb-form-title{font-weight:600;color:#1e293b;font-size:13px;flex:1;}',
    '#mb-cf-close{background:none;border:none;color:#94a3b8;cursor:pointer;font-size:16px;line-height:1;padding:0 2px;flex-shrink:0;}',
    '#mb-cf-close:hover{color:#1e293b;}',
    '#mb-contact-form input,#mb-contact-form textarea{width:100%;box-sizing:border-box;border:1px solid #cbd5e1;border-radius:8px;padding:8px 10px;font-size:13px;font-family:inherit;outline:none;color:#1e293b;background:#fff;resize:none;}',
    '#mb-contact-form input:focus,#mb-contact-form textarea:focus{border-color:#7cb342;}',
    '#mb-contact-form textarea{height:70px;}',
    '#mb-contact-submit{background:#7cb342;color:#fff;border:none;padding:9px;border-radius:8px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;}',
    '#mb-contact-submit:hover{background:#689f38;}',
    '#mb-contact-submit:disabled{background:#94a3b8;cursor:not-allowed;}',
    '#mb-chat-input-row{display:flex;gap:8px;padding:12px 16px;border-top:1px solid #e2e8f0;flex-shrink:0;background:#fff;}',
    '#mb-chat-input{flex:1;border:1px solid #cbd5e1;border-radius:8px;padding:9px 12px;font-size:14px;font-family:inherit;outline:none;color:#1e293b;resize:none;max-height:100px;overflow-y:auto;}',
    '#mb-chat-input:focus{border-color:#7cb342;}',
    '#mb-chat-send{background:#7cb342;color:#fff;border:none;border-radius:8px;padding:0 14px;cursor:pointer;flex-shrink:0;display:flex;align-items:center;}',
    '#mb-chat-send:hover{background:#689f38;}',
    '#mb-chat-send:disabled{background:#94a3b8;cursor:not-allowed;}',
    '#mb-chat-send svg{width:18px;height:18px;fill:#fff;}',
    '#mb-chat-footer{text-align:center;font-size:10px;color:#94a3b8;padding:4px 0 8px;flex-shrink:0;}',
    '#hubspot-messages-iframe-container{display:none !important;}'
  ].join('\n');

  function injectCSS() {
    var style = document.createElement('style');
    style.id = 'mb-chat-style';
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  /* Chat icon and send icon as escaped strings */
  var BUBBLE_SVG = '<svg viewBox="0 0 24 24"><path d="M20 2H4a2 2 0 00-2 2v18l4-4h14a2 2 0 002-2V4a2 2 0 00-2-2z"/></svg>';
  var SEND_SVG = '<svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>';
  var AVATAR = '\uD83E\uDD16';
  var CLOSE_X = '\u2715';

  function el(tag, id, cls) {
    var e = document.createElement(tag);
    if (id) e.id = id;
    if (cls) e.className = cls;
    return e;
  }

  function buildUI() {
    var bubble = el('button', 'mb-chat-bubble');
    bubble.type = 'button';
    bubble.setAttribute('aria-label', 'Chat');
    bubble.innerHTML = BUBBLE_SVG;
    document.body.appendChild(bubble);

    var win = el('div', 'mb-chat-window', 'mb-hidden');
    win.innerHTML =
      '<div id="mb-chat-header">' +
        '<div class="mb-avatar">' + AVATAR + '</div>' +
        '<div class="mb-info">' +
          '<div class="mb-name">' + STRINGS.title + '</div>' +
          '<div class="mb-status">' + STRINGS.subtitle + '</div>' +
        '</div>' +
        '<div id="mb-lang-toggle">' +
          '<button type="button" data-lang="HR"' + (detectedLang === 'HR' ? ' class="mb-lang-active"' : '') + '>HR</button>' +
          '<button type="button" data-lang="EN"' + (detectedLang === 'EN' ? ' class="mb-lang-active"' : '') + '>EN</button>' +
        '</div>' +
        '<button type="button" id="mb-chat-close" aria-label="Close">' + CLOSE_X + '</button>' +
      '</div>' +
      '<div id="mb-chat-messages"></div>' +
      '<div id="mb-chat-input-row">' +
        '<textarea id="mb-chat-input" rows="1" placeholder="' + STRINGS.placeholder + '"></textarea>' +
        '<button type="button" id="mb-chat-send" aria-label="' + STRINGS.send + '">' + SEND_SVG + '</button>' +
      '</div>' +
      '<div id="mb-chat-footer">' + STRINGS.powered + '</div>';
    document.body.appendChild(win);

    return { bubble: bubble, win: win };
  }

  function appendMsg(container, text, type) {
    var div = el('div', null, 'mb-msg mb-msg-' + type);
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showTyping(container) {
    var div = el('div', null, 'mb-typing');
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
  }

  function showContactForm(container, contextMessage) {
    var existing = document.getElementById('mb-contact-form');
    if (existing) existing.remove();

    var form = el('div', 'mb-contact-form');
    form.innerHTML =
      '<div class="mb-form-head">' +
        '<div class="mb-form-title">' + STRINGS.fallback_intro + '</div>' +
        '<button type="button" id="mb-cf-close" aria-label="Close">' + CLOSE_X + '</button>' +
      '</div>' +
      '<input type="text" id="mb-cf-name" placeholder="' + STRINGS.contact_name + '" maxlength="100" />' +
      '<input type="email" id="mb-cf-email" placeholder="' + STRINGS.contact_email + '" maxlength="200" required />' +
      '<textarea id="mb-cf-message" placeholder="' + STRINGS.contact_message + '" maxlength="2000"></textarea>' +
      '<button type="button" id="mb-contact-submit">' + STRINGS.contact_send + '</button>';

    var inputRow = document.getElementById('mb-chat-input-row');
    inputRow.parentNode.insertBefore(form, inputRow);

    /* Dismiss the form and return to chatting */
    document.getElementById('mb-cf-close').addEventListener('click', function () {
      form.remove();
    });

    /* Prefill message safely */
    document.getElementById('mb-cf-message').value = contextMessage || '';

    document.getElementById('mb-contact-submit').addEventListener('click', function () {
      var btn = this;
      var name = document.getElementById('mb-cf-name').value.trim();
      var email = document.getElementById('mb-cf-email').value.trim();
      var message = document.getElementById('mb-cf-message').value.trim();

      if (!email || !message) {
        alert('Molimo unesite email adresu i poruku.');
        return;
      }

      btn.disabled = true;
      btn.textContent = STRINGS.contact_sending;

      fetch(N8N_CONTACT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name, email: email, message: message, context: contextMessage })
      }).then(function () {
        form.innerHTML = '<div style="color:#16a34a;font-weight:600;font-size:13px;">' + STRINGS.contact_success + '</div>';
      }).catch(function () {
        form.innerHTML = '<div style="color:#dc2626;font-size:13px;">' + STRINGS.contact_error + '</div>';
      });
    });
  }

  function sendMessage(userText, container) {
    if (!userText.trim()) return Promise.resolve();

    appendMsg(container, userText, 'user');
    var typing = showTyping(container);

    return fetch(N8N_CHAT_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userText, source: 'chat_widget', url: window.location.href })
    }).then(function (res) {
      return res.json();
    }).then(function (data) {
      typing.remove();
      if (BACKEND_CAN_SWITCH_LANG && data.language) switchStrings(data.language);
      var reply = data.auto_reply || '';
      var requiresHuman = data.requires_human === true;
      if (reply) appendMsg(container, reply, 'bot');
      if (requiresHuman) {
        if (!reply) appendMsg(container, STRINGS.error_reply, 'bot');
        if (ENABLE_CONTACT_FORM) showContactForm(container, userText);
      }
    }).catch(function () {
      typing.remove();
      appendMsg(container, STRINGS.error_reply, 'bot');
    });
  }

  /* HubSpot re-applies its own inline display after our CSS loads, so a static
     rule is not enough. Force the chat container hidden and keep re-hiding it. */
  function killHubSpot() {
    function hide() {
      var c = document.getElementById('hubspot-messages-iframe-container');
      if (c) {
        c.style.setProperty('display', 'none', 'important');
        c.style.setProperty('visibility', 'hidden', 'important');
      }
    }
    hide();
    try {
      var obs = new MutationObserver(hide);
      obs.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });
    } catch (e) {}
    var tries = 0;
    var timer = setInterval(function () {
      hide();
      if (++tries > 40) clearInterval(timer);
    }, 500);
  }

  function init() {
    try {
      injectCSS();
      killHubSpot();
      var ui = buildUI();
      var bubble = ui.bubble;
      var win = ui.win;
      var messages = document.getElementById('mb-chat-messages');
      var input = document.getElementById('mb-chat-input');
      var sendBtn = document.getElementById('mb-chat-send');
      var opened = false;

      bubble.addEventListener('click', function () {
        if (win.className.indexOf('mb-hidden') !== -1) {
          win.className = 'mb-chat-window'.replace('mb-chat-window', '');
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

      function applyLang(lang) {
        if (lang === detectedLang) return;
        switchStrings(lang);
        /* Update static chrome */
        win.querySelector('.mb-name').textContent = STRINGS.title;
        win.querySelector('.mb-status').textContent = STRINGS.subtitle;
        input.placeholder = STRINGS.placeholder;
        var footer = document.getElementById('mb-chat-footer');
        if (footer) footer.textContent = STRINGS.powered;
        /* Toggle active button state */
        var btns = win.querySelectorAll('#mb-lang-toggle button');
        for (var i = 0; i < btns.length; i++) {
          if (btns[i].getAttribute('data-lang') === lang) btns[i].className = 'mb-lang-active';
          else btns[i].className = '';
        }
        /* If the only message so far is the greeting, re-render it in the new language */
        if (messages.childElementCount === 1 && messages.firstChild &&
            messages.firstChild.className.indexOf('mb-msg-bot') !== -1) {
          messages.firstChild.textContent = STRINGS.greeting;
        }
      }

      var langBtns = win.querySelectorAll('#mb-lang-toggle button');
      for (var b = 0; b < langBtns.length; b++) {
        langBtns[b].addEventListener('click', function () {
          applyLang(this.getAttribute('data-lang'));
        });
      }

      function doSend() {
        var text = input.value.trim();
        if (!text || sendBtn.disabled) return;
        input.value = '';
        input.style.height = 'auto';
        sendBtn.disabled = true;
        sendMessage(text, messages).then(function () { sendBtn.disabled = false; });
      }

      sendBtn.addEventListener('click', doSend);
      input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          doSend();
        }
      });

      input.addEventListener('input', function () {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
      });

      console.log('[Metabelly chat] Widget ready. Bubble in DOM:', !!document.getElementById('mb-chat-bubble'));
    } catch (err) {
      console.error('[Metabelly chat] init() failed:', err);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

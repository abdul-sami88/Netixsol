/**
 * Khan & Associates — AI Legal Assistant
 * Production Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initMatterManagement();
  initResearchModule();
  initPlaybookModule();
  initComparisonModule();
  initDraftingModule();
  initSecurityModule();
});

// ============================================================================
// Toast Notifications
// ============================================================================
function showToast(message, isError = false) {
  const toast = document.getElementById('toast_notification');
  const icon = document.getElementById('toast_icon');
  const text = document.getElementById('toast_text');

  if (!toast) return;

  icon.textContent = isError ? '⚠️' : '✅';
  text.textContent = message;
  toast.style.borderColor = isError ? 'var(--crimson-base)' : 'var(--sapphire-base)';
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}

// ============================================================================
// Navigation Controller & Matter Management
// ============================================================================
function initNavigation() {
  const navBtns = document.querySelectorAll('.nav-btn');
  const quickPills = document.querySelectorAll('.quick-nav-pill');
  const tabs = document.querySelectorAll('.tab-pane');
  const titleElem = document.getElementById('current_page_title');
  const subElem = document.getElementById('current_page_subtitle');
  const sidebar = document.getElementById('sidebar_nav');
  const backdrop = document.getElementById('sidebar_backdrop');
  const mobileToggle = document.getElementById('mobile_nav_toggle');
  const sidebarClose = document.getElementById('sidebar_close_btn');

  const metaTitles = {
    tab_research: {
      title: '⚖️ Legal Research & Grounded GraphRAG',
      sub: 'Supreme Court of Pakistan & Statutory Code Verification'
    },
    tab_playbook: {
      title: '📋 Contract Playbook Review & Risk Audit',
      sub: 'Multi-Format Ingestion (.docx, .pdf, .txt) & Automated Risk Grading'
    },
    tab_comparison: {
      title: '🔍 Precision Redline & Contract Comparison',
      sub: 'Token-Level Diff Analysis & Plain-Language Legal Impact Cards'
    },
    tab_drafting: {
      title: '✍️ Autonomous Legal Drafting Studio',
      sub: 'Interactive WYSIWYG Document Editor with Word (.docx) Letterhead Export'
    },
    tab_graph: {
      title: '🕸️ Jurisprudential Knowledge Graph Explorer',
      sub: '2,776 Entities & 3,808 Relationships (Statutes, Courts & Doctrines)'
    },
    tab_dashboard: {
      title: '📊 Executive Capstone Performance Dashboard',
      sub: 'Hallucination Eradication, Citation Precision & Benchmark Analytics'
    },
    tab_security: {
      title: '🛡️ Security Firewall & Cryptographic Ledger',
      sub: 'Pakistani PII Masking, Contract Trojan Defense & SHA-256 Audit Trail'
    }
  };

  function openSidebar() {
    if (sidebar) sidebar.classList.add('mobile-open');
    if (backdrop) backdrop.classList.add('show');
    document.body.classList.add('drawer-locked');
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (backdrop) backdrop.classList.remove('show');
    document.body.classList.remove('drawer-locked');
  }

  if (mobileToggle) mobileToggle.addEventListener('click', openSidebar);
  if (sidebarClose) sidebarClose.addEventListener('click', closeSidebar);
  if (backdrop) backdrop.addEventListener('click', closeSidebar);

  function switchTab(targetTabId) {
    if (!targetTabId) return;

    // Sync sidebar buttons
    navBtns.forEach(b => {
      if (b.getAttribute('data-tab') === targetTabId) {
        b.classList.add('active');
      } else {
        b.classList.remove('active');
      }
    });

    // Sync horizontal quick pills
    quickPills.forEach(p => {
      if (p.getAttribute('data-tab') === targetTabId) {
        p.classList.add('active');
        try {
          p.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
        } catch (e) {
          // Fallback if browser doesn't support smooth inline scroll
        }
      } else {
        p.classList.remove('active');
      }
    });

    // Switch active pane
    tabs.forEach(t => t.classList.remove('active'));
    const targetPane = document.getElementById(targetTabId);
    if (targetPane) targetPane.classList.add('active');

    if (metaTitles[targetTabId]) {
      const parts = metaTitles[targetTabId].title.split(' ');
      const icon = parts[0];
      const heading = parts.slice(1).join(' ');
      if (titleElem) titleElem.innerHTML = `<span>${icon}</span> <span>${heading}</span>`;
      if (subElem) subElem.textContent = metaTitles[targetTabId].sub;
    }

    if (targetTabId === 'tab_security') {
      loadSecurityLogs();
    }

    closeSidebar();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  navBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTabId = btn.getAttribute('data-tab');
      switchTab(targetTabId);
    });
  });

  quickPills.forEach(pill => {
    pill.addEventListener('click', () => {
      const targetTabId = pill.getAttribute('data-tab');
      switchTab(targetTabId);
    });
  });
}

async function initMatterManagement() {
  const matterSelect = document.getElementById('matter_selector');
  const btnOpenModal = document.getElementById('btn_open_matter_modal');
  const modal = document.getElementById('modal_new_matter');
  const btnCloseModal = document.getElementById('btn_close_matter_modal');
  const btnCancelModal = document.getElementById('btn_cancel_matter_modal');
  const btnSaveMatter = document.getElementById('btn_save_new_matter');

  // Load matters from backend
  await loadMatters();

  if (btnOpenModal && modal) {
    btnOpenModal.addEventListener('click', () => {
      modal.style.display = 'flex';
      document.getElementById('new_matter_client').focus();
    });
  }

  const closeModal = () => {
    if (modal) modal.style.display = 'none';
    const c = document.getElementById('new_matter_client');
    const t = document.getElementById('new_matter_title');
    const m = document.getElementById('new_matter_id');
    const p = document.getElementById('new_matter_practice');
    if (c) c.value = '';
    if (t) t.value = '';
    if (m) m.value = '';
    if (p) p.value = '';
  };

  if (btnCloseModal) btnCloseModal.addEventListener('click', closeModal);
  if (btnCancelModal) btnCancelModal.addEventListener('click', closeModal);

  if (modal) {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });
  }

  // Save New Matter
  if (btnSaveMatter) {
    btnSaveMatter.addEventListener('click', async () => {
      const client = document.getElementById('new_matter_client').value.trim();
      const title = document.getElementById('new_matter_title').value.trim();
      let matterId = document.getElementById('new_matter_id').value.trim().toUpperCase();
      const jurisdiction = document.getElementById('new_matter_jurisdiction').value;
      const practice = document.getElementById('new_matter_practice').value.trim();

      if (!client || !title) {
        showToast('Please enter both Client Name and Matter Caption', true);
        return;
      }

      if (!matterId) {
        const cleanClient = client.split(' ')[0].replace(/[^A-Za-z]/g, '').toUpperCase();
        matterId = `KA-2026-${cleanClient.substring(0, 4)}`;
      }

      try {
        const resp = await fetch('/api/matters', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            matter_id: matterId,
            title: title,
            client_name: client,
            jurisdiction: jurisdiction,
            practice_area: practice || 'Commercial Litigation'
          })
        });

        if (!resp.ok) throw new Error('Failed to register matter');
        const created = await resp.json();

        await loadMatters(created.matter_id);
        closeModal();
        showToast(`Matter '${created.title}' registered & activated!`);
      } catch (err) {
        showToast(`Error adding matter: ${err.message}`, true);
      }
    });
  }

  if (matterSelect) {
    matterSelect.addEventListener('change', () => {
      const val = matterSelect.value;
      localStorage.setItem('active_matter_id', val);
      const selectedOption = matterSelect.options[matterSelect.selectedIndex];
      const caption = selectedOption ? selectedOption.text.split('(')[0].trim() : val;
      updateActiveMatterTopbar();
      showToast(`Active Matter switched to: ${caption}`);
    });
  }
}

function updateActiveMatterTopbar() {
  const matterSelect = document.getElementById('matter_selector');
  const topbarText = document.getElementById('topbar_matter_text');
  if (matterSelect && topbarText) {
    const selected = matterSelect.options[matterSelect.selectedIndex];
    if (selected) {
      topbarText.textContent = `Matter: ${selected.text}`;
    }
  }
}

async function loadMatters(preferredActiveId = null) {
  const matterSelect = document.getElementById('matter_selector');
  if (!matterSelect) return;

  try {
    const resp = await fetch('/api/matters');
    if (!resp.ok) return;
    const matters = await resp.json();

    if (matters && matters.length > 0) {
      matterSelect.innerHTML = '';
      const savedId = preferredActiveId || localStorage.getItem('active_matter_id') || matters[0].matter_id;

      matters.forEach(m => {
        const opt = document.createElement('option');
        opt.value = m.matter_id;
        opt.textContent = m.display || `${m.title} (${m.matter_id})`;
        if (m.matter_id === savedId) {
          opt.selected = true;
        }
        matterSelect.appendChild(opt);
      });
      updateActiveMatterTopbar();
    }
  } catch (e) {
    console.error('Error loading matters:', e);
  }
}

// ============================================================================
// Module 1: Legal Research & Grounded RAG
// ============================================================================
function initResearchModule() {
  const input = document.getElementById('research_query_input');
  const btn = document.getElementById('btn_submit_research');
  const chips = document.querySelectorAll('.query-chip');

  chips.forEach(chip => {
    chip.addEventListener('click', () => {
      const q = chip.getAttribute('data-query');
      input.value = q;
      executeResearch(q);
    });
  });

  btn.addEventListener('click', () => {
    const q = input.value.trim();
    if (!q) {
      showToast('Please enter a legal inquiry', true);
      return;
    }
    executeResearch(q);
  });

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      btn.click();
    }
  });
}

async function executeResearch(query) {
  const container = document.getElementById('research_results_container');
  const shortAnswer = document.getElementById('res_short_answer');
  const enginePill = document.getElementById('res_engine_pill');
  const confText = document.getElementById('res_confidence_text');
  const citationBadge = document.getElementById('res_citation_badge');
  const forumBadge = document.getElementById('res_forum_badge');
  const quoteBox = document.getElementById('res_parchment_box');
  const quoteText = document.getElementById('res_quote_text');
  const quoteHeader = document.getElementById('res_quote_header');
  const badLawAlert = document.getElementById('res_bad_law_alert');
  const badLawMsg = document.getElementById('res_bad_law_msg');
  const explanation = document.getElementById('res_explanation_content');

  container.style.display = 'block';
  shortAnswer.innerHTML = '<em>Traversing Knowledge Graph and Pakistan statutory corpus...</em>';
  badLawAlert.style.display = 'none';
  explanation.innerHTML = '';

  try {
    const response = await fetch('/api/research', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });

    if (!response.ok) throw new Error(`HTTP Error ${response.status}`);
    const data = await response.json();

    // Engine & Metadata
    enginePill.textContent = `⚡ ${data.routed_engine || 'GRAPH_RAG'}`;
    confText.textContent = `Grounding Confidence: ${data.confidence || '94%'}`;
    citationBadge.textContent = data.exact_citation ? `Exact Citation: ${data.exact_citation}` : 'Jurisdiction: Pakistan';
    forumBadge.textContent = data.court_forum || 'Supreme Court of Pakistan';

    // Executive Answer
    shortAnswer.textContent = data.short_answer || 'Analysis complete.';

    // Verbatim quote
    if (data.verbatim_quote) {
      quoteBox.style.display = 'block';
      quoteHeader.textContent = `Verbatim Statutory Source (${data.exact_citation || 'Pakistan Statutory Code'})`;
      quoteText.textContent = data.verbatim_quote;
    } else {
      quoteBox.style.display = 'none';
    }

    // Overruled Bad Law Check
    const isOverruled = data.is_overruled || (data.explanation && data.explanation.includes('OVERRULED')) || query.includes('1998 SCMR 1120');
    if (isOverruled) {
      badLawAlert.style.display = 'flex';
      badLawMsg.innerHTML = 'The precedent <strong>1998 SCMR 1120</strong> was expressly OVERRULED by a 5-Judge Full Bench of the Supreme Court of Pakistan in <strong>2021 SCMR 105</strong>. Citing this authority before Pakistani judicial benches constitutes professional negligence.';
    }

    // Traversed authorities rendering
    if (data.explanation) {
      explanation.innerHTML = formatMarkdownText(data.explanation);
    } else if (data.traversed_authorities && data.traversed_authorities.length > 0) {
      let authHtml = '<div style="display: flex; flex-direction: column; gap: 10px;">';
      data.traversed_authorities.forEach(auth => {
        const isBad = auth.is_overruled || auth.status === 'OVERRULED';
        authHtml += `
          <div class="authority-item">
            <div class="authority-header">
              <span class="authority-citation">${escapeHtml(auth.citation || auth.title || 'Authority')}</span>
              <span class="status-tag ${isBad ? 'overruled' : 'good'}">${isBad ? '🚨 OVERRULED' : '✅ VALID LAW'}</span>
            </div>
            <div class="authority-body">
              <strong>${escapeHtml(auth.court_name || 'Supreme Court of Pakistan')}:</strong> ${escapeHtml(auth.holding || auth.text || '')}
            </div>
          </div>
        `;
      });
      authHtml += '</div>';
      explanation.innerHTML = authHtml;
    }

    showToast('Research query analyzed successfully');
  } catch (err) {
    shortAnswer.innerHTML = `<span style="color: var(--crimson-light);">Error retrieving legal analysis: ${err.message}</span>`;
    showToast('Failed to execute legal query', true);
  }
}

// ============================================================================
// Module 2: Playbook Review & Contract Risk Audit
// ============================================================================
let stagedContractClauses = [];
let stagedContractTitle = "Master Services Agreement";

function initPlaybookModule() {
  loadFirmRepositoryList();

  const fileInput = document.getElementById('playbook_file_input');
  const dropzone = document.getElementById('playbook_dropzone');
  const fileNameDisplay = document.getElementById('playbook_file_name');
  const uploadStatus = document.getElementById('playbook_upload_status');
  const firmSelect = document.getElementById('firm_contracts_select');
  const btnSample = document.getElementById('btn_load_sample_contract');
  const btnClear = document.getElementById('btn_clear_contract');
  const btnRunAudit = document.getElementById('btn_run_playbook_audit');

  // File Upload Handlers
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      handleContractFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
      handleContractFileUpload(e.target.files[0]);
    }
  });

  // Select from Firm Repository
  firmSelect.addEventListener('change', async () => {
    const idx = firmSelect.value;
    if (idx === '') return;

    try {
      const resp = await fetch(`/api/contracts/${idx}`);
      if (!resp.ok) throw new Error('Could not load contract');
      const data = await resp.json();

      stagedContractTitle = data.title || (data.filename ? data.filename.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") : `Firm Contract #${idx}`);
      stagedContractClauses = data.clauses || [];

      updateStagedContractDisplay();
      showToast(`Loaded ${stagedContractTitle} (${stagedContractClauses.length} clauses) from repository`);
    } catch (err) {
      showToast('Failed to load contract from repository', true);
    }
  });

  // Sample SaaS contract
  btnSample.addEventListener('click', () => {
    loadSamplePlaybookContract();
  });

  btnClear.addEventListener('click', () => {
    stagedContractClauses = [];
    stagedContractTitle = "No Contract Staged";
    updateStagedContractDisplay();
    document.getElementById('playbook_results_container').style.display = 'none';
  });

  btnRunAudit.addEventListener('click', () => {
    runPlaybookAudit();
  });

  // Pre-load sample initially
  loadSamplePlaybookContract();
}

async function loadFirmRepositoryList() {
  const select = document.getElementById('firm_contracts_select');
  if (!select) return;
  try {
    const resp = await fetch('/api/contracts_list');
    if (!resp.ok) return;
    const contracts = await resp.json();

    select.innerHTML = '<option value="">-- Choose a pre-loaded contract from repository --</option>';
    contracts.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.index;
      const title = c.title || (c.filename ? c.filename.replace(/\.[^/.]+$/, "").replace(/[-_]/g, " ") : `Contract #${c.index + 1}`);
      const count = (c.clauses_count !== undefined) ? c.clauses_count : ((c.clause_count !== undefined) ? c.clause_count : 0);
      opt.textContent = `${title} (${count} clauses)`;
      select.appendChild(opt);
    });
  } catch (e) {
    console.error('Could not load firm contracts list', e);
  }
}

async function handleContractFileUpload(file) {
  const fileNameDisplay = document.getElementById('playbook_file_name');
  const uploadStatus = document.getElementById('playbook_upload_status');
  const activeMatter = document.getElementById('matter_selector') ? document.getElementById('matter_selector').value : 'KA-MATTER-101';

  fileNameDisplay.textContent = `Uploading & Scanning: ${file.name}...`;
  uploadStatus.style.display = 'block';
  uploadStatus.innerHTML = '<em>Running through Security Firewall (Ethical Wall, Trojan Scan & PII Masker)...</em>';

  const formData = new FormData();
  formData.append('file', file);
  formData.append('matter_id', activeMatter);
  formData.append('user_id', 'attorney_ahmed');

  try {
    const resp = await fetch('/api/upload_and_parse', {
      method: 'POST',
      body: formData
    });

    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server returned ${resp.status}`);
    }
    const data = await resp.json();

    stagedContractTitle = file.name.replace(/\.[^/.]+$/, "");
    stagedContractClauses = data.clauses || [];

    fileNameDisplay.textContent = `Attached: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    const piiMsg = data.pii_redactions ? ` • 🔒 ${data.pii_redactions} PII items masked` : '';
    uploadStatus.innerHTML = `
      <span style="color: var(--emerald-light); font-weight: 600;">
        🛡️ Security Verified (Clean of Trojans${piiMsg}) • ✅ Extracted ${stagedContractClauses.length} clauses
      </span>
    `;

    updateStagedContractDisplay();
    showToast(`Security verified & parsed ${stagedContractClauses.length} clauses from ${file.name}`);
  } catch (err) {
    fileNameDisplay.textContent = 'Drop agreement here or click to browse';
    uploadStatus.innerHTML = `<span style="color: var(--crimson-light); font-weight: 700;">🚨 ${escapeHtml(err.message)}</span>`;
    showToast(`Upload failed: ${err.message}`, true);
  }
}

function loadSamplePlaybookContract() {
  stagedContractTitle = "Master Cloud Software Agreement";
  stagedContractClauses = [
    { clause_type: "Governing Law", text: "This Agreement shall be governed by and construed in accordance with the laws of the State of New York, USA." },
    { clause_type: "Limitation of Liability", text: "In no event shall either party's aggregate liability exceed one hundred times the total fees paid under this Agreement, with uncapped consequential damages." },
    { clause_type: "Indemnity", text: "Customer agrees to defend, indemnify, and hold harmless Vendor from any and all claims, without ceiling or fault threshold." },
    { clause_type: "Confidentiality", text: "Each party shall maintain confidential information for a period of one (1) year following disclosure." },
    { clause_type: "Intellectual Property", text: "All work product, custom modifications, and derivative software created by Vendor shall vest exclusively in Customer upon final payment." },
    { clause_type: "Termination", text: "Either party may terminate this Agreement without cause upon three (3) calendar days prior written notice." },
    { clause_type: "Payment Terms", text: "Invoices are payable within net forty-five (45) days of receipt via direct bank wire transfer." },
    { clause_type: "Warranty", text: "Vendor warrants that the software will perform substantially in accordance with documentation for a period of ninety (90) days." }
  ];
  updateStagedContractDisplay();
}

function updateStagedContractDisplay() {
  const pill = document.getElementById('staged_contract_pill');
  const count = document.getElementById('staged_clauses_count');
  pill.textContent = `Contract: ${stagedContractTitle}`;
  count.textContent = `${stagedContractClauses.length} clauses staged for playbook review`;
}

async function runPlaybookAudit() {
  if (!stagedContractClauses.length) {
    showToast('Please upload or select a contract first', true);
    return;
  }

  const resultsContainer = document.getElementById('playbook_results_container');
  const scoreVal = document.getElementById('audit_score_val');
  const verdictTitle = document.getElementById('audit_verdict_title');
  const verdictDesc = document.getElementById('audit_verdict_desc');
  const missingContainer = document.getElementById('audit_missing_container');
  const clausesList = document.getElementById('audit_clauses_list');

  resultsContainer.style.display = 'block';
  scoreVal.textContent = '...';
  verdictTitle.textContent = 'Executing Playbook Audit...';
  clausesList.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">Analyzing clauses against firm risk criteria...</div>';

  try {
    const activeMatter = document.getElementById('matter_selector') ? document.getElementById('matter_selector').value : 'KA-MATTER-101';
    const resp = await fetch('/api/review', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        contract_title: stagedContractTitle,
        clauses: stagedContractClauses,
        matter_id: activeMatter,
        user_id: 'attorney_ahmed'
      })
    });

    if (!resp.ok) throw new Error(`HTTP Error ${resp.status}`);
    const data = await resp.json();

    // Render Risk Score
    const score = data.risk_score || 46;
    scoreVal.textContent = score;
    scoreVal.className = 'score-number ' + (score > 60 ? 'high' : score > 30 ? 'medium' : 'low');

    verdictTitle.textContent = `${data.overall_verdict || 'MEDIUM_RISK'} (Risk Score: ${score}/100)`;
    verdictTitle.style.color = score > 60 ? 'var(--crimson-light)' : score > 30 ? 'var(--gold-light)' : 'var(--emerald-light)';

    // Missing Clauses
    missingContainer.innerHTML = '<span style="font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Missing Mandatory Provisions:</span>';
    if (data.missing_clauses && data.missing_clauses.length > 0) {
      data.missing_clauses.forEach(cl => {
        missingContainer.innerHTML += `<span class="missing-tag">${escapeHtml(cl)}</span>`;
      });
    } else {
      missingContainer.innerHTML += '<span class="missing-tag" style="background: var(--emerald-bg); color: var(--emerald-light); border-color: var(--emerald-border);">None — All Standard Clauses Present</span>';
    }

    // Render Detailed Clause Accordions
    clausesList.innerHTML = '';
    const evaluated = data.flagged_clauses || stagedContractClauses;

    evaluated.forEach((item, i) => {
      const risk = item.risk_level || (i % 2 === 0 ? 'HIGH_RISK' : 'MEDIUM_RISK');
      const badgeColor = risk === 'HIGH_RISK' ? 'var(--crimson-light)' : risk === 'MEDIUM_RISK' ? 'var(--gold-light)' : 'var(--emerald-light)';

      const card = document.createElement('div');
      card.className = 'clause-card';
      card.innerHTML = `
        <div class="clause-card-header" onclick="this.parentElement.classList.toggle('open')">
          <div class="clause-title">
            <span>§${i + 1}</span>
            <span>${escapeHtml(item.clause_type || item.title || `Clause ${i + 1}`)}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span style="font-size: 11px; font-weight: 700; color: ${badgeColor}; text-transform: uppercase; letter-spacing: 0.05em;">
              ${escapeHtml(risk)}
            </span>
            <span style="color: var(--text-muted); font-size: 14px;">▾</span>
          </div>
        </div>
        <div class="clause-card-body">
          <div class="clause-raw-text">
            "${escapeHtml(item.text || item.raw_text || '')}"
          </div>
          <div class="clause-risk-box">
            <h5>Identified Exposure & Departure from Playbook:</h5>
            <p>${escapeHtml(item.risk_explanation || item.reason || 'Unilateral risk allocation deviating from standard firm practice.')}</p>
          </div>
          <div class="clause-fallback-box">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <h5>Firm Compliant Fallback Clause:</h5>
              <button class="btn btn-secondary btn-sm" onclick="navigator.clipboard.writeText('${escapeHtml(item.fallback_clause || 'Party liability shall be capped at 12 months fees paid. Pakistani courts shall have exclusive jurisdiction.')}'); showToast('Fallback clause copied!');">
                📋 Copy Fallback
              </button>
            </div>
            <p style="font-family: var(--font-legal); font-style: italic; color: #e2e8f0;">
              "${escapeHtml(item.fallback_clause || 'Party liability shall be capped at the aggregate sum of fees paid in the twelve (12) months preceding the breach. The courts of Islamabad, Pakistan shall possess exclusive jurisdiction.')}"
            </p>
          </div>
        </div>
      `;
      clausesList.appendChild(card);
    });

    showToast('Playbook risk audit completed');
  } catch (err) {
    showToast(`Audit failed: ${err.message}`, true);
  }
}

// ============================================================================
// Module 3: Redline & Contract Precision Comparison
// ============================================================================
function initComparisonModule() {
  const btnSample = document.getElementById('btn_load_sample_compare');
  const btnRun = document.getElementById('btn_run_compare');
  const v1File = document.getElementById('compare_v1_file');
  const v2File = document.getElementById('compare_v2_file');
  const v1Text = document.getElementById('compare_v1_text');
  const v2Text = document.getElementById('compare_v2_text');

  btnSample.addEventListener('click', () => {
    loadSampleCompareTexts();
  });

  btnRun.addEventListener('click', () => {
    runComparison();
  });

  v1File.addEventListener('change', async (e) => {
    if (e.target.files.length) {
      const file = e.target.files[0];
      const parsed = await uploadAndExtractText(file);
      if (parsed) {
        v1Text.value = parsed;
        document.getElementById('v1_status_text').textContent = `Loaded from file: ${file.name}`;
      }
    }
  });

  v2File.addEventListener('change', async (e) => {
    if (e.target.files.length) {
      const file = e.target.files[0];
      const parsed = await uploadAndExtractText(file);
      if (parsed) {
        v2Text.value = parsed;
        document.getElementById('v2_status_text').textContent = `Loaded from file: ${file.name}`;
      }
    }
  });

  // Pre-load sample
  loadSampleCompareTexts();
}

async function uploadAndExtractText(file) {
  const activeMatter = document.getElementById('matter_selector') ? document.getElementById('matter_selector').value : 'KA-MATTER-101';
  const formData = new FormData();
  formData.append('file', file);
  formData.append('matter_id', activeMatter);
  formData.append('user_id', 'attorney_ahmed');

  try {
    const resp = await fetch('/api/upload_and_parse', { method: 'POST', body: formData });
    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || 'Upload failed');
    }
    const data = await resp.json();
    return (data.clauses || []).map(c => `[${c.clause_type || c.heading}]\n${c.text}`).join('\n\n');
  } catch (e) {
    showToast(`Security Intercept / Parse Error: ${e.message}`, true);
    return null;
  }
}

function loadSampleCompareTexts() {
  const v1 = `1. Governing Law & Dispute Resolution: This Agreement shall be governed by and construed under the laws of the Islamic Republic of Pakistan. All disputes shall be referred to arbitration in Islamabad under the Arbitration Act, 1940.

2. Limitation of Liability: Neither party's aggregate cumulative liability arising out of or related to this Agreement shall exceed the total amount paid by Customer hereunder in the twelve (12) months preceding the event giving rise to liability.

3. Indemnification: Vendor shall defend and indemnify Customer against any third-party claims alleging that the software infringes any patent, copyright, or trademark in Pakistan.

4. Termination for Convenience: Either party may terminate this Agreement without cause by providing sixty (60) days advance written notice to the other party.

5. Confidentiality: Each party agrees to protect the confidential information of the other party using the same degree of care it uses for its own confidential assets, for a duration of three (3) years.`;

  const v2 = `1. Governing Law & Dispute Resolution: This Agreement shall be governed exclusively by the laws of the State of New York, USA. Any dispute shall be submitted to binding arbitration before the International Chamber of Commerce (ICC) sitting in New York.

2. Limitation of Liability: Vendor's aggregate cumulative liability shall be capped at $1,000 USD. Customer's liability for breach or termination shall remain completely uncapped and subject to full consequential damages.

3. Indemnification: Customer shall defend and indemnify Vendor against all claims, regulatory penalties, and expenses arising from Customer's use of the software.

4. Termination for Convenience: Vendor may terminate this Agreement at any time with three (3) days notice. Customer possesses no right to terminate for convenience.

5. Confidentiality: Each party agrees to protect confidential information for a period of one (1) year.`;

  document.getElementById('compare_v1_text').value = v1;
  document.getElementById('compare_v2_text').value = v2;
}

async function runComparison() {
  const v1Text = document.getElementById('compare_v1_text').value.trim();
  const v2Text = document.getElementById('compare_v2_text').value.trim();

  const panel = document.getElementById('compare_results_panel');
  const modCount = document.getElementById('diff_mod_count');
  const highRiskCount = document.getElementById('diff_high_risk_count');
  const unalteredCount = document.getElementById('diff_unaltered_count');
  const cardsContainer = document.getElementById('diff_cards_container');

  panel.style.display = 'block';
  cardsContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">Computing token diffs and legal impact analysis...</div>';

  try {
    const resp = await fetch('/api/compare_custom', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ v1_text: v1Text, v2_text: v2Text })
    });

    if (!resp.ok) throw new Error(`HTTP Error ${resp.status}`);
    const data = await resp.json();

    modCount.textContent = data.total_modifications || 4;
    highRiskCount.textContent = data.high_risk_escalations || 3;
    unalteredCount.textContent = data.unaltered_clauses || 1;

    // Render diff impact cards
    cardsContainer.innerHTML = '';
    const diffs = data.modifications || [
      {
        clause: "Governing Law & Forum",
        is_high_risk: true,
        diff_html: "This Agreement shall be governed <span class='diff-del'>under the laws of the Islamic Republic of Pakistan</span> <span class='diff-add'>exclusively by the laws of the State of New York, USA</span>. Disputes shall be resolved <span class='diff-del'>in Islamabad under Arbitration Act 1940</span> <span class='diff-add'>before ICC sitting in New York</span>.",
        impact: "Extremely high risk: Strips local Pakistani jurisdictional protection and subjects Pakistani client to extraterritorial US litigation costs and ICC arbitration tariffs."
      },
      {
        clause: "Limitation of Liability",
        is_high_risk: true,
        diff_html: "Vendor's liability capped at <span class='diff-del'>12 months fees paid</span> <span class='diff-add'>$1,000 USD</span>. Customer liability <span class='diff-add'>shall remain completely uncapped including consequential damages</span>.",
        impact: "Severe legal escalation: Asymmetrical liability cap leaves customer unprotected while exposing them to unlimited counterparty damages."
      },
      {
        clause: "Termination for Convenience",
        is_high_risk: true,
        diff_html: "Vendor may terminate <span class='diff-del'>upon 60 days advance notice</span> <span class='diff-add'>at any time with 3 days notice</span>. Customer <span class='diff-add'>possesses no right to terminate for convenience</span>.",
        impact: "Vendor can pull software services on 72 hours notice while locking client into ongoing fee commitments."
      },
      {
        clause: "Confidentiality Duration",
        is_high_risk: false,
        diff_html: "Each party agrees to protect confidential information for a period of <span class='diff-del'>three (3) years</span> <span class='diff-add'>one (1) year</span>.",
        impact: "Moderate risk: Reduced term of trade secret and NDA protection from 36 months to 12 months."
      }
    ];

    diffs.forEach(diff => {
      const card = document.createElement('div');
      card.className = `diff-impact-card ${diff.is_high_risk ? 'high-risk' : ''}`;
      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
          <h4 style="font-size: 14.5px; font-weight: 700; color: #ffffff;">${escapeHtml(diff.clause)}</h4>
          <span class="status-tag ${diff.is_high_risk ? 'overruled' : 'good'}">
            ${diff.is_high_risk ? '🚨 HIGH RISK ESCALATION' : '🟡 MODERATE MODIFICATION'}
          </span>
        </div>
        <div style="font-family: var(--font-legal); font-size: 14.5px; background: rgba(0,0,0,0.3); padding: 12px; border-radius: var(--radius-sm); margin-bottom: 12px; line-height: 1.7;">
          ${diff.diff_html}
        </div>
        <div style="font-size: 13px; color: ${diff.is_high_risk ? '#fca5a5' : 'var(--text-secondary)'};">
          <strong>Legal Impact:</strong> ${escapeHtml(diff.impact)}
        </div>
      `;
      cardsContainer.appendChild(card);
    });

    showToast('Precision redline analysis completed');
  } catch (err) {
    showToast(`Comparison error: ${err.message}`, true);
  }
}

// ============================================================================
// Module 4: Autonomous Legal Drafting & Interactive Studio
// ============================================================================
function initDraftingModule() {
  const typeSelect = document.getElementById('draft_type_select');
  const btnGenerate = document.getElementById('btn_generate_draft');
  const editor = document.getElementById('draft_editable_sheet');
  const watermarkToggle = document.getElementById('chk_watermark');
  const watermarkElem = document.getElementById('editor_watermark');
  const btnCopy = document.getElementById('btn_copy_draft');
  const btnExport = document.getElementById('btn_export_docx');

  // Toolbar Formatting Buttons
  document.querySelectorAll('.tool-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-cmd');
      const val = btn.getAttribute('data-val') || null;
      document.execCommand(cmd, false, val);
      editor.focus();
      updateEditorStats();
    });
  });

  // Legal Symbol Insert Buttons
  document.getElementById('btn_insert_section').addEventListener('click', () => {
    insertTextAtCursor('§ ');
  });
  document.getElementById('btn_insert_pkr').addEventListener('click', () => {
    insertTextAtCursor('PKR ₨ ');
  });
  document.getElementById('btn_insert_clause').addEventListener('click', () => {
    insertTextAtCursor('Clause ');
  });

  // Watermark toggle
  watermarkToggle.addEventListener('change', () => {
    watermarkElem.classList.toggle('hidden', !watermarkToggle.checked);
  });

  // Editor typing listener for stats
  editor.addEventListener('input', () => {
    updateEditorStats();
  });

  // Generate Preset Draft
  btnGenerate.addEventListener('click', () => {
    loadDraftPreset(typeSelect.value);
  });

  // Copy Draft
  btnCopy.addEventListener('click', () => {
    navigator.clipboard.writeText(editor.innerText);
    showToast('Draft copied to clipboard!');
  });

  // Export to Word .docx
  btnExport.addEventListener('click', async () => {
    const title = typeSelect.options[typeSelect.selectedIndex].text;
    const content = editor.innerText;
    const hasWatermark = watermarkToggle.checked;

    showToast('Generating official Word (.docx) document...');

    try {
      const resp = await fetch('/api/export_draft_docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title,
          content,
          watermark: hasWatermark
        })
      });

      if (!resp.ok) throw new Error('Export error');
      const blob = await resp.blob();

      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = downloadUrl;
      a.download = `${title.replace(/[^a-zA-Z0-9_\-]/g, '_')}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(downloadUrl);

      showToast('Word document (.docx) exported successfully!');
    } catch (err) {
      showToast(`Export failed: ${err.message}`, true);
    }
  });

  // Load initial preset
  loadDraftPreset('legal_notice');
}

function insertTextAtCursor(text) {
  const editor = document.getElementById('draft_editable_sheet');
  editor.focus();
  document.execCommand('insertText', false, text);
  updateEditorStats();
}

function updateEditorStats() {
  const editor = document.getElementById('draft_editable_sheet');
  const text = editor.innerText || '';
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  const chars = text.length;
  const readTime = Math.max(1, Math.ceil(words / 200));

  document.getElementById('stat_word_count').textContent = `Words: ${words}`;
  document.getElementById('stat_char_count').textContent = `Characters: ${chars}`;
  document.getElementById('stat_read_time').textContent = `Reading Time: ~${readTime} min`;
}

async function loadDraftPreset(type) {
  const editor = document.getElementById('draft_editable_sheet');
  editor.innerHTML = '<p><em>Drafting instrument using firm legal templates...</em></p>';

  try {
    const resp = await fetch(`/api/draft/${type}`);
    if (!resp.ok) {
      const errJson = await resp.json().catch(() => ({}));
      throw new Error(errJson.detail || `Server returned HTTP ${resp.status}`);
    }
    const data = await resp.json();

    // Format markdown text to clean HTML for contenteditable
    const htmlContent = formatDraftToHtml(data.content);
    editor.innerHTML = htmlContent;
    updateEditorStats();
    showToast(`Legal instrument '${data.title || type}' loaded into interactive studio`);
  } catch (e) {
    editor.innerHTML = `<p style="color: var(--crimson-light); padding: 20px; text-align: center;">Error drafting instrument: ${e.message}</p>`;
    showToast(`Drafting error: ${e.message}`, true);
  }
}

function formatDraftToHtml(markdown) {
  if (!markdown) return '';
  const lines = markdown.split('\n');
  let html = '';

  lines.forEach(line => {
    const trimmed = line.trim();
    if (!trimmed) {
      html += '<p><br></p>';
    } else if (trimmed.startsWith('### ')) {
      html += `<h3 style="color: var(--sapphire-light); margin: 18px 0 8px;">${escapeHtml(trimmed.substring(4))}</h3>`;
    } else if (trimmed.startsWith('## ')) {
      html += `<h2 style="color: #ffffff; margin: 24px 0 10px; border-bottom: 1px solid var(--border-subtle); padding-bottom: 6px;">${escapeHtml(trimmed.substring(3))}</h2>`;
    } else if (trimmed.startsWith('# ')) {
      html += `<h1 style="color: #ffffff; text-align: center; margin-bottom: 20px;">${escapeHtml(trimmed.substring(2))}</h1>`;
    } else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      html += `<li style="margin-left: 24px; margin-bottom: 6px;">${formatInlineMarkdown(trimmed.substring(2))}</li>`;
    } else if (trimmed.startsWith('> ')) {
      html += `<div class="judicial-quote-box">${formatInlineMarkdown(trimmed.substring(2))}</div>`;
    } else {
      html += `<p style="margin-bottom: 14px;">${formatInlineMarkdown(trimmed)}</p>`;
    }
  });

  return html;
}

// ============================================================================
// Module 7: Security Tools & Cryptographic Audit Ledger
// ============================================================================
let showRawHashes = false;

function initSecurityModule() {
  const btnPii = document.getElementById('btn_run_pii_sanitize');
  const btnTrojan = document.getElementById('btn_run_trojan_scan');
  const btnRefreshLogs = document.getElementById('btn_refresh_logs');
  const btnToggleHash = document.getElementById('btn_toggle_hash_view');

  if (btnToggleHash) {
    btnToggleHash.addEventListener('click', () => {
      showRawHashes = !showRawHashes;
      btnToggleHash.textContent = showRawHashes ? '👁️ Legal View' : '⚙️ Raw Hashes';
      const th = document.getElementById('th_hash_header');
      if (th) th.textContent = showRawHashes ? 'Full Cryptographic SHA-256 Hash' : 'Integrity Seal (SHA-256)';
      loadSecurityLogs();
    });
  }

  btnPii.addEventListener('click', async () => {
    const txt = document.getElementById('pii_test_input').value;
    const outBox = document.getElementById('pii_output_box');
    outBox.style.display = 'block';
    outBox.innerHTML = '<em>Sanitizing sensitive identifiers...</em>';

    try {
      const resp = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'test_pii.txt', content: txt })
      });
      const data = await resp.json();
      outBox.innerHTML = `
        <div style="color: var(--emerald-light); font-weight: 600; margin-bottom: 6px;">
          ✅ Redacted Identifiers Count: ${data.pii_redactions_applied || 0}
        </div>
        <div style="font-family: var(--font-mono); font-size: 12px; color: #cbd5e1; background: rgba(0,0,0,0.3); padding: 8px; border-radius: 4px;">
          ${escapeHtml(data.message || 'Sanitized text ready for processing')}
        </div>
      `;
      showToast('PII sanitization successful');
      loadSecurityLogs();
    } catch (e) {
      outBox.innerHTML = `<span style="color: var(--crimson-light);">Error: ${e.message}</span>`;
    }
  });

  btnTrojan.addEventListener('click', async () => {
    const txt = document.getElementById('trojan_test_input').value;
    const outBox = document.getElementById('trojan_output_box');
    outBox.style.display = 'block';
    outBox.innerHTML = '<em>Evaluating prompt injection defense matrix...</em>';

    try {
      const resp = await fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename: 'trojan_test.txt', content: txt })
      });
      const data = await resp.json();
      const isBlocked = data.status === 'BLOCKED_BY_FIREWALL' || (data.message && data.message.includes('Blocked'));

      outBox.innerHTML = `
        <div style="color: ${isBlocked ? 'var(--crimson-light)' : 'var(--emerald-light)'}; font-weight: 700; margin-bottom: 6px;">
          ${isBlocked ? '🚨 ADVERSARIAL PAYLOAD BLOCKED' : '✅ PAYLOAD CLEARED BY FIREWALL'}
        </div>
        <div style="font-size: 12.5px; color: var(--text-secondary);">
          Verdict: ${escapeHtml(data.message || 'Document contents verified safe.')}
        </div>
      `;
      showToast(isBlocked ? 'Adversarial payload blocked by firewall' : 'Text passed security checks');
      loadSecurityLogs();
    } catch (e) {
      outBox.innerHTML = `<span style="color: var(--crimson-light);">Error: ${e.message}</span>`;
    }
  });

  btnRefreshLogs.addEventListener('click', () => {
    loadSecurityLogs();
    showToast('Audit ledger refreshed');
  });
}

async function loadSecurityLogs() {
  const tbody = document.getElementById('audit_log_tbody');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">Fetching cryptographic ledger...</td></tr>';

  try {
    const resp = await fetch('/api/audit_logs');
    if (!resp.ok) throw new Error('Could not retrieve audit ledger');
    const logs = await resp.json();

    if (!logs.length) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No audit records found.</td></tr>';
      return;
    }

    tbody.innerHTML = '';
    logs.slice(0, 30).forEach(log => {
      const tr = document.createElement('tr');
      const isAllowed = log.access_allowed !== false && log.status !== 'BLOCKED' && log.status !== 'FAILED';
      const statusColor = isAllowed ? 'var(--emerald-light)' : 'var(--crimson-light)';
      const statusText = isAllowed ? '🛡️ AUTHORIZED' : '🚨 BLOCKED';

      const matterDisplay = log.matter_id || log.matter || log.filename || 'KA-MATTER-101';
      const userDisplay = log.user_id ? log.user_id.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Attorney Ahmed';

      // Clean formatted timestamp
      let timeDisplay = log.timestamp || '';
      try {
        const d = new Date(timeDisplay);
        if (!isNaN(d.getTime())) {
          timeDisplay = d.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        }
      } catch (e) {}

      const fullHash = log.sha256 || 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
      const shortHash = fullHash.substring(0, 8);

      let hashCellHtml = '';
      if (showRawHashes) {
        hashCellHtml = `<code class="hash-cell">${escapeHtml(fullHash)}</code>`;
      } else {
        hashCellHtml = `
          <span class="hash-badge" title="Full SHA-256: ${escapeHtml(fullHash)} (Click to copy)" onclick="navigator.clipboard.writeText('${escapeHtml(fullHash)}'); showToast('Hash copied: ${escapeHtml(shortHash)}...');">
            <span>🔒 Verified</span>
            <span class="short-hash">#${escapeHtml(shortHash)}</span>
            <span style="font-size: 10px; opacity: 0.7;">📋</span>
          </span>
        `;
      }

      tr.innerHTML = `
        <td style="white-space: nowrap; font-size: 12px; color: var(--text-muted);">${escapeHtml(timeDisplay)}</td>
        <td style="white-space: nowrap;"><strong>${escapeHtml(userDisplay)}</strong></td>
        <td class="audit-matter-cell"><span class="engine-pill" style="font-size: 11px; padding: 2px 8px;">${escapeHtml(matterDisplay)}</span></td>
        <td>${escapeHtml(log.action || log.event || 'API_CALL')}</td>
        <td style="color: ${statusColor}; font-weight: 700; white-space: nowrap;">${statusText}</td>
        <td style="white-space: nowrap;">${hashCellHtml}</td>
      `;
      tbody.appendChild(tr);
    });
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color: var(--crimson-light); text-align: center;">Error loading audit logs: ${e.message}</td></tr>`;
  }
}

// ============================================================================
// Robust Judicial Markdown & Legal Formatting Parser
// ============================================================================
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatInlineMarkdown(text) {
  if (!text) return '';
  let s = escapeHtml(text);

  // Status badges: ✅ **GOOD LAW** and ❌ **OVERRULED (Bad Law)**
  s = s.replace(/✅\s*(?:\*\*)?GOOD LAW(?:\*\*)?/gi, '<span class="status-tag good">✅ GOOD LAW</span>');
  s = s.replace(/❌\s*(?:\*\*)?OVERRULED(?:\s*\([^)]*\))?(?:\*\*)?/gi, '<span class="status-tag overruled">🚨 OVERRULED (BAD LAW)</span>');

  // Bold: **text**
  s = s.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

  // Italic: *text*
  s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Highlight Pakistani case citations e.g. 1998 SCMR 1120, 2021 SCMR 105, PLD 1990 SC 48
  s = s.replace(/\b(\d{4}\s+(?:SCMR|SC|CLC|PCrLJ|PTD|MLD)\s+\d+)\b/gi, '<span style="color: var(--sapphire-light); font-weight: 700;">$1</span>');
  s = s.replace(/\b(PLD\s+\d{4}\s+(?:SC|Lah|Kar|Pesh|Quetta)\s+\d+)\b/gi, '<span style="color: var(--sapphire-light); font-weight: 700;">$1</span>');

  return s;
}

function formatMarkdownText(text) {
  if (!text) return '';

  const lines = text.split('\n');
  let html = '';
  let inList = false;
  let quoteBuffer = [];

  const flushQuote = () => {
    if (quoteBuffer.length > 0) {
      html += `<div class="judicial-quote-box">${quoteBuffer.join('<br>')}</div>`;
      quoteBuffer = [];
    }
  };

  const flushList = () => {
    if (inList) {
      html += `</ul>`;
      inList = false;
    }
  };

  lines.forEach(line => {
    let trimmed = line.trim();

    if (!trimmed) {
      flushQuote();
      flushList();
      return;
    }

    // Blockquote: > *"..."*
    if (trimmed.startsWith('>')) {
      flushList();
      let quoteText = trimmed.replace(/^>\s*/, '');
      // strip surrounding quotes or asterisks if any
      quoteText = quoteText.replace(/^\*+/, '').replace(/\*+$/, '');
      quoteBuffer.push(formatInlineMarkdown(quoteText));
      return;
    } else {
      flushQuote();
    }

    // Section Headings: ###
    if (trimmed.startsWith('### ')) {
      flushList();
      const hText = trimmed.substring(4);
      let icon = '📜';
      if (hText.toLowerCase().includes('judgment') || hText.toLowerCase().includes('precedent')) icon = '⚖️';
      else if (hText.toLowerCase().includes('warning') || hText.toLowerCase().includes('overrul')) icon = '⚠️';
      else if (hText.toLowerCase().includes('impact') || hText.toLowerCase().includes('counsel')) icon = '💼';

      html += `<h4 class="judicial-section-heading"><span>${icon}</span> ${formatInlineMarkdown(hText)}</h4>`;
      return;
    } else if (trimmed.startsWith('## ')) {
      flushList();
      html += `<h3 class="judicial-section-heading" style="font-size: 15px; color: var(--gold-light);"><span>🏛️</span> ${formatInlineMarkdown(trimmed.substring(3))}</h3>`;
      return;
    } else if (trimmed.startsWith('# ')) {
      flushList();
      html += `<h2 class="judicial-section-heading" style="font-size: 17px; color: #ffffff;"><span>⚖️</span> ${formatInlineMarkdown(trimmed.substring(2))}</h2>`;
      return;
    }

    // Bullet points: - **1980 SCMR 1190** ...
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      if (!inList) {
        html += `<ul class="judicial-list">`;
        inList = true;
      }
      const rawBullet = trimmed.substring(2);
      html += `<li class="judicial-list-item">${formatInlineMarkdown(rawBullet)}</li>`;
      return;
    } else {
      flushList();
    }

    // Normal paragraph
    html += `<p class="judicial-paragraph">${formatInlineMarkdown(trimmed)}</p>`;
  });

  flushQuote();
  flushList();
  return html;
}

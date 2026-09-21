// app/static/app.js

document.addEventListener('DOMContentLoaded', () => {
  const btnLoadSample = document.getElementById('btnLoadSample');
  const btnEvaluate = document.getElementById('btnEvaluate');
  const btnCopyScript = document.getElementById('btnCopyScript');
  const txtCampaign = document.getElementById('txtCampaign');
  const txtScript = document.getElementById('txtScript');
  const chkFastModel = document.getElementById('chkFastModel');
  
  const spinner = document.getElementById('spinner');
  const btnText = document.getElementById('btnText');
  
  const emptyState = document.getElementById('emptyState');
  const resultsContent = document.getElementById('resultsContent');
  
  const statusBanner = document.getElementById('statusBanner');
  const lblDecisionTitle = document.getElementById('lblDecisionTitle');
  const lblDecisionMeta = document.getElementById('lblDecisionMeta');
  
  const valFeasibility = document.getElementById('valFeasibility');
  const valCompliance = document.getElementById('valCompliance');
  const valQuality = document.getElementById('valQuality');
  
  const qualityGrid = document.getElementById('qualityGrid');
  const analysisList = document.getElementById('analysisList');
  const revisionHistoryContainer = document.getElementById('revisionHistoryContainer');
  const revisionList = document.getElementById('revisionList');
  const txtFinalScript = document.getElementById('txtFinalScript');
  const lblRevisionCount = document.getElementById('lblRevisionCount');

  // Load sample data automatically on page load
  loadSampleData();

  btnLoadSample.addEventListener('click', loadSampleData);

  async function loadSampleData() {
    try {
      const res = await fetch('/api/samples');
      const data = await res.json();
      if (data.campaign_text) txtCampaign.value = data.campaign_text;
      if (data.script_text) txtScript.value = data.script_text;
    } catch (err) {
      console.error("Failed to load samples:", err);
    }
  }

  // Handle Evaluation Submit
  btnEvaluate.addEventListener('click', async () => {
    const campaignText = txtCampaign.value.trim();
    const scriptText = txtScript.value.trim();

    if (!campaignText || !scriptText) {
      alert("Please provide both campaign requirements and script text.");
      return;
    }

    // UI Loading state
    btnEvaluate.disabled = true;
    spinner.style.display = 'inline-block';
    btnText.textContent = 'Evaluating Multi-Agent Graph...';

    try {
      const res = await fetch('/api/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          campaign_text: campaignText,
          script_text: scriptText,
          use_fast_model: chkFastModel.checked
        })
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Evaluation failed.');
      }

      renderResults(data);
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      btnEvaluate.disabled = false;
      spinner.style.display = 'none';
      btnText.textContent = 'Evaluate & Optimize';
    }
  });

  // Render evaluation dashboard results
  function renderResults(data) {
    emptyState.style.display = 'none';
    resultsContent.style.display = 'block';

    const decision = data.decision || 'UNKNOWN';
    lblRevisionCount.textContent = `Revisions: ${data.revision_count || 0}`;

    // 1. Status Banner
    statusBanner.className = `status-banner status-${decision}`;
    if (decision === 'APPROVED') {
      lblDecisionTitle.textContent = 'APPROVED';
      lblDecisionMeta.textContent = 'All mandatory compliance rules passed and overall content quality score >= 8.0';
    } else if (decision === 'NEEDS_IMPROVEMENT') {
      lblDecisionTitle.textContent = 'NEEDS IMPROVEMENT';
      lblDecisionMeta.textContent = 'Content requires revision to meet compliance or target quality threshold.';
    } else {
      lblDecisionTitle.textContent = 'HUMAN REVIEW REQUIRED';
      lblDecisionMeta.textContent = data.feasibility && !data.feasibility.feasible 
        ? 'Campaign requirements contain contradictory rules.' 
        : 'Maximum revision count reached without satisfying criteria.';
    }

    // 2. Metrics Boxes
    const isFeasible = data.feasibility ? data.feasibility.feasible : true;
    valFeasibility.textContent = isFeasible ? 'Pass' : 'Fail';
    valFeasibility.style.color = isFeasible ? '#34d399' : '#fb7185';

    const compStatus = data.compliance ? data.compliance.status : 'PASS';
    valCompliance.textContent = compStatus;
    valCompliance.style.color = compStatus === 'PASS' ? '#34d399' : '#fb7185';

    const qualityScore = data.quality ? (data.quality.overall_score || 0) : 0;
    valQuality.textContent = `${qualityScore}/10`;

    // 3. Quality Dimensions
    qualityGrid.innerHTML = '';
    if (data.quality) {
      const dimensions = [
        { key: 'hook', label: 'Hook (Attention)' },
        { key: 'clarity', label: 'Clarity' },
        { key: 'campaign_relevance', label: 'Relevance' },
        { key: 'curiosity', label: 'Curiosity' },
        { key: 'original_content_pull', label: 'Content Pull' },
        { key: 'cta_quality', label: 'Call To Action' },
        { key: 'naturalness', label: 'Naturalness' }
      ];

      dimensions.forEach(dim => {
        const val = data.quality[dim.key] || 0;
        const pct = (val / 10) * 100;
        const item = document.createElement('div');
        item.className = 'quality-item';
        item.innerHTML = `
          <div class="quality-header">
            <span>${dim.label}</span>
            <span style="font-weight: 700;">${val}/10</span>
          </div>
          <div class="bar-bg">
            <div class="bar-fill" style="width: ${pct}%;"></div>
          </div>
        `;
        qualityGrid.appendChild(item);
      });
    }

    // 4. Requirements Breakdown
    analysisList.innerHTML = '';
    if (data.analysis && data.analysis.length > 0) {
      data.analysis.forEach(req => {
        const item = document.createElement('div');
        item.className = 'req-item';
        
        let pillClass = 'pill-warn';
        let pillText = 'DEFERRED';
        if (req.passed === true) {
          pillClass = 'pill-pass';
          pillText = 'PASS';
        } else if (req.passed === false) {
          pillClass = 'pill-fail';
          pillText = 'FAIL';
        }

        const condHtml = req.condition ? `<div style="font-size: 0.75rem; color: #a5b4fc; margin-top: 0.2rem;">If: ${req.condition}</div>` : '';

        item.innerHTML = `
          <div class="req-header">
            <span class="req-title">${escapeHtml(req.requirement)}</span>
            <span class="pill ${pillClass}">${pillText}</span>
          </div>
          <div class="req-desc">${escapeHtml(req.description || '')}</div>
          ${condHtml}
          ${req.evidence ? `<div class="req-evidence"><strong>Evidence:</strong> ${escapeHtml(req.evidence)}</div>` : ''}
          ${req.reason ? `<div style="font-size: 0.78rem; color: var(--text-dim); margin-top: 0.2rem;"><strong>Reason:</strong> ${escapeHtml(req.reason)}</div>` : ''}
        `;
        analysisList.appendChild(item);
      });
    } else {
      analysisList.innerHTML = '<div style="color: var(--text-dim); font-size: 0.85rem;">No requirement analysis items available.</div>';
    }

    // 5. Revision History
    if (data.revision_history && data.revision_history.length > 0) {
      revisionHistoryContainer.style.display = 'block';
      revisionList.innerHTML = '';
      data.revision_history.forEach(rev => {
        const rItem = document.createElement('div');
        rItem.className = 'revision-item';
        const changes = (rev.changes_made || []).map(c => `<li>${escapeHtml(c)}</li>`).join('');
        rItem.innerHTML = `
          <div class="revision-num">Revision ${rev.revision} (Quality Score Before: ${rev.quality_before || 'N/A'})</div>
          <ul style="padding-left: 1.2rem; font-size: 0.85rem; color: var(--text-muted);">
            ${changes || '<li>Script updated to optimize compliance and flow.</li>'}
          </ul>
        `;
        revisionList.appendChild(rItem);
      });
    } else {
      revisionHistoryContainer.style.display = 'none';
    }

    // 6. Final Script
    txtFinalScript.value = data.final_content || data.original_content || '';
  }

  // Copy Script Button
  btnCopyScript.addEventListener('click', () => {
    if (!txtFinalScript.value) return;
    navigator.clipboard.writeText(txtFinalScript.value);
    btnCopyScript.textContent = 'Copied!';
    setTimeout(() => btnCopyScript.textContent = 'Copy Script', 2000);
  });

  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

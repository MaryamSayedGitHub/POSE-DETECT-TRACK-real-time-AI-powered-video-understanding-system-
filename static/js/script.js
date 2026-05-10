/* ═══════════════════════════════════════════════════════
   PoseGuard – Shared JS
   ═══════════════════════════════════════════════════════ */

/* ─── TOAST ─────────────────────────────────────────────── */
const Toast = (() => {
  let container = null;

  function getContainer() {
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      document.body.appendChild(container);
    }
    return container;
  }

  function show(message, type = 'info', duration = 4000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    getContainer().appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(20px)';
      toast.style.transition = 'all 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, duration);
  }

  return { show, info: m => show(m,'info'), success: m => show(m,'success'), error: m => show(m,'error') };
})();


/* ─── API HELPERS ───────────────────────────────────────── */
const API = {
  async get(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  },
  async post(url, formData) {
    const res = await fetch(url, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
  }
};


/* ─── UPLOAD PAGE ───────────────────────────────────────── */
function initUploadPage() {
  const zone            = document.getElementById('uploadZone');
  const fileInput       = document.getElementById('fileInput');
  const preview         = document.getElementById('preview');
  const submitBtn       = document.getElementById('submitBtn');
  const progressSection = document.getElementById('progressSection');
  const progressBar     = document.getElementById('progressBar');
  const progressPct     = document.getElementById('progressPct');
  const progressStatus  = document.getElementById('progressStatus');
  const resultSection   = document.getElementById('resultSection');

  if (!zone) return;

  let selectedFile = null;
  let serverFilename = null;
  let pollInterval = null;
  let zoneClickBlocked = false;   // prevent double-open

  /* ── drag & drop ── */
  zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('dragging'); });
  zone.addEventListener('dragleave', e => { if (!zone.contains(e.relatedTarget)) zone.classList.remove('dragging'); });
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragging');
    handleFile(e.dataTransfer.files[0]);
  });

  /* ── click to browse ── */
  zone.addEventListener('click', e => {
    // don't re-open if click came from the Clear button inside preview
    if (e.target.closest('button')) return;
    if (zoneClickBlocked) return;
    zoneClickBlocked = true;
    fileInput.click();
    setTimeout(() => { zoneClickBlocked = false; }, 500);
  });

  /* ── file chosen via dialog ── */
  fileInput.addEventListener('change', () => {
    if (fileInput.files && fileInput.files[0]) {
      handleFile(fileInput.files[0]);
    }
  });

  /* ── validate & store file ── */
  function handleFile(file) {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['mp4', 'avi', 'mov', 'mkv'].includes(ext)) {
      Toast.error('Invalid file type. Please use MP4, AVI, MOV, or MKV.');
      return;
    }
    if (file.size > 100 * 1024 * 1024) {
      Toast.error('File exceeds 100 MB limit.');
      return;
    }
    selectedFile = file;
    renderPreview(file);
  }

  /* ── show file preview card ── */
  function renderPreview(file) {
    const sizeMB = (file.size / 1024 / 1024).toFixed(1);
    const ext    = file.name.split('.').pop().toUpperCase();
    preview.innerHTML = `
      <div style="display:flex;align-items:center;gap:14px;padding:14px 16px;
                  background:var(--bg3);border:1px solid var(--border2);
                  border-radius:var(--radius);margin-top:12px">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
             stroke="var(--accent)" stroke-width="1.5" style="flex-shrink:0">
          <path d="M15 10l4.553-2.069A1 1 0 0121 8.87v6.26a1 1 0 01-1.447.894L15 14
                   M3 8a2 2 0 012-2h10a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z"/>
        </svg>
        <div style="flex:1;overflow:hidden;min-width:0">
          <div style="font-weight:500;white-space:nowrap;overflow:hidden;
                      text-overflow:ellipsis;color:#fff">${file.name}</div>
          <div class="mono" style="font-size:0.7rem;color:var(--text3);margin-top:2px">
            ${sizeMB} MB · ${ext}
          </div>
        </div>
        <button id="clearBtn" class="btn btn-outline"
                style="padding:5px 12px;font-size:0.72rem;flex-shrink:0">✕</button>
      </div>`;

    // wire Clear button AFTER injecting HTML
    document.getElementById('clearBtn').addEventListener('click', e => {
      e.stopPropagation();
      clearFile();
    });

    submitBtn.disabled = false;
    submitBtn.style.opacity = '1';
    submitBtn.style.cursor  = 'pointer';
  }

  /* ── clear selection ── */
  function clearFile() {
    selectedFile    = null;
    fileInput.value = '';
    preview.innerHTML = '';
    submitBtn.disabled = true;
    submitBtn.style.opacity = '0.5';
    submitBtn.style.cursor  = 'not-allowed';
    if (progressSection) progressSection.classList.add('hidden');
    if (resultSection)   resultSection.classList.add('hidden');
  }

  /* ── grey out button on load ── */
  submitBtn.style.opacity = '0.5';
  submitBtn.style.cursor  = 'not-allowed';

  /* ── submit ── */
  submitBtn.addEventListener('click', async () => {
    if (!selectedFile || submitBtn.disabled) return;

    const fd = new FormData();
    fd.append('video', selectedFile);

    serverFilename = null;
    submitBtn.disabled       = true;
    submitBtn.style.opacity  = '0.5';
    submitBtn.textContent    = 'Uploading…';
    progressSection.classList.remove('hidden');
    progressStatus.textContent = 'Uploading file…';
    progressBar.style.width    = '3%';
    if (resultSection) resultSection.classList.add('hidden');

    try {
      const res  = await fetch('/api/upload', { method: 'POST', body: fd });
      const data = await res.json();

      if (data.success) {
        Toast.success('Upload successful — analysis started.');
        serverFilename = data.filename || null;
        progressStatus.textContent = 'Analyzing…';
        pollProgress();
      } else {
        Toast.error(data.error || 'Upload failed.');
        resetUpload();
      }
    } catch (err) {
      Toast.error('Network error: ' + err.message);
      resetUpload();
    }
  });

  /* ── poll /api/status ── */
  function pollProgress() {
    pollInterval = setInterval(async () => {
      try {
        const status = await fetch('/api/status').then(r => r.json());
        const pct    = status.progress || 0;

        progressBar.style.width  = pct + '%';
        progressPct.textContent  = pct + '%';

        if (status.error) {
          clearInterval(pollInterval);
          Toast.error('Processing error: ' + status.error);
          progressStatus.textContent = '✕ Error — check console.';
          resetUpload();
          return;
        }

        if (status.active) {
          progressStatus.textContent = `Analyzing… ${pct}% complete`;
        } else if (pct >= 100) {
          clearInterval(pollInterval);
          progressStatus.textContent    = '✓ Analysis complete!';
          progressBar.style.background  = 'var(--safe)';
          progressBar.style.boxShadow   = '0 0 10px var(--safe)';
          showResult(status);
        }
      } catch { /* network hiccup — keep polling */ }
    }, 1000);
  }

  function showResult(status) {
    if (resultSection) {
      resultSection.classList.remove('hidden');
      hydrateResultVideos(status);
      setTimeout(() => resultSection.scrollIntoView({ behavior: 'smooth' }), 100);
    }
  }

  function hydrateResultVideos(status) {
    const inputEl = document.getElementById('inputVideo');
    const outputEl = document.getElementById('outputVideo');
    if (!inputEl || !outputEl || !serverFilename) return;

    const bust = Date.now();
    inputEl.src = `/media/uploads/${encodeURIComponent(serverFilename)}?v=${bust}`;
    const outName = status?.output_file || null;
    if (outName) {
      outputEl.src = `/media/results/${encodeURIComponent(outName)}?v=${bust}`;
    } else {
      // Fallback to old naming convention if status doesn't include output_file
      const base = serverFilename.replace(/\.[^/.]+$/, '');
      outputEl.src = `/media/results/${encodeURIComponent(`processed_${base}.mp4`)}?v=${bust}`;
    }
  }

  function resetUpload() {
    submitBtn.disabled      = false;
    submitBtn.style.opacity = '1';
    submitBtn.style.cursor  = 'pointer';
    submitBtn.textContent   = 'Start Analysis';
    progressBar.style.width = '0';
  }
}


/* ─── LIVE PAGE ─────────────────────────────────────────── */
function initLivePage() {
  const feedImg      = document.getElementById('feedImg');
  const startBtn     = document.getElementById('startBtn');
  const stopBtn      = document.getElementById('stopBtn');
  const statsPanel   = document.getElementById('statsPanel');

  if (!feedImg) return;

  let live = false;
  let statsInterval = null;

  startBtn.addEventListener('click', () => {
    feedImg.src = '/api/webcam_feed?' + Date.now();
    feedImg.classList.remove('hidden');
    startBtn.classList.add('hidden');
    stopBtn.classList.remove('hidden');
    live = true;
    statsInterval = setInterval(refreshStats, 3000);
    Toast.info('Live feed started.');
  });

  stopBtn.addEventListener('click', () => {
    feedImg.src = '';
    feedImg.classList.add('hidden');
    stopBtn.classList.add('hidden');
    startBtn.classList.remove('hidden');
    live = false;
    clearInterval(statsInterval);
    Toast.info('Live feed stopped.');
  });

  async function refreshStats() {
    try {
      const data = await API.get('/api/webcam_stats');
      renderLiveStats(data);
    } catch {}
  }

  function renderLiveStats(data) {
    if (!statsPanel) return;
    const stats = data.activity_statistics || {};
    const score = data.safety_score ?? 100;
    const alerts = data.total_alerts ?? 0;

    statsPanel.innerHTML = `
      <div class="panel-header">
        <span class="panel-title">Live Statistics</span>
        <span class="mono" style="font-size:0.65rem;color:var(--text3)">${new Date().toLocaleTimeString()}</span>
      </div>
      <div style="text-align:center;margin-bottom:20px">
        <div class="stat-value ${score >= 80 ? 'safe' : score >= 50 ? 'warn' : 'danger'}" style="font-size:3rem">${score}</div>
        <div class="mono" style="font-size:0.65rem;color:var(--text3);letter-spacing:0.15em">SESSION SCORE</div>
      </div>
      <table class="act-table">
        <tr><th>Activity</th><th>Count</th></tr>
        ${Object.entries(stats).map(([k,v]) => `
          <tr>
            <td>${k.replace('_',' ')}</td>
            <td class="mono">${v}</td>
          </tr>`).join('')}
      </table>
      <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border)">
        <div class="stat-label">Total Events</div>
        <div class="stat-value danger">${alerts}</div>
      </div>`;
  }
}


/* ─── DASHBOARD PAGE ────────────────────────────────────── */
function initDashboardPage() {
  const reportsTable = document.getElementById('reportsBody');
  if (!reportsTable) return;

  loadReports();

  async function loadReports() {
    try {
      const reports = await API.get('/api/reports');
      if (!reports.length) {
        reportsTable.innerHTML = '<tr><td colspan="5" style="color:var(--text3);text-align:center;padding:24px">No analysis reports yet.</td></tr>';
        return;
      }
      reportsTable.innerHTML = reports.map(r => {
        const score = r.safety_score ?? 0;
        const cls = score >= 80 ? 'safe' : score >= 50 ? 'warn' : 'danger';
        const date = r.timestamp ? new Date(r.timestamp).toLocaleString() : '—';
        return `
          <tr>
            <td class="mono" style="font-size:0.76rem">${date}</td>
            <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r.input_file || '—'}</td>
            <td><span class="badge badge-${cls}">${score}</span></td>
            <td><span class="badge badge-danger">${r.total_alerts ?? 0}</span></td>
            <td>
              <a href="/api/report/${r.filename}" target="_blank" class="btn btn-outline" style="padding:4px 12px;font-size:0.7rem">View</a>
            </td>
          </tr>`;
      }).join('');
    } catch (err) {
      reportsTable.innerHTML = '<tr><td colspan="5" style="color:var(--danger)">Failed to load reports.</td></tr>';
    }
  }

  /* mini chart using canvas */
  const canvas = document.getElementById('activityChart');
  if (canvas && window.reportData) {
    drawChart(canvas, window.reportData);
  }
  
}

function drawChart(canvas, data) {
  const ctx = canvas.getContext('2d');
  const stats = data.activity_statistics || {};
  const entries = Object.entries(stats);
  if (!entries.length) return;

  const W = canvas.width = canvas.offsetWidth;
  const H = canvas.height = canvas.offsetHeight;
  const max = Math.max(...entries.map(([,v]) => v), 1);
  const barW = (W - 40) / entries.length;
  const colors = { Standing:'#00d4ff', Walking:'#00e676', Squatting:'#ffaa00', Lifting:'#ff9800', Unsafe_Posture:'#ff3b3b' };

  ctx.clearRect(0, 0, W, H);

  entries.forEach(([label, value], i) => {
    const barH = ((value / max) * (H - 40));
    const x = 20 + i * barW + barW * 0.15;
    const y = H - 24 - barH;
    const bw = barW * 0.7;

    ctx.fillStyle = colors[label] || '#00d4ff';
    ctx.globalAlpha = 0.85;
    ctx.fillRect(x, y, bw, barH);

    ctx.globalAlpha = 1;
    ctx.fillStyle = '#7a9ab8';
    ctx.font = '10px Share Tech Mono, monospace';
    ctx.textAlign = 'center';
    ctx.fillText(label.replace('_',' ').replace('Unsafe','⚠'), x + bw / 2, H - 6);

    ctx.fillStyle = '#fff';
    ctx.fillText(value, x + bw / 2, y - 6);
  });
}


/* ─── SAFETY METER SVG ──────────────────────────────────── */
function updateMeter(score) {
  const fill = document.querySelector('.meter-fill');
  const val  = document.querySelector('.meter-value');
  if (!fill || !val) return;

  const circumference = 314;
  const offset = circumference - (score / 100) * circumference;
  fill.style.strokeDashoffset = offset;
  fill.style.stroke = score >= 80 ? 'var(--safe)' : score >= 50 ? 'var(--warn)' : 'var(--danger)';

  const num = val.querySelector('#meterNum');
  if (num) num.textContent = score;
}


/* ─── INIT ──────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  // Highlight active nav link
  const path = location.pathname;
  document.querySelectorAll('.nav-links a').forEach(a => {
    if (a.getAttribute('href') === path) a.classList.add('active');
  });

  initUploadPage();
  initLivePage();
  initDashboardPage();

  // Init meter if score present
  const scoreEl = document.getElementById('safetyScore');
  if (scoreEl) updateMeter(parseFloat(scoreEl.dataset.score || 100));
});
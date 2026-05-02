

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, request, jsonify, render_template_string
from src.rag_pipeline import recommend, reload_knowledge_base, DATA_SOURCE

app = Flask(__name__)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BIS Standards Finder – MSE Compliance Engine</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=JetBrains+Mono:wght@400;500&family=Inter:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --saffron: #FF6B00;
    --saffron-light: #FF8C33;
    --india-blue: #0A2463;
    --india-green: #1A7F4B;
    --cream: #FDF8F0;
    --card-bg: #FFFFFF;
    --border: #E8E0D0;
    --text: #1A1208;
    --muted: #6B5E4A;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Inter', sans-serif; background: var(--cream); color: var(--text); min-height: 100vh; }

  header {
    background: var(--india-blue);
    padding: 0 2rem;
    display: flex; align-items: center; justify-content: space-between;
    height: 64px; position: sticky; top: 0; z-index: 100;
    box-shadow: 0 2px 20px rgba(10,36,99,0.3);
  }
  .logo { display: flex; align-items: center; gap: 12px; }
  .logo-mark {
    width: 36px; height: 36px; background: var(--saffron); border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-weight: 800; font-size: 14px; color: white;
  }
  .logo-text { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 15px; color: white; }
  .logo-sub { font-size: 10px; color: rgba(255,255,255,0.5); letter-spacing: 1px; text-transform: uppercase; }

  /* data source banner */
  .source-bar {
    background: rgba(255,255,255,0.06);
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding: 6px 2rem;
    display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  }
  .source-dot {
    width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0;
  }
  .source-dot.pdf  { background: #4ADE80; box-shadow: 0 0 6px #4ADE80; }
  .source-dot.kb   { background: #FBBF24; box-shadow: 0 0 6px #FBBF24; }
  .source-label {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: rgba(255,255,255,0.7); flex: 1;
  }
  .reload-btn {
    background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.6); font-size: 11px; font-family: 'JetBrains Mono', monospace;
    padding: 3px 10px; border-radius: 4px; cursor: pointer; transition: all 0.2s;
  }
  .reload-btn:hover { background: rgba(255,107,0,0.2); color: var(--saffron-light); border-color: rgba(255,107,0,0.3); }

  .hero {
    background: var(--india-blue); padding: 3rem 2rem 4rem; text-align: center; position: relative; overflow: hidden;
  }
  .hero::before {
    content: ''; position: absolute; inset: 0;
    background: radial-gradient(ellipse 60% 80% at 50% 120%, rgba(255,107,0,0.15) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero-eyebrow { font-family: 'JetBrains Mono', monospace; font-size: 11px; letter-spacing: 2px; text-transform: uppercase; color: var(--saffron); margin-bottom: 1rem; }
  .hero h1 { font-family: 'Syne', sans-serif; font-size: clamp(1.8rem, 4vw, 3rem); font-weight: 800; color: white; line-height: 1.15; max-width: 700px; margin: 0 auto 1rem; }
  .hero h1 span { color: var(--saffron); }
  .hero-sub { color: rgba(255,255,255,0.6); font-size: 1rem; max-width: 500px; margin: 0 auto 2rem; line-height: 1.6; }

  .search-wrap { max-width: 720px; margin: 0 auto; position: relative; }
  .search-box {
    width: 100%; padding: 1.1rem 7rem 1.1rem 1.5rem;
    background: white; border: 2px solid transparent; border-radius: 12px;
    font-size: 1rem; font-family: 'Inter', sans-serif; color: var(--text);
    outline: none; transition: border-color 0.2s, box-shadow 0.2s;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15); resize: none;
  }
  .search-box:focus { border-color: var(--saffron); box-shadow: 0 4px 24px rgba(255,107,0,0.2); }
  .search-box::placeholder { color: #aaa; }
  .search-btn {
    position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
    background: var(--saffron); color: white; border: none; border-radius: 8px;
    padding: 0.6rem 1.2rem; font-family: 'Syne', sans-serif; font-weight: 700; font-size: 0.85rem;
    cursor: pointer; transition: background 0.2s; display: flex; align-items: center; gap: 6px;
  }
  .search-btn:hover { background: var(--saffron-light); }
  .search-btn:disabled { opacity: 0.6; cursor: not-allowed; }

  .quick-pills { display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; margin-top: 1rem; }
  .pill {
    background: rgba(255,255,255,0.08); color: rgba(255,255,255,0.7);
    border: 1px solid rgba(255,255,255,0.15); padding: 5px 14px; border-radius: 100px;
    font-size: 12px; cursor: pointer; transition: all 0.2s; white-space: nowrap;
  }
  .pill:hover { background: rgba(255,107,0,0.2); border-color: rgba(255,107,0,0.4); color: var(--saffron-light); }

  main { max-width: 900px; margin: 0 auto; padding: 2.5rem 1.5rem 4rem; }

  .status { text-align: center; padding: 3rem 1rem; display: none; }
  .spinner { width: 40px; height: 40px; border: 3px solid var(--border); border-top-color: var(--saffron); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 1rem; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .status-text { color: var(--muted); font-size: 0.9rem; }

  .results-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 1.5rem; padding-bottom: 1rem; border-bottom: 2px solid var(--border);
    flex-wrap: wrap; gap: 8px;
  }
  .results-title { font-family: 'Syne', sans-serif; font-size: 1.1rem; font-weight: 700; }
  .results-title span { color: var(--saffron); }
  .meta-chips { display: flex; gap: 8px; flex-wrap: wrap; }
  .latency-badge {
    font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--india-green);
    background: rgba(26,127,75,0.08); border: 1px solid rgba(26,127,75,0.2);
    padding: 4px 10px; border-radius: 100px;
  }
  .source-chip {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    padding: 4px 10px; border-radius: 100px;
  }
  .source-chip.pdf { background: rgba(74,222,128,0.1); color: #16a34a; border: 1px solid rgba(74,222,128,0.3); }
  .source-chip.kb  { background: rgba(251,191,36,0.1); color: #b45309; border: 1px solid rgba(251,191,36,0.3); }

  .cards { display: flex; flex-direction: column; gap: 1rem; }
  .card {
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px;
    padding: 1.5rem; position: relative; overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s;
    animation: slideIn 0.3s ease both;
  }
  @keyframes slideIn { from { opacity: 0; transform: translateY(16px); } to { opacity: 1; transform: translateY(0); } }
  .card:nth-child(2) { animation-delay: 0.06s; }
  .card:nth-child(3) { animation-delay: 0.12s; }
  .card:nth-child(4) { animation-delay: 0.18s; }
  .card:nth-child(5) { animation-delay: 0.24s; }
  .card:hover { box-shadow: 0 8px 30px rgba(0,0,0,0.08); transform: translateY(-2px); }
  .card::before {
    content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
    background: var(--saffron); border-radius: 4px 0 0 4px;
  }
  .card-header { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 0.75rem; gap: 12px; }
  .card-left { flex: 1; }
  .std-number { font-family: 'JetBrains Mono', monospace; font-weight: 500; font-size: 0.95rem; color: var(--saffron); margin-bottom: 3px; }
  .std-title { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1rem; color: var(--text); line-height: 1.3; }
  .card-meta { display: flex; gap: 6px; margin-top: 6px; flex-wrap: wrap; }
  .tag { font-size: 10px; font-family: 'JetBrains Mono', monospace; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
  .tag-cat { background: rgba(10,36,99,0.08); color: var(--india-blue); border: 1px solid rgba(10,36,99,0.15); }
  .tag-year { background: rgba(26,127,75,0.08); color: var(--india-green); border: 1px solid rgba(26,127,75,0.15); }
  .score-ring {
    width: 48px; height: 48px; border-radius: 50%; border: 3px solid var(--border);
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 500; color: var(--muted);
  }
  .score-ring.high { border-color: var(--saffron); color: var(--saffron); }
  .score-ring.med  { border-color: var(--india-green); color: var(--india-green); }
  .card-rationale {
    font-size: 0.875rem; color: #3D3028; line-height: 1.6;
    background: rgba(255,107,0,0.03); border: 1px solid rgba(255,107,0,0.1);
    border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 0.75rem;
  }
  .card-summary { font-size: 0.8rem; color: var(--muted); line-height: 1.5; }

  .empty { text-align: center; padding: 4rem 1rem; color: var(--muted); }
  .empty-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.5; }
  .error-banner { background: #FFF0F0; border: 1px solid #FCC; color: #C00; border-radius: 10px; padding: 1rem 1.5rem; font-size: 0.9rem; margin-bottom: 1rem; }

  /* ingest helper banner */
  .ingest-tip {
    background: rgba(251,191,36,0.08); border: 1px solid rgba(251,191,36,0.3);
    border-radius: 10px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;
    font-size: 0.82rem; color: #78350f; line-height: 1.6;
  }
  .ingest-tip code { background: rgba(0,0,0,0.07); padding: 1px 5px; border-radius: 3px; font-family: 'JetBrains Mono', monospace; }

  footer { background: var(--india-blue); color: rgba(255,255,255,0.4); text-align: center; padding: 1.5rem; font-size: 0.78rem; }
  footer strong { color: rgba(255,255,255,0.7); }
</style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-mark">BIS</div>
    <div>
      <div class="logo-text">Standards Finder</div>
      <div class="logo-sub">RAG · Building Materials</div>
    </div>
  </div>
</header>

<!-- Data source indicator bar -->
<div class="source-bar" id="sourceBar">
  <div class="source-dot" id="sourceDot"></div>
  <div class="source-label" id="sourceLabel">Loading data source…</div>
  <button class="reload-btn" onclick="reloadKB()" title="Re-load knowledge base from disk (after running ingest.py)">↻ Reload KB</button>
</div>

<div class="hero">
  <div class="hero-eyebrow">Powered by Retrieval-Augmented Generation</div>
  <h1>Find the right <span>BIS Standard</span> in seconds</h1>
  <p class="hero-sub">Describe your product and instantly get the top applicable BIS standards with clear rationale. Designed for Indian MSEs.</p>
  <div class="search-wrap">
    <textarea id="queryInput" class="search-box" rows="2"
      placeholder="e.g. 53 grade OPC cement for high-rise RCC structure..."></textarea>
    <button class="search-btn" id="searchBtn" onclick="search()">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
      Find
    </button>
  </div>
  <div class="quick-pills">
    <span class="pill" onclick="setQuery('43 grade ordinary portland cement for masonry construction')">OPC 43 Cement</span>
    <span class="pill" onclick="setQuery('TMT steel bars Fe500 for reinforced concrete columns')">TMT Steel Bars</span>
    <span class="pill" onclick="setQuery('coarse and fine aggregates for concrete mix M25')">Concrete Aggregates</span>
    <span class="pill" onclick="setQuery('hollow concrete blocks for load bearing masonry walls')">Concrete Blocks</span>
    <span class="pill" onclick="setQuery('chemical admixture superplasticiser for high workability concrete')">Admixture</span>
    <span class="pill" onclick="setQuery('fly ash for use in concrete as pozzolana')">Fly Ash</span>
  </div>
</div>

<main id="main">
  <div class="empty" id="emptyState">
    <div class="empty-icon">🏗️</div>
    <p>Enter a product description above to discover applicable BIS standards.</p>
  </div>
  <div class="status" id="loadingState">
    <div class="spinner"></div>
    <p class="status-text">Searching BIS knowledge base…</p>
  </div>
  <div id="resultsContainer"></div>
</main>

<footer>
 RAG-Based Standards Engine
</footer>

<script>
// ── Initialise source banner ──────────────────────────────────────────────
async function refreshSourceBanner() {
  try {
    const r = await fetch('/api/health');
    const d = await r.json();
    const isPdf = d.data_source && d.data_source.includes('PDF');
    document.getElementById('sourceDot').className = 'source-dot ' + (isPdf ? 'pdf' : 'kb');
    document.getElementById('sourceLabel').textContent = '📦 Data source: ' + d.data_source;
  } catch(e) {
    document.getElementById('sourceLabel').textContent = 'Could not reach server';
  }
}
refreshSourceBanner();

async function reloadKB() {
  const btn = document.querySelector('.reload-btn');
  btn.textContent = '↻ Reloading…'; btn.disabled = true;
  try {
    const r = await fetch('/api/reload', { method: 'POST' });
    const d = await r.json();
    await refreshSourceBanner();
    alert('Knowledge base reloaded: ' + d.data_source);
  } catch(e) { alert('Reload failed: ' + e.message); }
  finally { btn.textContent = '↻ Reload KB'; btn.disabled = false; }
}

function setQuery(text) {
  document.getElementById('queryInput').value = text;
  document.getElementById('queryInput').focus();
}

document.getElementById('queryInput').addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); search(); }
});

async function search() {
  const query = document.getElementById('queryInput').value.trim();
  if (!query) return;
  const btn = document.getElementById('searchBtn');
  btn.disabled = true;
  document.getElementById('emptyState').style.display = 'none';
  document.getElementById('loadingState').style.display = 'block';
  document.getElementById('resultsContainer').innerHTML = '';

  try {
    const resp = await fetch('/api/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 5 }),
    });
    const data = await resp.json();
    document.getElementById('loadingState').style.display = 'none';
    if (data.error) {
      document.getElementById('resultsContainer').innerHTML = `<div class="error-banner">⚠️ ${data.error}</div>`;
    } else {
      renderResults(data);
    }
  } catch(err) {
    document.getElementById('loadingState').style.display = 'none';
    document.getElementById('resultsContainer').innerHTML = `<div class="error-banner">⚠️ ${err.message}</div>`;
  } finally { btn.disabled = false; }
}

function renderResults(data) {
  const stds = data.retrieved_standards || [];
  if (!stds.length) {
    document.getElementById('resultsContainer').innerHTML =
      '<div class="empty"><div class="empty-icon">🔍</div><p>No matching standards found.</p></div>';
    return;
  }
  const latMs = (data.latency_seconds * 1000).toFixed(0);
  const isPdf = data.data_source && data.data_source.includes('PDF');
  const srcClass = isPdf ? 'pdf' : 'kb';
  const srcLabel = isPdf ? '📄 BIS SP-21 PDF' : '📦 Built-in KB';

  // Show ingest tip if using built-in KB
  const tip = isPdf ? '' : `
    <div class="ingest-tip">
      ℹ️ Currently using the built-in knowledge base. For full coverage from the official BIS SP-21 PDF, run:<br>
      <code>python src/ingest.py --pdf data/BIS_SP21.pdf --output data/chunks.json</code><br>
      then click <strong>↻ Reload KB</strong> above.
    </div>`;

  let html = tip + `
    <div class="results-header">
      <div class="results-title">Found <span>${stds.length}</span> applicable standard${stds.length > 1 ? 's' : ''}</div>
      <div class="meta-chips">
        <div class="latency-badge">⚡ ${latMs}ms</div>
        <div class="source-chip ${srcClass}">${srcLabel}</div>
      </div>
    </div>
    <div class="cards">`;

  stds.forEach(s => {
    const pct = Math.round(Math.min((s.relevance_score || 0) * 200, 100));
    const cls = pct >= 60 ? 'high' : (pct >= 35 ? 'med' : '');
    html += `
      <div class="card">
        <div class="card-header">
          <div class="card-left">
            <div class="std-number">${esc(s.standard_id)}</div>
            <div class="std-title">${esc(s.title)}</div>
            <div class="card-meta">
              <span class="tag tag-cat">${esc(s.category)}</span>
              ${s.year ? `<span class="tag tag-year">${esc(s.year)}</span>` : ''}
            </div>
          </div>
          <div class="score-ring ${cls}">${pct}%</div>
        </div>
        <div class="card-rationale">💡 ${esc(s.rationale)}</div>
        <div class="card-summary">${esc(s.summary || '')}</div>
      </div>`;
  });

  html += '</div>';
  document.getElementById('resultsContainer').innerHTML = html;
}

function esc(s) {
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/api/recommend", methods=["POST"])
def api_recommend():
    data = request.get_json(force=True, silent=True) or {}
    query = data.get("query", "").strip()
    top_k = min(int(data.get("top_k", 5)), 10)
    if not query:
        return jsonify({"error": "query field is required"}), 400
    try:
        result = recommend(query, top_k=top_k)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/reload", methods=["POST"])
def api_reload():
    """Re-load knowledge base from disk (call after running ingest.py)."""
    source = reload_knowledge_base()
    return jsonify({"status": "ok", "data_source": source})


@app.route("/api/health")
def health():
    from src.rag_pipeline import DATA_SOURCE
    return jsonify({"status": "ok", "model": "BIS-RAG-v1", "data_source": DATA_SOURCE})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

/**
 * OmniStock Alpha - Frontend Application Logic
 * Handles horizon switching, multi-source stock recommendations,
 * deep dive modal, and interactive Chart.js visualizations.
 */

let currentHorizon = 'short_term';
let currentCategory = '';
let currentSpotlightSymbol = 'NVDA';
let chartInstance = null;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  loadData();
});

// Switch between Short-Term (1-2w), Medium-Term (1-2m), Long-Term (1-2y)
function selectHorizon(horizon) {
  if (currentHorizon === horizon) return;
  currentHorizon = horizon;

  // Update tabs UI
  const btnShort = document.getElementById('btn-horizon-short');
  const btnMed = document.getElementById('btn-horizon-medium');
  const btnLong = document.getElementById('btn-horizon-long');

  btnShort.className = 'horizon-tab px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all bg-slate-900/60 border border-slate-800 hover:border-slate-700';
  btnMed.className = 'horizon-tab px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all bg-slate-900/60 border border-slate-800 hover:border-slate-700';
  btnLong.className = 'horizon-tab px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all bg-slate-900/60 border border-slate-800 hover:border-slate-700';

  const heroText = document.getElementById('hero-horizon-text');
  const heroDesc = document.getElementById('hero-horizon-desc');
  const spotlightGlow = document.getElementById('spotlight-glow');
  const spotlightReturnBox = document.getElementById('spotlight-return-box');
  const targetLabel = document.getElementById('spotlight-target-label');

  if (horizon === 'short_term') {
    btnShort.className = 'horizon-tab active-short px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all';
    heroText.className = 'bg-gradient-to-r from-rose-400 to-pink-500 bg-clip-text text-transparent';
    heroText.innerText = 'Short-Term (1-2 Weeks)';
    heroDesc.innerText = 'Exploiting high-velocity momentum breakouts, RSI power zones, volume surges, and immediate news catalysts.';
    spotlightGlow.className = 'absolute -right-20 -top-20 w-80 h-80 bg-rose-500/10 rounded-full blur-3xl pointer-events-none';
    spotlightReturnBox.className = 'bg-gradient-to-br from-rose-950/40 to-slate-900 p-4 rounded-xl border border-rose-500/30 min-w-[190px]';
    targetLabel.innerText = 'Target Return (1-2w)';
  } else if (horizon === 'medium_term') {
    btnMed.className = 'horizon-tab active-medium px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all';
    heroText.className = 'bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent';
    heroText.innerText = 'Medium-Term (1-2 Months)';
    heroDesc.innerText = 'Capturing quarterly earnings acceleration, 50-day moving average trend continuations, and Wall Street upgrades.';
    spotlightGlow.className = 'absolute -right-20 -top-20 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none';
    spotlightReturnBox.className = 'bg-gradient-to-br from-cyan-950/40 to-slate-900 p-4 rounded-xl border border-cyan-500/30 min-w-[190px]';
    targetLabel.innerText = 'Target Return (1-2m)';
  } else {
    btnLong.className = 'horizon-tab active-long px-5 py-3 rounded-xl flex items-center space-x-3 text-left transition-all';
    heroText.className = 'bg-gradient-to-r from-emerald-400 to-teal-500 bg-clip-text text-transparent';
    heroText.innerText = 'Long-Term (1-2 Years)';
    heroDesc.innerText = 'Compounding wealth with market-beating fundamentals: pristine balance sheets, high ROE, and competitive moats.';
    spotlightGlow.className = 'absolute -right-20 -top-20 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none';
    spotlightReturnBox.className = 'bg-gradient-to-br from-emerald-950/40 to-slate-900 p-4 rounded-xl border border-emerald-500/30 min-w-[190px]';
    targetLabel.innerText = 'Target Return (1-2y)';
  }

  loadData();
}

// Set universe filter
function setCategoryFilter(category) {
  currentCategory = category;
  document.querySelectorAll('.cat-pill').forEach(btn => {
    btn.className = 'cat-pill px-3 py-1 rounded-full text-xs font-medium bg-slate-900 text-slate-400 border border-slate-800 hover:text-slate-200';
  });
  event.target.className = 'cat-pill active px-3 py-1 rounded-full text-xs font-medium bg-slate-800 text-cyan-300 border border-cyan-500/30';
  loadData();
}

// Load recommendations from backend API
async function loadData() {
  const loading = document.getElementById('loading-container');
  const dashboard = document.getElementById('dashboard-content');
  const refreshIcon = document.getElementById('refresh-icon');

  if (refreshIcon) refreshIcon.classList.add('animate-spin');
  loading.classList.remove('hidden');
  dashboard.classList.add('hidden');

  try {
    let url = `/api/recommendations?horizon=${currentHorizon}`;
    if (currentCategory) {
      url += `&category=${encodeURIComponent(currentCategory)}`;
    }
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('Failed to fetch recommendations');
    const data = await resp.json();

    renderDashboard(data);
  } catch (err) {
    console.error('Error loading recommendations:', err);
    alert('Failed to load stock recommendations. Please try again or check the server log.');
  } finally {
    loading.classList.add('hidden');
    dashboard.classList.remove('hidden');
    if (refreshIcon) refreshIcon.classList.remove('animate-spin');
    if (window.lucide) lucide.createIcons();
  }
}

// Refresh button
function refreshData() {
  loadData();
}

// Render the entire dashboard with fetched data
function renderDashboard(data) {
  const spotlight = data.spotlight_stock;
  const leaderboard = data.leaderboard || [];

  if (spotlight) {
    renderSpotlight(spotlight);
  }

  renderLeaderboard(leaderboard);
}

// Render the #1 Best Stock spotlight section
function renderSpotlight(stock) {
  currentSpotlightSymbol = stock.symbol;
  const horizonData = stock.horizons[currentHorizon] || {};
  const proj = horizonData.projection || {};
  const tradeSetup = stock.horizons.short_term?.trade_setup || {};

  document.getElementById('spotlight-symbol').innerText = stock.symbol;
  document.getElementById('spotlight-name').innerText = stock.name || stock.symbol;
  document.getElementById('spotlight-sector').innerText = stock.sector || 'N/A';
  document.getElementById('spotlight-industry').innerText = stock.industry || 'N/A';
  
  const priceFormatted = `$${stock.current_price.toFixed(2)}`;
  document.getElementById('spotlight-price').innerText = priceFormatted;

  const changeElem = document.getElementById('spotlight-change');
  const isPos = stock.change_pct >= 0;
  changeElem.innerText = `${isPos ? '+' : ''}${stock.change_pct.toFixed(2)}% Today`;
  changeElem.className = `text-xs font-semibold mt-0.5 ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;

  // Badge & Title
  const badgeTitle = document.getElementById('spotlight-badge-title');
  const signalBadge = document.getElementById('spotlight-signal-badge');
  const horizonLabels = {
    short_term: '#1 Best Stock For 1-2 Weeks',
    medium_term: '#1 Best Stock For 1-2 Months',
    long_term: '#1 Best Stock For 1-2 Years'
  };
  badgeTitle.innerText = horizonLabels[currentHorizon] || '#1 Best Stock';
  signalBadge.innerText = horizonData.signal || 'STRONG BUY';
  signalBadge.className = `px-2.5 py-0.5 rounded-full text-xs font-semibold ${horizonData.badge || 'badge-strong-buy'}`;

  // Return & Price Targets
  const retColor = currentHorizon === 'short_term' ? 'text-rose-400' : (currentHorizon === 'medium_term' ? 'text-cyan-400' : 'text-emerald-400');
  const returnElem = document.getElementById('spotlight-return');
  returnElem.innerText = `+${proj.target_return_pct?.toFixed(1) || 0}%`;
  returnElem.className = `text-3xl font-black font-mono ${retColor}`;
  document.getElementById('spotlight-target-price').innerText = `Target: $${proj.target_price?.toFixed(2) || '--'} (${proj.range_min_pct}% - ${proj.range_max_pct}%)`;

  // Score & Win probability
  document.getElementById('spotlight-score').innerText = `${horizonData.score?.toFixed(0) || 85}/100`;
  document.getElementById('spotlight-winprob').innerText = `${horizonData.win_probability?.toFixed(0) || 80}% Win Probability`;

  // Trade Setup
  document.getElementById('spotlight-entry').innerText = `$${tradeSetup.entry_price?.toFixed(2) || stock.current_price.toFixed(2)}`;
  document.getElementById('spotlight-stop').innerText = `$${tradeSetup.stop_loss?.toFixed(2) || '--'} (-${tradeSetup.risk_pct || 5}%)`;
  document.getElementById('spotlight-tp1').innerText = `$${tradeSetup.take_profit_1?.toFixed(2) || '--'} (+${tradeSetup.target_pct_tp1 || 8}%)`;
  document.getElementById('spotlight-tp2').innerText = `$${tradeSetup.take_profit_2?.toFixed(2) || '--'} (+${tradeSetup.target_pct_tp2 || 15}%)`;
  document.getElementById('spotlight-rr').innerText = `Risk/Reward: ${tradeSetup.risk_reward_ratio || 2.5}:1`;

  // Predictive Rationale Bullets
  const reasonsList = document.getElementById('spotlight-reasons');
  reasonsList.innerHTML = '';
  const reasons = horizonData.key_reasons || [];
  if (reasons.length === 0) {
    reasons.push('High composite multi-factor score outperforming universe.');
  }

  reasons.forEach(r => {
    const li = document.createElement('li');
    li.className = 'flex items-start space-x-2';
    li.innerHTML = `
      <i data-lucide="check-circle-2" class="w-4 h-4 text-emerald-400 shrink-0 mt-0.5"></i>
      <span>${escapeHtml(r)}</span>
    `;
    reasonsList.appendChild(li);
  });

  if (window.lucide) lucide.createIcons();
}

// Render Leaderboard table
function renderLeaderboard(stocks) {
  const tbody = document.getElementById('leaderboard-body');
  tbody.innerHTML = '';

  const titleElem = document.getElementById('leaderboard-title');
  const horizonTitles = {
    short_term: 'Top Ranked Stocks For 1-2 Weeks (Short-Term)',
    medium_term: 'Top Ranked Stocks For 1-2 Months (Medium-Term)',
    long_term: 'Top Ranked Stocks For 1-2 Years (Long-Term)'
  };
  titleElem.innerText = horizonTitles[currentHorizon] || 'Top Ranked Stocks';
  document.getElementById('analyzed-count').innerText = `Screened ${stocks.length} Stocks`;

  const progressClass = currentHorizon === 'short_term' ? 'progress-short' : (currentHorizon === 'medium_term' ? 'progress-medium' : 'progress-long');

  stocks.forEach((stock, idx) => {
    const horizonData = stock.horizons[currentHorizon] || {};
    const proj = horizonData.projection || {};
    const isPos = stock.change_pct >= 0;
    const score = horizonData.score || 50;

    const tr = document.createElement('tr');
    tr.className = 'hover:bg-slate-900/40 transition-colors';
    tr.innerHTML = `
      <td class="py-3.5 px-4 text-center font-bold font-mono text-slate-400">
        ${idx === 0 ? '<span class="text-amber-400">🥇 #1</span>' : (idx === 1 ? '<span class="text-slate-300">🥈 #2</span>' : (idx === 2 ? '<span class="text-amber-600">🥉 #3</span>' : `#${idx + 1}`))}
      </td>
      <td class="py-3.5 px-4">
        <div class="flex items-center space-x-2.5">
          <button onclick="openDeepDive('${stock.symbol}')" class="font-bold font-mono text-white hover:text-cyan-400 transition-colors">
            ${stock.symbol}
          </button>
          <span class="text-xs text-slate-400 truncate max-w-[120px] sm:max-w-[180px]">${escapeHtml(stock.name || '')}</span>
        </div>
      </td>
      <td class="py-3.5 px-4 text-right font-mono font-medium text-slate-200">
        $${stock.current_price.toFixed(2)}
      </td>
      <td class="py-3.5 px-4 text-right font-mono text-xs ${isPos ? 'text-emerald-400 font-semibold' : 'text-rose-400'}">
        ${isPos ? '+' : ''}${stock.change_pct.toFixed(2)}%
      </td>
      <td class="py-3.5 px-4 text-center">
        <div class="flex items-center justify-center space-x-2">
          <div class="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
            <div class="${progressClass} h-1.5 rounded-full" style="width: ${score}%"></div>
          </div>
          <span class="font-mono text-xs text-slate-300 font-bold">${score.toFixed(0)}</span>
        </div>
      </td>
      <td class="py-3.5 px-4 text-right font-mono font-bold text-sm text-cyan-300">
        +${proj.target_return_pct?.toFixed(1) || 0}%
      </td>
      <td class="py-3.5 px-4 text-center">
        <span class="px-2 py-0.5 rounded text-[11px] font-semibold ${horizonData.badge || 'badge-buy'}">
          ${horizonData.signal || 'BUY'}
        </span>
      </td>
      <td class="py-3.5 px-4 text-center font-mono text-xs text-slate-300">
        ${horizonData.win_probability?.toFixed(0) || 75}%
      </td>
      <td class="py-3.5 px-4 text-center">
        <button 
          onclick="openDeepDive('${stock.symbol}')"
          class="px-2.5 py-1 bg-slate-800 hover:bg-cyan-600 hover:text-white text-slate-300 text-xs rounded-lg font-medium transition-all"
        >
          Analyze
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Open Deep-Dive Modal for any stock
async function openDeepDive(symbol) {
  const modal = document.getElementById('deepdive-modal');
  modal.classList.remove('hidden');

  // Fill placeholder loading state
  document.getElementById('modal-avatar').innerText = symbol;
  document.getElementById('modal-symbol').innerText = symbol;
  document.getElementById('modal-name').innerText = 'Loading live data...';

  try {
    const resp = await fetch(`/api/stock/${encodeURIComponent(symbol)}`);
    if (!resp.ok) throw new Error('Stock not found');
    const data = await resp.json();
    populateModalData(data);
  } catch (err) {
    alert(`Could not fetch data for ${symbol}: ${err.message}`);
    closeDeepDive();
  }
}

// Populate Deep-Dive Modal with stock details
function populateModalData(data) {
  document.getElementById('modal-avatar').innerText = data.symbol;
  document.getElementById('modal-symbol').innerText = data.symbol;
  document.getElementById('modal-name').innerText = data.name || data.symbol;
  document.getElementById('modal-sector').innerText = data.sector || 'N/A';
  document.getElementById('modal-industry').innerText = data.industry || 'N/A';
  document.getElementById('modal-price').innerText = `$${data.current_price.toFixed(2)}`;

  const isPos = data.change_pct >= 0;
  const changeElem = document.getElementById('modal-change');
  changeElem.innerText = `${isPos ? '+' : ''}${data.change_pct.toFixed(2)}% Today`;
  changeElem.className = `font-semibold ${isPos ? 'text-emerald-400' : 'text-rose-400'}`;

  // 3 Horizons cards
  const st = data.horizons.short_term || {};
  const mt = data.horizons.medium_term || {};
  const lt = data.horizons.long_term || {};

  document.getElementById('modal-st-badge').innerText = st.signal || 'BUY';
  document.getElementById('modal-st-badge').className = `px-2 py-0.5 rounded text-[10px] font-bold ${st.badge || 'badge-buy'}`;
  document.getElementById('modal-st-return').innerText = `+${st.projection?.target_return_pct?.toFixed(1) || 0}%`;
  document.getElementById('modal-st-target').innerText = `Target: $${st.projection?.target_price?.toFixed(2) || '--'}`;
  document.getElementById('modal-st-reason').innerText = st.key_reasons?.[0] || 'High velocity momentum';

  document.getElementById('modal-mt-badge').innerText = mt.signal || 'BUY';
  document.getElementById('modal-mt-badge').className = `px-2 py-0.5 rounded text-[10px] font-bold ${mt.badge || 'badge-buy'}`;
  document.getElementById('modal-mt-return').innerText = `+${mt.projection?.target_return_pct?.toFixed(1) || 0}%`;
  document.getElementById('modal-mt-target').innerText = `Target: $${mt.projection?.target_price?.toFixed(2) || '--'}`;
  document.getElementById('modal-mt-reason').innerText = mt.key_reasons?.[0] || 'Trend continuation above 50 SMA';

  document.getElementById('modal-lt-badge').innerText = lt.signal || 'QUALITY COMPOUNDER';
  document.getElementById('modal-lt-badge').className = `px-2 py-0.5 rounded text-[10px] font-bold ${lt.badge || 'badge-buy'}`;
  document.getElementById('modal-lt-return').innerText = `+${lt.projection?.target_return_pct?.toFixed(1) || 0}%`;
  document.getElementById('modal-lt-target').innerText = `Target: $${lt.projection?.target_price?.toFixed(2) || '--'}`;
  document.getElementById('modal-lt-reason').innerText = lt.key_reasons?.[0] || 'Superior ROE & balance sheet quality';

  // Technical Indicators
  const tech = data.technicals || {};
  document.getElementById('modal-tech-rsi').innerText = tech.rsi ? tech.rsi.toFixed(1) : '--';
  document.getElementById('modal-tech-macd').innerText = tech.macd_hist ? tech.macd_hist.toFixed(2) : '--';
  document.getElementById('modal-tech-vol').innerText = tech.volume_surge_ratio ? `${tech.volume_surge_ratio.toFixed(1)}x` : '--';
  document.getElementById('modal-tech-sma50').innerText = tech.sma_50 ? `$${tech.sma_50.toFixed(2)}` : '--';
  document.getElementById('modal-tech-sma200').innerText = tech.sma_200 ? `$${tech.sma_200.toFixed(2)}` : '--';
  document.getElementById('modal-tech-atr').innerText = tech.atr ? `$${tech.atr.toFixed(2)}` : '--';

  // Fundamental Indicators
  const fund = data.fundamentals || {};
  const metrics = fund.metrics || {};
  document.getElementById('modal-fund-pe').innerText = metrics.trailing_pe ? metrics.trailing_pe.toFixed(1) : 'N/A';
  document.getElementById('modal-fund-fwdpe').innerText = metrics.forward_pe ? metrics.forward_pe.toFixed(1) : 'N/A';
  document.getElementById('modal-fund-peg').innerText = metrics.peg_ratio ? metrics.peg_ratio.toFixed(2) : 'N/A';
  document.getElementById('modal-fund-roe').innerText = metrics.roe ? `${metrics.roe.toFixed(1)}%` : 'N/A';
  document.getElementById('modal-fund-margin').innerText = metrics.profit_margin ? `${metrics.profit_margin.toFixed(1)}%` : 'N/A';
  document.getElementById('modal-fund-de').innerText = metrics.debt_to_equity ? `${metrics.debt_to_equity.toFixed(1)}%` : 'N/A';

  // News Catalysts
  const newsList = document.getElementById('modal-news-list');
  newsList.innerHTML = '';
  const news = data.sentiment?.recent_catalysts || [];
  if (news.length === 0) {
    newsList.innerHTML = '<p class="text-xs text-slate-500 italic">No recent news headlines available for this ticker.</p>';
  } else {
    news.forEach(item => {
      const div = document.createElement('div');
      div.className = 'flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800/80 text-xs';
      const badgeStyle = item.sentiment === 'BULLISH' ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' : (item.sentiment === 'BEARISH' ? 'text-rose-400 bg-rose-500/10 border border-rose-500/20' : 'text-slate-400 bg-slate-800');
      
      div.innerHTML = `
        <div class="flex items-center space-x-2 truncate mr-3">
          <span class="px-1.5 py-0.5 rounded text-[10px] font-bold ${badgeStyle}">${item.sentiment}</span>
          <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="truncate text-slate-300 hover:text-cyan-400 hover:underline">
            ${escapeHtml(item.title)}
          </a>
        </div>
        <span class="text-[10px] text-slate-500 shrink-0">${escapeHtml(item.publisher || '')}</span>
      `;
      newsList.appendChild(div);
    });
  }

  // Draw Price & Forecast Chart
  drawModalChart(data);

  if (window.lucide) lucide.createIcons();
}

// Draw Chart.js Line Chart with Forecast Targets
function drawModalChart(data) {
  const ctx = document.getElementById('deepdive-chart').getContext('2d');
  if (chartInstance) {
    chartInstance.destroy();
  }

  const candles = data.chart_data || [];
  const labels = candles.map(c => c.time);
  const closes = candles.map(c => c.close);

  const currentPrice = data.current_price;
  const targetST = data.horizons.short_term?.projection?.target_price || currentPrice * 1.08;
  const targetMT = data.horizons.medium_term?.projection?.target_price || currentPrice * 1.18;

  // Add forecast point into chart
  const extendedLabels = [...labels, '+10 Days (1-2w)', '+45 Days (1-2m)'];
  const historySeries = [...closes, null, null];
  
  const forecastSTSeries = Array(closes.length - 1).fill(null);
  forecastSTSeries.push(currentPrice, targetST, null);

  const forecastMTSeries = Array(closes.length - 1).fill(null);
  forecastMTSeries.push(currentPrice, null, targetMT);

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: extendedLabels,
      datasets: [
        {
          label: 'Historical Close ($)',
          data: historySeries,
          borderColor: '#38bdf8',
          backgroundColor: 'rgba(56, 189, 248, 0.08)',
          fill: true,
          tension: 0.2,
          pointRadius: 0,
          borderWidth: 2
        },
        {
          label: '1-2 Weeks Forecast',
          data: forecastSTSeries,
          borderColor: '#f43f5e',
          borderDash: [5, 5],
          pointRadius: 4,
          pointBackgroundColor: '#f43f5e',
          borderWidth: 2
        },
        {
          label: '1-2 Months Forecast',
          data: forecastMTSeries,
          borderColor: '#10b981',
          borderDash: [5, 5],
          pointRadius: 4,
          pointBackgroundColor: '#10b981',
          borderWidth: 2
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleColor: '#f8fafc',
          bodyColor: '#cbd5e1',
          borderColor: '#334155',
          borderWidth: 1,
          padding: 10,
          callbacks: {
            label: function(context) {
              if (context.raw !== null) {
                return `${context.dataset.label}: $${context.raw.toFixed(2)}`;
              }
              return null;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(255, 255, 255, 0.04)' },
          ticks: { color: '#64748b', maxTicksLimit: 8 }
        },
        y: {
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: {
            color: '#64748b',
            callback: function(value) { return '$' + value; }
          }
        }
      }
    }
  });
}

// Close Deep-Dive Modal
function closeDeepDive() {
  const modal = document.getElementById('deepdive-modal');
  modal.classList.add('hidden');
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

// Close on backdrop click
document.getElementById('deepdive-modal')?.addEventListener('click', (e) => {
  if (e.target.id === 'deepdive-modal') {
    closeDeepDive();
  }
});

// Handle search form submission
function handleSearch(event) {
  event.preventDefault();
  const input = document.getElementById('search-input');
  const symbol = input.value.trim().toUpperCase();
  if (symbol) {
    openDeepDive(symbol);
    input.value = '';
  }
}

// Helper: Escape HTML to prevent XSS
function escapeHtml(text) {
  if (!text) return '';
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}


/* OEYC — vanilla JS. Reads the committed scan and renders everything from it.
   No framework, no build step, no storage. */

'use strict';

/* The scan lives at data/results.json in the repo. Depending on how the site
   is served -- straight from the repo, or from an assembled Pages artifact --
   it sits at a different depth, so try each in turn. */
const DATA_PATHS = ['../data/results.json', 'data/results.json', './results.json'];

const COL = {
  ink: '#dfe6ef', dim: '#97a4b6', faint: '#64738a',
  line: '#1f2a38', moon: '#e9e4d6', accent: '#7fb8ff',
  good: '#6ee7a8', warn: '#f5c26b', bad: '#f2807c'
};

let DATA = null;
let ROWS = [];
let EPS = 0.1;
let sortKey = 'Y', sortDir = 1;
let chartE = null, chartG = null;

/* ------------------------------------------------------------------ utils */

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

const int = n => n.toLocaleString('en-US');
const deg = (v, p = 3) => v.toFixed(p) + '°';
const pct = v => (v * 100).toFixed(2) + '%';

function degAdaptive(v) {
  if (v < 0.001) return v.toExponential(2) + '°';
  if (v < 1) return v.toFixed(4) + '°';
  return v.toFixed(2) + '°';
}

function fill(name, html) {
  $$('[data-fill="' + name + '"]').forEach(el => { el.innerHTML = html; });
}

function numsBlock(pairs) {
  return pairs.map(([k, v]) =>
    '<div><span class="k">' + k + '</span><span class="v">' + v + '</span></div>'
  ).join('');
}

function yn(b) {
  return b ? '<span class="yes">yes</span>' : '<span class="no">no</span>';
}

/* ------------------------------------------------------- svg diagrams */

/* Lunar disc at elongation theta. Illuminated fraction is (1 - cos theta)/2;
   the terminator is a half ellipse whose x-radius is r*cos(theta). */
function moonDisc(theta, size) {
  const r = size / 2 - 7, cx = size / 2, cy = size / 2;
  const waning = theta > 180;
  const th = waning ? 360 - theta : theta;
  const semi = r * Math.cos(th * Math.PI / 180);
  const sweep = semi > 0 ? 0 : 1;
  const d = 'M ' + cx + ' ' + (cy - r) +
            ' A ' + r + ' ' + r + ' 0 0 1 ' + cx + ' ' + (cy + r) +
            ' A ' + Math.abs(semi).toFixed(2) + ' ' + r + ' 0 0 ' + sweep +
            ' ' + cx + ' ' + (cy - r) + ' Z';
  const flip = waning ? ' transform="translate(' + (2 * cx) + ',0) scale(-1,1)"' : '';
  return '' +
    '<svg width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '" role="img" ' +
      'aria-label="Moon at elongation ' + theta.toFixed(2) + ' degrees">' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="#161d28" stroke="' + COL.line + '"/>' +
      '<path d="' + d + '" fill="' + COL.moon + '"' + flip + '/>' +
    '</svg>';
}

/* Top-down geometry: Earth at centre, Sun to the right, Moon at longitude
   theta measured anticlockwise from the Sun direction. */
function elongationDiagram(theta, w, h) {
  const cx = w * 0.42, cy = h / 2, R = Math.min(w, h) * 0.30;
  const a = theta * Math.PI / 180;
  const mx = cx + R * Math.cos(a), my = cy - R * Math.sin(a);
  const large = theta > 180 ? 1 : 0;
  const ar = R * 0.42;
  const arc = 'M ' + (cx + ar) + ' ' + cy +
              ' A ' + ar + ' ' + ar + ' 0 ' + large + ' 0 ' +
              (cx + ar * Math.cos(a)) + ' ' + (cy - ar * Math.sin(a));
  return '' +
    '<svg width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + ' ' + h + '" role="img" ' +
      'aria-label="Sun Earth Moon geometry, elongation ' + theta.toFixed(2) + ' degrees">' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="' + R + '" fill="none" stroke="' + COL.line + '" stroke-dasharray="2 4"/>' +
      '<line x1="' + cx + '" y1="' + cy + '" x2="' + (w - 6) + '" y2="' + cy + '" stroke="' + COL.warn + '" stroke-width="1" opacity="0.55"/>' +
      '<path d="' + arc + '" fill="none" stroke="' + COL.accent + '" stroke-width="1.4"/>' +
      '<line x1="' + cx + '" y1="' + cy + '" x2="' + mx.toFixed(1) + '" y2="' + my.toFixed(1) + '" stroke="' + COL.accent + '" stroke-width="1" opacity="0.55"/>' +
      '<circle cx="' + (w - 6) + '" cy="' + cy + '" r="6" fill="' + COL.warn + '"/>' +
      '<circle cx="' + cx + '" cy="' + cy + '" r="4.5" fill="' + COL.accent + '"/>' +
      '<circle cx="' + mx.toFixed(1) + '" cy="' + my.toFixed(1) + '" r="3.6" fill="' + COL.moon + '"/>' +
      '<text class="diagram-val" x="6" y="' + (h - 6) + '">θ = ' + theta.toFixed(2) + '°</text>' +
    '</svg>';
}

/* --------------------------------------------------------------- table */

function visible() {
  return ROWS.filter(r => r.E < EPS);
}

function renderTable() {
  const rows = visible().slice().sort((a, b) => {
    const x = a[sortKey], y = b[sortKey];
    const c = typeof x === 'string' ? x.localeCompare(y) : x - y;
    return c * sortDir;
  });

  const best = ROWS.reduce((m, r) => (r.E < m.E ? r : m), ROWS[0]);
  const tb = $('#series-table tbody');
  tb.innerHTML = rows.map(r => {
    const isBest = r.Y === best.Y;
    return '<tr>' +
      '<td class="num' + (isBest ? ' best' : '') + '">' + r.Y + '</td>' +
      '<td class="moon-cell">' + r.date + '</td>' +
      '<td class="num">' + int(r.D) + '</td>' +
      '<td class="num dim">' + r.L + '</td>' +
      '<td class="num">' + int(r.Z) + '</td>' +
      '<td class="num">' + int(r.K) + '</td>' +
      '<td class="num dim">' + (r.slip >= 0 ? '+' : '') + r.slip.toFixed(4) + '</td>' +
      '<td class="num' + (isBest ? ' best' : '') + '">' + degAdaptive(r.E) + '</td>' +
      '<td class="num dim">' + pct(r.illum) + '</td>' +
      '<td class="num dim">' + r.dr_Y + '·' + r.dr_D + '·' + r.dr_Z + '·' + r.dr_K + '</td>' +
    '</tr>';
  }).join('');

  $('#empty-note').hidden = rows.length > 0;

  $('#n-members').textContent = rows.length;
  $('#pct-members').textContent = ROWS.length
    ? (100 * rows.length / ROWS.length).toFixed(1) + '%' : '—';
  const ys = visible().map(r => r.Y).sort((a, b) => a - b);
  $('#first-member').textContent = ys.length ? 'Y = ' + ys[0] : '—';
  $('#last-member').textContent = ys.length ? 'Y = ' + ys[ys.length - 1] : '—';

  $$('#series-table thead th').forEach(th => {
    if (th.dataset.key === sortKey) {
      th.setAttribute('aria-sort', sortDir === 1 ? 'ascending' : 'descending');
    } else {
      th.removeAttribute('aria-sort');
    }
  });
}

/* -------------------------------------------------------------- charts */

const GRID = { color: COL.line, drawTicks: false };
const TICK = { color: COL.faint, font: { family: 'ui-monospace, monospace', size: 11 } };

function buildChartE() {
  const ctx = $('#chart-e');
  const floor = 1e-4;
  const pts = ROWS.map(r => ({ x: r.Y, y: Math.max(r.E, floor), _r: r }));
  const run = DATA.summary.running_minimum.map(p => ({ x: p.Y, y: Math.max(p.E, floor) }));
  const last = ROWS[ROWS.length - 1];
  if (run.length) run.push({ x: last.Y, y: run[run.length - 1].y });

  chartE = new Chart(ctx, {
    data: {
      datasets: [
        {
          type: 'scatter', label: 'outside S(ε)', data: pts,
          pointRadius: 2.2, pointHoverRadius: 5,
          backgroundColor: c => (c.raw && c.raw._r.E < EPS ? COL.good : 'rgba(151,164,182,0.42)')
        },
        {
          type: 'line', label: 'running minimum', data: run,
          borderColor: COL.moon, borderWidth: 1.6, stepped: 'after',
          pointRadius: 0, fill: false
        },
        {
          type: 'line', label: 'ε', borderColor: COL.accent, borderWidth: 1,
          borderDash: [5, 4], pointRadius: 0, fill: false,
          data: [{ x: ROWS[0].Y, y: EPS }, { x: last.Y, y: EPS }]
        }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      animation: false, parsing: false,
      interaction: { mode: 'nearest', intersect: true },
      scales: {
        x: { type: 'linear', title: { display: true, text: 'Y  (years after 2026)', color: COL.dim },
             grid: GRID, ticks: TICK, border: { color: COL.line } },
        y: { type: 'logarithmic', title: { display: true, text: 'E(Y)   degrees from full', color: COL.dim },
             grid: GRID, ticks: TICK, border: { color: COL.line } }
      },
      plugins: {
        legend: { labels: { color: COL.dim, boxWidth: 12, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: c => {
              const r = c.raw._r;
              if (!r) return 'ε = ' + degAdaptive(EPS);
              return ['Y = ' + r.Y + '   ' + r.date,
                      'E = ' + degAdaptive(r.E),
                      'slip = ' + r.slip.toFixed(4) + ' d',
                      'lit ' + pct(r.illum)];
            }
          }
        }
      }
    }
  });
}

function buildChartG() {
  chartG = new Chart($('#chart-gaps'), {
    type: 'bar',
    data: { labels: [], datasets: [{ label: 'gap to next member (years)', data: [],
            backgroundColor: 'rgba(127,184,255,0.55)', borderColor: COL.accent, borderWidth: 1 }] },
    options: {
      responsive: true, maintainAspectRatio: false, animation: false,
      scales: {
        x: { title: { display: true, text: 'from Y', color: COL.dim }, grid: { display: false }, ticks: TICK, border: { color: COL.line } },
        y: { title: { display: true, text: 'years', color: COL.dim }, grid: GRID, ticks: TICK, border: { color: COL.line }, beginAtZero: true }
      },
      plugins: { legend: { display: false } }
    }
  });
}

function updateCharts() {
  const last = ROWS[ROWS.length - 1];
  chartE.data.datasets[2].data = [{ x: ROWS[0].Y, y: EPS }, { x: last.Y, y: EPS }];
  chartE.update();

  const m = visible().slice().sort((a, b) => a.Y - b.Y);
  const labels = [], vals = [];
  for (let i = 0; i < m.length - 1; i++) {
    labels.push(String(m[i].Y));
    vals.push(m[i + 1].Y - m[i].Y);
  }
  chartG.data.labels = labels;
  chartG.data.datasets[0].data = vals;
  chartG.update();

  const note = $('#gap-note');
  if (vals.length < 2) {
    note.textContent = 'Fewer than three members at this tolerance — no gap sequence to speak of.';
  } else {
    const uniq = Array.from(new Set(vals)).sort((a, b) => a - b);
    const mean = vals.reduce((a, b) => a + b, 0) / vals.length;
    note.innerHTML = vals.length + ' gaps, ' + uniq.length + ' distinct values (' +
      uniq.join(', ') + '), mean <b>' + mean.toFixed(1) + '</b> years. ' +
      'No value repeats often enough at any ε to suggest a period.';
  }
}

/* ---------------------------------------------------------- conjectures */

function renderConjectures() {
  const c = DATA.conjectures;

  /* (a) additivity */
  const a = c.additivity;
  const closed = a.closed_under_addition;
  fill('add-status', closed
    ? '<span class="status ok">holds so far</span>'
    : '<span class="status falsified">falsified</span>');
  fill('add-nums', numsBlock([
    ['pairs tested', int(a.pairs_tested)],
    ['sum in S', int(a.sum_in_S) + ' (' + (100 * a.fraction_in_S).toFixed(1) + '%)'],
    ['sum passes C1', int(a.sum_satisfies_c1) + ' (' + (100 * a.fraction_c1).toFixed(1) + '%)'],
    ['closed', closed ? 'yes' : 'no']
  ]));
  const ex = a.examples.map(e => e.a + ' + ' + e.b + ' = ' + e.sum);
  const dadd = c.d_additivity;
  fill('add-detail',
    'S is not closed under addition. It cannot be: D itself is only additive ' +
    (100 * dadd.fraction).toFixed(1) + '% of the time (' + int(dadd.holds) + ' of ' +
    int(dadd.pairs_tested) + ' pairs), because L counts leap years in a window ' +
    'anchored at the base year and two such windows do not tile a longer one ' +
    'whenever a skipped century falls differently. The smallest failure is ' +
    'D(1) + D(1) = 730 against D(2) = 731. ' +
    (ex.length ? 'Sums that <em>do</em> land in S: ' + ex.join(', ') + '.' : ''));

  /* the 179 + 437 = 616 triple */
  const t = c.spec_triple;
  $('#triple-table tbody').innerHTML = t.terms.map(x =>
    '<tr>' +
      '<td class="num">' + x.Y + '</td>' +
      '<td class="num">' + int(x.D_gregorian) + '</td>' +
      '<td class="num">' + x.weeks_gregorian.toFixed(4) + '</td>' +
      '<td>' + yn(x.c1_gregorian) + '</td>' +
      '<td class="num">' + int(x.D_julian) + '</td>' +
      '<td class="num">' + x.weeks_julian.toFixed(0) + '</td>' +
      '<td>' + yn(x.c1_julian) + '</td>' +
    '</tr>').join('');
  fill('triple-detail',
    'The published week counts match the <b>Julian</b> column exactly and the ' +
    'Gregorian column in none of the three cases. They were computed with a ' +
    'plain every-fourth-year leap rule, giving L = 45, 109 and 154 where the ' +
    'Gregorian rule of condition C2 gives 43, 106 and 149. Under C2 as ' +
    'specified, <b>none of 179, 437 or 616 satisfies C1 at all</b>. What does ' +
    'survive: D(179) + D(437) = ' + int(t.terms[2].D_gregorian) + ' = D(616) ' +
    'exactly, so the triple really is D-additive, and the lunation counts add ' +
    'as claimed. The arithmetic was right; the leap rule was not.');

  /* (b) continued fractions */
  const cf = c.continued_fractions;
  fill('cf-ratio', cf.ratio.toFixed(9));
  const inr = cf.convergents.filter(v => v.in_range);
  const nearest = inr.filter(v => v.distance_years !== undefined)
                     .reduce((m, v) => (m === null || v.distance_years < m ? v.distance_years : m), null);
  fill('cf-status', nearest !== null && nearest < 5
    ? '<span class="status ok">predictive</span>'
    : '<span class="status falsified">no correspondence</span>');
  $('#cf-table tbody').innerHTML = inr.map(v =>
    '<tr>' +
      '<td class="num moon-cell">' + int(v.p) + ' / ' + int(v.q) + '</td>' +
      '<td class="num">' + int(v.D_pred) + '</td>' +
      '<td class="num">' + v.Y_pred.toFixed(2) + '</td>' +
      '<td class="num">' + (v.nearest_member_Y !== undefined ? v.nearest_member_Y : '—') + '</td>' +
      '<td class="num dim">' + (v.distance_years !== undefined ? v.distance_years.toFixed(1) + ' y' : '—') + '</td>' +
    '</tr>').join('');
  fill('cf-detail',
    'No convergent predicts a member of S. The closest any comes is ' +
    (nearest === null ? 'n/a' : nearest.toFixed(1) + ' years') + ', against gaps ' +
    'of order 100 years — that is not a prediction. The reason is ' +
    'structural: the convergents optimise Z/K freely, while a real member must ' +
    'also have D land exactly on a Gregorian whole-year boundary. Two ' +
    'constraints, and the convergents only respect one. ' +
    'Note too that M/7 = ' + cf.ratio_exact + ' is <em>rational</em>, so this ' +
    'continued fraction terminates after ' + cf.cf_terms.length + ' terms; its ' +
    'final convergent is not an approximation but the exact identity behind ' +
    'the theorem.');

  /* (c) gap periodicity */
  const g = c.gap_periodicity;
  fill('gap-status', g.is_periodic
    ? '<span class="status ok">periodic</span>'
    : '<span class="status open">inconclusive</span>');
  fill('gap-nums', numsBlock([
    ['gaps observed', g.length],
    ['distinct values', g.distinct_values.length],
    ['exact periods', g.exact_periods.length ? g.exact_periods.join(', ') : 'none'],
    ['best partial', (100 * g.best_partial.match_fraction).toFixed(0) + '% at p = ' + g.best_partial.period]
  ]));
  fill('gap-detail',
    'With only ' + g.length + ' gaps and ' + g.distinct_values.length +
    ' distinct values (' + g.distinct_values.join(', ') + '), no period repeats ' +
    'even once. The best partial match explains ' +
    (100 * g.best_partial.match_fraction).toFixed(0) + '% of the sequence, which ' +
    'is noise. This is <b>not evidence against periodicity</b> — the sample ' +
    'is far too small to decide. A scan to Y = 50000 would be the next step.');

  /* established: 400-periodicity */
  const p = DATA.c1_periodicity;
  fill('period-nums', numsBlock([
    ['period', p.period + ' years'],
    ['days per cycle', int(p.days_per_cycle)],
    ['weeks per cycle', int(p.weeks_per_cycle)],
    ['residues mod 400', p.residue_count],
    ['pairs checked', int(p.pairs_checked)],
    ['violations', p.violations]
  ]));
}

/* ----------------------------------------------------------- static fill */

function renderStatic() {
  const m = DATA.meta, s = DATA.summary, th = DATA.theorem, ref = DATA.reference_instance;

  fill('exact-k', int(th.minimal_exact.K));
  fill('exact-years', (th.minimal_exact.years_tropical / 1e6).toFixed(2) + ' million');
  fill('scanned', int(m.years_scanned));
  fill('survivors', int(m.counts.c1_survivors));
  fill('survivors-inline', int(m.counts.c1_survivors));
  fill('survivors-inline2', int(m.counts.c1_survivors));
  fill('exact-found', String(m.counts.exact_solutions));
  fill('best-e', degAdaptive(s.best_E));

  /* reference instance */
  const e87 = ref.ends[0], e26 = ref.ends[1];
  fill('ref-1987-theta', deg(e87.theta_00ut, 2));
  fill('ref-1987-illum', pct(e87.illum_00ut));
  fill('ref-2026-theta', deg(e26.theta_00ut, 2));
  fill('ref-2026-illum', pct(e26.illum_00ut));

  $('[data-moon="1987"]').innerHTML =
    moonDisc(e87.theta_00ut, 104) + elongationDiagram(e87.theta_00ut, 150, 104);
  $('[data-moon="2026"]').innerHTML =
    moonDisc(e26.theta_00ut, 104) + elongationDiagram(e26.theta_00ut, 150, 104);

  const met = ref.metonic;
  fill('metonic-19', met.lunations_19.toFixed(4));
  fill('metonic-38-err', Math.abs(met.lunations_38 - Math.round(met.lunations_38)).toFixed(3));
  fill('metonic-extra', met.extra_year_lunations.toFixed(4));
  fill('metonic-frac', (met.extra_year_lunations % 1).toFixed(2));
  fill('ref-slip', ref.slip.toFixed(2));

  /* methods */
  fill('kernel', m.kernel);
  fill('kernel-span', m.kernel_valid_from + ' to ' + m.kernel_valid_to);
  fill('skyfield-ver', m.software.skyfield);
  fill('python-ver', m.software.python);
  fill('generated', m.generated_utc);
  fill('runtime', m.runtime_s + ' s');
  fill('ymax-inline', String(m.ymax));
  fill('min-slip', s.abs_slip_min.toFixed(4));

  const maxDt = ROWS.reduce((x, r) => Math.max(x, Math.abs(r.delta_t_h)), 0);
  fill('max-dt', maxDt.toFixed(1));

  const bad = ROWS.find(r => r.Y === 1031);
  fill('bad-1031', bad ? deg(bad.theta, 2) : 'n/a');
}

/* ---------------------------------------------------------------- wiring */

function wire() {
  const slider = $('#eps'), out = $('#eps-out');

  function apply() {
    EPS = Math.pow(10, parseFloat(slider.value));
    out.textContent = degAdaptive(EPS);
    renderTable();
    updateCharts();
  }
  slider.addEventListener('input', apply);

  $$('#series-table thead th').forEach(th => {
    th.addEventListener('click', () => {
      const k = th.dataset.key;
      if (k === sortKey) sortDir = -sortDir;
      else { sortKey = k; sortDir = k === 'E' || k === 'slip' ? 1 : 1; }
      renderTable();
    });
  });

  apply();
}

/* ------------------------------------------------------------------ boot */

const sleep = ms => new Promise(r => setTimeout(r, ms));

/* results.json is a couple of hundred kilobytes, and a connection that
   drops mid-body yields a 200 whose json() still rejects. Retry each
   candidate a few times with a short backoff before giving up, so one bad
   read does not blank the page. */
async function load() {
  const tried = [];
  let lastErr = null;
  for (const url of DATA_PATHS) {
    for (let attempt = 1; attempt <= 3; attempt++) {
      try {
        const r = await fetch(url, { cache: 'no-cache' });
        if (!r.ok) { lastErr = new Error(url + ' -> HTTP ' + r.status); break; }
        return await r.json();
      } catch (e) {
        lastErr = e;
        tried.push(url + ' #' + attempt + ': ' + e.message);
        if (attempt < 3) await sleep(250 * attempt);
      }
    }
  }
  const err = lastErr || new Error('results.json not found');
  err.tried = tried;
  throw err;
}

load().then(d => {
  DATA = d;
  ROWS = d.rows.slice().sort((a, b) => a.Y - b.Y);
  EPS = d.meta.eps_default;
  $('#eps').value = Math.log10(EPS);
  renderStatic();
  renderConjectures();
  buildChartE();
  buildChartG();
  wire();
}).catch(err => {
  document.body.insertAdjacentHTML('afterbegin',
    '<div style="padding:20px;margin:20px;border:1px solid #f2807c;border-radius:8px;' +
    'background:#1a1013;color:#f2807c;font-family:ui-monospace,monospace;font-size:14px">' +
    '<b>Could not load data/results.json</b><br>' + String(err) +
    '<br><br>Serve the repository over HTTP rather than opening the file directly:<br>' +
    '<code>python -m http.server</code> from the repository root, then visit ' +
    '<code>/site/</code>.</div>');
  console.error(err);
});

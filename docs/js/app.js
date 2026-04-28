/* ═══════════════════════════════════════
   MediChat-RD v2.0 — app.js
   Interactive functionality for all pages
   ═══════════════════════════════════════ */

(function() {
  'use strict';

  /* ── Mobile Navigation ── */
  var toggle = document.querySelector('.nav-toggle');
  var navLinks = document.querySelector('.nav-links');
  if (toggle && navLinks) {
    toggle.addEventListener('click', function() {
      navLinks.classList.toggle('open');
    });
    document.addEventListener('click', function(e) {
      if (!toggle.contains(e.target) && !navLinks.contains(e.target)) {
        navLinks.classList.remove('open');
      }
    });
  }

  /* ── Scroll Reveal ── */
  var reveals = document.querySelectorAll('.reveal');
  if (reveals.length > 0) {
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    reveals.forEach(function(el) { observer.observe(el); });
  }

  /* ── Counter Animation ── */
  function animateCounter(el) {
    var target = parseFloat(el.getAttribute('data-count') || el.textContent.replace(/[^0-9.]/g, ''));
    var suffix = el.getAttribute('data-suffix') || '';
    var prefix = el.getAttribute('data-prefix') || '';
    var decimals = (target % 1 !== 0) ? 1 : 0;
    var duration = 2000;
    var start = 0;
    var startTime = null;

    function step(timestamp) {
      if (!startTime) startTime = timestamp;
      var progress = Math.min((timestamp - startTime) / duration, 1);
      var eased = 1 - Math.pow(1 - progress, 3);
      var current = start + (target - start) * eased;
      el.textContent = prefix + current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + suffix;
      if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  var counters = document.querySelectorAll('[data-count]');
  if (counters.length > 0) {
    var counterObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          counterObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });
    counters.forEach(function(el) { counterObserver.observe(el); });
  }

  /* ── Smooth Scroll for Anchor Links ── */
  document.querySelectorAll('a[href^="#"]').forEach(function(a) {
    a.addEventListener('click', function(e) {
      var target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (navLinks) navLinks.classList.remove('open');
      }
    });
  });

  /* ── Active Nav Link Highlight ── */
  var sections = document.querySelectorAll('section[id]');
  if (sections.length > 0) {
    var navObserver = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          var id = entry.target.getAttribute('id');
          document.querySelectorAll('.nav-links a').forEach(function(a) {
            a.classList.toggle('active', a.getAttribute('href') === '#' + id);
          });
        }
      });
    }, { threshold: 0.3 });
    sections.forEach(function(s) { navObserver.observe(s); });
  }

  /* ── Copy Code Button ── */
  document.querySelectorAll('.copy-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var code = this.closest('.code-block').querySelector('code').textContent;
      navigator.clipboard.writeText(code).then(function() {
        btn.textContent = 'Copied!';
        setTimeout(function() { btn.textContent = 'Copy'; }, 2000);
      });
    });
  });

  /* ── Diagnosis Demo ── */
  var diagnosisForm = document.getElementById('diagnosis-form');
  var diagnosisResult = document.getElementById('diagnosis-result');
  if (diagnosisForm && diagnosisResult) {
    diagnosisForm.addEventListener('submit', function(e) {
      e.preventDefault();
      var symptoms = document.getElementById('symptoms-input').value.trim();
      if (!symptoms) return;

      diagnosisResult.classList.add('show');
      diagnosisResult.innerHTML = '<div style="text-align:center;padding:2rem"><div class="animate-pulse" style="font-size:1.2rem">AI Analysis in progress...</div></div>';

      setTimeout(function() {
        var results = generateDiagnosis(symptoms);
        var html = '<h3>AI Diagnostic Results</h3>';
        html += '<p style="color:var(--text-dim);margin-bottom:1rem">Based on symptom analysis: <em>"' + symptoms + '"</em></p>';
        results.forEach(function(r) {
          html += '<div class="diagnosis-item">';
          html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.3rem">';
          html += '<strong>' + r.name + '</strong>';
          html += '<span class="confidence ' + r.level + '">' + r.confidence + '% confidence</span>';
          html += '</div>';
          html += '<p style="font-size:0.85rem;color:var(--text-dim);margin:0">' + r.desc + '</p>';
          html += '</div>';
        });
        html += '<p style="margin-top:1rem;font-size:0.8rem;color:var(--text-dim)">Disclaimer: This is a demo simulation. Real diagnosis requires clinical evaluation.</p>';
        diagnosisResult.innerHTML = html;
      }, 1500);
    });
  }

  function generateDiagnosis(symptoms) {
    var s = symptoms.toLowerCase();
    var results = [];
    if (s.match(/fatigue|weakness|tired|exhaust/i)) {
      results.push({ name: 'Myasthenia Gravis', confidence: 72, level: 'high', desc: 'Autoimmune neuromuscular disorder causing skeletal muscle weakness' });
      results.push({ name: 'Chronic Fatigue Syndrome', confidence: 58, level: 'medium', desc: 'Complex disorder with extreme fatigue not improved by rest' });
    }
    if (s.match(/joint|pain|swelling|stiff/i)) {
      results.push({ name: 'Ehlers-Danlos Syndrome', confidence: 65, level: 'medium', desc: 'Group of inherited connective tissue disorders affecting collagen' });
      results.push({ name: 'Systemic Lupus Erythematosus', confidence: 45, level: 'medium', desc: 'Chronic autoimmune disease affecting multiple organ systems' });
    }
    if (s.match(/skin|rash|blister|itch/i)) {
      results.push({ name: 'Pemphigus Vulgaris', confidence: 68, level: 'medium', desc: 'Rare autoimmune blistering disease affecting skin and mucous membranes' });
      results.push({ name: 'Epidermolysis Bullosa', confidence: 52, level: 'medium', desc: 'Group of genetic conditions causing fragile, blistering skin' });
    }
    if (s.match(/vision|eye|blind|see/i)) {
      results.push({ name: 'Retinitis Pigmentosa', confidence: 74, level: 'high', desc: 'Inherited degenerative eye disease causing progressive vision loss' });
    }
    if (s.match(/breath|lung|respirat|cough/i)) {
      results.push({ name: 'Pulmonary Fibrosis', confidence: 61, level: 'medium', desc: 'Progressive scarring of lung tissue impairing respiratory function' });
      results.push({ name: 'Cystic Fibrosis', confidence: 48, level: 'medium', desc: 'Inherited disorder causing damage to lungs and digestive system' });
    }
    if (s.match(/muscle|atrophy|weak|paraly/i)) {
      results.push({ name: 'Spinal Muscular Atrophy', confidence: 70, level: 'high', desc: 'Genetic disease destroying motor neurons controlling voluntary muscles' });
      results.push({ name: 'Duchenne Muscular Dystrophy', confidence: 55, level: 'medium', desc: 'X-linked genetic disorder characterized by progressive muscle degeneration' });
    }
    if (s.match(/seizure|epilep|convuls/i)) {
      results.push({ name: 'Dravet Syndrome', confidence: 66, level: 'medium', desc: 'Severe form of epilepsy with prolonged seizures beginning in infancy' });
    }
    if (s.match(/blood|bleed|bruise|clot/i)) {
      results.push({ name: 'Hemophilia A', confidence: 71, level: 'high', desc: 'X-linked bleeding disorder caused by deficiency of clotting factor VIII' });
      results.push({ name: 'von Willebrand Disease', confidence: 54, level: 'medium', desc: 'Most common inherited bleeding disorder affecting blood clotting' });
    }
    if (results.length === 0) {
      results.push({ name: 'Multi-system Rare Disease Assessment', confidence: 42, level: 'low', desc: 'Symptoms may be associated with multiple rare conditions. Recommend comprehensive genetic testing.' });
      results.push({ name: 'Mitochondrial Disease', confidence: 38, level: 'low', desc: 'Group of disorders caused by dysfunctional mitochondria affecting energy production' });
    }
    results.sort(function(a, b) { return b.confidence - a.confidence; });
    return results.slice(0, 4);
  }

  /* ── Knowledge Graph Visualization ── */
  var graphCanvas = document.getElementById('knowledge-graph-canvas');
  if (graphCanvas) {
    var ctx = graphCanvas.getContext('2d');
    var W = graphCanvas.parentElement.clientWidth;
    var H = 500;
    graphCanvas.width = W;
    graphCanvas.height = H;

    var diseases = [
      {name:'Myasthenia Gravis',cat:'Neuro',x:0.3,y:0.3,color:'#e94560'},
      {name:'Ehlers-Danlos',cat:'Connective',x:0.6,y:0.2,color:'#06b6d4'},
      {name:'Retinitis Pigmentosa',cat:'Ophthalmology',x:0.2,y:0.6,color:'#8b5cf6'},
      {name:'Hemophilia A',cat:'Hematology',x:0.7,y:0.5,color:'#f59e0b'},
      {name:'Cystic Fibrosis',cat:'Pulmonology',x:0.5,y:0.7,color:'#10b981'},
      {name:'SMA',cat:'Neuro',x:0.15,y:0.45,color:'#e94560'},
      {name:'Pemphigus',cat:'Dermatology',x:0.8,y:0.3,color:'#ec4899'},
      {name:'Lupus (SLE)',cat:'Autoimmune',x:0.45,y:0.45,color:'#14b8a6'},
      {name:'Dravet Syndrome',cat:'Neuro',x:0.25,y:0.15,color:'#e94560'},
      {name:'Pulmonary Fibrosis',cat:'Pulmonology',x:0.65,y:0.7,color:'#10b981'},
      {name:'Marfan Syndrome',cat:'Connective',x:0.75,y:0.15,color:'#06b6d4'},
      {name:'Gaucher Disease',cat:'Metabolic',x:0.5,y:0.15,color:'#a78bfa'},
    ];

    var connections = [
      [0,5],[0,7],[1,10],[2,6],[3,4],[4,9],[5,8],[7,1],[7,6],[9,4],[10,1],[11,7]
    ];

    var nodes = diseases.map(function(d) {
      return { x: W * d.x, y: H * d.y, vx: 0, vy: 0, data: d, r: 6 };
    });

    function drawGraph() {
      ctx.clearRect(0, 0, W, H);
      connections.forEach(function(c) {
        var a = nodes[c[0]], b = nodes[c[1]];
        ctx.beginPath();
        ctx.moveTo(a.x, a.y);
        ctx.lineTo(b.x, b.y);
        ctx.strokeStyle = 'rgba(255,255,255,0.08)';
        ctx.lineWidth = 1;
        ctx.stroke();
      });
      nodes.forEach(function(n) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.data.color;
        ctx.fill();
        ctx.strokeStyle = 'rgba(255,255,255,0.2)';
        ctx.lineWidth = 1;
        ctx.stroke();
        ctx.fillStyle = '#e2e8f0';
        ctx.font = '10px Inter, system-ui, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(n.data.name, n.x, n.y + n.r + 14);
      });
    }

    // Draggable nodes
    var dragging = null;
    graphCanvas.addEventListener('mousedown', function(e) {
      var rect = graphCanvas.getBoundingClientRect();
      var mx = e.clientX - rect.left, my = e.clientY - rect.top;
      for (var i = 0; i < nodes.length; i++) {
        var dx = nodes[i].x - mx, dy = nodes[i].y - my;
        if (Math.sqrt(dx * dx + dy * dy) < 20) { dragging = i; break; }
      }
    });
    graphCanvas.addEventListener('mousemove', function(e) {
      if (dragging !== null) {
        var rect = graphCanvas.getBoundingClientRect();
        nodes[dragging].x = e.clientX - rect.left;
        nodes[dragging].y = e.clientY - rect.top;
        drawGraph();
      }
    });
    graphCanvas.addEventListener('mouseup', function() { dragging = null; });
    graphCanvas.addEventListener('mouseleave', function() { dragging = null; });

    drawGraph();
  }

  /* ── Database Search/Filter ── */
  var dbSearch = document.getElementById('db-search');
  var dbCategory = document.getElementById('db-category');
  if (dbSearch && dbCategory) {
    function filterDB() {
      var q = dbSearch.value.toLowerCase();
      var cat = dbCategory.value;
      document.querySelectorAll('.db-row').forEach(function(row) {
        var text = row.textContent.toLowerCase();
        var rowCat = row.getAttribute('data-category') || '';
        var show = text.indexOf(q) >= 0 && (!cat || rowCat === cat);
        row.style.display = show ? '' : 'none';
      });
    }
    dbSearch.addEventListener('input', filterDB);
    dbCategory.addEventListener('change', filterDB);
  }

  /* ── API Endpoint Toggle ── */
  document.querySelectorAll('.api-endpoint-header').forEach(function(header) {
    header.addEventListener('click', function() {
      var body = this.nextElementSibling;
      if (body) {
        body.style.display = body.style.display === 'none' ? 'block' : 'none';
        this.classList.toggle('active');
      }
    });
  });

  /* ── FAQ Accordion ── */
  document.querySelectorAll('.faq-question').forEach(function(q) {
    q.addEventListener('click', function() {
      var answer = this.nextElementSibling;
      var isOpen = answer.style.maxHeight;
      document.querySelectorAll('.faq-answer').forEach(function(a) { a.style.maxHeight = null; });
      if (!isOpen) answer.style.maxHeight = answer.scrollHeight + 'px';
    });
  });

})();

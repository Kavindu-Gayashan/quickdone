# ============================================================
# QUICKDONE — HTML TEMPLATES & PRESENTATION LAYER
# File: templates.py
# ============================================================
# Offersale Dribbble-inspired UI Design System
# Jinja2 template strings rendered via render_template_string()
# ============================================================

# ============================================================
# HTML TEMPLATES & CSS
# All embedded templates use render_template_string with Jinja2.
# SHARED_CSS is defined once and embedded in every page via Python
# string concatenation at module load time (no runtime overhead).
# ============================================================

SHARED_CSS = """
/* ---- RESET & BASE ---- */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
:root{
  --g950:#062F25;--g900:#083B2E;--g800:#0B4A39;--g700:#12634A;
  --m100:#E7F2EC;--m200:#D4E8DC;
  --bg:#F7F8F5;--surf:#FFFFFF;
  --tp:#18231E;--ts:#69766F;--bd:#E5EAE6;--star:#E9AD45;
  --r:10px;--rl:16px;--sh:0 2px 12px rgba(0,0,0,.07);
}
body{font-family:'Inter',system-ui,-apple-system,BlinkMacSystemFont,sans-serif;
  background:var(--bg);color:var(--tp);line-height:1.65;font-size:15px;
  -webkit-font-smoothing:antialiased;}
a{color:inherit;text-decoration:none;}
img{max-width:100%;display:block;}
button,input,select,textarea{font-family:inherit;}

/* ---- CONTAINER ---- */
.c{max-width:1240px;margin:0 auto;padding:0 24px;}

/* ---- NAVIGATION ---- */
.nav-h{position:absolute;top:0;left:0;right:0;z-index:100;}
.nav-s{position:sticky;top:0;z-index:100;background:var(--surf);
  border-bottom:1.5px solid var(--bd);}
.nav-i{max-width:1240px;margin:0 auto;padding:0 24px;
  display:flex;align-items:center;height:68px;}
.nav-logo{display:flex;align-items:center;gap:9px;font-size:19px;
  font-weight:800;letter-spacing:-.5px;flex-shrink:0;}
.nav-logo-mark{width:30px;height:30px;background:var(--g700);border-radius:8px;
  display:flex;align-items:center;justify-content:center;
  font-size:14px;font-weight:900;color:#fff;}
.nav-h .nav-logo{color:#fff;}
.nav-s .nav-logo{color:var(--tp);}
.nav-h .nav-logo-mark{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.25);}
.nav-links{display:flex;gap:4px;list-style:none;margin:0 auto;}
.nav-links a{font-size:14px;font-weight:500;padding:7px 14px;
  border-radius:7px;transition:background .15s,color .15s;}
.nav-h .nav-links a{color:rgba(255,255,255,.85);}
.nav-h .nav-links a:hover{background:rgba(255,255,255,.1);color:#fff;}
.nav-s .nav-links a{color:var(--ts);}
.nav-s .nav-links a:hover{background:var(--bg);color:var(--tp);}
.nav-actions{display:flex;gap:8px;align-items:center;}

/* ---- BUTTONS ---- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;
  padding:10px 20px;border-radius:var(--r);font-size:14px;font-weight:600;
  border:none;cursor:pointer;transition:all .15s;text-align:center;
  line-height:1;white-space:nowrap;}
.btn-p{background:var(--g800);color:#fff;}
.btn-p:hover{background:var(--g700);}
.btn-s{background:#fff;color:var(--g800);border:1.5px solid var(--bd);}
.btn-s:hover{border-color:var(--g700);color:var(--g700);}
.btn-d{background:#FEE2E2;color:#991B1B;}
.btn-d:hover{background:#FECACA;}
.btn-sm{padding:7px 15px;font-size:13px;}
.btn-fw{width:100%;display:flex;}
.btn-ghost-w{color:rgba(255,255,255,.9);border:1.5px solid rgba(255,255,255,.3);}
.btn-ghost-w:hover{background:rgba(255,255,255,.1);}
.btn-cta-hero{background:#fff;color:var(--g900);}
.btn-cta-hero:hover{background:var(--m100);}
.btn-s-nav{background:#fff;color:var(--g800);border:1.5px solid var(--bd);}
.btn-s-nav:hover{border-color:var(--g700);}

/* ---- HERO ---- */
.hero{position:relative;min-height:580px;display:flex;align-items:center;
  background:var(--g950);overflow:hidden;}
.hero-bg{position:absolute;inset:0;background-size:cover;
  background-position:center;opacity:.38;}
.hero-ov{position:absolute;inset:0;
  background:linear-gradient(135deg,rgba(6,47,37,.93) 0%,rgba(8,59,46,.78) 55%,rgba(11,74,57,.65) 100%);}
.hero-ct{position:relative;z-index:10;width:100%;max-width:1240px;
  margin:0 auto;padding:112px 24px 64px;text-align:center;}
.hero-title{font-size:clamp(28px,5vw,54px);font-weight:800;color:#fff;
  line-height:1.08;letter-spacing:-.025em;margin-bottom:16px;}
.hero-sub{font-size:17px;color:rgba(255,255,255,.78);max-width:500px;
  margin:0 auto 36px;line-height:1.6;}

/* ---- SEARCH BAR ---- */
.sb-wrap{max-width:700px;margin:0 auto;}
.sb{background:#fff;border-radius:50px;display:flex;align-items:center;
  padding:5px 5px 5px 22px;box-shadow:0 10px 40px rgba(0,0,0,.28);}
.sb input[type=text]{flex:1;border:none;outline:none;font-size:15px;
  color:var(--tp);background:transparent;min-width:0;}
.sb input[type=text]::placeholder{color:var(--ts);}
.sb-div{width:1.5px;height:24px;background:var(--bd);margin:0 12px;flex-shrink:0;}
.sb select{border:none;outline:none;font-size:14px;color:var(--ts);
  background:transparent;cursor:pointer;padding:0 4px;min-width:130px;
  -webkit-appearance:none;}
.sb-btn{background:var(--g800);color:#fff;border:none;border-radius:44px;
  padding:12px 28px;font-size:14px;font-weight:600;cursor:pointer;
  transition:background .15s;flex-shrink:0;}
.sb-btn:hover{background:var(--g700);}

/* ---- CATEGORY SHORTCUTS ---- */
.cat-short{display:flex;flex-wrap:wrap;gap:10px;justify-content:center;
  margin-top:28px;position:relative;z-index:10;}
.cat-pill{display:flex;align-items:center;gap:7px;
  background:rgba(255,255,255,.11);border:1.5px solid rgba(255,255,255,.22);
  border-radius:50px;padding:7px 16px;color:#fff;font-size:13px;
  font-weight:500;transition:all .15s;backdrop-filter:blur(4px);}
.cat-pill:hover{background:rgba(255,255,255,.20);border-color:rgba(255,255,255,.4);}

/* ---- SECTIONS ---- */
.sec{padding:72px 0;}
.sec-sm{padding:48px 0;}
.sec-bg-w{background:#fff;}
.sec-bg-pg{background:var(--bg);}
.sl{font-size:11.5px;font-weight:700;letter-spacing:.09em;
  text-transform:uppercase;color:var(--g700);margin-bottom:10px;}
.st{font-size:30px;font-weight:800;color:var(--tp);letter-spacing:-.02em;
  margin-bottom:10px;line-height:1.1;}
.ss{font-size:15px;color:var(--ts);max-width:480px;line-height:1.65;}
.sh{margin-bottom:44px;}
.sh-row{display:flex;align-items:flex-end;justify-content:space-between;
  margin-bottom:44px;}

/* ---- CATEGORY CARDS (tall, image-based) ---- */
.cc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:20px;}
.cc{position:relative;border-radius:var(--rl);overflow:hidden;height:310px;
  display:block;transition:transform .2s;}
.cc:hover{transform:translateY(-4px);}
.cc:hover .cc-bg{transform:scale(1.05);}
.cc-bg{position:absolute;inset:0;background-size:cover;background-position:center;
  background-color:var(--g800);transition:transform .3s ease;}
.cc-ov{position:absolute;inset:0;
  background:linear-gradient(to top,rgba(6,47,37,.92) 0%,rgba(6,47,37,.35) 55%,transparent 100%);}
.cc-body{position:absolute;bottom:0;left:0;right:0;padding:20px;}
.cc-name{color:#fff;font-size:18px;font-weight:700;line-height:1.2;}
.cc-count{color:rgba(255,255,255,.70);font-size:13px;margin-top:5px;}

/* ---- WORKER CARDS ---- */
.wc-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:20px;}
.wc{background:#fff;border-radius:var(--rl);border:1.5px solid var(--bd);
  padding:20px;display:flex;flex-direction:column;gap:14px;
  transition:box-shadow .2s,transform .2s;}
.wc:hover{box-shadow:var(--sh);transform:translateY(-2px);}
.wc-top{display:flex;align-items:flex-start;gap:14px;}
.av{width:50px;height:50px;border-radius:50%;background:var(--g800);color:#fff;
  font-size:17px;font-weight:700;display:flex;align-items:center;
  justify-content:center;flex-shrink:0;}
.av-lg{width:76px;height:76px;font-size:26px;}
.av-xl{width:88px;height:88px;font-size:30px;border:3px solid rgba(255,255,255,.2);}
.wn{font-size:16px;font-weight:700;line-height:1.2;}
.wm{font-size:13px;color:var(--ts);display:flex;align-items:center;
  gap:10px;flex-wrap:wrap;margin-top:4px;}
.tags{display:flex;flex-wrap:wrap;gap:6px;}
.tag{display:inline-block;background:var(--m100);color:var(--g800);
  font-size:12px;font-weight:600;padding:3px 10px;border-radius:50px;}
.rate-t{font-size:13px;color:var(--ts);}
.rate-t strong{color:var(--tp);}

/* ---- STEPS ---- */
.steps-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:32px;}
.step-card{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:32px 24px;text-align:center;}
.step-num{width:46px;height:46px;border-radius:50%;background:var(--g800);
  color:#fff;font-size:20px;font-weight:800;display:flex;align-items:center;
  justify-content:center;margin:0 auto 16px;}
.step-title{font-size:16px;font-weight:700;margin-bottom:8px;}
.step-desc{font-size:14px;color:var(--ts);}

/* ---- FOOTER ---- */
.footer{background:var(--g950);color:rgba(255,255,255,.65);padding:56px 0 28px;}
.ft{display:flex;justify-content:space-between;align-items:flex-start;
  margin-bottom:44px;gap:32px;}
.fl{font-size:20px;font-weight:800;color:#fff;display:flex;
  align-items:center;gap:9px;margin-bottom:10px;}
.fl-mark{width:28px;height:28px;background:var(--g700);border-radius:7px;
  display:flex;align-items:center;justify-content:center;
  font-size:13px;color:#fff;font-weight:900;}
.ft-tag{font-size:13px;max-width:260px;line-height:1.6;}
.ft-cols{display:flex;gap:56px;}
.ft-col h4{color:#fff;font-size:13px;font-weight:700;margin-bottom:14px;}
.ft-col a{display:block;font-size:13px;color:rgba(255,255,255,.60);
  line-height:2.2;transition:color .15s;}
.ft-col a:hover{color:#fff;}
.ft-bot{border-top:1px solid rgba(255,255,255,.10);padding-top:24px;font-size:12.5px;}

/* ---- FLASH ---- */
.fl-wrap{padding:12px 0;}
.fl-ct{max-width:1240px;margin:0 auto;padding:0 24px;}
.fl-msg{padding:12px 18px;border-radius:8px;font-size:14px;margin-bottom:8px;}
.fl-success{background:#D1FAE5;color:#065F46;border:1px solid #A7F3D0;}
.fl-error{background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;}
.fl-info{background:var(--m100);color:var(--g900);border:1px solid var(--m200);}
.fl-warning{background:#FEF3C7;color:#92400E;border:1px solid #FDE68A;}

/* ---- FORMS ---- */
.fg{margin-bottom:20px;}
.fl-label{display:block;font-size:12.5px;font-weight:700;color:var(--ts);
  letter-spacing:.05em;text-transform:uppercase;margin-bottom:7px;}
.fi,.fsel,.fta{width:100%;padding:11px 14px;border:1.5px solid var(--bd);
  border-radius:var(--r);font-size:15px;color:var(--tp);background:#fff;
  transition:border-color .15s;outline:none;-webkit-appearance:none;}
.fi:focus,.fsel:focus,.fta:focus{border-color:var(--g700);
  box-shadow:0 0 0 3px rgba(18,99,74,.10);}
.fta{min-height:100px;resize:vertical;}
.fsel{appearance:none;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8'%3E%3Cpath fill='%2369766F' d='M6 8L0 0h12z'/%3E%3C/svg%3E");
  background-repeat:no-repeat;background-position:right 14px center;padding-right:36px;}
.fr{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.f-hint{font-size:12px;color:var(--ts);margin-top:5px;}

/* ---- PAGE HEADER ---- */
.ph{background:var(--g900);padding:44px 0;color:#fff;}
.ph h1{font-size:26px;font-weight:800;margin-bottom:6px;}
.ph p{color:rgba(255,255,255,.70);font-size:15px;}

/* ---- PROFILE PAGE ---- */
.prof-h{background:var(--g900);padding:48px 0;}
.prof-hi{max-width:1240px;margin:0 auto;padding:0 24px;
  display:flex;align-items:flex-start;gap:24px;}
.prof-info h1{font-size:26px;font-weight:800;color:#fff;margin-bottom:8px;}
.prof-meta{display:flex;flex-wrap:wrap;gap:16px;color:rgba(255,255,255,.75);
  font-size:14px;}
.prof-meta span{display:flex;align-items:center;gap:5px;}
.prof-rating{margin-top:12px;display:flex;align-items:center;gap:10px;}
.r-big{font-size:22px;font-weight:800;color:#fff;}
.prof-body{max-width:1240px;margin:0 auto;padding:32px 24px 56px;
  display:grid;grid-template-columns:1fr 320px;gap:24px;}
.panel{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  overflow:hidden;margin-bottom:20px;}
.pan-h{padding:15px 20px;font-size:14px;font-weight:700;
  border-bottom:1.5px solid var(--bd);color:var(--tp);}
.pan-b{padding:20px;}
.pan-b p{font-size:14px;color:var(--ts);line-height:1.65;}
.avail-row{display:flex;gap:10px;align-items:center;
  padding:7px 0;border-bottom:1px solid var(--bd);font-size:14px;}
.avail-row:last-child{border-bottom:none;}
.avail-day{width:100px;font-weight:600;color:var(--tp);}
.avail-time{color:var(--ts);}
.rev-item{padding:16px 0;border-bottom:1px solid var(--bd);}
.rev-item:last-child{border-bottom:none;}
.rev-hd{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.rev-nm{font-weight:700;font-size:14px;}
.rev-dt{font-size:12px;color:var(--ts);margin-left:auto;}
.rev-txt{font-size:14px;color:var(--ts);line-height:1.65;}

/* ---- DASHBOARD ---- */
.dash-wrap{display:flex;min-height:calc(100vh - 68px);}
.sidebar{width:220px;background:#fff;border-right:1.5px solid var(--bd);
  padding:20px 0;flex-shrink:0;}
.sb-logo{padding:0 16px 16px;border-bottom:1.5px solid var(--bd);margin-bottom:8px;}
.sb-logo-txt{font-size:17px;font-weight:800;color:var(--tp);
  display:flex;align-items:center;gap:7px;}
.sb-logo-mark{width:24px;height:24px;background:var(--g800);color:#fff;
  border-radius:6px;display:flex;align-items:center;justify-content:center;
  font-size:12px;font-weight:900;}
.sb-user{font-size:12px;color:var(--ts);margin-top:5px;}
.sb-nav{padding:8px 0;}
.sb-nav a{display:flex;align-items:center;gap:8px;padding:9px 16px;
  font-size:14px;font-weight:500;color:var(--ts);
  border-left:3px solid transparent;transition:all .15s;}
.sb-nav a:hover,.sb-nav a.active{background:var(--m100);color:var(--g800);
  border-left-color:var(--g800);}
.sb-sec{font-size:11px;font-weight:700;text-transform:uppercase;
  letter-spacing:.07em;color:var(--ts);padding:12px 16px 4px;opacity:.7;}
.dash-main{flex:1;padding:32px;overflow-y:auto;background:var(--bg);}
.dash-title{font-size:22px;font-weight:800;margin-bottom:24px;}

/* ---- KPI ---- */
.kpi-row{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));
  gap:16px;margin-bottom:28px;}
.kpi{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:20px;}
.kpi-gl{border-left:3px solid var(--g700);}
.kpi-l{font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.06em;color:var(--ts);margin-bottom:10px;}
.kpi-v{font-size:32px;font-weight:800;color:var(--tp);line-height:1;}
.kpi-s{font-size:12px;color:var(--ts);margin-top:5px;}

/* ---- TABLES ---- */
.tw{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  overflow:hidden;margin-bottom:24px;}
.tw-hd{display:flex;align-items:center;justify-content:space-between;
  padding:14px 20px;border-bottom:1.5px solid var(--bd);}
.tw-t{font-size:15px;font-weight:700;}
table{width:100%;border-collapse:collapse;}
thead th{text-align:left;padding:10px 16px;font-size:11px;font-weight:700;
  text-transform:uppercase;letter-spacing:.06em;color:var(--ts);
  background:var(--bg);border-bottom:1.5px solid var(--bd);}
tbody td{padding:12px 16px;font-size:14px;border-bottom:1px solid var(--bd);
  vertical-align:middle;}
tbody tr:last-child td{border-bottom:none;}
tbody tr:hover td{background:#FAFBFA;}

/* ---- STATUS ---- */
.st-b{display:inline-block;padding:3px 10px;border-radius:50px;
  font-size:11.5px;font-weight:700;letter-spacing:.03em;}
.s-PENDING{background:#FEF3C7;color:#92400E;}
.s-CONFIRMED{background:#DBEAFE;color:#1E40AF;}
.s-IN_PROGRESS{background:var(--m100);color:var(--g800);}
.s-COMPLETED{background:#D1FAE5;color:#065F46;}
.s-CANCELLED{background:#FEE2E2;color:#991B1B;}

/* ---- BADGE PILL ---- */
.badge-pill{display:inline-flex;align-items:center;gap:5px;background:var(--m100);
  color:var(--g800);font-size:12px;font-weight:700;padding:4px 11px;
  border-radius:50px;border:1.5px solid var(--m200);}

/* ---- AUTH PAGES ---- */
.auth-pg{min-height:100vh;display:flex;align-items:center;justify-content:center;
  background:var(--g950);padding:24px;}
.auth-card{background:#fff;border-radius:var(--rl);padding:40px;
  width:100%;max-width:460px;box-shadow:0 20px 60px rgba(0,0,0,.35);}
.auth-logo{text-align:center;margin-bottom:28px;}
.auth-logo-mark{width:48px;height:48px;background:var(--g800);border-radius:13px;
  color:#fff;font-size:22px;font-weight:900;display:inline-flex;
  align-items:center;justify-content:center;margin-bottom:10px;}
.auth-logo-name{font-size:22px;font-weight:800;color:var(--tp);}
.auth-t{font-size:20px;font-weight:800;margin-bottom:5px;}
.auth-s{font-size:14px;color:var(--ts);margin-bottom:28px;}
.auth-sw{text-align:center;font-size:13px;color:var(--ts);margin-top:20px;}
.auth-sw a{color:var(--g800);font-weight:600;}
.ut-tabs{display:flex;border:1.5px solid var(--bd);border-radius:var(--r);
  overflow:hidden;margin-bottom:24px;}
.ut-tab{flex:1;padding:10px;text-align:center;font-size:14px;font-weight:600;
  cursor:pointer;color:var(--ts);border:none;background:#fff;
  transition:all .15s;}
.ut-tab.act{background:var(--g800);color:#fff;}

/* ---- FILTER BAR ---- */
.fbar{background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);
  padding:20px;display:flex;gap:16px;align-items:flex-end;
  flex-wrap:wrap;margin-bottom:28px;}
.fg-f{display:flex;flex-direction:column;gap:6px;min-width:150px;flex:1;}
.fg-fl{font-size:11.5px;font-weight:700;text-transform:uppercase;
  letter-spacing:.05em;color:var(--ts);}
.f-in,.f-sel{padding:9px 13px;border:1.5px solid var(--bd);
  border-radius:var(--r);font-size:14px;color:var(--tp);
  background:#fff;outline:none;-webkit-appearance:none;
  transition:border-color .15s;width:100%;}
.f-in:focus,.f-sel:focus{border-color:var(--g700);}

/* ---- EMPTY STATE ---- */
.empty{text-align:center;padding:56px 24px;}
.empty-icon{font-size:48px;margin-bottom:16px;}
.empty-t{font-size:18px;font-weight:700;margin-bottom:8px;}
.empty-s{font-size:14px;color:var(--ts);max-width:320px;margin:0 auto 20px;}

/* ---- MISC ---- */
.div{height:1.5px;background:var(--bd);margin:20px 0;}
.tc{text-align:center;}.ts-m{color:var(--ts);}.ts-sm{font-size:13px;}
.fw7{font-weight:700;}.mt-a{margin-top:auto;}
.mt16{margin-top:16px;}.mb16{margin-bottom:16px;}.mb24{margin-bottom:24px;}
.star-y{color:var(--star);}
.flex-row{display:flex;align-items:center;gap:12px;}
.ml-a{margin-left:auto;}
.p0{padding:0;}

/* ---- BOOKING ACTION FORM ---- */
.ba-form{display:inline;}

/* ---- RESPONSIVE ---- */
@media(max-width:768px){
  .nav-links{display:none;}
  .hero{min-height:480px;}
  .hero-ct{padding:90px 20px 50px;}
  .sb{flex-wrap:wrap;border-radius:16px;padding:12px;border-radius:14px;}
  .sb-div{display:none;}
  .sb-btn{width:100%;border-radius:var(--r);margin-top:8px;padding:12px;}
  .cc-grid{grid-template-columns:repeat(2,1fr);}
  .steps-grid{grid-template-columns:1fr;}
  .prof-body{grid-template-columns:1fr;}
  .dash-wrap{flex-direction:column;}
  .sidebar{width:100%;border-right:none;border-bottom:1.5px solid var(--bd);}
  .ft{flex-direction:column;}
  .ft-cols{flex-wrap:wrap;gap:24px;}
  .fr{grid-template-columns:1fr;}
  .kpi-row{grid-template-columns:repeat(2,1fr);}
  .sh-row{flex-direction:column;gap:16px;align-items:flex-start;}
  .wc-grid{grid-template-columns:1fr;}
}
"""

# -- Shared nav + footer Jinja2 template fragments --

_NAV_H = """
<nav class="nav-h">
  <div class="nav-i">
    <a class="nav-logo" href="/"><span class="nav-logo-mark">Q</span>QuickDone</a>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/workers">Find Workers</a></li>
    </ul>
    <div class="nav-actions">
      {% if session.get('user_type') == 'customer' %}
        <a href="/dashboard/customer" class="btn btn-sm btn-ghost-w">My Bookings</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% elif session.get('user_type') == 'worker' %}
        <a href="/dashboard/worker" class="btn btn-sm btn-ghost-w">Dashboard</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% elif session.get('user_type') == 'admin' %}
        <a href="/admin/dashboard" class="btn btn-sm btn-ghost-w">Admin</a>
        <a href="/logout" class="btn btn-sm btn-cta-hero">Log Out</a>
      {% else %}
        <a href="/login" class="btn btn-sm btn-ghost-w">Log In</a>
        <a href="/register/customer" class="btn btn-sm btn-cta-hero">Get Started</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

_NAV_S = """
<nav class="nav-s">
  <div class="nav-i">
    <a class="nav-logo" href="/"><span class="nav-logo-mark" style="background:var(--g700);border:none;">Q</span>QuickDone</a>
    <ul class="nav-links">
      <li><a href="/">Home</a></li>
      <li><a href="/workers">Find Workers</a></li>
    </ul>
    <div class="nav-actions">
      {% if session.get('user_type') == 'customer' %}
        <a href="/dashboard/customer" class="btn btn-sm btn-s-nav">My Bookings</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% elif session.get('user_type') == 'worker' %}
        <a href="/dashboard/worker" class="btn btn-sm btn-s-nav">Dashboard</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% elif session.get('user_type') == 'admin' %}
        <a href="/admin/dashboard" class="btn btn-sm btn-s-nav">Admin Panel</a>
        <a href="/logout" class="btn btn-sm btn-p">Log Out</a>
      {% else %}
        <a href="/login" class="btn btn-sm btn-s">Log In</a>
        <a href="/register/customer" class="btn btn-sm btn-p">Get Started</a>
      {% endif %}
    </div>
  </div>
</nav>
"""

_FLASHES = """
{% with messages = get_flashed_messages(with_categories=True) %}
{% if messages %}
<div class="fl-wrap"><div class="fl-ct">
{% for cat, msg in messages %}
<div class="fl-msg fl-{{ cat }}">{{ msg }}</div>
{% endfor %}
</div></div>
{% endif %}
{% endwith %}
"""

_FOOTER = """
<footer class="footer">
  <div class="c">
    <div class="ft">
      <div>
        <div class="fl"><span class="fl-mark">Q</span>QuickDone</div>
        <p class="ft-tag">Connecting trusted local service professionals with people who need them across Sri Lanka.</p>
      </div>
      <div class="ft-cols">
        <div class="ft-col">
          <h4>Find Services</h4>
          <a href="/workers">All Workers</a>
          <a href="/workers?category_id=1">Electrical</a>
          <a href="/workers?category_id=2">Plumbing</a>
          <a href="/workers?category_id=3">AC Servicing</a>
          <a href="/workers?category_id=4">Deep Cleaning</a>
          <a href="/workers?category_id=5">Carpentry</a>
        </div>
        <div class="ft-col">
          <h4>Account</h4>
          <a href="/login">Log In</a>
          <a href="/register/customer">Register as Customer</a>
          <a href="/register/worker">Join as Worker</a>
          <a href="/admin/login">Admin Login</a>
        </div>
      </div>
    </div>
    <div class="ft-bot">© 2026 QuickDone — DBMS Foundations Assignment</div>
  </div>
</footer>
"""


def _page(title, body, nav='solid'):
    """Wrap body Jinja2 string in a complete HTML page with shared CSS."""
    nav_html = _NAV_H if nav == 'hero' else _NAV_S
    return (
        '<!DOCTYPE html><html lang="en"><head>'
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        '<title>' + title + ' | QuickDone</title>'
        '<link rel="preconnect" href="https://fonts.googleapis.com">'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
        '<style>' + SHARED_CSS + '</style>'
        '</head><body>'
        + nav_html + _FLASHES + body + _FOOTER +
        '</body></html>'
    )


# ============================================================
# PAGE: HOMEPAGE
# ============================================================

HOME_TEMPLATE = _page('Find Skilled Workers', """
<section class="hero">
  <div class="hero-bg" style="background-image:url('{{ hero_image }}')"></div>
  <div class="hero-ov"></div>
  <div class="hero-ct">
    <h1 class="hero-title">Find the right professional<br>for every job.</h1>
    <p class="hero-sub">Discover and book trusted local service workers in Sri Lanka. Electrical, plumbing, AC, cleaning, carpentry — done right, done quickly.</p>
    <div class="sb-wrap">
      <form class="sb" action="/workers" method="GET">
        <input type="text" name="name" placeholder="Search by worker name…" value="{{ request.args.get('name','') }}">
        <span class="sb-div"></span>
        <select name="category_id" class="sb" style="border:none;outline:none;font-size:14px;color:var(--ts);background:transparent;cursor:pointer;padding:0 4px;min-width:130px;-webkit-appearance:none;">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat['category_id'] }}">{{ cat['name'] }}</option>
          {% endfor %}
        </select>
        <button type="submit" class="sb-btn">Search</button>
      </form>
    </div>
    <div class="cat-short">
      {% for cat in categories %}
      <a href="/workers?category_id={{ cat['category_id'] }}" class="cat-pill">
        <span>{{ category_icons.get(cat['name'],'🔧') }}</span>{{ cat['name'] }}
      </a>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-pg">
  <div class="c">
    <div class="sh-row">
      <div>
        <div class="sl">Browse by Category</div>
        <h2 class="st">Popular Services</h2>
        <p class="ss">From licensed electricians to master carpenters — find the specialist your home needs.</p>
      </div>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;">View All Workers</a>
    </div>
    <div class="cc-grid">
      {% for cat in categories %}
      <a href="/workers?category_id={{ cat['category_id'] }}" class="cc">
        <div class="cc-bg" style="background-image:url('{{ category_images.get(cat['name'],'') }}')"></div>
        <div class="cc-ov"></div>
        <div class="cc-body">
          <div class="cc-name">{{ cat['name'] }}</div>
          <div class="cc-count">{{ cat['worker_count'] }} worker{{ 's' if cat['worker_count'] != 1 else '' }} available</div>
        </div>
      </a>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-w">
  <div class="c">
    <div class="sh-row">
      <div>
        <div class="sl">Top Rated</div>
        <h2 class="st">Featured Professionals</h2>
        <p class="ss">Skilled, vetted and highly rated workers ready for your next project.</p>
      </div>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;">See All Workers</a>
    </div>
    <div class="wc-grid">
      {% for w in workers %}
      <div class="wc">
        <div class="wc-top">
          {% if w['profile_image_url'] %}
          <img src="{{ w['profile_image_url'] }}" alt="{{ w['first_name'] }}" class="av" style="object-fit:cover;">
          {% else %}
          <div class="av">{{ get_initials(w['first_name'] + ' ' + w['last_name']) }}</div>
          {% endif %}
          <div>
            <div class="wn">{{ w['first_name'] }} {{ w['last_name'] }}</div>
            <div class="wm">
              <span>📍 {{ w['city'] }}</span>
              <span>🛠 {{ w['experience_years'] }}yr</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="star-y" style="font-size:14px;">★ {{ "%.1f"|format(w['avg_rating']) }}</span>
          <span class="ts-m ts-sm">· {{ w['completed_jobs'] }} jobs done</span>
        </div>
        <div class="tags">
          {% if w['service_names'] %}{% for svc in w['service_names'].split(',') %}
          <span class="tag">{{ svc.strip() }}</span>
          {% endfor %}{% endif %}
        </div>
        {% if w['min_rate'] %}<p class="rate-t">From <strong>LKR {{ w['min_rate']|lkr }}/hr</strong></p>{% endif %}
        <a href="/worker/{{ w['worker_id'] }}" class="btn btn-p btn-sm" style="margin-top:auto;">View Profile</a>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section class="sec sec-bg-pg">
  <div class="c">
    <div class="sh tc">
      <div class="sl">Simple Process</div>
      <h2 class="st">How QuickDone Works</h2>
    </div>
    <div class="steps-grid">
      <div class="step-card">
        <div class="step-num">1</div>
        <div class="step-title">Find</div>
        <p class="step-desc">Search workers by name, city or service category. View profiles, qualifications, weekly availability and real customer reviews.</p>
      </div>
      <div class="step-card">
        <div class="step-num">2</div>
        <div class="step-title">Book</div>
        <p class="step-desc">Select a service and confirm your booking. The worker's agreed hourly rate is shown upfront — no hidden charges.</p>
      </div>
      <div class="step-card">
        <div class="step-num">3</div>
        <div class="step-title">Review</div>
        <p class="step-desc">After the job is done, leave an honest rating. Your review updates the worker's profile instantly via the database trigger.</p>
      </div>
    </div>
  </div>
</section>
""", nav='hero')


# ============================================================
# PAGE: WORKER LISTING
# ============================================================

WORKERS_TEMPLATE = _page('Find Workers', """
<div class="ph">
  <div class="c">
    <h1>Find a Worker</h1>
    <p>Search from our network of verified service professionals.</p>
  </div>
</div>
""" + _FLASHES + """
<div class="sec sec-sm">
  <div class="c">
    <form class="fbar" method="GET" action="/workers">
      <div class="fg-f">
        <label class="fg-fl">Worker Name</label>
        <input class="f-in" type="text" name="name" value="{{ name }}" placeholder="e.g. Kasun">
      </div>
      <div class="fg-f">
        <label class="fg-fl">City</label>
        <input class="f-in" type="text" name="city" value="{{ city }}" placeholder="e.g. Colombo">
      </div>
      <div class="fg-f">
        <label class="fg-fl">Category</label>
        <select class="f-sel" name="category_id">
          <option value="">All Categories</option>
          {% for cat in categories %}
          <option value="{{ cat['category_id'] }}" {% if category_id == cat['category_id']|string %}selected{% endif %}>
            {{ category_icons.get(cat['name'],'') }} {{ cat['name'] }}
          </option>
          {% endfor %}
        </select>
      </div>
      <button type="submit" class="btn btn-p" style="flex-shrink:0;align-self:flex-end;">Search</button>
      <a href="/workers" class="btn btn-s" style="flex-shrink:0;align-self:flex-end;">Clear</a>
    </form>

    {% if workers %}
    <p style="font-size:14px;color:var(--ts);margin-bottom:20px;">{{ workers|length }} worker{{ 's' if workers|length != 1 else '' }} found</p>
    <div class="wc-grid">
      {% for w in workers %}
      <div class="wc">
        <div class="wc-top">
          {% if w['profile_image_url'] %}
          <img src="{{ w['profile_image_url'] }}" alt="{{ w['first_name'] }}" class="av" style="object-fit:cover;">
          {% else %}
          <div class="av">{{ get_initials(w['first_name'] + ' ' + w['last_name']) }}</div>
          {% endif %}
          <div>
            <div class="wn">{{ w['first_name'] }} {{ w['last_name'] }}</div>
            <div class="wm">
              <span>📍 {{ w['city'] }}</span>
              <span>🛠 {{ w['experience_years'] }}yr exp</span>
            </div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="star-y" style="font-size:14px;">★ {{ "%.1f"|format(w['avg_rating']) }}</span>
          <span class="ts-m ts-sm">· {{ w['completed_jobs'] }} jobs</span>
        </div>
        <div class="tags">
          {% if w['service_names'] %}{% for svc in w['service_names'].split(',') %}
          <span class="tag">{{ svc.strip() }}</span>
          {% endfor %}{% endif %}
        </div>
        <div class="rate-t">
          {% if w['min_rate'] == w['max_rate'] %}
            Rate: <strong>LKR {{ w['min_rate']|lkr }}/hr</strong>
          {% elif w['min_rate'] %}
            From <strong>LKR {{ w['min_rate']|lkr }}</strong> to <strong>LKR {{ w['max_rate']|lkr }}/hr</strong>
          {% endif %}
        </div>
        <a href="/worker/{{ w['worker_id'] }}" class="btn btn-p btn-sm" style="margin-top:auto;">View Profile</a>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty">
      <div class="empty-icon">🔍</div>
      <div class="empty-t">No workers found</div>
      <p class="empty-s">Try a different name, city or category filter.</p>
      <a href="/workers" class="btn btn-p">Clear filters</a>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: WORKER PROFILE
# ============================================================

WORKER_PROFILE_TEMPLATE = _page('{{ worker["first_name"] }} {{ worker["last_name"] }}', """
<div class="prof-h">
  <div class="prof-hi">
    {% if worker['profile_image_url'] %}
    <img src="{{ worker['profile_image_url'] }}" alt="{{ worker['first_name'] }}" class="av av-xl" style="object-fit:cover;border:3px solid rgba(255,255,255,.25);">
    {% else %}
    <div class="av av-xl">{{ get_initials(worker['first_name'] + ' ' + worker['last_name']) }}</div>
    {% endif %}
    <div class="prof-info">
      <h1>{{ worker['first_name'] }} {{ worker['last_name'] }}</h1>
      <div class="prof-meta">
        <span>📍 {{ worker['city'] }}</span>
        <span>🛠 {{ worker['experience_years'] }} years experience</span>
        <span>✅ {{ worker['completed_jobs'] }} jobs completed</span>
      </div>
      <div class="prof-rating">
        <span class="r-big star-y">★ {{ "%.1f"|format(worker['avg_rating']) }}</span>
        <span style="color:rgba(255,255,255,.65);font-size:14px;">average rating</span>
        {% for b in badges %}
        <span class="badge-pill" style="background:rgba(255,255,255,.12);border-color:rgba(255,255,255,.25);color:#fff;">
          🏅 {{ b['badge_name'] }}
        </span>
        {% endfor %}
      </div>
    </div>
    <div style="margin-left:auto;">
      {% if session.get('user_type') == 'customer' %}
      <a href="/book/{{ worker['worker_id'] }}" class="btn btn-cta-hero" style="font-size:15px;padding:12px 28px;">Book Now</a>
      {% elif not session.get('user_type') %}
      <a href="/login" class="btn btn-ghost-w">Log in to Book</a>
      {% endif %}
    </div>
  </div>
</div>

<div class="prof-body">
  <div>
    <div class="panel">
      <div class="pan-h">About</div>
      <div class="pan-b">
        <p>{% if worker['bio'] %}{{ worker['bio'] }}{% else %}No bio provided.{% endif %}</p>
      </div>
    </div>

    {% if portfolio %}
    <div class="panel">
      <div class="pan-h" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Work Examples &amp; Previous Projects</span>
        <span class="ts-sm ts-m">{{ portfolio|length }} photo{{ 's' if portfolio|length != 1 else '' }}</span>
      </div>
      <div class="pan-b">
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:16px;">
          {% for item in portfolio %}
          <div style="border:1.5px solid var(--bd);border-radius:var(--r);overflow:hidden;background:#fff;transition:transform .2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='none'">
            <a href="{{ item['image_url'] }}" target="_blank" rel="noopener" title="Click to view full image">
              <img src="{{ item['image_url'] }}" alt="{{ item['title'] or 'Work Example' }}" style="width:100%;height:150px;object-fit:cover;">
            </a>
            {% if item['title'] %}
            <div style="padding:10px 12px;font-size:13px;font-weight:600;color:var(--tp);line-height:1.35;">
              {{ item['title'] }}
            </div>
            {% endif %}
          </div>
          {% endfor %}
        </div>
      </div>
    </div>
    {% endif %}

    <div class="panel">
      <div class="pan-h">Services &amp; Rates</div>
      <div class="pan-b p0">
        <table>
          <thead><tr><th>Service</th><th>Description</th><th>Hourly Rate</th></tr></thead>
          <tbody>
          {% for s in services %}
          <tr>
            <td><strong>{{ s['category_name'] }}</strong></td>
            <td class="ts-m ts-sm">{{ s['category_description'][:60] }}…</td>
            <td><strong>LKR {{ s['hourly_rate']|lkr }}/hr</strong></td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    {% if qualifications %}
    <div class="panel">
      <div class="pan-h">Qualifications</div>
      <div class="pan-b p0">
        <table>
          <thead><tr><th>#</th><th>Title</th><th>Institution</th><th>Year</th></tr></thead>
          <tbody>
          {% for q in qualifications %}
          <tr>
            <td class="ts-m">{{ q['qualification_no'] }}</td>
            <td><strong>{{ q['title'] }}</strong></td>
            <td class="ts-m">{{ q['institution'] }}</td>
            <td class="ts-m">{{ q['year_obtained'] }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>
    {% endif %}

    <div class="panel">
      <div class="pan-h">Customer Reviews{% if reviews %} ({{ reviews|length }}){% endif %}</div>
      <div class="pan-b">
        {% if reviews %}
        {% for r in reviews %}
        <div class="rev-item">
          <div class="rev-hd">
            <div class="av" style="width:34px;height:34px;font-size:12px;">{{ get_initials(r['customer_name']) }}</div>
            <div class="rev-nm">{{ r['customer_name'] }}</div>
            <div class="star-y" style="font-size:13px;">{{ r['rating']|stars }}</div>
            <div class="rev-dt">{{ r['review_date'][:10] }}</div>
          </div>
          {% if r['comment'] %}<p class="rev-txt">{{ r['comment'] }}</p>{% endif %}
        </div>
        {% endfor %}
        {% else %}
        <p class="ts-m ts-sm">No reviews yet.</p>
        {% endif %}
      </div>
    </div>
  </div>

  <div>
    <div class="panel">
      <div class="pan-h">Weekly Availability</div>
      <div class="pan-b p0">
        <div style="padding:12px 20px;">
          <p class="ts-sm ts-m" style="margin-bottom:12px;">Recurring weekly schedule (not date-specific calendar slots)</p>
          {% if availability %}
          {% for a in availability %}
          <div class="avail-row">
            <div class="avail-day">{{ a['day_of_week'] }}</div>
            <div class="avail-time">{{ a['start_time'] }} – {{ a['end_time'] }}</div>
          </div>
          {% endfor %}
          {% else %}
          <p class="ts-m ts-sm">No availability listed.</p>
          {% endif %}
        </div>
      </div>
    </div>

    {% if badges %}
    <div class="panel">
      <div class="pan-h">Badges Earned</div>
      <div class="pan-b">
        {% for b in badges %}
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <span class="badge-pill">🏅 {{ b['badge_name'] }}</span>
          <span class="ts-sm ts-m">{{ b['awarded_date'] }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endif %}

    {% if session.get('user_type') == 'customer' %}
    <div class="panel" style="border-color:var(--g800);">
      <div class="pan-h" style="background:var(--g900);color:#fff;">Ready to book?</div>
      <div class="pan-b">
        <p class="ts-m ts-sm" style="margin-bottom:16px;">Select a service and schedule your appointment.</p>
        <a href="/book/{{ worker['worker_id'] }}" class="btn btn-p btn-fw">Book {{ worker['first_name'] }}</a>
      </div>
    </div>
    {% elif not session.get('user_type') %}
    <div class="panel">
      <div class="pan-b tc">
        <p class="ts-m ts-sm" style="margin-bottom:16px;">Log in to book this worker.</p>
        <a href="/login" class="btn btn-p btn-fw">Log In</a>
        <a href="/register/customer" class="btn btn-s btn-fw mt16">Register as Customer</a>
      </div>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: LOGIN
# ============================================================

LOGIN_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Log In | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone</div>
    </div>
    <h2 class="auth-t">Welcome back</h2>
    <p class="auth-s">Log in to your account</p>
    <form method="POST">
      <div class="ut-tabs" id="ut-tabs">
        <button type="button" class="ut-tab act" onclick="setType('customer',this)">I'm a Customer</button>
        <button type="button" class="ut-tab" onclick="setType('worker',this)">I'm a Worker</button>
      </div>
      <input type="hidden" name="user_type" id="user_type_field" value="customer">
      <div class="fg">
        <label class="fl-label">Email Address</label>
        <input class="fi" type="email" name="email" required placeholder="your@email.com">
      </div>
      <div class="fg">
        <label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••">
      </div>
      <button class="btn btn-p btn-fw" type="submit">Log In</button>
    </form>
    <div class="auth-sw">
      No account? <a href="/register/customer">Register as Customer</a> or <a href="/register/worker">Join as Worker</a>
    </div>
    <div class="auth-sw" style="margin-top:8px;">
      <a href="/admin/login" style="color:var(--ts);">Admin login →</a>
    </div>
  </div>
</div>
<script>
function setType(type, btn) {
  document.getElementById('user_type_field').value = type;
  document.querySelectorAll('.ut-tab').forEach(b => b.classList.remove('act'));
  btn.classList.add('act');
}
</script>
</body></html>"""
)


# ============================================================
# PAGE: CUSTOMER REGISTRATION
# ============================================================

REGISTER_CUSTOMER_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Register | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card" style="max-width:500px;">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone</div>
    </div>
    <h2 class="auth-t">Create your account</h2>
    <p class="auth-s">Join thousands of customers finding great workers</p>
    <form method="POST">
      <div class="fr">
        <div class="fg"><label class="fl-label">First Name</label>
          <input class="fi" type="text" name="first_name" required placeholder="Amaya"></div>
        <div class="fg"><label class="fl-label">Last Name</label>
          <input class="fi" type="text" name="last_name" required placeholder="Perera"></div>
      </div>
      <div class="fg"><label class="fl-label">Email Address</label>
        <input class="fi" type="email" name="email" required placeholder="amaya@email.lk"></div>
      <div class="fg"><label class="fl-label">Phone Number</label>
        <input class="fi" type="text" name="phone" required placeholder="077-1234567"></div>
      <div class="fg"><label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••" minlength="6"></div>
      <div class="fg"><label class="fl-label">Address</label>
        <input class="fi" type="text" name="address" required placeholder="42 Flower Rd, Colombo 07"></div>
      <button class="btn btn-p btn-fw" type="submit">Create Account</button>
    </form>
    <div class="auth-sw">Already have an account? <a href="/login">Log In</a></div>
    <div class="auth-sw" style="margin-top:6px;">Want to offer services? <a href="/register/worker">Join as Worker</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: WORKER REGISTRATION
# ============================================================

REGISTER_WORKER_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Join as Worker | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div style="background:var(--bg);padding:40px 24px;min-height:100vh;">
  <div style="max-width:720px;margin:0 auto;">
    <div style="text-align:center;margin-bottom:32px;">
      <a href="/" style="display:inline-flex;align-items:center;gap:9px;font-size:19px;font-weight:800;color:var(--tp);">
        <span style="width:32px;height:32px;background:var(--g800);border-radius:9px;color:#fff;font-size:15px;font-weight:900;display:inline-flex;align-items:center;justify-content:center;">Q</span>QuickDone
      </a>
      <h1 style="font-size:26px;font-weight:800;margin-top:20px;">Join as a Service Worker</h1>
      <p style="color:var(--ts);font-size:15px;margin-top:8px;">Create your profile and start receiving booking requests today.</p>
    </div>

    <form method="POST" style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:32px;">

      <h3 style="font-size:16px;font-weight:700;margin-bottom:20px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Personal Details</h3>
      <div class="fr">
        <div class="fg"><label class="fl-label">First Name *</label>
          <input class="fi" type="text" name="first_name" required placeholder="Kasun"></div>
        <div class="fg"><label class="fl-label">Last Name *</label>
          <input class="fi" type="text" name="last_name" required placeholder="Bandara"></div>
      </div>
      <div class="fr">
        <div class="fg"><label class="fl-label">Email Address *</label>
          <input class="fi" type="email" name="email" required placeholder="kasun@email.lk"></div>
        <div class="fg"><label class="fl-label">Phone Number *</label>
          <input class="fi" type="text" name="phone" required placeholder="077-5501122"></div>
      </div>
      <div class="fg"><label class="fl-label">Password *</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••" minlength="6"></div>
      <div class="fr">
        <div class="fg"><label class="fl-label">City *</label>
          <input class="fi" type="text" name="city" required placeholder="Colombo"></div>
        <div class="fg"><label class="fl-label">Years of Experience *</label>
          <input class="fi" type="number" name="experience_years" min="0" max="60" value="0" required></div>
      </div>
      <div class="fg"><label class="fl-label">Bio (optional)</label>
        <textarea class="fta" name="bio" placeholder="Briefly describe your expertise and specialisations…" style="min-height:80px;"></textarea></div>
      <div class="fg"><label class="fl-label">Profile Picture URL (optional)</label>
        <input class="fi" type="url" name="profile_image_url" placeholder="https://images.unsplash.com/... or any image link">
        <p class="f-hint">Provide an image link, or leave blank to display your name initials avatar.</p></div>

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Services &amp; Rates *</h3>
      <p class="f-hint" style="margin-bottom:14px;">Select the services you offer and enter your hourly rate in LKR for each.</p>
      {% for cat in categories %}
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;padding:12px;border:1.5px solid var(--bd);border-radius:var(--r);">
        <input type="checkbox" name="category_ids" value="{{ cat['category_id'] }}" id="cat_{{ cat['category_id'] }}" style="width:18px;height:18px;accent-color:var(--g800);">
        <label for="cat_{{ cat['category_id'] }}" style="min-width:140px;font-weight:600;cursor:pointer;">{{ cat['name'] }}</label>
        <input class="fi" type="number" name="rate_{{ cat['category_id'] }}" placeholder="Hourly rate (LKR)" min="1" step="0.01" style="max-width:200px;margin-bottom:0;">
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Qualifications (optional, up to 3)</h3>
      {% for i in [1,2,3] %}
      <div style="border:1.5px solid var(--bd);border-radius:var(--r);padding:16px;margin-bottom:12px;">
        <p style="font-size:12px;font-weight:700;color:var(--ts);text-transform:uppercase;letter-spacing:.05em;margin-bottom:12px;">Qualification {{ i }}</p>
        <div class="fr">
          <div class="fg" style="margin-bottom:0;"><label class="fl-label">Title</label>
            <input class="fi" type="text" name="qual_title_{{ i }}" placeholder="e.g. NVQ Level 4 Electrical"></div>
          <div class="fg" style="margin-bottom:0;"><label class="fl-label">Year Obtained</label>
            <input class="fi" type="number" name="qual_year_{{ i }}" placeholder="2020" min="1950" max="2026"></div>
        </div>
        <div class="fg" style="margin-top:12px;margin-bottom:0;"><label class="fl-label">Institution</label>
          <input class="fi" type="text" name="qual_institution_{{ i }}" placeholder="e.g. VTA Sri Lanka"></div>
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Weekly Availability (optional)</h3>
      <p class="f-hint" style="margin-bottom:14px;">Select the days you are available and your working hours for each.</p>
      {% for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] %}
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:10px;">
        <input type="checkbox" name="avail_days" value="{{ day }}" id="day_{{ day }}" style="width:18px;height:18px;accent-color:var(--g800);">
        <label for="day_{{ day }}" style="min-width:100px;font-weight:600;cursor:pointer;">{{ day }}</label>
        <input type="time" name="avail_start_{{ day }}" value="08:00" class="fi" style="max-width:120px;margin-bottom:0;">
        <span style="color:var(--ts);font-size:13px;">to</span>
        <input type="time" name="avail_end_{{ day }}" value="17:00" class="fi" style="max-width:120px;margin-bottom:0;">
      </div>
      {% endfor %}

      <h3 style="font-size:16px;font-weight:700;margin:28px 0 16px;padding-bottom:12px;border-bottom:1.5px solid var(--bd);">Work Examples / Previous Jobs (optional, up to 5)</h3>
      <p class="f-hint" style="margin-bottom:14px;">Add image links of previous jobs or completed projects to showcase on your profile.</p>
      {% for i in [1,2,3,4,5] %}
      <div style="border:1.5px solid var(--bd);border-radius:var(--r);padding:14px;margin-bottom:10px;">
        <div class="fr">
          <div class="fg" style="margin-bottom:0;">
            <label class="fl-label">Work Photo {{ i }} URL</label>
            <input class="fi" type="url" name="portfolio_url_{{ i }}" placeholder="https://...">
          </div>
          <div class="fg" style="margin-bottom:0;">
            <label class="fl-label">Project Title / Caption</label>
            <input class="fi" type="text" name="portfolio_title_{{ i }}" placeholder="e.g. Master Breaker Panel Upgrade">
          </div>
        </div>
      </div>
      {% endfor %}

      <div style="margin-top:28px;">
        <button class="btn btn-p btn-fw" type="submit" style="padding:14px;">Create Worker Profile</button>
      </div>
    </form>
    <div class="auth-sw" style="text-align:center;margin-top:16px;">Already have an account? <a href="/login">Log In</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: CUSTOMER DASHBOARD
# ============================================================

CUSTOMER_DASHBOARD_TEMPLATE = _page('My Bookings', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Customer') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/customer" class="active">📋 My Bookings</a>
      <a href="/workers">🔍 Find Workers</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">My Bookings</div>
    {% if bookings %}
    <div class="tw">
      <div class="tw-hd"><span class="tw-t">All Bookings</span>
        <a href="/workers" class="btn btn-p btn-sm">+ New Booking</a></div>
      <table>
        <thead><tr>
          <th>Booking</th><th>Worker</th><th>Service</th>
          <th>Scheduled</th><th>Rate/hr</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td><strong>{{ b['worker_name'] }}</strong><br>
            <span class="ts-sm ts-m">📍 {{ b['worker_city'] }}</span></td>
          <td><span class="tag">{{ b['category_name'] }}</span></td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td><strong>LKR {{ b['agreed_rate']|lkr }}</strong></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              <a href="/booking/{{ b['booking_id'] }}" class="btn btn-s btn-sm">Details</a>
              {% if b['status'] == 'COMPLETED' and not b['review_id'] %}
              <a href="/booking/{{ b['booking_id'] }}/review" class="btn btn-p btn-sm">★ Review</a>
              {% elif b['review_id'] %}
              <span class="st-b s-COMPLETED">Reviewed ★{{ b['rating'] }}</span>
              {% endif %}
              {% if b['status'] in ('PENDING','CONFIRMED') %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/cancel"
                    onsubmit="return confirm('Cancel this booking?')">
                <button class="btn btn-d btn-sm" type="submit">Cancel</button>
              </form>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty">
      <div class="empty-icon">📋</div>
      <div class="empty-t">No bookings yet</div>
      <p class="empty-s">Find a skilled worker and make your first booking today.</p>
      <a href="/workers" class="btn btn-p">Find Workers</a>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: BOOKING FORM (Customer books a worker)
# ============================================================

BOOK_TEMPLATE = _page('Book {{ worker["first_name"] }}', """
<div class="ph">
  <div class="c">
    <h1>Book {{ worker['first_name'] }} {{ worker['last_name'] }}</h1>
    <p>Fill in the job details below. The agreed rate is taken from the worker's listed service rate.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:640px;">
    <div style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:28px;">
      <form method="POST">
        <div class="fg">
          <label class="fl-label">Service *</label>
          <select class="fsel" name="category_id" required id="svc-sel" onchange="updateRate(this)">
            {% for s in services %}
            <option value="{{ s['category_id'] }}" data-rate="{{ s['hourly_rate'] }}">
              {{ s['category_name'] }} — LKR {{ s['hourly_rate']|lkr }}/hr
            </option>
            {% endfor %}
          </select>
        </div>
        <div class="fg">
          <label class="fl-label">Agreed Rate (LKR/hr)</label>
          <input class="fi" type="text" id="rate-display" readonly
            value="LKR {{ services[0]['hourly_rate']|lkr }}/hr — set automatically from selected service"
            style="background:var(--bg);color:var(--ts);">
          <p class="f-hint">This rate is automatically set from the worker's listed price for the selected service.</p>
        </div>
        <div class="fg">
          <label class="fl-label">Job Description *</label>
          <textarea class="fta" name="job_description" required
            placeholder="Describe what needs to be done, e.g. Replace main RCB breaker and fix kitchen socket trip"></textarea>
        </div>
        <div class="fg">
          <label class="fl-label">Job Address *</label>
          <input class="fi" type="text" name="job_address" required placeholder="e.g. 42 Flower Rd, Colombo 07">
        </div>
        <div class="fg">
          <label class="fl-label">Scheduled Start *</label>
          <input class="fi" type="datetime-local" name="scheduled_start" required>
          <p class="f-hint">Note: availability is based on weekly recurring slots, not a fully locked calendar.</p>
        </div>
        <div style="display:flex;gap:12px;margin-top:4px;">
          <button class="btn btn-p" type="submit" style="flex:1;">Confirm Booking</button>
          <a href="/worker/{{ worker['worker_id'] }}" class="btn btn-s" style="flex:1;">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div>
<script>
function updateRate(sel) {
  var rate = sel.options[sel.selectedIndex].getAttribute('data-rate');
  var n = parseFloat(rate).toLocaleString('en-LK', {maximumFractionDigits:0});
  document.getElementById('rate-display').value = 'LKR ' + n + '/hr — set automatically from selected service';
}
</script>
""")


# ============================================================
# PAGE: BOOKING DETAIL
# ============================================================

BOOKING_DETAIL_TEMPLATE = _page('Booking #{{ booking["booking_id"] }}', """
<div class="ph">
  <div class="c">
    <h1>Booking #{{ booking['booking_id'] }}</h1>
    <p>Details for your service booking.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:720px;">
    <div class="panel">
      <div class="pan-h" style="display:flex;align-items:center;justify-content:space-between;">
        <span>Booking Summary</span>
        <span class="st-b s-{{ booking['status'] }}">{{ booking['status'].replace('_',' ') }}</span>
      </div>
      <div class="pan-b">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:20px;">
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">WORKER</div>
            <div class="fw7">{{ booking['worker_name'] }}</div>
            <div class="ts-sm ts-m">{{ booking['worker_city'] }} · {{ booking['worker_phone'] }}</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">SERVICE</div>
            <div class="fw7">{{ booking['category_name'] }}</div>
            <div class="ts-sm ts-m">LKR {{ booking['agreed_rate']|lkr }}/hr</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">SCHEDULED START</div>
            <div class="fw7">{{ booking['scheduled_start'][:16].replace('T',' ') }}</div>
          </div>
          <div>
            <div class="ts-sm ts-m" style="margin-bottom:4px;">BOOKED ON</div>
            <div class="fw7">{{ booking['created_at'][:10] }}</div>
          </div>
        </div>
        <div class="div"></div>
        <div style="margin-bottom:16px;">
          <div class="ts-sm ts-m" style="margin-bottom:4px;">JOB DESCRIPTION</div>
          <div>{{ booking['job_description'] }}</div>
        </div>
        <div>
          <div class="ts-sm ts-m" style="margin-bottom:4px;">JOB ADDRESS</div>
          <div>{{ booking['job_address'] }}</div>
        </div>
        {% if booking['review_id'] %}
        <div class="div"></div>
        <div style="background:var(--m100);border-radius:var(--r);padding:14px;">
          <div class="ts-sm ts-m" style="margin-bottom:4px;">YOUR REVIEW</div>
          <div class="star-y">{{ booking['rating']|stars }}</div>
          {% if booking['comment'] %}<p style="margin-top:8px;font-size:14px;">{{ booking['comment'] }}</p>{% endif %}
        </div>
        {% endif %}
        <div style="display:flex;gap:10px;margin-top:20px;">
          <a href="/dashboard/customer" class="btn btn-s btn-sm">← Back to Bookings</a>
          {% if booking['status'] == 'COMPLETED' and not booking['review_id'] %}
          <a href="/booking/{{ booking['booking_id'] }}/review" class="btn btn-p btn-sm">★ Write Review</a>
          {% endif %}
          {% if booking['status'] in ('PENDING','CONFIRMED') %}
          <form method="POST" action="/booking/{{ booking['booking_id'] }}/cancel"
                onsubmit="return confirm('Cancel this booking?')">
            <button class="btn btn-d btn-sm" type="submit">Cancel Booking</button>
          </form>
          {% endif %}
        </div>
      </div>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: WRITE REVIEW
# ============================================================

REVIEW_TEMPLATE = _page('Write a Review', """
<div class="ph">
  <div class="c">
    <h1>Write a Review</h1>
    <p>Share your experience for booking #{{ booking['booking_id'] }} with {{ booking['worker_name'] }}.</p>
  </div>
</div>
<div class="sec sec-sm">
  <div class="c" style="max-width:560px;">
    <div style="background:#fff;border:1.5px solid var(--bd);border-radius:var(--rl);padding:28px;">
      <div style="display:flex;align-items:center;gap:14px;margin-bottom:24px;padding-bottom:20px;border-bottom:1.5px solid var(--bd);">
        <div class="av">{{ get_initials(booking['worker_name']) }}</div>
        <div>
          <div class="fw7">{{ booking['worker_name'] }}</div>
          <div class="ts-sm ts-m">{{ booking['category_name'] }}</div>
        </div>
      </div>
      <form method="POST">
        <div class="fg">
          <label class="fl-label">Star Rating *</label>
          <div style="display:flex;gap:8px;margin-top:4px;" id="star-row">
            {% for i in [1,2,3,4,5] %}
            <button type="button" class="star-btn" data-val="{{ i }}"
              onclick="setStar({{ i }})"
              style="background:none;border:none;font-size:36px;cursor:pointer;color:var(--bd);transition:color .1s;padding:0;">★</button>
            {% endfor %}
          </div>
          <input type="hidden" name="rating" id="rating-val" value="">
        </div>
        <div class="fg">
          <label class="fl-label">Comment (optional)</label>
          <textarea class="fta" name="comment"
            placeholder="Describe the quality of work, punctuality, professionalism…"></textarea>
        </div>
        <div style="display:flex;gap:12px;">
          <button class="btn btn-p" type="submit" style="flex:1;">Submit Review</button>
          <a href="/dashboard/customer" class="btn btn-s" style="flex:1;">Cancel</a>
        </div>
      </form>
    </div>
  </div>
</div>
<script>
var selected = 0;
function setStar(n) {
  selected = n;
  document.getElementById('rating-val').value = n;
  var btns = document.querySelectorAll('.star-btn');
  btns.forEach(function(b, i) {
    b.style.color = i < n ? 'var(--star)' : 'var(--bd)';
  });
}
</script>
""")


# ============================================================
# PAGE: WORKER DASHBOARD
# ============================================================

WORKER_DASHBOARD_TEMPLATE = _page('Worker Dashboard', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Worker') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/worker" class="active">📋 Bookings</a>
      <a href="/dashboard/worker/profile">👤 My Profile</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    {% if worker %}
    <div class="kpi-row">
      <div class="kpi kpi-gl"><div class="kpi-l">Avg Rating</div>
        <div class="kpi-v star-y">{{ "%.2f"|format(worker['avg_rating']) }}</div>
        <div class="kpi-s">★ out of 5.00</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Completed Jobs</div>
        <div class="kpi-v">{{ worker['completed_jobs'] }}</div>
        <div class="kpi-s">trigger-maintained count</div></div>
      <div class="kpi"><div class="kpi-l">Experience</div>
        <div class="kpi-v">{{ worker['experience_years'] }}yr</div></div>
      <div class="kpi"><div class="kpi-l">Badges</div>
        <div class="kpi-v">{{ badges|length }}</div>
        <div class="kpi-s">{% for b in badges %}<span class="badge-pill">{{ b['badge_name'] }}</span> {% endfor %}</div></div>
    </div>
    {% endif %}

    <div class="tw">
      <div class="tw-hd"><span class="tw-t">Booking Requests</span></div>
      {% if bookings %}
      <table>
        <thead><tr>
          <th>#</th><th>Customer</th><th>Service</th>
          <th>Scheduled</th><th>Rate/hr</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td>
            <strong>{{ b['customer_name'] }}</strong><br>
            <span class="ts-sm ts-m">{{ b['customer_phone'] }}</span>
          </td>
          <td>
            <span class="tag">{{ b['category_name'] }}</span><br>
            <span class="ts-sm" style="color:var(--tp);font-weight:500;">{{ b['job_description'] }}</span><br>
            <span class="ts-sm ts-m">📍 {{ b['job_address'] }}</span>
          </td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td><strong>LKR {{ b['agreed_rate']|lkr }}</strong></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">
              {% if b['status'] == 'PENDING' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CONFIRMED">
                <button class="btn btn-p btn-sm" type="submit">Accept</button>
              </form>
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CANCELLED">
                <button class="btn btn-d btn-sm" type="submit">Reject</button>
              </form>
              {% elif b['status'] == 'CONFIRMED' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="IN_PROGRESS">
                <button class="btn btn-p btn-sm" type="submit">Start</button>
              </form>
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status">
                <input type="hidden" name="status" value="CANCELLED">
                <button class="btn btn-d btn-sm" type="submit">Cancel</button>
              </form>
              {% elif b['status'] == 'IN_PROGRESS' %}
              <form class="ba-form" method="POST" action="/booking/{{ b['booking_id'] }}/status"
                    onsubmit="return confirm('Mark as COMPLETED? This will trigger the completed_jobs counter and award eligible badges.')">
                <input type="hidden" name="status" value="COMPLETED">
                <button class="btn btn-p btn-sm" type="submit">Complete</button>
              </form>
              {% endif %}
            </div>
          </td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
      <div class="empty"><div class="empty-icon">📋</div>
        <div class="empty-t">No bookings yet</div>
        <p class="empty-s">Your booking requests will appear here.</p></div>
      {% endif %}
    </div>
    <div style="margin-top:12px;">
      <p class="ts-sm ts-m">Status transitions: PENDING → CONFIRMED → IN_PROGRESS → COMPLETED. Trigger <code>trg_update_worker_jobs_on_complete</code> fires on COMPLETED, updating your completed jobs counter and checking badge eligibility.</p>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: WORKER PROFILE EDIT
# ============================================================

WORKER_PROFILE_EDIT_TEMPLATE = _page('Edit My Profile', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>QuickDone</div>
      <div class="sb-user">{{ session.get('user_name','Worker') }}</div>
    </div>
    <nav class="sb-nav">
      <a href="/dashboard/worker">📋 Bookings</a>
      <a href="/dashboard/worker/profile" class="active">👤 My Profile</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">My Profile</div>

    <!-- PROFILE UPDATE -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Basic Information</span></div>
      <div style="padding:20px;">
        <form method="POST">
          <input type="hidden" name="action" value="update_profile">
          <div class="fr">
            <div class="fg"><label class="fl-label">Bio</label>
              <textarea class="fta" name="bio" style="min-height:80px;">{{ worker['bio'] or '' }}</textarea></div>
            <div>
              <div class="fg"><label class="fl-label">Profile Picture URL (optional)</label>
                <input class="fi" type="url" name="profile_image_url" value="{{ worker['profile_image_url'] or '' }}" placeholder="https://images.unsplash.com/..."></div>
              <div class="fg"><label class="fl-label">Phone</label>
                <input class="fi" type="text" name="phone" value="{{ worker['phone'] }}"></div>
              <div class="fg"><label class="fl-label">City</label>
                <input class="fi" type="text" name="city" value="{{ worker['city'] }}"></div>
              <div class="fg"><label class="fl-label">Experience (years)</label>
                <input class="fi" type="number" name="experience_years" value="{{ worker['experience_years'] }}" min="0"></div>
            </div>
          </div>
          <button class="btn btn-p btn-sm" type="submit">Save Profile</button>
        </form>
      </div>
    </div>

    <!-- WORK EXAMPLES / PORTFOLIO -->
    <div class="tw mb24">
      <div class="tw-hd" style="display:flex;align-items:center;justify-content:space-between;">
        <span class="tw-t">Work Examples / Portfolio (Max 5)</span>
        <span class="ts-sm ts-m">{{ portfolio|length }} of 5 uploaded</span>
      </div>
      <div style="padding:20px;">
        {% if portfolio %}
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px;margin-bottom:20px;">
          {% for item in portfolio %}
          <div style="border:1.5px solid var(--bd);border-radius:var(--r);overflow:hidden;background:#fff;display:flex;flex-direction:column;">
            <a href="{{ item['image_url'] }}" target="_blank" rel="noopener">
              <img src="{{ item['image_url'] }}" alt="{{ item['title'] or 'Work Example' }}" style="width:100%;height:120px;object-fit:cover;">
            </a>
            <div style="padding:10px;display:flex;flex-direction:column;flex:1;">
              <div style="font-weight:600;font-size:13px;color:var(--tp);margin-bottom:8px;line-height:1.3;">{{ item['title'] or 'Work Sample' }}</div>
              <form method="POST" style="margin-top:auto;" onsubmit="return confirm('Remove this work sample photo?')">
                <input type="hidden" name="action" value="remove_portfolio">
                <input type="hidden" name="portfolio_id" value="{{ item['portfolio_id'] }}">
                <button class="btn btn-d btn-sm" type="submit" style="width:100%;padding:4px 8px;font-size:12px;">Remove</button>
              </form>
            </div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <p class="ts-sm ts-m" style="margin-bottom:16px;">You haven't added any work example photos yet.</p>
        {% endif %}

        {% if portfolio|length < 5 %}
        <form method="POST" style="background:var(--bg);border:1.5px dashed var(--bd);border-radius:var(--r);padding:16px;">
          <input type="hidden" name="action" value="add_portfolio">
          <p style="font-size:13px;font-weight:700;color:var(--tp);margin-bottom:12px;">Add Work Example Photo ({{ 5 - portfolio|length }} slot{{ 's' if (5 - portfolio|length) != 1 else '' }} remaining)</p>
          <div class="fr">
            <div class="fg" style="margin-bottom:0;">
              <label class="fl-label">Image URL *</label>
              <input class="fi" type="url" name="image_url" required placeholder="https://images.unsplash.com/... or image link">
            </div>
            <div class="fg" style="margin-bottom:0;">
              <label class="fl-label">Project Title / Caption (optional)</label>
              <input class="fi" type="text" name="title" placeholder="e.g. Master Breaker Panel Upgrade">
            </div>
          </div>
          <button class="btn btn-p btn-sm" type="submit" style="margin-top:12px;">+ Add Work Example</button>
        </form>
        {% else %}
        <div style="padding:12px 16px;background:var(--m100);border-radius:var(--r);color:var(--g900);font-size:13px;font-weight:600;">
          ✓ You have reached the maximum of 5 work example photos. Remove an existing image above to add a new one.
        </div>
        {% endif %}
      </div>
    </div>

    <!-- SERVICES -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">My Services</span>
        <span class="ts-sm ts-m">Rate in LKR per hour</span></div>
      <div style="padding:20px;">
        {% if services %}
        <table style="margin-bottom:20px;">
          <thead><tr><th>Category</th><th>Rate / hr</th><th>Action</th></tr></thead>
          <tbody>
          {% for s in services %}
          <tr>
            <td><strong>{{ s['category_name'] }}</strong></td>
            <td>LKR {{ s['hourly_rate']|lkr }}</td>
            <td>
              <form class="ba-form" method="POST"
                    onsubmit="return confirm('Remove {{ s[\"category_name\"] }} from your services?')">
                <input type="hidden" name="action" value="remove_service">
                <input type="hidden" name="category_id" value="{{ s['category_id'] }}">
                <button class="btn btn-d btn-sm" type="submit">Remove</button>
              </form>
            </td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% endif %}
        <form method="POST" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;">
          <input type="hidden" name="action" value="add_service">
          <div class="fg-f" style="min-width:160px;flex:1;">
            <label class="fg-fl">Add Category</label>
            <select class="f-sel" name="category_id">
              {% for cat in all_categories %}
              <option value="{{ cat['category_id'] }}">{{ cat['name'] }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="fg-f" style="min-width:140px;">
            <label class="fg-fl">Hourly Rate (LKR)</label>
            <input class="f-in" type="number" name="hourly_rate" placeholder="e.g. 2500" min="1" step="0.01">
          </div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add Service</button>
        </form>
      </div>
    </div>

    <!-- QUALIFICATIONS -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Qualifications</span></div>
      <div style="padding:20px;">
        {% if qualifications %}
        <table style="margin-bottom:20px;">
          <thead><tr><th>#</th><th>Title</th><th>Institution</th><th>Year</th></tr></thead>
          <tbody>
          {% for q in qualifications %}
          <tr>
            <td class="ts-m">{{ q['qualification_no'] }}</td>
            <td><strong>{{ q['title'] }}</strong></td>
            <td class="ts-m">{{ q['institution'] }}</td>
            <td class="ts-m">{{ q['year_obtained'] }}</td>
          </tr>
          {% endfor %}
          </tbody>
        </table>
        {% endif %}
        <form method="POST" style="display:grid;grid-template-columns:2fr 2fr 1fr auto;gap:12px;align-items:flex-end;">
          <input type="hidden" name="action" value="add_qualification">
          <div class="fg-f"><label class="fg-fl">Title</label>
            <input class="f-in" type="text" name="qual_title" placeholder="NVQ Level 4 Electrical"></div>
          <div class="fg-f"><label class="fg-fl">Institution</label>
            <input class="f-in" type="text" name="qual_institution" placeholder="VTA Sri Lanka"></div>
          <div class="fg-f"><label class="fg-fl">Year</label>
            <input class="f-in" type="number" name="qual_year" placeholder="2020" min="1950" max="2026"></div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add</button>
        </form>
      </div>
    </div>

    <!-- AVAILABILITY -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Weekly Availability</span>
        <span class="ts-sm ts-m">Recurring weekday slots (not calendar-specific)</span></div>
      <div style="padding:20px;">
        {% if availability %}
        <div style="margin-bottom:20px;">
          {% for a in availability %}
          <div class="avail-row"><div class="avail-day">{{ a['day_of_week'] }}</div>
            <div class="avail-time">{{ a['start_time'] }} – {{ a['end_time'] }}</div></div>
          {% endfor %}
        </div>
        {% endif %}
        <form method="POST" style="display:flex;gap:12px;align-items:flex-end;flex-wrap:wrap;">
          <input type="hidden" name="action" value="add_availability">
          <div class="fg-f" style="min-width:140px;">
            <label class="fg-fl">Day</label>
            <select class="f-sel" name="avail_day">
              {% for day in ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'] %}
              <option value="{{ day }}">{{ day }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="fg-f"><label class="fg-fl">Start</label>
            <input class="f-in" type="time" name="avail_start" value="08:00"></div>
          <div class="fg-f"><label class="fg-fl">End</label>
            <input class="f-in" type="time" name="avail_end" value="17:00"></div>
          <button class="btn btn-p btn-sm" type="submit" style="align-self:flex-end;">Add / Update</button>
        </form>
      </div>
    </div>

    <!-- BADGES -->
    {% if worker %}
    <div class="tw">
      <div class="tw-hd"><span class="tw-t">Badges</span></div>
      <div style="padding:20px;">
        {% for b in services %}{% endfor %}
        <p class="ts-sm ts-m" style="margin-bottom:12px;">
          Badges are awarded automatically after a booking is marked COMPLETED.
          Current completed jobs: <strong>{{ worker['completed_jobs'] }}</strong>
        </p>
        <a href="/worker/{{ session.get('user_id') }}" class="btn btn-s btn-sm">View Public Profile</a>
      </div>
    </div>
    {% endif %}
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN LOGIN
# ============================================================

ADMIN_LOGIN_TEMPLATE = (
    '<!DOCTYPE html><html lang="en"><head>'
    '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">'
    '<title>Admin Login | QuickDone</title>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
    '<style>' + SHARED_CSS + '</style>'
    '</head><body>'
    + _FLASHES + """
<div class="auth-pg">
  <div class="auth-card">
    <div class="auth-logo">
      <div class="auth-logo-mark">Q</div>
      <div class="auth-logo-name">QuickDone Admin</div>
    </div>
    <h2 class="auth-t">Admin Login</h2>
    <p class="auth-s">Credentials are defined in Python only — no database table.</p>
    <form method="POST">
      <div class="fg"><label class="fl-label">Username</label>
        <input class="fi" type="text" name="username" required placeholder="admin"></div>
      <div class="fg"><label class="fl-label">Password</label>
        <input class="fi" type="password" name="password" required placeholder="••••••••"></div>
      <button class="btn btn-p btn-fw" type="submit">Log In as Admin</button>
    </form>
    <div class="auth-sw"><a href="/">← Back to QuickDone</a></div>
  </div>
</div>
</body></html>"""
)


# ============================================================
# PAGE: ADMIN DASHBOARD
# ============================================================

ADMIN_DASHBOARD_TEMPLATE = _page('Admin Dashboard', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard" class="active">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Admin Dashboard</div>

    <!-- KPI ROW -->
    <div class="kpi-row">
      <div class="kpi kpi-gl"><div class="kpi-l">Total Customers</div>
        <div class="kpi-v">{{ stats.total_customers }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Workers</div>
        <div class="kpi-v">{{ stats.total_workers }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Bookings</div>
        <div class="kpi-v">{{ stats.total_bookings }}</div></div>
      <div class="kpi kpi-gl"><div class="kpi-l">Total Reviews</div>
        <div class="kpi-v">{{ stats.total_reviews }}</div></div>
      <div class="kpi"><div class="kpi-l">Avg Platform Rating</div>
        <div class="kpi-v star-y">{{ "%.2f"|format(stats.avg_rating) }}</div>
        <div class="kpi-s">★ out of 5.00 (AVG aggregate)</div></div>
      <div class="kpi"><div class="kpi-l">Rate Range (LKR)</div>
        <div class="kpi-v" style="font-size:18px;">{{ stats.min_rate|lkr }}–{{ stats.max_rate|lkr }}</div>
        <div class="kpi-s">MIN and MAX aggregates</div></div>
    </div>

    <!-- BOOKING STATUS BREAKDOWN -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Bookings by Status</span>
          <span class="ts-sm ts-m">GROUP BY</span></div>
        <table>
          <thead><tr><th>Status</th><th>Count</th></tr></thead>
          <tbody>
          {% for row in stats.bookings_by_status %}
          <tr><td><span class="st-b s-{{ row['status'] }}">{{ row['status'].replace('_',' ') }}</span></td>
              <td><strong>{{ row['cnt'] }}</strong></td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Popular Categories</span>
          <span class="ts-sm ts-m">GROUP BY + HAVING</span></div>
        <table>
          <thead><tr><th>Category</th><th>Workers</th><th>Bookings</th></tr></thead>
          <tbody>
          {% for row in stats.popular_categories %}
          <tr><td><strong>{{ row['name'] }}</strong></td>
              <td>{{ row['worker_count'] }}</td>
              <td>{{ row['booking_count'] }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- TOP WORKERS (uses subquery) -->
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px;">
      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Top-Rated Workers</span>
          <span class="ts-sm ts-m">Subquery (workers with reviews only)</span></div>
        <table>
          <thead><tr><th>Worker</th><th>Rating</th><th>Jobs</th></tr></thead>
          <tbody>
          {% for w in stats.top_workers %}
          <tr><td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a><br>
              <span class="ts-sm ts-m">{{ w['city'] }}</span></td>
              <td class="star-y">★ {{ "%.2f"|format(w['avg_rating']) }}</td>
              <td>{{ w['completed_jobs'] }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>

      <div class="tw">
        <div class="tw-hd"><span class="tw-t">Most Active Workers</span>
          <span class="ts-sm ts-m">ORDER BY completed_jobs DESC</span></div>
        <table>
          <thead><tr><th>Worker</th><th>Completed</th><th>Rating</th></tr></thead>
          <tbody>
          {% for w in stats.most_active %}
          <tr><td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a><br>
              <span class="ts-sm ts-m">{{ w['city'] }}</span></td>
              <td><strong>{{ w['completed_jobs'] }}</strong></td>
              <td class="star-y">★ {{ "%.1f"|format(w['avg_rating']) }}</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </div>

    <!-- RECENT BOOKINGS -->
    <div class="tw mb24">
      <div class="tw-hd"><span class="tw-t">Recent Bookings</span>
        <span class="ts-sm ts-m">INNER JOIN across booking, customer, worker, category</span></div>
      <table>
        <thead><tr><th>#</th><th>Customer</th><th>Worker</th><th>Category</th>
          <th>Status</th><th>Rate</th><th>Scheduled</th></tr></thead>
        <tbody>
        {% for b in stats.recent_bookings %}
        <tr>
          <td class="ts-sm ts-m">#{{ b['booking_id'] }}</td>
          <td>{{ b['customer_name'] }}</td>
          <td><a href="/worker/{{ b['worker_id'] }}" style="color:var(--g800);">{{ b['worker_name'] }}</a></td>
          <td><span class="tag">{{ b['category_name'] }}</span></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>LKR {{ b['agreed_rate']|lkr }}</td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>

    <!-- VIEW: v_worker_derived_stats -->
    <div class="tw">
      <div class="tw-hd">
        <span class="tw-t">Worker Statistics — View <code style="font-size:11px;background:var(--m100);padding:2px 6px;border-radius:4px;">v_worker_derived_stats</code></span>
        <span class="ts-sm ts-m">Dynamically derived values vs trigger-maintained stored values</span>
      </div>
      <table>
        <thead><tr>
          <th>Worker</th><th>City</th><th>Exp</th>
          <th>Completed Jobs (view)</th><th>Avg Rating (view)</th>
        </tr></thead>
        <tbody>
        {% for v in view_stats %}
        <tr>
          <td><strong>{{ v['worker_name'] }}</strong></td>
          <td class="ts-m">{{ v['city'] }}</td>
          <td class="ts-m">{{ v['experience_years'] }}yr</td>
          <td><strong>{{ v['completed_jobs'] }}</strong></td>
          <td class="star-y">{% if v['avg_rating'] %}★ {{ "%.2f"|format(v['avg_rating']) }}{% else %}—{% endif %}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — CUSTOMERS
# ============================================================

ADMIN_CUSTOMERS_TEMPLATE = _page('Customers — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers" class="active">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Customers ({{ customers|length }})</div>
    <div class="tw">
      <table>
        <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Phone</th><th>Address</th><th>Registered</th></tr></thead>
        <tbody>
        {% for c in customers %}
        <tr>
          <td class="ts-m">{{ c['customer_id'] }}</td>
          <td><strong>{{ c['first_name'] }} {{ c['last_name'] }}</strong></td>
          <td class="ts-m">{{ c['email'] }}</td>
          <td class="ts-m">{{ c['phone'] }}</td>
          <td class="ts-sm ts-m">{{ c['address'] }}</td>
          <td class="ts-sm ts-m">{{ c['registered_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — WORKERS
# ============================================================

ADMIN_WORKERS_TEMPLATE = _page('Workers — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers" class="active">🔧 Workers</a>
      <a href="/admin/bookings">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">Workers ({{ workers|length }})</div>
    <div class="tw">
      <table>
        <thead><tr>
          <th>ID</th><th>Name</th><th>City</th><th>Exp</th>
          <th>Avg Rating</th><th>Completed</th><th>Services</th><th>Registered</th>
        </tr></thead>
        <tbody>
        {% for w in workers %}
        <tr>
          <td class="ts-m">{{ w['worker_id'] }}</td>
          <td><a href="/worker/{{ w['worker_id'] }}" class="fw7" style="color:var(--g800);">{{ w['name'] }}</a></td>
          <td class="ts-m">{{ w['city'] }}</td>
          <td class="ts-m">{{ w['experience_years'] }}yr</td>
          <td class="star-y">{% if w['avg_rating'] > 0 %}★ {{ "%.2f"|format(w['avg_rating']) }}{% else %}—{% endif %}</td>
          <td><strong>{{ w['completed_jobs'] }}</strong></td>
          <td class="ts-m">{{ w['service_count'] }}</td>
          <td class="ts-sm ts-m">{{ w['registered_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")


# ============================================================
# PAGE: ADMIN — BOOKINGS
# ============================================================

ADMIN_BOOKINGS_TEMPLATE = _page('Bookings — Admin', """
<div class="dash-wrap">
  <div class="sidebar">
    <div class="sb-logo">
      <div class="sb-logo-txt"><span class="sb-logo-mark">Q</span>Admin</div>
      <div class="sb-user">QuickDone Admin</div>
    </div>
    <nav class="sb-nav">
      <a href="/admin/dashboard">📊 Dashboard</a>
      <a href="/admin/customers">👥 Customers</a>
      <a href="/admin/workers">🔧 Workers</a>
      <a href="/admin/bookings" class="active">📋 Bookings</a>
      <a href="/logout">↩ Log Out</a>
    </nav>
  </div>
  <div class="dash-main">
    <div class="dash-title">All Bookings ({{ bookings|length }})</div>
    <div class="tw">
      <table>
        <thead><tr>
          <th>#</th><th>Customer</th><th>Worker</th><th>Category &amp; Details</th>
          <th>Status</th><th>Rate</th><th>Scheduled</th><th>Created</th>
        </tr></thead>
        <tbody>
        {% for b in bookings %}
        <tr>
          <td class="ts-m">#{{ b['booking_id'] }}</td>
          <td>{{ b['customer_name'] }}</td>
          <td>{{ b['worker_name'] }}</td>
          <td><span class="tag">{{ b['category_name'] }}</span><br><span class="ts-sm ts-m">{{ b['job_description'] }}</span></td>
          <td><span class="st-b s-{{ b['status'] }}">{{ b['status'].replace('_',' ') }}</span></td>
          <td>LKR {{ b['agreed_rate']|lkr }}</td>
          <td class="ts-sm ts-m">{{ b['scheduled_start'][:16].replace('T',' ') }}</td>
          <td class="ts-sm ts-m">{{ b['created_at'][:10] }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
""")



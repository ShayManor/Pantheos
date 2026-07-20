export const CSS = `
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

.gs {
  --paper:#F4F6F8; --surface:#FFFFFF; --surface-2:#FAFBFD; --surface-3:#EEF1F5;
  --ink:#14191F; --ink-2:#586573; --ink-3:#8E99A4;
  --line:#E4E8ED; --line-2:#D3DAE1;
  --go:#0F7A4B; --go-soft:#E5F2EB; --go-line:#BFE0CE;
  --caution:#B0730F; --caution-soft:#F7EEDC; --caution-line:#EAD6A8;
  --fault:#BF3A3A; --fault-soft:#F8E5E5; --fault-line:#EBC2C2;
  --info:#2563A6; --info-soft:#E5EDF6;
  --mono:'IBM Plex Mono',ui-monospace,monospace;
  --sans:'IBM Plex Sans',system-ui,sans-serif;
  --disp:'Space Grotesk',var(--sans);
  color:var(--ink); font-family:var(--sans); position:relative;
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
}
.gs *{box-sizing:border-box;}
.gs button{font-family:inherit;cursor:pointer;border:none;background:none;color:inherit;}
.gs ::selection{background:var(--go-soft);}

/* layout */
.gs-shell{display:flex;height:100vh;background:var(--paper);overflow:hidden;}
.gs-rail{width:212px;flex-shrink:0;background:var(--surface);border-right:1px solid var(--line);
  display:flex;flex-direction:column;}
.gs-main{flex:1;display:flex;flex-direction:column;min-width:0;position:relative;}
.gs-body{flex:1;overflow-y:auto;padding:22px 26px 40px;}

/* wordmark */
.gs-brand{padding:18px 18px 14px;border-bottom:1px solid var(--line);display:flex;gap:10px;align-items:center;}
.gs-brand-mark{width:30px;height:30px;border-radius:8px;background:var(--ink);color:#fff;
  display:grid;place-items:center;flex-shrink:0;}
.gs-brand-name{font-family:var(--disp);font-weight:700;font-size:15px;letter-spacing:-0.02em;line-height:1;}
.gs-brand-sub{font-family:var(--mono);font-size:9.5px;color:var(--ink-3);letter-spacing:0.14em;margin-top:3px;}

/* nav */
.gs-nav{padding:12px 10px;display:flex;flex-direction:column;gap:2px;}
.gs-nav-label{font-family:var(--mono);font-size:9.5px;letter-spacing:0.16em;color:var(--ink-3);
  padding:10px 10px 6px;}
.gs-nav-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;
  font-size:13.5px;font-weight:500;color:var(--ink-2);width:100%;text-align:left;transition:all .13s;}
.gs-nav-item:hover{background:var(--surface-3);color:var(--ink);}
.gs-nav-item.active{background:var(--go-soft);color:var(--go);font-weight:600;}
.gs-nav-item .cnt{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--ink-3);}
.gs-nav-item.active .cnt{color:var(--go);}

.gs-rail-foot{margin-top:auto;padding:14px;border-top:1px solid var(--line);}
.gs-flight-card{background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:11px 12px;}
.gs-flight-card .row{display:flex;align-items:center;gap:8px;}
.gs-flight-card .nm{font-family:var(--disp);font-weight:600;font-size:13px;}
.gs-flight-card .st{font-family:var(--mono);font-size:9.5px;color:var(--go);margin-top:5px;letter-spacing:0.1em;}

/* status strip */
.gs-strip{height:52px;border-bottom:1px solid var(--line);background:var(--surface);
  display:flex;align-items:center;padding:0 26px;gap:22px;position:relative;overflow:hidden;}
.gs-strip::before{content:"";position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(90deg,var(--line) 1px,transparent 1px);
  background-size:13px 100%;opacity:.35;}
.gs-strip-title{font-family:var(--disp);font-weight:600;font-size:15px;letter-spacing:-0.01em;z-index:1;}
.gs-strip-spacer{flex:1;}
.gs-met{font-family:var(--mono);font-size:11px;color:var(--ink-2);z-index:1;display:flex;gap:7px;align-items:center;}
.gs-met b{color:var(--ink);font-weight:600;}
.gs-stat-chip{display:flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;
  padding:5px 9px;border-radius:7px;z-index:1;font-weight:500;}

/* generic */
.gs-eyebrow{font-family:var(--mono);font-size:10px;letter-spacing:0.16em;color:var(--ink-3);
  text-transform:uppercase;margin-bottom:14px;display:flex;align-items:center;gap:8px;}
.gs-h1{font-family:var(--disp);font-weight:700;font-size:24px;letter-spacing:-0.02em;margin:0 0 3px;}
.gs-sub{color:var(--ink-2);font-size:13.5px;margin:0 0 20px;overflow-wrap:anywhere;}
.gs-card{background:var(--surface);border:1px solid var(--line);border-radius:12px;}

/* filter bar */
.gs-filters{display:flex;gap:6px;margin-bottom:16px;flex-wrap:wrap;}
.gs-filter{font-family:var(--mono);font-size:11px;letter-spacing:0.03em;padding:6px 12px;border-radius:20px;
  border:1px solid var(--line-2);color:var(--ink-2);background:var(--surface);transition:all .13s;font-weight:500;}
.gs-filter:hover{border-color:var(--ink-3);color:var(--ink);}
.gs-filter.on{background:var(--ink);color:#fff;border-color:var(--ink);}

/* ticket row */
.gs-trow{display:grid;grid-template-columns:26px 1fr auto;gap:14px;align-items:center;
  padding:14px 16px;border-bottom:1px solid var(--line);cursor:pointer;transition:background .12s;}
.gs-trow:last-child{border-bottom:none;}
.gs-trow:hover{background:var(--surface-2);}
.gs-trow-main{min-width:0;}
.gs-trow-top{display:flex;align-items:center;gap:9px;margin-bottom:5px;}
.gs-trow-id{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);letter-spacing:0.02em;}
.gs-trow-title{font-weight:600;font-size:14px;letter-spacing:-0.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-trow-sum{font-size:12.5px;color:var(--ink-2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-trow-right{display:flex;align-items:center;gap:14px;}
.gs-due{font-family:var(--mono);font-size:11px;color:var(--ink-2);text-align:right;white-space:nowrap;}
.gs-due.hot{color:var(--fault);font-weight:600;}
.gs-score{font-family:var(--mono);font-size:11px;color:var(--ink-3);width:38px;text-align:right;}

/* priority tag */
.pri{font-family:var(--mono);font-size:10px;font-weight:600;padding:2px 6px;border-radius:5px;letter-spacing:0.04em;}
.pri.p0{background:var(--fault-soft);color:var(--fault);}
.pri.p1{background:var(--caution-soft);color:var(--caution);}
.pri.p2{background:var(--surface-3);color:var(--ink-2);}
.pri.p3{background:var(--surface-3);color:var(--ink-3);}

/* pills */
.pill{font-family:var(--mono);font-size:10px;font-weight:500;padding:3px 8px;border-radius:20px;
  letter-spacing:0.04em;display:inline-flex;align-items:center;gap:5px;border:1px solid transparent;white-space:nowrap;}
.pill.go{background:var(--go-soft);color:var(--go);border-color:var(--go-line);}
.pill.cau{background:var(--caution-soft);color:var(--caution);border-color:var(--caution-line);}
.pill.flt{background:var(--fault-soft);color:var(--fault);border-color:var(--fault-line);}
.pill.neu{background:var(--surface-3);color:var(--ink-2);border-color:var(--line-2);}
.pill.info{background:var(--info-soft);color:var(--info);}

/* dots */
.dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;}
.dot.go{background:var(--go);box-shadow:0 0 0 3px var(--go-soft);}
.dot.cau{background:var(--caution);box-shadow:0 0 0 3px var(--caution-soft);}
.dot.flt{background:var(--fault);box-shadow:0 0 0 3px var(--fault-soft);}
.dot.los{background:var(--ink-3);}

/* buttons */
.gs-btn{display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:600;
  padding:9px 15px;border-radius:9px;transition:all .13s;font-family:var(--sans);}
.gs-btn.primary{background:var(--go);color:#fff;}
.gs-btn.primary:hover{background:#0c6a41;}
.gs-btn.ghost{background:var(--surface);border:1px solid var(--line-2);color:var(--ink);}
.gs-btn.ghost:hover{border-color:var(--ink-3);background:var(--surface-2);}
.gs-btn.danger{background:var(--surface);border:1px solid var(--fault-line);color:var(--fault);}
.gs-btn.danger:hover{background:var(--fault-soft);border-color:var(--fault);}
.gs-btn:focus-visible{outline:2px solid var(--go);outline-offset:2px;}

/* project cards */
.gs-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;}
.gs-pcard{padding:16px 17px;cursor:pointer;transition:all .14s;}
.gs-pcard:hover{border-color:var(--line-2);transform:translateY(-1px);box-shadow:0 6px 18px -12px rgba(20,25,31,.24);}
.gs-pcard-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;}
.gs-pcard-nm{font-family:var(--disp);font-weight:600;font-size:16px;letter-spacing:-0.01em;}
.gs-pcard-area{font-family:var(--mono);font-size:10px;color:var(--ink-3);letter-spacing:0.08em;margin-top:2px;}
.gs-pcard-metrics{display:flex;gap:18px;margin-top:12px;padding-top:12px;border-top:1px solid var(--line);}
.gs-metric .v{font-family:var(--mono);font-size:16px;font-weight:600;letter-spacing:-0.01em;}
.gs-metric .l{font-family:var(--mono);font-size:9.5px;color:var(--ink-3);letter-spacing:0.06em;margin-top:2px;}

/* detail */
.gs-back{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;
  color:var(--ink-2);letter-spacing:0.04em;margin-bottom:18px;padding:4px 0;}
.gs-back:hover{color:var(--ink);}
.gs-detail-grid{display:grid;grid-template-columns:1fr 268px;gap:20px;align-items:start;}
.gs-section{margin-bottom:22px;}
.gs-section-h{font-family:var(--mono);font-size:10px;letter-spacing:0.14em;color:var(--ink-3);
  text-transform:uppercase;margin-bottom:10px;display:flex;align-items:center;gap:7px;}
.gs-body-text{font-size:13.5px;line-height:1.65;color:var(--ink);}
.gs-body-text.muted{color:var(--ink-2);}
.gs-result{background:var(--go-soft);border:1px solid var(--go-line);border-radius:10px;padding:13px 15px;
  font-size:13.5px;color:var(--ink);line-height:1.55;display:flex;gap:10px;}
.gs-meta-card{padding:15px 16px;}
.gs-meta-row{display:flex;align-items:center;justify-content:space-between;padding:9px 0;border-bottom:1px solid var(--line);}
.gs-meta-row:last-child{border-bottom:none;}
.gs-meta-k{font-family:var(--mono);font-size:11px;color:var(--ink-3);letter-spacing:0.03em;}
.gs-meta-v{font-family:var(--mono);font-size:12px;color:var(--ink);font-weight:500;}
.gs-link{display:flex;align-items:center;gap:9px;padding:9px 11px;border:1px solid var(--line);border-radius:8px;
  margin-bottom:7px;font-size:12.5px;transition:all .12s;cursor:pointer;}
.gs-link:hover{border-color:var(--line-2);background:var(--surface-2);}
.gs-link .u{font-family:var(--mono);font-size:11px;color:var(--ink-3);margin-left:auto;}
.gs-dep{display:flex;align-items:center;gap:9px;padding:8px 0;font-size:12.5px;color:var(--ink-2);}

/* monitor */
.gs-host-group{margin-bottom:24px;}
.gs-host-head{display:flex;align-items:center;gap:11px;margin-bottom:11px;padding-bottom:9px;border-bottom:1px solid var(--line);}
.gs-host-nm{font-family:var(--disp);font-weight:600;font-size:15px;}
.gs-host-tag{font-family:var(--mono);font-size:10px;color:var(--ink-3);letter-spacing:0.08em;}
.gs-svc{display:grid;grid-template-columns:1fr 64px 68px 60px 78px 18px;gap:16px;align-items:center;
  padding:13px 18px;border-bottom:1px solid var(--line);font-size:13px;transition:background .12s;cursor:pointer;}
.gs-svc:last-child{border-bottom:none;border-radius:0 0 12px 12px;}
.gs-svc:hover{background:var(--surface-2);}
.gs-svc-chev{display:grid;place-items:center;color:var(--ink-3);}

/* toggle */
.gs-toggle{display:inline-flex;background:var(--surface-3);border:1px solid var(--line);border-radius:9px;
  padding:3px;gap:2px;margin-bottom:20px;}
.gs-toggle button{font-family:var(--mono);font-size:11px;letter-spacing:0.04em;padding:7px 14px;border-radius:7px;
  color:var(--ink-2);font-weight:500;transition:all .12s;display:flex;align-items:center;gap:7px;}
.gs-toggle button.on{background:var(--surface);color:var(--ink);box-shadow:0 1px 2px rgba(20,25,31,.06);}
.gs-svc-nm{display:flex;align-items:center;gap:11px;min-width:0;}
.gs-svc-nm .id{font-size:13.5px;font-weight:500;letter-spacing:-0.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-svc-nm .sub{font-family:var(--mono);font-size:10px;color:var(--ink-3);letter-spacing:0.04em;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-svc-val{font-family:var(--mono);font-size:12.5px;text-align:right;color:var(--ink);white-space:nowrap;}
.gs-svc-head{font-family:var(--mono);font-size:9px;letter-spacing:0.11em;color:var(--ink-3);
  text-transform:uppercase;padding:11px 18px;display:grid;grid-template-columns:1fr 64px 68px 60px 78px 18px;gap:16px;
  background:var(--surface-2);border-bottom:1px solid var(--line);border-radius:12px 12px 0 0;}
.gs-svc-head span:not(:first-child){text-align:right;}

/* flight chat */
.gs-chat{display:flex;flex-direction:column;height:100%;max-width:760px;margin:0 auto;width:100%;}
.gs-msgs{flex:1;overflow-y:auto;display:flex;flex-direction:column;gap:16px;padding:6px 2px 18px;}
.gs-msg{display:flex;gap:11px;max-width:88%;}
.gs-msg.me{align-self:flex-end;flex-direction:row-reverse;}
.gs-msg-av{width:28px;height:28px;border-radius:7px;flex-shrink:0;display:grid;place-items:center;}
.gs-msg-av.flight{background:var(--ink);color:#fff;}
.gs-msg-av.me{background:var(--surface-3);color:var(--ink-2);}
.gs-bub{padding:11px 14px;border-radius:11px;font-size:13.5px;line-height:1.55;}
.gs-msg.flight .gs-bub{background:var(--surface);border:1px solid var(--line);}
.gs-msg.me .gs-bub{background:var(--ink);color:#fff;}
.gs-bub .mono{font-family:var(--mono);font-size:12px;}
.gs-chips{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:12px;}
.gs-chip{font-family:var(--mono);font-size:11px;padding:6px 11px;border-radius:18px;border:1px solid var(--line-2);
  color:var(--ink-2);background:var(--surface);transition:all .12s;}
.gs-chip:hover{border-color:var(--go);color:var(--go);background:var(--go-soft);}
.gs-composer{display:flex;gap:9px;padding:12px;border:1px solid var(--line-2);border-radius:12px;background:var(--surface);}
.gs-composer input{flex:1;border:none;outline:none;font-family:var(--sans);font-size:13.5px;color:var(--ink);background:transparent;}
.gs-composer input::placeholder{color:var(--ink-3);}

.gs-run{display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--line);font-size:12.5px;}
.gs-run:last-child{border-bottom:none;}

/* flight console */
.gs-flight-wrap{display:flex;flex-direction:column;height:100%;}
.gs-flight-content{flex:1;min-height:0;display:flex;flex-direction:column;}
.gs-panel{flex:1;overflow-y:auto;max-width:760px;width:100%;margin:0 auto;padding:2px 2px 8px;}
.gs-switch{width:34px;height:20px;border-radius:20px;background:var(--line-2);position:relative;transition:all .15s;flex-shrink:0;cursor:pointer;}
.gs-switch.on{background:var(--go);}
.gs-switch::after{content:"";position:absolute;top:2px;left:2px;width:16px;height:16px;border-radius:50%;background:#fff;transition:all .15s;box-shadow:0 1px 2px rgba(0,0,0,.22);}
.gs-switch.on::after{left:16px;}
.gs-conn{display:flex;align-items:center;gap:13px;padding:13px 15px;border:1px solid var(--line);border-radius:11px;margin-bottom:9px;background:var(--surface);transition:border-color .12s;}
.gs-conn.off{background:var(--surface-2);}
.gs-conn-ic{width:36px;height:36px;border-radius:9px;background:var(--surface-3);display:grid;place-items:center;color:var(--ink-2);flex-shrink:0;}
.gs-conn-nm{font-weight:600;font-size:13.5px;letter-spacing:-0.01em;display:flex;align-items:center;gap:8px;}
.gs-conn-meta{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-conn-act{margin-left:auto;display:flex;align-items:center;gap:12px;flex-shrink:0;}
.gs-icon-btn{display:grid;place-items:center;width:30px;height:30px;border-radius:8px;color:var(--ink-3);transition:all .12s;}
.gs-icon-btn:hover{background:var(--fault-soft);color:var(--fault);}
.gs-addrow{display:flex;gap:8px;margin-top:10px;}
.gs-input{flex:1;border:1px solid var(--line-2);border-radius:9px;padding:9px 12px;font-family:var(--mono);font-size:12px;color:var(--ink);background:var(--surface);outline:none;transition:border-color .12s;}
.gs-input:focus{border-color:var(--go);}
.gs-input::placeholder{color:var(--ink-3);}
.gs-atts{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:9px;}
.gs-att{display:flex;align-items:center;gap:7px;padding:6px 10px;border:1px solid var(--line);border-radius:8px;font-size:12px;background:var(--surface-2);max-width:220px;}
.gs-att .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-att .rm{color:var(--ink-3);display:grid;place-items:center;cursor:pointer;flex-shrink:0;}
.gs-att .rm:hover{color:var(--fault);}
.gs-attach-btn{display:grid;place-items:center;width:38px;border-radius:9px;color:var(--ink-3);cursor:pointer;transition:all .12s;flex-shrink:0;}
.gs-attach-btn:hover{background:var(--surface-3);color:var(--ink);}
.gs-fact{display:flex;gap:10px;align-items:flex-start;padding:11px 0;border-bottom:1px solid var(--line);font-size:13px;color:var(--ink);line-height:1.5;}
.gs-fact:last-child{border-bottom:none;}

@media (max-width:820px){
  .gs-rail{display:none;}
  .gs-detail-grid{grid-template-columns:1fr;}
  .gs-svc{grid-template-columns:1fr 56px 68px 18px;}
  .gs-svc-head{grid-template-columns:1fr 56px 68px 18px;}
  .gs-svc > :nth-child(3), .gs-svc > :nth-child(4){display:none;}
  .gs-svc-head span:nth-child(3), .gs-svc-head span:nth-child(4){display:none;}
}
@media (prefers-reduced-motion:reduce){ .gs *{transition:none !important;} }

/* breadcrumb */
.gs-crumb{display:flex;align-items:center;gap:6px;font-size:14px;z-index:1;min-width:0;}
.gs-crumb button{font-family:var(--disp);font-weight:600;font-size:15px;letter-spacing:-0.01em;color:var(--ink-3);transition:color .12s;white-space:nowrap;}
.gs-crumb button:hover{color:var(--ink);}
.gs-crumb .cur{font-family:var(--disp);font-weight:600;font-size:15px;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-crumb .sep{color:var(--ink-3);flex-shrink:0;}

/* strip search button */
.gs-kbtn{display:flex;align-items:center;gap:9px;padding:6px 10px 6px 11px;border:1px solid var(--line-2);border-radius:8px;
  color:var(--ink-3);font-size:12px;transition:all .12s;z-index:1;background:var(--surface);}
.gs-kbtn:hover{border-color:var(--ink-3);color:var(--ink-2);}
.gs-kbtn kbd{font-family:var(--mono);font-size:10px;background:var(--surface-3);border:1px solid var(--line);border-radius:4px;padding:1px 5px;color:var(--ink-2);}

/* search palette */
.gs-overlay{position:absolute;inset:0;background:rgba(20,25,31,.28);backdrop-filter:blur(2px);z-index:50;
  display:flex;justify-content:center;padding-top:12vh;animation:gsfade .12s ease;}
@keyframes gsfade{from{opacity:0}to{opacity:1}}
.gs-pal{width:min(560px,92%);height:max-content;max-height:64%;background:var(--surface);border:1px solid var(--line-2);
  border-radius:14px;box-shadow:0 24px 60px -20px rgba(20,25,31,.45);display:flex;flex-direction:column;overflow:hidden;}
.gs-pal-in{display:flex;align-items:center;gap:11px;padding:15px 17px;border-bottom:1px solid var(--line);}
.gs-pal-in input{flex:1;border:none;outline:none;font-family:var(--sans);font-size:15px;color:var(--ink);background:transparent;}
.gs-pal-in input::placeholder{color:var(--ink-3);}
.gs-pal-res{overflow-y:auto;padding:7px;}
.gs-pal-grp{font-family:var(--mono);font-size:9.5px;letter-spacing:0.12em;color:var(--ink-3);text-transform:uppercase;padding:9px 11px 5px;}
.gs-pal-item{display:flex;align-items:center;gap:11px;padding:9px 11px;border-radius:9px;cursor:pointer;transition:background .1s;}
.gs-pal-item.sel,.gs-pal-item:hover{background:var(--surface-3);}
.gs-pal-item .ic{width:28px;height:28px;border-radius:7px;background:var(--surface-3);display:grid;place-items:center;color:var(--ink-2);flex-shrink:0;}
.gs-pal-item.sel .ic{background:var(--surface);}
.gs-pal-item .t{font-size:13.5px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-pal-item .s{font-family:var(--mono);font-size:10.5px;color:var(--ink-3);margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-pal-item .k{margin-left:auto;font-family:var(--mono);font-size:10px;color:var(--ink-3);flex-shrink:0;}
.gs-pal-empty{padding:26px;text-align:center;color:var(--ink-3);font-size:13px;}

/* toast */
.gs-toasts{position:absolute;bottom:22px;left:50%;transform:translateX(-50%);z-index:60;display:flex;flex-direction:column;gap:9px;align-items:center;}
.gs-toast{display:flex;align-items:center;gap:11px;background:var(--ink);color:#fff;padding:11px 15px;border-radius:11px;
  font-size:13px;box-shadow:0 12px 30px -10px rgba(20,25,31,.5);animation:gsrise .18s ease;max-width:420px;}
.gs-toast .go{color:#5fd39b;}
.gs-toast button{color:#9fb0bd;font-weight:600;font-size:12px;font-family:var(--mono);margin-left:4px;}
.gs-toast button:hover{color:#fff;}
@keyframes gsrise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}

/* queue tools */
.gs-qtools{display:flex;gap:9px;margin-bottom:14px;align-items:center;flex-wrap:wrap;}
.gs-qsearch{display:flex;align-items:center;gap:9px;flex:1;min-width:180px;border:1px solid var(--line-2);border-radius:9px;padding:8px 12px;background:var(--surface);transition:border-color .12s;}
.gs-qsearch:focus-within{border-color:var(--go);}
.gs-qsearch input{flex:1;border:none;outline:none;font-family:var(--sans);font-size:13px;color:var(--ink);background:transparent;}
.gs-qsearch input::placeholder{color:var(--ink-3);}
.gs-sort{font-family:var(--mono);font-size:11px;color:var(--ink-2);border:1px solid var(--line-2);border-radius:9px;padding:8px 11px;background:var(--surface);cursor:pointer;outline:none;}
.gs-chip-x{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:11px;padding:6px 8px 6px 11px;border-radius:20px;background:var(--go-soft);color:var(--go);border:1px solid var(--go-line);}
.gs-chip-x button{display:grid;place-items:center;color:var(--go);}

/* clickable inline reference */
.gs-ref{color:var(--go);font-weight:600;cursor:pointer;border-bottom:1px solid transparent;transition:border-color .12s;}
.gs-ref:hover{border-color:var(--go);}
.gs-linkable{cursor:pointer;transition:color .12s;}
.gs-linkable:hover{color:var(--go);}
.gs-empty{padding:40px 20px;text-align:center;color:var(--ink-3);font-size:13.5px;}

/* flight header */
.gs-fl-head{display:flex;align-items:center;gap:11px;margin-bottom:16px;}
.gs-fl-id{display:flex;align-items:center;gap:10px;}
.gs-fl-av{width:32px;height:32px;border-radius:9px;background:var(--ink);color:#fff;display:grid;place-items:center;}
.gs-fl-nm{font-family:var(--disp);font-weight:600;font-size:16px;letter-spacing:-0.01em;line-height:1;}
.gs-fl-st{font-family:var(--mono);font-size:9.5px;color:var(--go);letter-spacing:0.08em;margin-top:4px;display:flex;align-items:center;gap:5px;}
.gs-hbtn{display:flex;align-items:center;gap:7px;padding:7px 11px;border:1px solid var(--line-2);border-radius:9px;
  color:var(--ink-2);font-size:12.5px;font-weight:500;transition:all .12s;background:var(--surface);}
.gs-hbtn:hover{border-color:var(--ink-3);color:var(--ink);background:var(--surface-2);}
.gs-hbtn.icon{padding:8px;}

/* welcome */
.gs-welcome{flex:1;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;gap:5px;padding-bottom:8px;}
.gs-welcome h2{font-family:var(--disp);font-weight:600;font-size:20px;letter-spacing:-0.02em;margin:6px 0 2px;}
.gs-welcome p{color:var(--ink-2);font-size:13.5px;margin:0 0 20px;}
.gs-sugg{display:grid;grid-template-columns:1fr 1fr;gap:10px;width:100%;max-width:540px;}
.gs-sugg button{text-align:left;padding:13px 15px;border:1px solid var(--line);border-radius:11px;background:var(--surface);
  transition:all .13s;display:flex;flex-direction:column;gap:3px;}
.gs-sugg button:hover{border-color:var(--line-2);background:var(--surface-2);transform:translateY(-1px);}
.gs-sugg .t{font-size:13px;font-weight:600;color:var(--ink);}
.gs-sugg .d{font-size:11.5px;color:var(--ink-3);}

/* tool-call chips */
.gs-tools{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:7px;}
.gs-toolchip{display:inline-flex;align-items:center;gap:6px;font-family:var(--mono);font-size:10px;padding:3px 8px;
  border-radius:6px;background:var(--surface-3);color:var(--ink-2);border:1px solid var(--line);}
.gs-toolchip .ck{color:var(--go);display:grid;place-items:center;}

/* thinking */
.gs-think{display:flex;align-items:center;gap:5px;padding:11px 14px;}
.gs-think i{width:6px;height:6px;border-radius:50%;background:var(--ink-3);animation:gsblink 1.1s infinite;}
.gs-think i:nth-child(2){animation-delay:.18s;} .gs-think i:nth-child(3){animation-delay:.36s;}
@keyframes gsblink{0%,60%,100%{opacity:.25;transform:translateY(0)}30%{opacity:1;transform:translateY(-2px)}}

/* message copy action */
.gs-msg-copy{margin-top:5px;display:flex;gap:2px;opacity:0;transition:opacity .12s;}
.gs-msg.flight:hover .gs-msg-copy{opacity:1;}
.gs-msg-copy button{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10px;color:var(--ink-3);padding:3px 7px;border-radius:6px;transition:all .12s;}
.gs-msg-copy button:hover{background:var(--surface-3);color:var(--ink-2);}

/* voice / mic */
.gs-mic{display:grid;place-items:center;width:38px;border-radius:9px;color:var(--ink-3);cursor:pointer;transition:all .12s;flex-shrink:0;}
.gs-mic:hover{background:var(--surface-3);color:var(--ink);}
.gs-mic.rec{color:var(--fault);}
.gs-recbar{flex:1;display:flex;align-items:center;gap:12px;padding:0 4px;}
.gs-wave{display:flex;align-items:center;gap:3px;height:22px;}
.gs-wave i{width:3px;border-radius:3px;background:var(--fault);animation:gswave 0.9s infinite ease-in-out;}
.gs-wave i:nth-child(2){animation-delay:.1s}.gs-wave i:nth-child(3){animation-delay:.2s}.gs-wave i:nth-child(4){animation-delay:.3s}
.gs-wave i:nth-child(5){animation-delay:.15s}.gs-wave i:nth-child(6){animation-delay:.25s}.gs-wave i:nth-child(7){animation-delay:.05s}
@keyframes gswave{0%,100%{height:5px}50%{height:20px}}
.gs-rec-label{font-family:var(--mono);font-size:12px;color:var(--fault);letter-spacing:0.04em;}

/* config drawer */
.gs-drawer-bg{position:absolute;inset:0;background:rgba(20,25,31,.20);backdrop-filter:blur(1px);z-index:30;animation:gsfade .12s ease;}
.gs-drawer{position:absolute;top:0;right:0;bottom:0;width:min(400px,86%);background:var(--surface);border-left:1px solid var(--line-2);
  z-index:31;display:flex;flex-direction:column;box-shadow:-16px 0 40px -20px rgba(20,25,31,.35);animation:gsslide .18s ease;}
@keyframes gsslide{from{transform:translateX(24px);opacity:.6}to{transform:translateX(0);opacity:1}}
.gs-drawer-head{display:flex;align-items:center;gap:10px;padding:16px 18px;border-bottom:1px solid var(--line);}
.gs-drawer-head .ttl{font-family:var(--disp);font-weight:600;font-size:15px;}
.gs-drawer-body{flex:1;overflow-y:auto;padding:16px 18px;}
.gs-drawer.left{left:0;right:auto;border-left:none;border-right:1px solid var(--line-2);
  box-shadow:16px 0 40px -20px rgba(20,25,31,.35);animation:gsslideL .18s ease;}
@keyframes gsslideL{from{transform:translateX(-24px);opacity:.6}to{transform:translateX(0);opacity:1}}

/* model selector */
.gs-model{display:flex;align-items:center;gap:8px;padding:7px 10px;border:1px solid var(--line-2);border-radius:9px;
  background:var(--surface);font-size:12.5px;font-weight:600;color:var(--ink);transition:all .12s;}
.gs-model:hover{border-color:var(--ink-3);background:var(--surface-2);}
.gs-menu-catch{position:fixed;inset:0;z-index:40;}
.gs-menu{position:absolute;top:calc(100% + 6px);right:0;z-index:41;background:var(--surface);border:1px solid var(--line-2);
  border-radius:11px;box-shadow:0 16px 40px -16px rgba(20,25,31,.35);padding:6px;min-width:236px;animation:gsfade .1s ease;}
.gs-menu-lbl{font-family:var(--mono);font-size:9px;letter-spacing:0.12em;color:var(--ink-3);text-transform:uppercase;padding:6px 10px 4px;}
.gs-menu-item{display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:8px;cursor:pointer;transition:background .1s;width:100%;text-align:left;}
.gs-menu-item:hover{background:var(--surface-3);}
.gs-menu-item .t{font-size:13px;font-weight:500;color:var(--ink);}
.gs-menu-item .g{font-family:var(--mono);font-size:9.5px;color:var(--ink-3);margin-top:1px;}
.gs-menu-item .chk{margin-left:auto;color:var(--go);display:grid;place-items:center;}

/* session history */
.gs-sess{display:flex;flex-direction:column;gap:3px;padding:11px 12px;border-radius:10px;cursor:pointer;transition:all .1s;border:1px solid transparent;margin-bottom:4px;}
.gs-sess:hover{background:var(--surface-2);}
.gs-sess.active{background:var(--go-soft);border-color:var(--go-line);}
.gs-sess .t{font-size:13px;font-weight:500;color:var(--ink);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gs-sess .m{font-family:var(--mono);font-size:10px;color:var(--ink-3);display:flex;gap:9px;}

/* logs */
.gs-logbox{border:1px solid var(--line);border-radius:12px;background:var(--surface);overflow:hidden;}
.gs-logline{display:grid;grid-template-columns:70px 46px 1fr;gap:12px;padding:5px 16px;font-family:var(--mono);font-size:11.5px;border-bottom:1px solid var(--surface-3);align-items:baseline;}
.gs-logline:last-child{border-bottom:none;}
.gs-logline:hover{background:var(--surface-2);}
.gs-logline .ts{color:var(--ink-3);}
.gs-logline .lv{font-weight:600;letter-spacing:0.03em;}
.gs-logline .lv.info{color:var(--info);} .gs-logline .lv.warn{color:var(--caution);} .gs-logline .lv.err{color:var(--fault);}
.gs-logline .mg{color:var(--ink);white-space:pre-wrap;word-break:break-word;}
.gs-loggap{display:block;width:100%;text-align:center;font-family:var(--mono);font-size:11px;
  color:var(--ink-3);background:none;border:none;border-top:1px dashed var(--line-2);
  border-bottom:1px dashed var(--line-2);padding:6px 0;margin:4px 0;cursor:pointer;letter-spacing:0.04em;}
.gs-loggap:hover{color:var(--ink);background:var(--surface-3);}
.gs-loggap.older{border:none;}
.gs-logline.ctx{opacity:0.72;}
.gs-follow{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11px;color:var(--go);padding:6px 11px;border:1px solid var(--go-line);background:var(--go-soft);border-radius:20px;}

/* markdown + chain-of-thought */
.gs-cot{margin:0 0 8px}
.gs-cot-head{display:flex;align-items:center;gap:6px;background:none;border:none;color:var(--ink-3);font-size:12px;cursor:pointer;padding:2px 0}
.gs-cot-head:hover{color:var(--ink-2)}
.gs-cot-body{margin:6px 0 2px;padding:8px 12px;border-left:2px solid var(--line);color:var(--ink-2);font-size:13px}
.gs-md{overflow-wrap:anywhere}
.gs-md p{margin:0 0 8px}.gs-md p:last-child{margin:0}
.gs-md pre{overflow:auto;border-radius:8px;padding:10px 12px;margin:8px 0;font-family:var(--mono);font-size:12.5px}
.gs-md code{font-family:var(--mono);font-size:12.5px}
.gs-md table{border-collapse:collapse}.gs-md th,.gs-md td{border:1px solid var(--line);padding:4px 8px}
`;

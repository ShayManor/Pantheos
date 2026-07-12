import React, { useState, useEffect, useMemo, useRef, useContext } from "react";
import {
  Radio, Satellite, Gauge, ListChecks, Rocket, GitPullRequest, GitBranch,
  Clock, AlertTriangle, ArrowLeft, Send, Cpu, Server, HardDrive, Activity,
  ChevronRight, Zap, MessageSquare, Link2, Calendar, Hash, CircleDot,
  CheckCircle2, PauseCircle, Layers, Signal, SignalZero, Terminal, Boxes,
  Paperclip, Plus, X, Check, Wrench, Brain, Trash2, FileText, Plug,
  Mic, Square, Copy, Settings, SquarePen, Sparkles, History, ChevronDown, ArrowUpDown, Download
} from "lucide-react";
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid
} from "recharts";

/* ============================== DESIGN TOKENS ============================== */
const CSS = `
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
.gs-shell{display:flex;min-height:640px;height:88vh;background:var(--paper);
  border:1px solid var(--line);border-radius:14px;overflow:hidden;}
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
.gs-sub{color:var(--ink-2);font-size:13.5px;margin:0 0 20px;}
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
.gs-follow{display:inline-flex;align-items:center;gap:7px;font-family:var(--mono);font-size:11px;color:var(--go);padding:6px 11px;border:1px solid var(--go-line);background:var(--go-soft);border-radius:20px;}
`;

/* ============================== MOCK DATA ============================== */
const spark = (base, n = 14, amp = 0.25) =>
  Array.from({ length: n }, (_, i) => ({
    d: i,
    v: Math.max(0, Math.round(base * (1 + Math.sin(i / 2.3) * amp * 0.5 + (Math.random() - 0.5) * amp)))
  }));

const PROJECTS = {
  merlin:    { name: "MERLIN", area: "IDEAS LAB", autonomy: "auto_pr", status: "go",
               users: null, blurb: "Metric edge reconstruction for lightweight indoor nav", repo: "ideas-lab/merlin" },
  guardrail: { name: "Guardrail", area: "IDEAS LAB", autonomy: "auto_pr", status: "go",
               users: null, blurb: "Teacher-supervised failure detection under domain shift", repo: "ideas-lab/guardrail" },
  ghstats:   { name: "gh-stats", area: "SIDE PROJECTS", autonomy: "full", status: "flt",
               users: 3820, blurb: "GitHub profile analytics", repo: "shaymanor/gh-stats" },
  gpufindr:  { name: "GPUFindr", area: "SIDE PROJECTS", autonomy: "full", status: "cau",
               users: 1140, blurb: "GPU availability + price aggregator", repo: "shaymanor/gpufindr" },
  rviewer:   { name: "ResearchViewer", area: "SIDE PROJECTS", autonomy: "full", status: "go",
               users: 640, blurb: "Research paper exploration tool", repo: "shaymanor/researchviewer" },
  evc:       { name: "Autonomy Stack", area: "EVC", autonomy: "propose", status: "go",
               users: null, blurb: "Autonomous kart control + perception", repo: "evc-purdue/autonomy" },
  groundstation: { name: "Pantheos", area: "SIDE PROJECTS", autonomy: "full", status: "go",
               users: null, blurb: "This platform — tickets, monitoring, and Delphi", repo: "shaymanor/pantheos" },
};

const TICKETS = [
  { id: "GRD-0182", proj: "guardrail", title: "TMLR camera-ready revisions", pri: 0,
    due: "in 2d", hot: true, score: "9.4", life: "active", agent: "idle", source: "manual",
    summary: "Address reviewer 2's ablation request and re-run the OOD detection sweep before Friday.",
    body: "Reviewers accepted with minor revisions. R2 wants an ablation isolating the teacher-confidence threshold from the entropy gate, plus a table over 3 domain-shift severities. Re-run sweep on Gautschi (8×A100), regenerate Fig 4, update related work with the two ICLR'26 citations flagged by R1.",
    report: "Ran threshold sweep τ∈{0.5,0.7,0.9} × severity {light,med,heavy}. Cosine-gated variant held +1.2 mIoU over entropy-only at heavy shift. Fig 4 + Table 3 regenerated.",
    result: "Ablation confirms the teacher gate is the load-bearing component; camera-ready draft ready for your review.",
    deps: [], links: [
      { kind: "github_issue", label: "ideas-lab/guardrail #182", url: "/issues/182" },
      { kind: "file", label: "reviews_r1_r2.pdf", url: "attach" }],
    effort: "6h", area: "IDEAS LAB" },

  { id: "GHS-0311", proj: "ghstats", title: "500-rate breach on api container", pri: 0,
    due: "now", hot: true, score: "9.1", life: "active", agent: "executing", source: "alert",
    summary: "Alert: gh-stats-api 500-rate > 5% for 11m on minipc. Auto-filed, Delphi dispatched.",
    body: "Alertmanager fired traefik_5xx_ratio{project=ghstats} = 0.061 sustained 11m. Restart count on gh-stats-api jumped to 4 in the last hour. Recent deploy c7f2a1 touched the rate-limit middleware. Likely a null-deref on the new Redis path when the cache is cold.",
    report: "Reproduced cold-cache null deref in rate-limit middleware. Added guard + fallback to in-memory bucket. CI green. PR opened, self-merge blocked pending green canary.",
    result: "Fix identified and PR pushed; 500-rate down to 0.3% on canary. Awaiting your merge (full-autonomy would auto-merge on green).",
    deps: [], links: [
      { kind: "github_pr", label: "gh-stats#94 fix(rate-limit)", url: "/pull/94" },
      { kind: "github_issue", label: "auto: alert GHS-0311", url: "/issues/x" }],
    effort: "1h", area: "SIDE PROJECTS" },

  { id: "EVC-0074", proj: "evc", title: "Fix motor sync on left rear", pri: 1,
    due: "in 4d", hot: false, score: "6.8", life: "queued", agent: "idle", source: "slack",
    summary: "Encoder counts drift ~3% between rear motors above 20 km/h; suspect CAN timing.",
    body: "From #autonomy Slack: left-rear encoder desyncs from right-rear under load. Reproduces above 20 km/h. Hypothesis: CAN frame jitter on the VESC bus starves the sync loop. Check bus load %, confirm frame IDs aren't colliding with the IMU stream, consider raising sync-loop rate to 200Hz.",
    report: null, result: null,
    deps: [{ id: "EVC-0071", title: "CAN bus load profiling", done: true }],
    links: [{ kind: "slack_message", label: "#autonomy · thread", url: "slack" }],
    effort: "5h", area: "EVC" },

  { id: "MER-0093", proj: "merlin", title: "Port edge extractor to Rubik Pi 3", pri: 1,
    due: "in 6d", hot: false, score: "5.9", life: "queued", agent: "idle", source: "github",
    summary: "Cross-compile the metric edge stage for the Rubik Pi NPU and benchmark vs Orin Nano.",
    body: "Move the edge-reconstruction stage off the Jetson Orin Nano onto the Rubik Pi 3 to free the Orin for the planner. Needs INT8 quantization of the extractor, a QNN delegate path, and a latency comparison at 640×480. Target < 22ms/frame.",
    report: null, result: null,
    deps: [{ id: "MER-0088", title: "INT8 quant of extractor", done: false }],
    links: [{ kind: "github_issue", label: "ideas-lab/merlin #93", url: "/issues/93" }],
    effort: "8h", area: "IDEAS LAB" },

  { id: "STA-0044", proj: null, title: "STAT 511 · Problem Set 4", pri: 1,
    due: "in 3d", hot: false, score: "6.1", life: "queued", agent: "idle", source: "brightspace",
    summary: "MLE, sufficient statistics, and a Fisher-information derivation. PDF pulled from Brightspace.",
    body: "Brightspace: PS4 covers maximum likelihood estimation, sufficiency + the factorization theorem, and Cramér-Rao lower bound. 6 problems. Problem 5 asks for the Fisher information of a Gamma(α, β) with known β. Due 11:59pm.",
    report: null, result: null, deps: [],
    links: [
      { kind: "brightspace", label: "STAT 511 · PS4", url: "bs" },
      { kind: "file", label: "ps4.pdf", url: "attach" }],
    effort: "4h", area: "STAT 511" },

  { id: "GHS-0308", proj: "ghstats", title: "SEO: programmatic profile pages", pri: 2,
    due: "in 12d", hot: false, score: "3.4", life: "queued", agent: "idle", source: "manual",
    summary: "Generate indexable per-user stat pages to break the traffic plateau.",
    body: "User growth flat ~3.8k/wk. Hypothesis: no long-tail SEO surface. Generate static, cacheable /u/<handle> pages with OG images, sitemap, and schema.org markup. Measure index coverage in Search Console after 2 weeks.",
    report: null, result: null, deps: [],
    links: [{ kind: "github_issue", label: "gh-stats #308", url: "/issues/308" }],
    effort: "6h", area: "SIDE PROJECTS" },

  { id: "GPU-0021", proj: "gpufindr", title: "Stale prices on 2 providers", pri: 2,
    due: "in 5d", hot: false, score: "3.1", life: "queued", agent: "idle", source: "alert",
    summary: "Scraper for Lambda + RunPod returning cached data > 6h old; freshness caution.",
    body: "Freshness monitor shows lambda + runpod feeds > 6h stale. Their markup changed; selectors likely broke. Re-derive selectors, add a freshness alert at 2h, backfill.",
    report: null, result: null, deps: [],
    links: [{ kind: "github_issue", label: "gpufindr #21", url: "/issues/21" }],
    effort: "3h", area: "SIDE PROJECTS" },

  { id: "MER-0088", proj: "merlin", title: "INT8 quantization of extractor", pri: 2,
    due: null, hot: false, score: "2.7", life: "backburner", agent: "idle", source: "manual",
    summary: "Post-training INT8 quant with a calibration set from the lab hallway captures.",
    body: "Prereq for the Rubik Pi port. Build a 300-frame calibration set from hallway captures, run PTQ, verify edge-F1 stays within 2% of FP16.",
    report: null, result: null, deps: [], links: [], effort: "5h", area: "IDEAS LAB" },

  { id: "RV-0012", proj: "rviewer", title: "Add citation-graph hover cards", pri: 3,
    due: null, hot: false, score: "1.4", life: "backburner", agent: "idle", source: "manual",
    summary: "Show a mini citation neighborhood on hover over any paper node.",
    body: "Low stakes, full autonomy. On hover over a paper, fetch its 5 most-cited neighbors from the Semantic Scholar API and render a small card. Nice-to-have.",
    report: null, result: null, deps: [], links: [], effort: "3h", area: "SIDE PROJECTS" },
];

const HOSTS = {
  minipc:  { id: "minipc", name: "minipc", kind: "always_on", icon: Server, tag: "ALWAYS-ON · local", loc: "Purdue apt" },
  gcp:     { id: "gcp", name: "GCP · Cloud Run", kind: "intermittent", icon: Boxes, tag: "SCALE-TO-ZERO · polled", loc: "us-central1" },
  jetson:  { id: "jetson", name: "Jetson Orin Nano", kind: "intermittent", icon: Cpu, tag: "INTERMITTENT · onboard", loc: "EVC kart" },
  rubikpi: { id: "rubikpi", name: "Rubik Pi 3", kind: "intermittent", icon: HardDrive, tag: "INTERMITTENT · onboard", loc: "EVC kart" },
};

// a container belongs to exactly one project and runs on exactly one host
const CONTAINERS = [
  { id: "gh-stats-api", proj: "ghstats", host: "minipc", role: "api", status: "flt",
    cpu: "38%", cpuN: 38, mem: "512M", err: "6.1%", rps: "142/s", p95: "890 ms", restarts: 4, up: "AOS", image: "ghstats/api:c7f2a1" },
  { id: "gh-stats-web", proj: "ghstats", host: "minipc", role: "web", status: "go",
    cpu: "4%", cpuN: 4, mem: "96M", err: "0.0%", rps: "38/s", p95: "64 ms", restarts: 0, up: "AOS", image: "ghstats/web:1f9d0e" },
  { id: "gpufindr-api", proj: "gpufindr", host: "minipc", role: "api", status: "cau",
    cpu: "12%", cpuN: 12, mem: "210M", err: "0.4%", rps: "22/s", p95: "120 ms", restarts: 1, up: "AOS", image: "gpufindr/api:8a41c2" },
  { id: "gpufindr-scraper", proj: "gpufindr", host: "minipc", role: "worker", status: "cau",
    cpu: "22%", cpuN: 22, mem: "180M", err: "—", rps: "—", p95: "—", restarts: 0, up: "AOS", image: "gpufindr/scraper:8a41c2" },
  { id: "gs-platform", proj: "groundstation", host: "minipc", role: "api", status: "go",
    cpu: "9%", cpuN: 9, mem: "340M", err: "0.0%", rps: "12/s", p95: "48 ms", restarts: 0, up: "AOS", image: "pantheos/platform:dev" },
  { id: "rviewer", proj: "rviewer", host: "gcp", role: "web", status: "go",
    cpu: "—", cpuN: 6, mem: "—", err: "0.1%", rps: "3/s", p95: "210 ms", restarts: 0, up: "AOS", image: "gcr.io/rviewer:live" },
  { id: "merlin-planner", proj: "merlin", host: "jetson", role: "planner", status: "los",
    cpu: "—", cpuN: 0, mem: "—", err: "—", rps: "—", p95: "—", restarts: 0, up: "LOS", image: "merlin/planner:orin" },
  { id: "merlin-edge", proj: "merlin", host: "jetson", role: "perception", status: "los",
    cpu: "—", cpuN: 0, mem: "—", err: "—", rps: "—", p95: "—", restarts: 0, up: "LOS", image: "merlin/edge:orin" },
  { id: "edge-npu", proj: "merlin", host: "rubikpi", role: "perception", status: "los",
    cpu: "—", cpuN: 0, mem: "—", err: "—", rps: "—", p95: "—", restarts: 0, up: "LOS", image: "merlin/edge:qnn" },
];

const autoLabel = (a) => ({ propose: "propose", auto_pr: "auto-pr", full: "full" }[a] || a);
const registryUrl = (img) => img.startsWith("gcr.io/") ? `https://${img}` : `https://ghcr.io/shaymanor/${img.split(":")[0]}`;
const repoUrl = (r) => `https://github.com/${r}`;
const byProject = (pk) => CONTAINERS.filter(c => c.proj === pk);
const byHost = (hid) => CONTAINERS.filter(c => c.host === hid);

const MCP_INIT = [
  { id: "github", name: "GitHub", url: "api.github.com", tools: 8, on: true, desc: "Issues, PRs, CI, commits" },
  { id: "gcal", name: "Google Calendar", url: "calendarmcp.googleapis.com", tools: 4, on: true, desc: "Events, free/busy, scheduling" },
  { id: "gmail", name: "Gmail", url: "gmailmcp.googleapis.com", tools: 5, on: true, desc: "Starred mail → tickets" },
  { id: "brightspace", name: "Brightspace", url: "browser-agent · isolated", tools: 3, on: true, desc: "Assignments + PDFs via browser session" },
  { id: "metrics", name: "VictoriaMetrics", url: "vm.minipc.local", tools: 2, on: true, desc: "PromQL over fleet telemetry" },
  { id: "hf", name: "Hugging Face", url: "huggingface.co/mcp", tools: 10, on: false, desc: "Models, datasets, spaces" },
  { id: "exa", name: "Exa", url: "mcp.exa.ai", tools: 2, on: false, desc: "Web search + fetch" },
];
const SKILL_INIT = [
  { id: "enrich", name: "enrich-ticket", on: true, trigger: "on create", desc: "Read sources, write summary + problem statement" },
  { id: "exec", name: "launch-claude-code", on: true, trigger: "manual / CI", desc: "Spawn headless session under project ceiling" },
  { id: "rerank", name: "re-rank-queue", on: true, trigger: "nightly", desc: "Score importance × urgency, propagate deadlines" },
  { id: "bs", name: "brightspace-pull", on: true, trigger: "hourly", desc: "New assignments → enriched tickets" },
  { id: "digest", name: "weekly-digest", on: false, trigger: "Sun 6pm", desc: "Summarize the week, flag slipping deadlines" },
];
const MEMORY_FACTS = [
  "Prefers terse, technically precise replies",
  "EVC → PR-only, never touch main",
  "Does exams in one sitting — block the full window",
  "Guardrail + MERLIN under active submission; results integrity matters",
];
const AGENT_RUNS = [
  { ticket: "GHS-0311", kind: "execute", status: "needs review", cost: "$0.42", when: "12m ago" },
  { ticket: "GRD-0182", kind: "enrich", status: "done", cost: "$0.03", when: "1h ago" },
  { ticket: "STA-0044", kind: "enrich", status: "done", cost: "$0.05", when: "3h ago" },
  { ticket: "EVC-0074", kind: "enrich", status: "done", cost: "$0.04", when: "5h ago" },
];
const rollup = (cs) => {
  if (!cs.length) return null;
  if (cs.some(c => c.status === "flt")) return "flt";
  if (cs.some(c => c.status === "cau")) return "cau";
  if (cs.every(c => c.status === "los")) return "los";
  return "go";
};

const USAGE = spark(3820, 14, 0.18);
const ERRSERIES = spark(2, 14, 0.9).map((p, i) => ({ ...p, v: i > 10 ? p.v + 5 : p.v * 0.4 }));

const LINK_ICON = {
  github_issue: GitBranch, github_pr: GitPullRequest, slack_message: MessageSquare,
  discord_message: MessageSquare, brightspace: Calendar, file: Hash, url: Link2,
};
const LINK_KIND = {
  github_issue: "info", github_pr: "go", slack_message: "neu",
  brightspace: "cau", file: "neu", url: "neu",
};

/* ============================== SMALL COMPONENTS ============================== */
const StatusPill = ({ s }) => {
  const map = { go: ["go", "NOMINAL"], cau: ["cau", "CAUTION"], flt: ["flt", "FAULT"], los: ["neu", "LOS"] };
  const [c, t] = map[s] || map.go;
  return <span className={`pill ${c}`}><span className={`dot ${s}`} style={{ width: 6, height: 6, boxShadow: "none" }} />{t}</span>;
};

const LifePill = ({ life, agent }) => {
  if (agent === "executing") return <span className="pill go"><Rocket size={11} />EXECUTING</span>;
  if (agent === "enriching") return <span className="pill info"><Zap size={11} />ENRICHING</span>;
  const map = {
    active: ["go", CircleDot, "ACTIVE"], queued: ["neu", Clock, "QUEUED"],
    backburner: ["neu", PauseCircle, "BACKBURNER"], blocked: ["cau", AlertTriangle, "BLOCKED"],
    archived: ["neu", CheckCircle2, "ARCHIVED"],
  };
  const [c, I, t] = map[life] || map.queued;
  return <span className={`pill ${c}`}><I size={11} />{t}</span>;
};
/* ============================== NAV CONTEXT ============================== */
const Nav = React.createContext(null);
const useNav = () => useContext(Nav);

/* ============================== SHARED ============================== */
// container list, reused everywhere. sub = "host" | "proj"
function ContainerTable({ containers, sub }) {
  const { go } = useNav();
  return (
    <div className="gs-card" style={{ overflow: "hidden" }}>
      <div className="gs-svc-head">
        <span>Container</span><span>CPU</span><span>Mem</span><span>5xx</span><span>Signal</span><span />
      </div>
      {containers.map(c => (
        <div key={c.id} className="gs-svc" onClick={() => go({ view: "monitor", containerId: c.id })}>
          <div className="gs-svc-nm">
            <span className={`dot ${c.status}`} style={{ boxShadow: "none" }} />
            <div style={{ minWidth: 0 }}>
              <div className="id">{c.id}</div>
              <div className="sub">{sub === "host" ? HOSTS[c.host].name : PROJECTS[c.proj].name} · {c.role}</div>
            </div>
          </div>
          <div className="gs-svc-val">{c.cpu}</div>
          <div className="gs-svc-val">{c.mem}</div>
          <div className="gs-svc-val" style={{ color: c.status === "flt" ? "var(--fault)" : "var(--ink-2)" }}>{c.err}</div>
          <div className="gs-svc-val" style={{ color: c.up === "LOS" ? "var(--ink-3)" : "var(--go)" }}>{c.up}</div>
          <div className="gs-svc-chev"><ChevronRight size={15} /></div>
        </div>
      ))}
    </div>
  );
}

// ticket rows, reused in queue + project detail
function TicketRow({ t }) {
  const { go } = useNav();
  return (
    <div className="gs-trow" onClick={() => go({ view: "queue", ticketId: t.id })}>
      <span className={`pri p${t.pri}`}>P{t.pri}</span>
      <div className="gs-trow-main">
        <div className="gs-trow-top">
          <span className="gs-trow-id">{t.id}</span>
          <span className="gs-trow-title">{t.title}</span>
          <LifePill life={t.life} agent={t.agent} />
        </div>
        <div className="gs-trow-sum">{t.summary}</div>
      </div>
      <div className="gs-trow-right">
        <span className={`gs-due ${t.hot ? "hot" : ""}`}>{t.due || "no deadline"}</span>
        <span className="gs-score">{t.score}</span>
        <ChevronRight size={15} color="var(--ink-3)" />
      </div>
    </div>
  );
}

// renders text with ticket IDs (e.g. GHS-0311) turned into clickable refs
function RichText({ text }) {
  const { go } = useNav();
  const ids = TICKETS.map(t => t.id);
  const re = new RegExp(`\\b(${ids.join("|")})\\b`, "g");
  const parts = text.split(re);
  return <>{parts.map((p, i) => ids.includes(p)
    ? <span key={i} className="gs-ref" onClick={() => go({ view: "queue", ticketId: p })}>{p}</span>
    : <React.Fragment key={i}>{p}</React.Fragment>)}</>;
}

/* ============================== CONTAINER DETAIL ============================== */
function ContainerDetail({ id }) {
  const { go, toast } = useNav();
  const c = CONTAINERS.find(x => x.id === id);
  const p = PROJECTS[c.proj], h = HOSTS[c.host];
  const series = useMemo(() => spark(c.cpuN || 5, 20, 0.5), [c.id]);
  const off = c.up === "LOS";
  const relTicket = TICKETS.find(t => t.proj === c.proj && t.source === "alert");
  const tiles = [
    ["CPU", c.cpu, c.status === "flt"], ["MEMORY", c.mem, false], ["5XX RATE", c.err, c.status === "flt"],
    ["REQ/S", c.rps, false], ["P95 LATENCY", c.p95, false], ["RESTARTS · 1H", String(c.restarts), c.restarts > 2],
  ];
  return (
    <>
      <div className="gs-eyebrow">
        <span className="gs-linkable" onClick={() => go({ view: "monitor", projectId: c.proj })} style={{ fontFamily: "var(--mono)" }}>{p.name}</span><span>·</span>
        <span className="gs-linkable" onClick={() => go({ view: "monitor", hostId: c.host })}>{h.name}</span><span>·</span><span>{c.role}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 4 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{c.id}</h1><StatusPill s={c.status} />
      </div>
      <p className="gs-sub" style={{ fontFamily: "var(--mono)", fontSize: 12 }}>
        <span className="gs-ref" onClick={() => toast(`Opening ${registryUrl(c.image)}`)}>{c.image}</span>
      </p>

      {c.status === "flt" && relTicket && (
        <div className="gs-card" style={{ padding: "12px 15px", marginBottom: 20, background: "var(--fault-soft)", borderColor: "var(--fault-line)", cursor: "pointer" }}
          onClick={() => go({ view: "queue", ticketId: relTicket.id })}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", color: "var(--fault)", fontSize: 13 }}>
            <AlertTriangle size={15} /><span>Fault filed as <b>{relTicket.id}</b> — {relTicket.title}</span>
            <ChevronRight size={15} style={{ marginLeft: "auto" }} />
          </div>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(120px,1fr))", gap: 12, marginBottom: 22 }}>
        {tiles.map(([l, v, hot]) => (
          <div key={l} className="gs-card" style={{ padding: "14px 15px" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em",
              color: hot ? "var(--fault)" : off ? "var(--ink-3)" : "var(--ink)" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>

      {off ? (
        <div className="gs-card" style={{ padding: "14px 16px", marginBottom: 22, background: "var(--surface-2)" }}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", color: "var(--ink-2)", fontSize: 13 }}>
            <SignalZero size={16} /><span>Loss of signal · last reported 3h ago. Intermittent host, no alert.</span>
          </div>
        </div>
      ) : (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div className="gs-section-h" style={{ marginBottom: 14 }}><Activity size={12} />CPU · LAST 20 MIN</div>
          <div style={{ height: 120 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <defs><linearGradient id="gc" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={c.status === "flt" ? "#BF3A3A" : "#0F7A4B"} stopOpacity={0.16} />
                  <stop offset="100%" stopColor={c.status === "flt" ? "#BF3A3A" : "#0F7A4B"} stopOpacity={0} />
                </linearGradient></defs>
                <CartesianGrid stroke="#E4E8ED" vertical={false} />
                <XAxis dataKey="d" tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} width={40} />
                <Tooltip contentStyle={{ fontFamily: "var(--mono)", fontSize: 11, borderRadius: 8, border: "1px solid #E4E8ED" }} />
                <Area type="monotone" dataKey="v" stroke={c.status === "flt" ? "#BF3A3A" : "#0F7A4B"} strokeWidth={2} fill="url(#gc)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="gs-card gs-meta-card">
        <div className="gs-meta-row"><span className="gs-meta-k">project</span>
          <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "monitor", projectId: c.proj })}>{p.name} ›</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">host</span>
          <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "monitor", hostId: c.host })}>{h.name} ›</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">role</span><span className="gs-meta-v">{c.role}</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">image</span>
          <span className="gs-meta-v gs-linkable" onClick={() => toast(`Opening ${registryUrl(c.image)}`)}>{c.image} ↗</span></div>
        <div className="gs-meta-row"><span className="gs-meta-k">restart policy</span><span className="gs-meta-v">always</span></div>
      </div>
      <div style={{ display: "flex", gap: 8, marginTop: 14 }}>
        <button className="gs-btn ghost" onClick={() => go({ view: "monitor", containerId: c.id, logs: true })}><Terminal size={15} />View logs</button>
        <button className="gs-btn ghost" onClick={() => toast(`Opening ${registryUrl(c.image)}`)}><Boxes size={15} />Registry</button>
      </div>
    </>
  );
}

/* ============================== CONTAINER LOGS ============================== */
function genLogs(c) {
  const routes = ["/api/stats", "/api/user/shaymanor", "/healthz", "/api/repos", "/metrics"];
  const base = [];
  let hh = 14, mm = 2;
  const stamp = () => { mm += 1 + Math.floor(Math.random() * 3); if (mm >= 60) { mm -= 60; hh++; } return `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")}:${String(Math.floor(Math.random() * 60)).padStart(2, "0")}`; };
  base.push(["info", `starting ${c.id} (${c.image})`]);
  base.push(["info", "connected to postgres · pool=10"]);
  if (c.up === "LOS") {
    base.push(["info", "heartbeat ok"]);
    base.push(["warn", "no telemetry ack from collector"]);
    base.push(["err", "signal lost — host unreachable, entering intermittent mode"]);
    return base.map(([lvl, msg]) => ({ t: stamp(), lvl, msg }));
  }
  for (let i = 0; i < 6; i++) base.push(["info", `GET ${routes[i % routes.length]} 200 ${8 + Math.floor(Math.random() * 40)}ms`]);
  if (c.status === "flt") {
    base.push(["info", "GET /api/stats 200 42ms"]);
    base.push(["warn", "redis cache miss — falling through to cold path"]);
    base.push(["err", "TypeError: cannot read properties of undefined (reading 'window')"]);
    base.push(["err", "  at rateLimit (middleware/ratelimit.js:41:18)"]);
    base.push(["err", "GET /api/stats 500 3ms"]);
    base.push(["warn", "restarting worker (restart #4)"]);
    base.push(["info", "hotfix c8a91f applied · guard added, in-memory fallback active"]);
    base.push(["info", "GET /api/stats 200 39ms"]);
  } else if (c.status === "cau") {
    base.push(["warn", "upstream selector drift — 2 fields missing"]);
    base.push(["info", "scrape complete · 18/20 providers fresh"]);
  } else {
    base.push(["info", "GET /healthz 200 2ms"]);
  }
  return base.map(([lvl, msg]) => ({ t: stamp(), lvl, msg }));
}

function ContainerLogs({ id }) {
  const { go, toast } = useNav();
  const c = CONTAINERS.find(x => x.id === id);
  const p = PROJECTS[c.proj], h = HOSTS[c.host];
  const [lvl, setLvl] = useState("all");
  const all = useMemo(() => genLogs(c), [id]);
  const lines = all.filter(l => lvl === "all" || l.lvl === lvl);
  const LV = { info: "INFO", warn: "WARN", err: "ERROR" };
  return (
    <>
      <div className="gs-eyebrow">
        <span className="gs-linkable" onClick={() => go({ view: "monitor", containerId: c.id })} style={{ fontFamily: "var(--mono)" }}>{c.id}</span><span>·</span>
        <span>{p.name}</span><span>·</span><span>{h.name}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 16 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>Logs</h1>
        <StatusPill s={c.status} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {c.up !== "LOS" && <span className="gs-follow"><span className="dot go" style={{ boxShadow: "none", width: 6, height: 6 }} />following</span>}
          <button className="gs-btn ghost" onClick={() => toast("Log bundle downloaded")}><Download size={15} />Download</button>
        </div>
      </div>
      <div className="gs-filters">
        {["all", "info", "warn", "err"].map(k => (
          <button key={k} className={`gs-filter ${lvl === k ? "on" : ""}`} onClick={() => setLvl(k)}>
            {k === "all" ? "All" : LV[k]}</button>
        ))}
      </div>
      <div className="gs-logbox">
        {lines.map((l, i) => (
          <div key={i} className="gs-logline">
            <span className="ts">{l.t}</span>
            <span className={`lv ${l.lvl}`}>{LV[l.lvl]}</span>
            <span className="mg">{l.msg}</span>
          </div>
        ))}
      </div>
    </>
  );
}

/* ============================== QUEUE ============================== */
function QueueView() {
  const { tickets, filter, setFilter } = useNav();
  const [hz, setHz] = useState("Queue");
  const [q, setQ] = useState("");
  const [sort, setSort] = useState("score");
  const horizons = ["Queue", "Now", "This week", "This month", "Someday"];

  let list = tickets.filter(t => {
    if (hz === "Now") return t.life === "active" || t.pri === 0;
    if (hz === "This week") return t.due && !t.due.includes("12d") && t.life !== "backburner";
    if (hz === "This month") return t.due;
    if (hz === "Someday") return t.life === "backburner";
    return true;
  });
  if (filter) list = list.filter(t => filter.kind === "area" ? t.area === filter.val
    : filter.kind === "source" ? t.source === filter.val
    : filter.kind === "project" ? t.proj === filter.val : true);
  if (q.trim()) {
    const s = q.toLowerCase();
    list = list.filter(t => (t.id + t.title + t.summary).toLowerCase().includes(s));
  }
  list = [...list].sort((a, b) =>
    sort === "score" ? parseFloat(b.score) - parseFloat(a.score)
    : sort === "priority" ? a.pri - b.pri
    : (a.due ? 0 : 1) - (b.due ? 0 : 1) || 0);

  return (
    <>
      <div className="gs-eyebrow"><ListChecks size={13} />STATION · QUEUE</div>
      <h1 className="gs-h1">Queue</h1>
      <div className="gs-qtools">
        <div className="gs-qsearch">
          <MessageSquare size={14} color="var(--ink-3)" style={{ display: "none" }} />
          <Hash size={14} color="var(--ink-3)" />
          <input value={q} onChange={e => setQ(e.target.value)} placeholder="Filter tickets…" />
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 7, color: "var(--ink-3)" }}>
          <ArrowUpDown size={14} />
          <select className="gs-sort" value={sort} onChange={e => setSort(e.target.value)}>
            <option value="score">Score</option>
            <option value="priority">Priority</option>
            <option value="deadline">Deadline</option>
          </select>
        </div>
      </div>
      <div className="gs-filters">
        {horizons.map(h => <button key={h} className={`gs-filter ${hz === h ? "on" : ""}`} onClick={() => setHz(h)}>{h}</button>)}
        {filter && <span className="gs-chip-x">{filter.kind}: {PROJECTS[filter.val]?.name || filter.val}
          <button onClick={() => setFilter(null)}><X size={13} /></button></span>}
      </div>
      {list.length === 0
        ? <div className="gs-card gs-empty">No tickets match.</div>
        : <div className="gs-card">{list.map(t => <TicketRow key={t.id} t={t} />)}</div>}
    </>
  );
}

/* ============================== TICKET DETAIL ============================== */
function TicketDetail({ id }) {
  const { go, tickets, launchTicket, setLifecycle, setFilter, toast } = useNav();
  const t = tickets.find(x => x.id === id);
  if (!t) return <div className="gs-empty">Ticket not found.</div>;
  const p = t.proj ? PROJECTS[t.proj] : null;

  return (
    <>
      <div className="gs-detail-grid">
        <div>
          <div className="gs-eyebrow">
            <span className={`pri p${t.pri}`}>P{t.pri}</span>
            <span style={{ fontFamily: "var(--mono)" }}>{t.id}</span>
            <span>·</span>
            <span className="gs-linkable" onClick={() => { setFilter({ kind: "area", val: t.area }); go({ view: "queue" }); }}>{t.area}</span>
          </div>
          <h1 className="gs-h1">{t.title}</h1>
          <p className="gs-sub">{t.summary}</p>

          {t.result && (
            <div className="gs-section">
              <div className="gs-section-h"><CheckCircle2 size={12} />RESULT</div>
              <div className="gs-result"><Zap size={16} color="var(--go)" style={{ flexShrink: 0, marginTop: 1 }} />{t.result}</div>
            </div>
          )}
          {t.report && (
            <div className="gs-section">
              <div className="gs-section-h"><Terminal size={12} />REPORT · latest run</div>
              <div className="gs-body-text muted">{t.report}</div>
            </div>
          )}
          <div className="gs-section">
            <div className="gs-section-h"><Layers size={12} />PROBLEM STATEMENT · agent-written</div>
            <div className="gs-body-text">{t.body}</div>
          </div>
          {t.deps.length > 0 && (
            <div className="gs-section">
              <div className="gs-section-h"><GitBranch size={12} />DEPENDENCIES · non-blocking</div>
              {t.deps.map(d => {
                const exists = tickets.some(x => x.id === d.id);
                return (
                  <div key={d.id} className={`gs-dep ${exists ? "gs-linkable" : ""}`} onClick={() => exists && go({ view: "queue", ticketId: d.id })}>
                    <span className={`dot ${d.done ? "go" : "cau"}`} style={{ boxShadow: "none" }} />
                    <span style={{ fontFamily: "var(--mono)", fontSize: 11, color: "var(--ink-3)" }}>{d.id}</span>
                    {d.title}
                    <span style={{ marginLeft: "auto", fontFamily: "var(--mono)", fontSize: 10, color: d.done ? "var(--go)" : "var(--caution)" }}>
                      {d.done ? "DONE" : "OPEN"}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div>
          <div className="gs-card gs-meta-card" style={{ marginBottom: 14 }}>
            <button className="gs-btn primary" style={{ width: "100%", justifyContent: "center", marginBottom: 10 }}
              onClick={() => launchTicket(t.id)} disabled={t.agent === "executing"}>
              <Rocket size={15} />{t.agent === "executing" ? "Delphi is running…" : "Launch Delphi"}
            </button>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              {t.life === "backburner"
                ? <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "queued"); toast(`${t.id} → queued`); }}><Clock size={14} />Activate</button>
                : <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "backburner"); toast(`${t.id} → backburner`); }}><PauseCircle size={14} />Backburner</button>}
              {t.life !== "archived" && <button className="gs-btn ghost" style={{ flex: 1, justifyContent: "center" }} onClick={() => { setLifecycle(t.id, "archived"); toast(`${t.id} archived`); }}><CheckCircle2 size={14} />Done</button>}
            </div>
            <div className="gs-meta-row"><span className="gs-meta-k">status</span><LifePill life={t.life} agent={t.agent} /></div>
            <div className="gs-meta-row"><span className="gs-meta-k">deadline</span>
              <span className="gs-meta-v" style={{ color: t.hot ? "var(--fault)" : "var(--ink)" }}>{t.due || "none"}</span></div>
            <div className="gs-meta-row"><span className="gs-meta-k">est. effort</span><span className="gs-meta-v">{t.effort}</span></div>
            <div className="gs-meta-row"><span className="gs-meta-k">score</span><span className="gs-meta-v">{t.score}</span></div>
            <div className="gs-meta-row"><span className="gs-meta-k">source</span>
              <span className="gs-meta-v gs-linkable" onClick={() => { setFilter({ kind: "source", val: t.source }); go({ view: "queue" }); }}>{t.source}</span></div>
            {p && <div className="gs-meta-row"><span className="gs-meta-k">project</span>
              <span className="gs-meta-v gs-linkable" onClick={() => go({ view: "projects", projectId: t.proj })}>{p.name} ›</span></div>}
            {p && <div className="gs-meta-row"><span className="gs-meta-k">autonomy</span>
              <span className="pill neu" style={{ textTransform: "none" }}>{autoLabel(p.autonomy)}</span></div>}
          </div>

          {p && p.autonomy === "propose" && (
            <div className="gs-card" style={{ padding: "12px 14px", marginBottom: 14, background: "var(--caution-soft)", borderColor: "var(--caution-line)" }}>
              <div style={{ display: "flex", gap: 9, fontSize: 12, color: "var(--caution)", lineHeight: 1.5 }}>
                <AlertTriangle size={15} style={{ flexShrink: 0 }} />
                <span><b>PR-only.</b> Opens a pull request and stops for your review.</span>
              </div>
            </div>
          )}

          {t.links.length > 0 && (
            <div className="gs-card gs-meta-card">
              <div className="gs-section-h" style={{ marginBottom: 11 }}><Link2 size={12} />LINKS</div>
              {t.links.map((l, i) => {
                const I = LINK_ICON[l.kind] || Link2;
                return (
                  <div key={i} className="gs-link" onClick={() => toast(`Opening ${l.label}`)}>
                    <span className={`pill ${LINK_KIND[l.kind] || "neu"}`} style={{ padding: 4, borderRadius: 6 }}><I size={12} /></span>
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.label}</span>
                    <ChevronRight size={14} color="var(--ink-3)" style={{ marginLeft: "auto" }} />
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

/* ============================== PROJECTS ============================== */
function ProjectsView() {
  const { go, tickets } = useNav();
  const areas = [...new Set(Object.values(PROJECTS).map(p => p.area))];
  return (
    <>
      <div className="gs-eyebrow"><Satellite size={13} />STATION · PROJECTS</div>
      <h1 className="gs-h1">Projects</h1>
      {areas.map(area => (
        <div key={area} style={{ marginBottom: 26 }}>
          <div className="gs-eyebrow" style={{ marginBottom: 12 }}>{area}</div>
          <div className="gs-grid">
            {Object.entries(PROJECTS).filter(([, p]) => p.area === area).map(([k, p]) => {
              const open = tickets.filter(t => t.proj === k && t.life !== "archived").length;
              return (
                <div key={k} className="gs-card gs-pcard" onClick={() => go({ view: "projects", projectId: k })}>
                  <div className="gs-pcard-top">
                    <div><div className="gs-pcard-nm">{p.name}</div><div className="gs-pcard-area">{autoLabel(p.autonomy).toUpperCase()}</div></div>
                    <StatusPill s={p.status} />
                  </div>
                  <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5 }}>{p.blurb}</div>
                  <div className="gs-pcard-metrics">
                    <div className="gs-metric"><div className="v">{open}</div><div className="l">OPEN TICKETS</div></div>
                    {p.users != null
                      ? <div className="gs-metric"><div className="v">{p.users.toLocaleString()}</div><div className="l">USERS · 7D</div></div>
                      : <div className="gs-metric"><div className="v" style={{ color: "var(--ink-3)" }}>—</div><div className="l">NO ANALYTICS</div></div>}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </>
  );
}

function UsersChart() {
  return (
    <div style={{ height: 150 }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={USAGE} margin={{ top: 4, right: 4, left: -22, bottom: 0 }}>
          <defs><linearGradient id="gu" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0F7A4B" stopOpacity={0.16} />
            <stop offset="100%" stopColor="#0F7A4B" stopOpacity={0} />
          </linearGradient></defs>
          <CartesianGrid stroke="#E4E8ED" vertical={false} />
          <XAxis dataKey="d" tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} width={44} />
          <Tooltip contentStyle={{ fontFamily: "var(--mono)", fontSize: 11, borderRadius: 8, border: "1px solid #E4E8ED" }} />
          <Area type="monotone" dataKey="v" stroke="#0F7A4B" strokeWidth={2} fill="url(#gu)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

function ProjectDetail({ pk }) {
  const { go, tickets, toast } = useNav();
  const p = PROJECTS[pk];
  const tix = tickets.filter(t => t.proj === pk);
  const conts = byProject(pk);
  return (
    <>
      <div className="gs-eyebrow">{p.area} · <span className="pill neu" style={{ textTransform: "none" }}>{autoLabel(p.autonomy)}</span></div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 6 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{p.name}</h1><StatusPill s={p.status} />
        <div style={{ marginLeft: "auto", display: "flex", gap: 8 }}>
          {p.repo && <button className="gs-btn ghost" onClick={() => toast(`Opening ${repoUrl(p.repo)}`)}><GitBranch size={14} />Repo</button>}
          {conts.length > 0 && <button className="gs-btn ghost" onClick={() => go({ view: "monitor", projectId: pk })}><Gauge size={14} />Monitor</button>}
        </div>
      </div>
      <p className="gs-sub">{p.blurb}</p>

      {p.users != null && (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
            <div className="gs-section-h" style={{ margin: 0 }}><Activity size={12} />DAILY ACTIVE · LAST 14 DAYS</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--ink-2)" }}><b style={{ color: "var(--ink)" }}>{p.users.toLocaleString()}</b> active</div>
          </div>
          <UsersChart />
        </div>
      )}

      {conts.length > 0 && (
        <>
          <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
          <div style={{ marginBottom: 22 }}><ContainerTable containers={conts} sub="host" /></div>
        </>
      )}

      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><ListChecks size={12} />TICKETS · {tix.length}</div>
      {tix.length === 0
        ? <div className="gs-card gs-empty">No tickets yet.</div>
        : <div className="gs-card">{tix.map(t => <TicketRow key={t.id} t={t} />)}</div>}
    </>
  );
}

/* ============================== MONITOR ============================== */
const MON_PROJECTS = [...new Set(CONTAINERS.map(c => c.proj))];

function MonProjectDetail({ pk }) {
  const { go } = useNav();
  const p = PROJECTS[pk], conts = byProject(pk);
  return (
    <>
      <div className="gs-eyebrow">{p.area}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 6 }}>
        <h1 className="gs-h1" style={{ margin: 0 }}>{p.name}</h1><StatusPill s={rollup(conts)} />
        <button className="gs-btn ghost" style={{ marginLeft: "auto" }} onClick={() => go({ view: "projects", projectId: pk })}><ListChecks size={14} />Tickets</button>
      </div>
      <p className="gs-sub">{p.blurb}</p>

      {p.users != null && (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
            <div className="gs-section-h" style={{ margin: 0 }}><Activity size={12} />DAILY ACTIVE · LAST 14 DAYS</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 12, color: "var(--ink-2)" }}><b style={{ color: "var(--ink)" }}>{p.users.toLocaleString()}</b> active</div>
          </div>
          <UsersChart />
        </div>
      )}

      {pk === "ghstats" && (
        <div className="gs-card" style={{ padding: "18px 20px", marginBottom: 22 }}>
          <div className="gs-section-h" style={{ marginBottom: 14 }}><AlertTriangle size={12} color="var(--fault)" />gh-stats-api · 5XX RATE · breach at t-11m → <span className="gs-ref" onClick={() => go({ view: "queue", ticketId: "GHS-0311" })}>GHS-0311</span></div>
          <div style={{ height: 120 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={ERRSERIES} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <defs><linearGradient id="ge" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#BF3A3A" stopOpacity={0.18} />
                  <stop offset="100%" stopColor="#BF3A3A" stopOpacity={0} />
                </linearGradient></defs>
                <CartesianGrid stroke="#E4E8ED" vertical={false} />
                <XAxis dataKey="d" tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontFamily: "var(--mono)", fontSize: 10, fill: "#8E99A4" }} axisLine={false} tickLine={false} width={44} />
                <Tooltip contentStyle={{ fontFamily: "var(--mono)", fontSize: 11, borderRadius: 8, border: "1px solid #E4E8ED" }} />
                <Area type="monotone" dataKey="v" stroke="#BF3A3A" strokeWidth={2} fill="url(#ge)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
      <ContainerTable containers={conts} sub="host" />
    </>
  );
}

function HostDetail({ hid }) {
  const h = HOSTS[hid], conts = byHost(hid), I = h.icon;
  const online = h.kind === "always_on" || !conts.every(c => c.status === "los");
  return (
    <>
      <div className="gs-eyebrow">{h.tag} · {h.loc}</div>
      <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 18 }}>
        <I size={22} color="var(--ink-2)" />
        <h1 className="gs-h1" style={{ margin: 0 }}>{h.name}</h1>
        {online ? <span className="pill go"><Signal size={11} />AOS</span> : <span className="pill neu"><SignalZero size={11} />LOS · last seen 3h ago</span>}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(130px,1fr))", gap: 12, marginBottom: 22 }}>
        {[["CONTAINERS", String(conts.length)], ["FAULTS", String(conts.filter(c => c.status === "flt").length)],
          ["CLASS", h.kind === "always_on" ? "ALWAYS-ON" : "INTERMITTENT"]].map(([l, v]) => (
          <div key={l} className="gs-card" style={{ padding: "14px 15px" }}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 20, fontWeight: 600, letterSpacing: "-0.02em" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>
      <div className="gs-eyebrow" style={{ marginBottom: 12 }}><Server size={12} />CONTAINERS · {conts.length}</div>
      <ContainerTable containers={conts} sub="proj" />
    </>
  );
}

function MonitorView({ mode, setMode }) {
  const { go } = useNav();
  const faults = CONTAINERS.filter(c => c.status === "flt").length;
  const hostsOnline = Object.values(HOSTS).filter(h => h.kind === "always_on" || !byHost(h.id).every(c => c.status === "los")).length;
  return (
    <>
      <div className="gs-eyebrow"><Gauge size={13} />STATION · MONITOR</div>
      <h1 className="gs-h1">Monitor</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(150px,1fr))", gap: 14, marginBottom: 22 }}>
        {[["ACTIVE USERS · 7D", "5,600", "go", null],
          ["FAULTS", String(faults), faults ? "flt" : "go", "faults"],
          ["HOSTS ONLINE", `${hostsOnline} / ${Object.keys(HOSTS).length}`, "cau", "compute"],
          ["GLOBAL 5XX", "1.2%", "cau", null]].map(([l, v, c, act]) => (
          <div key={l} className="gs-card" style={{ padding: "15px 17px", cursor: act ? "pointer" : "default" }}
            onClick={() => act === "compute" ? setMode("compute") : act === "faults" ? go({ view: "monitor", containerId: "gh-stats-api" }) : null}>
            <div style={{ fontFamily: "var(--mono)", fontSize: 22, fontWeight: 600, letterSpacing: "-0.02em",
              color: c === "flt" ? "var(--fault)" : c === "cau" ? "var(--caution)" : "var(--ink)" }}>{v}</div>
            <div style={{ fontFamily: "var(--mono)", fontSize: 9.5, color: "var(--ink-3)", letterSpacing: "0.06em", marginTop: 3 }}>{l}</div>
          </div>
        ))}
      </div>

      <div className="gs-toggle">
        <button className={mode === "projects" ? "on" : ""} onClick={() => setMode("projects")}><Satellite size={13} />Project</button>
        <button className={mode === "compute" ? "on" : ""} onClick={() => setMode("compute")}><Cpu size={13} />Compute</button>
      </div>

      {mode === "projects" ? (
        <div className="gs-grid">
          {MON_PROJECTS.map(pk => {
            const p = PROJECTS[pk], conts = byProject(pk), st = rollup(conts);
            const worstErr = conts.map(c => parseFloat(c.err)).filter(n => !isNaN(n)).sort((a, b) => b - a)[0];
            return (
              <div key={pk} className="gs-card gs-pcard" onClick={() => go({ view: "monitor", projectId: pk })}>
                <div className="gs-pcard-top">
                  <div><div className="gs-pcard-nm">{p.name}</div><div className="gs-pcard-area">{p.area}</div></div>
                  <StatusPill s={st} />
                </div>
                <div style={{ fontSize: 12.5, color: "var(--ink-2)", lineHeight: 1.5 }}>{p.blurb}</div>
                <div className="gs-pcard-metrics">
                  <div className="gs-metric"><div className="v">{conts.length}</div><div className="l">CONTAINERS</div></div>
                  {p.users != null
                    ? <div className="gs-metric"><div className="v">{p.users.toLocaleString()}</div><div className="l">USERS · 7D</div></div>
                    : <div className="gs-metric"><div className="v" style={{ color: "var(--ink-3)" }}>—</div><div className="l">NO ANALYTICS</div></div>}
                  <div className="gs-metric"><div className="v" style={{ color: st === "flt" ? "var(--fault)" : "var(--ink)" }}>
                    {worstErr != null ? `${worstErr}%` : "—"}</div><div className="l">MAX 5XX</div></div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="gs-grid">
          {Object.values(HOSTS).map(h => {
            const conts = byHost(h.id), I = h.icon;
            const online = h.kind === "always_on" || !conts.every(c => c.status === "los");
            return (
              <div key={h.id} className="gs-card gs-pcard" onClick={() => go({ view: "monitor", hostId: h.id })}>
                <div className="gs-pcard-top">
                  <div style={{ display: "flex", gap: 11, alignItems: "center" }}>
                    <I size={20} color="var(--ink-2)" />
                    <div><div className="gs-pcard-nm">{h.name}</div><div className="gs-pcard-area">{h.loc}</div></div>
                  </div>
                  {online ? <span className="pill go"><Signal size={11} />AOS</span> : <span className="pill neu"><SignalZero size={11} />LOS</span>}
                </div>
                <div style={{ fontFamily: "var(--mono)", fontSize: 10.5, color: "var(--ink-3)", letterSpacing: "0.06em" }}>{h.tag}</div>
                <div className="gs-pcard-metrics">
                  <div className="gs-metric"><div className="v">{conts.length}</div><div className="l">CONTAINERS</div></div>
                  <div className="gs-metric"><div className="v" style={{ color: conts.some(c => c.status === "flt") ? "var(--fault)" : "var(--ink)" }}>
                    {conts.filter(c => c.status === "flt").length}</div><div className="l">FAULTS</div></div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

/* ============================== FLIGHT ============================== */
const TOOLMAP = {
  github: [GitBranch, "GitHub"], vm: [Activity, "VictoriaMetrics"], calendar: [Calendar, "Calendar"],
  brightspace: [FileText, "Brightspace"], queue: [ListChecks, "Queue"], claude: [Terminal, "Claude Code"],
};
const VOICE_PHRASES = [
  "What's blocking the MERLIN Rubik Pi port?",
  "Show me everything due before Friday",
  "Did the gh-stats fix pass canary?",
];
const MODELS = [
  { id: "hermes4", name: "Hermes 4 70B", tag: "local · Ollama" },
  { id: "opus", name: "Claude Opus 4.8", tag: "hosted" },
  { id: "llama4", name: "Llama 4 Maverick", tag: "local · vLLM" },
  { id: "qwen3", name: "Qwen3 235B", tag: "hosted" },
  { id: "deepseek", name: "DeepSeek-V3", tag: "hosted" },
];
const SESSIONS_INIT = [
  { id: "s1", title: "EKF drift on the kart", ts: "Yesterday", msgs: [
    { who: "me", text: "Why is the EKF drifting on the EVC kart?" },
    { who: "flight", text: "The GEM1305 RTK fix was dropping to float during the sweep. I correlated the covariance spikes with EVC-0071 — CAN bus load hitting 82%. Raising the IMU publish rate to 200Hz and re-timing the fusion loop settled it.", tools: ["queue", "vm"] },
  ] },
  { id: "s2", title: "Guardrail rebuttal plan", ts: "2d ago", msgs: [
    { who: "me", text: "Draft a plan for the Guardrail rebuttal" },
    { who: "flight", text: "R2's ablation is the crux. I outlined a 3-point response and staged the sweep under GRD-0182. The teacher-gate isolation is the strongest evidence — cosine-gated held +1.2 mIoU at heavy shift.", tools: ["brightspace", "queue"] },
  ] },
  { id: "s3", title: "gh-stats SEO ideas", ts: "Mar 3", msgs: [
    { who: "me", text: "How do I break the gh-stats traffic plateau?" },
    { who: "flight", text: "Programmatic per-profile pages are the highest-leverage move — indexable long-tail surface you don't have yet. Filed as GHS-0308 with OG images + schema.org markup.", tools: ["github", "vm"] },
  ] },
];

function FlightView() {
  const { toast } = useNav();
  const [msgs, setMsgs] = useState([
    { who: "flight", text: "Delphi online. Two things want your attention: GRD-0182 (TMLR) is due in 2 days, and my fix for the gh-stats 500-rate breach is in a PR waiting on your merge." },
  ]);
  const [input, setInput] = useState("");
  const [atts, setAtts] = useState([]);
  const [thinking, setThinking] = useState(false);
  const [recording, setRecording] = useState(false);
  const [drawer, setDrawer] = useState(null); // null | connectors | skills | memory
  const [histOpen, setHistOpen] = useState(false);
  const [sessions, setSessions] = useState(SESSIONS_INIT);
  const [activeSess, setActiveSess] = useState(null);
  const [model, setModel] = useState(MODELS[0]);
  const [modelOpen, setModelOpen] = useState(false);
  const [servers, setServers] = useState(MCP_INIT);
  const [skills, setSkills] = useState(SKILL_INIT);
  const [newSrv, setNewSrv] = useState({ name: "", url: "" });
  const [newSkill, setNewSkill] = useState("");
  const fileRef = useRef(null);
  const scrollRef = useRef(null);
  useEffect(() => { scrollRef.current?.scrollTo(0, 1e6); }, [msgs, thinking]);

  const suggestions = [
    ["What's due this week?", "Deadlines, ranked by urgency"],
    ["Status of MERLIN", "Tickets + onboard containers"],
    ["What did you do to gh-stats?", "Walk through the auto-fix"],
    ["Re-rank my queue", "Recompute importance × urgency"],
  ];

  const reply = (q) => {
    const l = q.toLowerCase();
    if (l.includes("due") || l.includes("friday") || l.includes("week")) return { text: "This week: GRD-0182 TMLR revisions (2d, P0), STA-0044 STAT 511 PS4 (3d, P1), EVC-0074 motor sync (4d, P1). The TMLR one is the only P0 with real slack risk — 6h of work, 2 days out. I'd start it today.", tools: ["calendar", "brightspace", "queue"] };
    if (l.includes("merlin") || l.includes("rubik")) return { text: "MERLIN is nominal. 2 open tickets: MER-0093 (Rubik Pi port), blocked-ish on MER-0088 (INT8 quant, backburner). Both onboard containers are LOS — the Jetson's been off ~3h, expected, not an incident.", tools: ["queue", "vm"] };
    if (l.includes("gh-stats") || l.includes("500") || l.includes("canary")) return { text: "Alert at t-11m: 5XX hit 6.1% on gh-stats-api. I traced a cold-cache null-deref in the rate-limit middleware, added a guard + fallback, and opened the fix under GHS-0311. Canary 5XX back to 0.3%, waiting on your merge.", tools: ["vm", "github", "claude"] };
    if (l.includes("rank") || l.includes("queue")) return { text: "Re-ranked. Top: GHS-0311 (9.1, executing), GRD-0182 (9.4), EVC-0074 (6.8), STA-0044 (6.1). Nothing else moved.", tools: ["queue"] };
    return { text: "I can pull ticket status, project health, run history, or metrics — or launch on any ticket. Try a suggestion, attach a file, or dictate.", tools: [] };
  };
  const send = (q) => {
    const text = q ?? input.trim();
    if (!text && atts.length === 0) return;
    const sent = atts;
    setMsgs(m => [...m, { who: "me", text: text || "(attachment)", atts: sent }]);
    setInput(""); setAtts([]); setThinking(true);
    setTimeout(() => { const r = reply(text); setThinking(false); setMsgs(m => [...m, { who: "flight", text: r.text, tools: r.tools }]); }, 650);
  };
  const onFiles = (e) => {
    const picked = Array.from(e.target.files || []).map(f => ({ name: f.name, img: f.type.startsWith("image/") }));
    setAtts(a => [...a, ...picked]); e.target.value = "";
  };
  const stopRec = () => { setRecording(false); setInput(VOICE_PHRASES[Math.floor(Math.random() * VOICE_PHRASES.length)]); };
  const addServer = () => {
    if (!newSrv.name.trim()) return;
    setServers(s => [{ id: Date.now().toString(), name: newSrv.name.trim(), url: newSrv.url.trim() || "custom", tools: "—", on: true, desc: "Custom connector" }, ...s]);
    setNewSrv({ name: "", url: "" }); toast(`Connected ${newSrv.name.trim()}`);
  };
  const addSkill = () => {
    if (!newSkill.trim()) return;
    setSkills(s => [{ id: Date.now().toString(), name: newSkill.trim(), on: true, trigger: "manual", desc: "Custom skill" }, ...s]);
    setNewSkill(""); toast(`Added ${newSkill.trim()}`);
  };
  const copy = (t) => { try { navigator.clipboard?.writeText(t); } catch (e) {} toast("Copied to clipboard"); };

  const snapshot = () => {
    if (msgs.length <= 1) return null;
    const title = (msgs.find(m => m.who === "me")?.text || "New chat").slice(0, 42);
    return { id: activeSess || Date.now().toString(), title, ts: "Just now", msgs };
  };
  const newChat = () => {
    const snap = snapshot();
    if (snap) setSessions(s => [snap, ...s.filter(x => x.id !== snap.id)]);
    setMsgs(msgs.slice(0, 1)); setActiveSess(null); toast("Started a new chat");
  };
  const loadSession = (sess) => {
    const snap = snapshot();
    setSessions(s => { let n = s.filter(x => x.id !== sess.id); if (snap) n = [snap, ...n.filter(x => x.id !== snap.id)]; return n; });
    setMsgs(sess.msgs); setActiveSess(sess.id); setHistOpen(false);
  };
  const welcome = msgs.length <= 1;

  return (
    <div className="gs-flight-wrap">
      <div className="gs-fl-head">
        <div className="gs-fl-id">
          <div className="gs-fl-av"><Radio size={17} /></div>
          <div>
            <div className="gs-fl-nm">Delphi</div>
            <div className="gs-fl-st"><span className="dot go" style={{ boxShadow: "none", width: 6, height: 6 }} />ONLINE · {servers.filter(s => s.on).length} CONNECTORS</div>
          </div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", gap: 8, position: "relative" }}>
          <button className="gs-model" onClick={() => setModelOpen(v => !v)}>
            <Sparkles size={14} color="var(--go)" />{model.name}<ChevronDown size={14} color="var(--ink-3)" />
          </button>
          {modelOpen && (
            <>
              <div className="gs-menu-catch" onClick={() => setModelOpen(false)} />
              <div className="gs-menu">
                <div className="gs-menu-lbl">Agent model</div>
                {MODELS.map(mo => (
                  <button key={mo.id} className="gs-menu-item" onClick={() => { setModel(mo); setModelOpen(false); toast(`Switched to ${mo.name}`); }}>
                    <div><div className="t">{mo.name}</div><div className="g">{mo.tag}</div></div>
                    {model.id === mo.id && <span className="chk"><Check size={15} /></span>}
                  </button>
                ))}
              </div>
            </>
          )}
          <button className="gs-hbtn icon" onClick={() => setHistOpen(true)} title="Chat history"><History size={16} /></button>
          <button className="gs-hbtn" onClick={newChat}><SquarePen size={15} />New</button>
          <button className="gs-hbtn icon" onClick={() => setDrawer("connectors")} title="Connectors, skills & memory"><Settings size={16} /></button>
        </div>
      </div>

      <div className="gs-flight-content">
        <div className="gs-msgs" ref={scrollRef}>
          {welcome ? (
            <div className="gs-welcome">
              <div className="gs-fl-av" style={{ width: 44, height: 44, borderRadius: 12 }}><Radio size={22} /></div>
              <h2>Talk to Delphi</h2>
              <p>It knows every ticket, project, and container you own.</p>
              <div className="gs-sugg">
                {suggestions.map(([t, d]) => (
                  <button key={t} onClick={() => send(t)}><span className="t">{t}</span><span className="d">{d}</span></button>
                ))}
              </div>
            </div>
          ) : msgs.map((m, i) => (
            <div key={i} className={`gs-msg ${m.who}`}>
              <div className={`gs-msg-av ${m.who === "flight" ? "flight" : "me"}`}>
                {m.who === "flight" ? <Radio size={15} /> : <span style={{ fontFamily: "var(--mono)", fontSize: 11 }}>S</span>}
              </div>
              <div style={{ minWidth: 0 }}>
                {m.tools && m.tools.length > 0 && (
                  <div className="gs-tools">
                    {m.tools.map(tk => { const [I, label] = TOOLMAP[tk]; return (
                      <span key={tk} className="gs-toolchip"><span className="ck"><Check size={10} /></span><I size={11} />{label}</span>
                    ); })}
                  </div>
                )}
                <div className="gs-bub">{m.who === "flight" ? <RichText text={m.text} /> : m.text}</div>
                {m.atts && m.atts.length > 0 && (
                  <div className="gs-atts" style={{ marginTop: 7, marginBottom: 0 }}>
                    {m.atts.map((a, j) => <span key={j} className="gs-att">{a.img ? <Hash size={12} /> : <FileText size={12} />}<span className="nm">{a.name}</span></span>)}
                  </div>
                )}
                {m.who === "flight" && (
                  <div className="gs-msg-copy">
                    <button onClick={() => copy(m.text)}><Copy size={11} />Copy</button>
                  </div>
                )}
              </div>
            </div>
          ))}
          {thinking && (
            <div className="gs-msg flight">
              <div className="gs-msg-av flight"><Radio size={15} /></div>
              <div className="gs-bub" style={{ padding: 0 }}><div className="gs-think"><i /><i /><i /></div></div>
            </div>
          )}
        </div>

        {!welcome && (
          <div className="gs-chips">
            {suggestions.slice(0, 4).map(([c]) => <button key={c} className="gs-chip" onClick={() => send(c)}>{c}</button>)}
          </div>
        )}

        {atts.length > 0 && (
          <div className="gs-atts">
            {atts.map((a, i) => (
              <span key={i} className="gs-att">{a.img ? <Hash size={12} /> : <FileText size={12} />}<span className="nm">{a.name}</span>
                <span className="rm" onClick={() => setAtts(atts.filter((_, j) => j !== i))}><X size={13} /></span></span>
            ))}
          </div>
        )}

        <div className="gs-composer">
          <input ref={fileRef} type="file" multiple hidden onChange={onFiles} />
          {recording ? (
            <div className="gs-recbar">
              <span className="dot flt" style={{ boxShadow: "none" }} />
              <span className="gs-rec-label">Listening…</span>
              <div className="gs-wave">{Array.from({ length: 7 }).map((_, i) => <i key={i} />)}</div>
              <div style={{ flex: 1 }} />
              <button className="gs-btn ghost" onClick={stopRec}><Square size={13} />Stop</button>
            </div>
          ) : (
            <>
              <button className="gs-attach-btn" onClick={() => fileRef.current?.click()} title="Attach files or images"><Paperclip size={17} /></button>
              <button className="gs-mic" onClick={() => setRecording(true)} title="Dictate"><Mic size={17} /></button>
              <input value={input} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === "Enter" && send()} placeholder="Ask Delphi, attach a file, or dictate…" />
              <button className="gs-btn primary" onClick={() => send()}><Send size={15} /></button>
            </>
          )}
        </div>
      </div>

      {histOpen && (
        <>
          <div className="gs-drawer-bg" onClick={() => setHistOpen(false)} />
          <div className="gs-drawer left">
            <div className="gs-drawer-head">
              <History size={16} color="var(--ink-2)" />
              <span className="ttl">Chats</span>
              <button className="gs-hbtn" style={{ marginLeft: "auto" }} onClick={() => { newChat(); setHistOpen(false); }}><SquarePen size={14} />New</button>
              <button className="gs-hbtn icon" onClick={() => setHistOpen(false)}><X size={16} /></button>
            </div>
            <div className="gs-drawer-body">
              {!welcome && (
                <div className="gs-sess active">
                  <span className="t">{(msgs.find(m => m.who === "me")?.text || "Current chat").slice(0, 42)}</span>
                  <span className="m"><span>Current</span><span>{msgs.filter(m => m.who === "me").length} messages</span></span>
                </div>
              )}
              {sessions.length === 0 && welcome
                ? <div className="gs-empty">No past chats yet.</div>
                : sessions.map(s => (
                  <div key={s.id} className="gs-sess" onClick={() => loadSession(s)}>
                    <span className="t">{s.title}</span>
                    <span className="m"><span>{s.ts}</span><span>{s.msgs.filter(m => m.who === "me").length} messages</span></span>
                  </div>
                ))}
            </div>
          </div>
        </>
      )}

      {drawer && (
        <>
          <div className="gs-drawer-bg" onClick={() => setDrawer(null)} />
          <div className="gs-drawer">
            <div className="gs-drawer-head">
              <Sparkles size={16} color="var(--go)" />
              <span className="ttl">Agent context</span>
              <button className="gs-hbtn icon" style={{ marginLeft: "auto" }} onClick={() => setDrawer(null)}><X size={16} /></button>
            </div>
            <div style={{ padding: "12px 18px 0" }}>
              <div className="gs-toggle" style={{ marginBottom: 4, width: "100%" }}>
                {[["connectors", "Connectors", Plug], ["skills", "Skills", Wrench], ["memory", "Memory", Brain]].map(([k, label, I]) => (
                  <button key={k} className={drawer === k ? "on" : ""} onClick={() => setDrawer(k)} style={{ flex: 1, justifyContent: "center" }}><I size={13} />{label}</button>
                ))}
              </div>
            </div>
            <div className="gs-drawer-body">
              {drawer === "connectors" && (
                <>
                  {servers.map(s => (
                    <div key={s.id} className={`gs-conn ${s.on ? "" : "off"}`}>
                      <div className="gs-conn-ic"><Plug size={16} /></div>
                      <div style={{ minWidth: 0 }}>
                        <div className="gs-conn-nm">{s.name}<span className="pill neu" style={{ fontSize: 9 }}>{s.tools} tools</span></div>
                        <div className="gs-conn-meta">{s.url}</div>
                      </div>
                      <div className="gs-conn-act">
                        <div className={`gs-switch ${s.on ? "on" : ""}`} onClick={() => setServers(servers.map(x => x.id === s.id ? { ...x, on: !x.on } : x))} />
                        <button className="gs-icon-btn" onClick={() => setServers(servers.filter(x => x.id !== s.id))}><Trash2 size={15} /></button>
                      </div>
                    </div>
                  ))}
                  <div className="gs-addrow" style={{ flexDirection: "column" }}>
                    <input className="gs-input" placeholder="Connector name" value={newSrv.name} onChange={e => setNewSrv({ ...newSrv, name: e.target.value })} />
                    <div style={{ display: "flex", gap: 8 }}>
                      <input className="gs-input" placeholder="server URL" value={newSrv.url} onChange={e => setNewSrv({ ...newSrv, url: e.target.value })} onKeyDown={e => e.key === "Enter" && addServer()} />
                      <button className="gs-btn primary" onClick={addServer}><Plus size={15} />Add</button>
                    </div>
                  </div>
                </>
              )}
              {drawer === "skills" && (
                <>
                  {skills.map(s => (
                    <div key={s.id} className={`gs-conn ${s.on ? "" : "off"}`}>
                      <div className="gs-conn-ic"><Wrench size={15} /></div>
                      <div style={{ minWidth: 0 }}>
                        <div className="gs-conn-nm" style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{s.name}<span className="pill neu" style={{ fontSize: 9, fontFamily: "var(--sans)" }}>{s.trigger}</span></div>
                        <div className="gs-conn-meta" style={{ fontFamily: "var(--sans)", fontSize: 11.5, whiteSpace: "normal" }}>{s.desc}</div>
                      </div>
                      <div className="gs-conn-act">
                        <div className={`gs-switch ${s.on ? "on" : ""}`} onClick={() => setSkills(skills.map(x => x.id === s.id ? { ...x, on: !x.on } : x))} />
                        <button className="gs-icon-btn" onClick={() => setSkills(skills.filter(x => x.id !== s.id))}><Trash2 size={15} /></button>
                      </div>
                    </div>
                  ))}
                  <div className="gs-addrow">
                    <input className="gs-input" placeholder="skill-name" value={newSkill} onChange={e => setNewSkill(e.target.value)} onKeyDown={e => e.key === "Enter" && addSkill()} />
                    <button className="gs-btn primary" onClick={addSkill}><Plus size={15} />Add</button>
                  </div>
                </>
              )}
              {drawer === "memory" && (
                <>
                  <div className="gs-section-h" style={{ marginBottom: 6 }}><Brain size={12} />LEARNED FACTS</div>
                  <div className="gs-card" style={{ padding: "6px 16px", marginBottom: 22 }}>
                    {MEMORY_FACTS.map((f, i) => <div key={i} className="gs-fact"><Check size={15} color="var(--go)" style={{ flexShrink: 0, marginTop: 1 }} />{f}</div>)}
                  </div>
                  <div className="gs-section-h" style={{ marginBottom: 10 }}><Terminal size={12} />RECENT RUNS</div>
                  <div className="gs-card">{AGENT_RUNS.map((r, i) => <RunRow key={i} r={r} />)}</div>
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function RunRow({ r }) {
  const { go } = useNav();
  return (
    <div className="gs-svc" style={{ gridTemplateColumns: "1fr auto auto auto", gap: 14 }} onClick={() => go({ view: "queue", ticketId: r.ticket })}>
      <div className="gs-svc-nm">
        {r.kind === "execute" ? <Rocket size={14} color="var(--go)" /> : <Zap size={14} color="var(--info)" />}
        <div><div className="id" style={{ fontFamily: "var(--mono)", fontSize: 12.5 }}>{r.ticket}</div><div className="sub">{r.kind}</div></div>
      </div>
      <span className={`pill ${r.status === "needs review" ? "cau" : "go"}`}>{r.status}</span>
      <span className="gs-svc-val" style={{ color: "var(--ink-2)" }}>{r.cost}</span>
      <span className="gs-svc-val" style={{ color: "var(--ink-3)" }}>{r.when}</span>
    </div>
  );
}

/* ============================== SEARCH PALETTE ============================== */
function SearchPalette({ tickets, onClose }) {
  const { go } = useNav();
  const [q, setQ] = useState("");
  const [sel, setSel] = useState(0);
  const inRef = useRef(null);
  useEffect(() => { inRef.current?.focus(); }, []);

  const s = q.toLowerCase();
  const tRes = (q ? tickets.filter(t => (t.id + t.title + t.summary).toLowerCase().includes(s)) : tickets).slice(0, 6)
    .map(t => ({ kind: "Ticket", icon: ListChecks, t: t.title, sub: `${t.id} · ${t.area}`, k: `P${t.pri}`, go: { view: "queue", ticketId: t.id } }));
  const pRes = Object.entries(PROJECTS).filter(([, p]) => !q || p.name.toLowerCase().includes(s)).slice(0, 4)
    .map(([k, p]) => ({ kind: "Project", icon: Satellite, t: p.name, sub: p.area, k: "", go: { view: "projects", projectId: k } }));
  const cRes = CONTAINERS.filter(c => !q || c.id.toLowerCase().includes(s)).slice(0, 4)
    .map(c => ({ kind: "Container", icon: Server, t: c.id, sub: `${PROJECTS[c.proj].name} · ${HOSTS[c.host].name}`, k: c.up, go: { view: "monitor", containerId: c.id } }));
  const hRes = Object.values(HOSTS).filter(h => !q || h.name.toLowerCase().includes(s)).slice(0, 3)
    .map(h => ({ kind: "Host", icon: Cpu, t: h.name, sub: h.loc, k: "", go: { view: "monitor", hostId: h.id } }));
  const groups = [["Tickets", tRes], ["Projects", pRes], ["Containers", cRes], ["Hosts", hRes]].filter(([, r]) => r.length);
  const flat = groups.flatMap(([, r]) => r);
  const pick = (i) => { const r = flat[i]; if (r) { go(r.go); onClose(); } };

  const onKey = (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); setSel(x => Math.min(x + 1, flat.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setSel(x => Math.max(x - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); pick(sel); }
    else if (e.key === "Escape") onClose();
  };

  let idx = -1;
  return (
    <div className="gs-overlay" onClick={onClose}>
      <div className="gs-pal" onClick={e => e.stopPropagation()}>
        <div className="gs-pal-in">
          <Radio size={17} color="var(--ink-3)" />
          <input ref={inRef} value={q} onChange={e => { setQ(e.target.value); setSel(0); }} onKeyDown={onKey}
            placeholder="Search tickets, projects, containers, hosts…" />
          <kbd style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--ink-3)", border: "1px solid var(--line)", borderRadius: 4, padding: "2px 6px" }}>esc</kbd>
        </div>
        <div className="gs-pal-res">
          {flat.length === 0 ? <div className="gs-pal-empty">No matches for "{q}"</div> : groups.map(([label, rows]) => (
            <div key={label}>
              <div className="gs-pal-grp">{label}</div>
              {rows.map(r => { idx++; const my = idx; const I = r.icon; return (
                <div key={r.t + my} className={`gs-pal-item ${sel === my ? "sel" : ""}`} onMouseEnter={() => setSel(my)} onClick={() => pick(my)}>
                  <div className="ic"><I size={15} /></div>
                  <div style={{ minWidth: 0 }}><div className="t">{r.t}</div><div className="s">{r.sub}</div></div>
                  {r.k && <span className="k">{r.k}</span>}
                </div>
              ); })}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ============================== SHELL ============================== */
export default function Pantheos() {
  const [tickets, setTickets] = useState(TICKETS);
  const [stack, setStack] = useState([{ view: "queue" }]);
  const [monMode, setMonMode] = useState("projects");
  const [filter, setFilter] = useState(null);
  const [toasts, setToasts] = useState([]);
  const [searchOpen, setSearchOpen] = useState(false);
  const [met, setMet] = useState(15153);

  const cur = stack[stack.length - 1];
  useEffect(() => { const t = setInterval(() => setMet(m => m + 1), 1000); return () => clearInterval(t); }, []);
  const clock = `${String(Math.floor(met / 3600)).padStart(2, "0")}:${String(Math.floor(met / 60) % 60).padStart(2, "0")}:${String(met % 60).padStart(2, "0")}`;
  const cCount = {
    flt: CONTAINERS.filter(c => c.status === "flt").length,
    cau: CONTAINERS.filter(c => c.status === "cau").length,
    go: CONTAINERS.filter(c => c.status === "go").length,
  };

  const toast = (text, action) => {
    const id = Date.now() + Math.random();
    setToasts(t => [...t, { id, text, action }]);
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3200);
  };
  const go = (node) => setStack(s => [...s, node]);
  const back = () => setStack(s => s.length > 1 ? s.slice(0, -1) : s);
  const root = (view) => { setStack([{ view }]); setFilter(null); };

  const launchTicket = (id) => {
    setTickets(ts => ts.map(t => t.id === id ? { ...t, agent: "executing", life: t.life === "backburner" ? "queued" : t.life } : t));
    const t = tickets.find(x => x.id === id);
    const p = t?.proj ? PROJECTS[t.proj] : null;
    toast(p?.autonomy === "propose" ? `Delphi dispatched on ${id} · PR-only, stops for review` : `Delphi dispatched on ${id} · Claude Code session spawning`);
  };
  const setLifecycle = (id, life) => setTickets(ts => ts.map(t => t.id === id ? { ...t, life } : t));

  const api = { go, back, root, toast, tickets, launchTicket, setLifecycle, filter, setFilter };

  // sidebar highlight
  const section = cur.ticketId ? "queue" : cur.view;

  // breadcrumb trail
  const crumbs = [];
  const secName = { queue: "Queue", projects: "Projects", monitor: "Monitor", flight: "Delphi" }[section] || "Queue";
  crumbs.push({ label: secName, node: { view: section }, mode: section === "monitor" });
  if (cur.ticketId) crumbs.push({ label: tickets.find(t => t.id === cur.ticketId)?.id || cur.ticketId });
  else if (cur.projectId) crumbs.push({ label: PROJECTS[cur.projectId].name });
  else if (cur.hostId) crumbs.push({ label: HOSTS[cur.hostId].name });
  else if (cur.containerId) { crumbs.push({ label: CONTAINERS.find(c => c.id === cur.containerId)?.id }); if (cur.logs) crumbs.push({ label: "Logs" }); }

  // body
  let body;
  if (cur.containerId && cur.logs) body = <ContainerLogs id={cur.containerId} />;
  else if (cur.containerId) body = <ContainerDetail id={cur.containerId} />;
  else if (cur.ticketId) body = <TicketDetail id={cur.ticketId} />;
  else if (cur.view === "projects" && cur.projectId) body = <ProjectDetail pk={cur.projectId} />;
  else if (cur.view === "monitor" && cur.projectId) body = <MonProjectDetail pk={cur.projectId} />;
  else if (cur.view === "monitor" && cur.hostId) body = <HostDetail hid={cur.hostId} />;
  else if (cur.view === "queue") body = <QueueView />;
  else if (cur.view === "projects") body = <ProjectsView />;
  else if (cur.view === "monitor") body = <MonitorView mode={monMode} setMode={setMonMode} />;
  else if (cur.view === "flight") body = <FlightView />;

  useEffect(() => {
    const h = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") { e.preventDefault(); setSearchOpen(true); }
      else if (e.key === "Escape" && !searchOpen) back();
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [searchOpen]);

  const nav = [
    { k: "queue", label: "Queue", icon: ListChecks, cnt: tickets.filter(t => t.life !== "archived").length },
    { k: "projects", label: "Projects", icon: Satellite, cnt: Object.keys(PROJECTS).length },
    { k: "monitor", label: "Monitor", icon: Gauge, cnt: null },
  ];

  return (
    <div className="gs">
      <style>{CSS}</style>
      <Nav.Provider value={api}>
      <div className="gs-shell">
        <aside className="gs-rail">
          <div className="gs-brand" style={{ cursor: "pointer" }} onClick={() => root("queue")}>
            <div className="gs-brand-mark"><Satellite size={17} /></div>
            <div><div className="gs-brand-name">Pantheos</div><div className="gs-brand-sub">LIFE OS</div></div>
          </div>
          <nav className="gs-nav">
            <div className="gs-nav-label">STATIONS</div>
            {nav.map(n => (
              <button key={n.k} className={`gs-nav-item ${section === n.k ? "active" : ""}`} onClick={() => root(n.k)}>
                <n.icon size={16} />{n.label}{n.cnt != null && <span className="cnt">{n.cnt}</span>}
              </button>
            ))}
            <div className="gs-nav-label" style={{ marginTop: 8 }}>AGENT</div>
            <button className={`gs-nav-item ${section === "flight" ? "active" : ""}`} onClick={() => root("flight")}><Radio size={16} />Delphi</button>
          </nav>
          <div className="gs-rail-foot">
            <div className="gs-flight-card" style={{ cursor: "pointer" }} onClick={() => root("flight")}>
              <div className="row"><span className="dot go" /><span className="nm">Delphi</span><Radio size={13} color="var(--ink-3)" style={{ marginLeft: "auto" }} /></div>
              <div className="st">● ONLINE · 40 RUNS LOGGED</div>
            </div>
          </div>
        </aside>

        <main className="gs-main">
          <div className="gs-strip">
            <div className="gs-crumb">
              {crumbs.map((c, i) => (
                <React.Fragment key={i}>
                  {i > 0 && <ChevronRight size={14} className="sep" />}
                  {i < crumbs.length - 1
                    ? <button onClick={() => { if (c.mode !== undefined) root(section); else back(); }}>{c.label}</button>
                    : <span className="cur">{c.label}</span>}
                </React.Fragment>
              ))}
            </div>
            <div className="gs-strip-spacer" />
            <button className="gs-kbtn" onClick={() => setSearchOpen(true)}>
              <Radio size={13} />Search <kbd>⌘K</kbd>
            </button>
            <span className="gs-stat-chip" style={{ background: "var(--fault-soft)", color: "var(--fault)", cursor: "pointer" }}
              onClick={() => go({ view: "monitor", containerId: "gh-stats-api" })}>
              <span className="dot flt" style={{ boxShadow: "none" }} />{cCount.flt} fault</span>
            <span className="gs-met"><Clock size={12} />MET <b>{clock}</b></span>
          </div>

          <div className="gs-body">{body}</div>
        </main>
      </div>

      {searchOpen && <SearchPalette tickets={tickets} onClose={() => setSearchOpen(false)} />}
      {toasts.length > 0 && (
        <div className="gs-toasts">
          {toasts.map(t => (
            <div key={t.id} className="gs-toast">
              <Check size={15} className="go" />{t.text}
            </div>
          ))}
        </div>
      )}
      </Nav.Provider>
    </div>
  );
}
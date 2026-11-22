import React,{useEffect,useRef,useState} from 'react';
import {Activity,ArrowDownToLine,Check,CheckCircle2,ChevronDown,Code2,Database,History,Home,LayoutDashboard,LockKeyhole,Menu,MessageSquare,Plus,Send,ShieldCheck,Sparkles,Table2,Terminal,Workflow,X,AlertTriangle,RefreshCw,Bot,Bell,UserCircle,BarChart3,FileText,Network,Clock3} from 'lucide-react';
const API=(import.meta.env.VITE_API_BASE_URL||'https://enterprise-bi-agent.onrender.com').replace(/\/$/,'');
const SUGGESTIONS=['How many customers are from India?','Show the top 5 customers by order count','What is the average order value for completed orders?','Which products are available in the warehouse?'];
const rowsOf=(data)=>Array.isArray(data)?data.map(r=>Array.isArray(r)?r:(r&&typeof r==='object'?Object.values(r):[r])):[];
const cell=(v)=>v==null?'—':typeof v==='object'?JSON.stringify(v):String(v);

function Robot({mood='idle',small=false,onClick}) {
 const [tilt,setTilt]=useState({x:0,y:0});
 function track(e){
  const r=e.currentTarget.getBoundingClientRect();
  const dx=(e.clientX-(r.left+r.width/2))/(r.width/2);
  const dy=(e.clientY-(r.top+r.height/2))/(r.height/2);
  setTilt({x:Math.max(-10,Math.min(10,-dy*10)),y:Math.max(-13,Math.min(13,dx*13))});
 }
 return <div className={'orka-avatar '+(small?'orka-avatar-small ':'')+'orka-avatar-'+mood}
  role={onClick?'button':'img'} tabIndex={onClick?0:undefined} aria-label="Orka AI 3D virtual assistant"
  onMouseMove={track} onMouseLeave={()=>setTilt({x:0,y:0})}
  onClick={onClick} onKeyDown={e=>{if(onClick&&(e.key==='Enter'||e.key===' ')){e.preventDefault();onClick();}}}
  style={{'--orka-tilt-x':tilt.x+'deg','--orka-tilt-y':tilt.y+'deg'}}>
  <img src="/images/orca-avatar-live.gif" alt="Orka AI friendly 3D robot mascot" />
 </div>;
}

function OrcaWidget({thinking,onOpenChat}) {
 const [bubble,setBubble]=useState(false);
 const [tilt,setTilt]=useState({x:0,y:0});
 function track(e){
  const r=e.currentTarget.getBoundingClientRect();
  const dx=(e.clientX-(r.left+r.width/2))/(window.innerWidth/2);
  const dy=(e.clientY-(r.top+r.height/2))/(window.innerHeight/2);
  setTilt({x:Math.max(-22,Math.min(22,-dy*22)),y:Math.max(-22,Math.min(22,dx*22))});
 }
 return <div className={'orca-widget '+(thinking?'thinking':'')+(bubble?' show-bubble':'')}>
  <div className="orca-bubble">{thinking?'Orka is thinking...':'Hi! Ask Orka anything.'}</div>
  <div className="orca-float">
   <button className="orca-tilt" type="button" aria-label="Open Orka AI chat" onMouseMove={track} onMouseLeave={()=>setTilt({x:0,y:0})} onClick={()=>{setBubble(v=>!v);onOpenChat?.();}} style={{transform:`rotateX(${tilt.x}deg) rotateY(${tilt.y}deg)`}}>
    <img src="/images/orca-avatar-live.gif" alt="Orka AI mascot" className="orca-img"/>
    <span className="orca-shadow"/>
   </button>
  </div>
 </div>;
}

function Result({data,onCsv}){const rows=rowsOf(data.result);return <div className="result-card"><div className="result-head"><div className="bot-avatar"><Bot size={17}/></div><div><b>orka.ai</b><small>ANALYSIS COMPLETE</small></div><span className="done"><CheckCircle2 size={12}/> Returned</span></div>{data.error&&<p className="warn"><AlertTriangle size={14}/>{data.error}</p>}{data.sql&&<details open className="sql"><summary><span><Terminal size={14}/> Generated SQL</span><ChevronDown size={14}/></summary><pre>{data.sql}</pre></details>}<div className="table-head"><div><b><Table2 size={15}/> Query results</b><small>{rows.length} rows returned</small></div>{rows.length>0&&<button onClick={()=>onCsv(data)}><ArrowDownToLine size={13}/> CSV</button>}</div>{rows.length?<div className="table-scroll"><table><thead><tr>{rows[0].map((_,i)=><th key={i}>Column {i+1}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{cell(v)}</td>)}</tr>)}</tbody></table></div>:<div className="empty">No rows returned.</div>}<div className="result-meta"><span><CheckCircle2 size={12}/> Workflow finished</span><span>{data.retries||0} retries</span><span>{data.cache_hit?'Cache hit':'Fresh query'}</span></div></div>}

export default function App(){
 const [q,setQ]=useState(''),[role,setRole]=useState('analyst'),[messages,setMessages]=useState([]),[busy,setBusy]=useState(false),[health,setHealth]=useState('checking'),[pending,setPending]=useState(null),[toast,setToast]=useState(''),[menu,setMenu]=useState(false);
 const input=useRef(null),bottom=useRef(null);
 useEffect(()=>{fetch(API+'/health').then(r=>{if(!r.ok)throw Error();setHealth('online')}).catch(()=>setHealth('offline'))},[]);
 useEffect(()=>{bottom.current&&bottom.current.scrollIntoView({behavior:'smooth'})},[messages,busy,pending]);
 useEffect(()=>{if(toast){const t=setTimeout(()=>setToast(''),3500);return()=>clearTimeout(t)}},[toast]);
 async function ask(text){const question=(text||q).trim();if(!question||busy)return;const id=Date.now();setQ('');setBusy(true);setMessages(m=>m.concat([{id,question,answer:null}]));try{const r=await fetch(API+'/query',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,role})});const d=await r.json();if(!r.ok)throw Error(d.detail||'API request failed');setMessages(m=>m.map(x=>x.id===id?{...x,answer:d}:x));if(d.approval_required)setPending({threadId:d.thread_id,question,sql:d.sql});if(d.error)setToast(d.error)}catch(e){setMessages(m=>m.map(x=>x.id===id?{...x,error:e.message}:x));setToast(e.message)}finally{setBusy(false)}}
 async function approve(yes){if(!pending)return;setBusy(true);try{const u=new URL(API+'/approve');u.searchParams.set('thread_id',pending.threadId);const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({approved:yes})});const d=await r.json();if(!r.ok)throw Error(d.detail||'Approval failed');setMessages(m=>m.map(x=>x.question===pending.question&&x.answer?.thread_id===pending.threadId?{...x,answer:{...x.answer,...d,approval_required:false}}:x));setPending(null);setToast(yes?'Approved. Query resumed.':'Query rejected.')}catch(e){setToast(e.message)}finally{setBusy(false)}}
 function csv(data){const rr=rowsOf(data.result);const txt=rr.map(r=>r.map(v=>'"'+cell(v).replaceAll('"','""')+'"').join(',')).join('\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([txt],{type:'text/csv'}));a.download='enterprise-bi-results.csv';a.click();URL.revokeObjectURL(a.href)}
 function reset(){setMessages([]);setPending(null);setQ('');input.current?.focus()}
 const actions=[{label:'Analyze Revenue',sub:'Get instant insights',icon:<BarChart3/>,question:'Show total revenue by month.'},{label:'Write SQL',sub:'Generate & validate SQL',icon:<Database/>,question:'Show me a SQL query for the top 10 customers by revenue.'},{label:'Build Workflow',sub:'Create AI workflows',icon:<Network/>,question:'Explain the agent workflow used to answer a business analytics question.'},{label:'Get Insights',sub:'Discover data patterns',icon:<Sparkles/>,question:'Give me useful insights from the available business data.'}];
 return <div className="hero-shell">
  <aside className={'hero-sidebar '+(menu?'open':'')}><div className="hero-brand"><div className="hero-brand-mark"><Robot small/></div><b>orka.ai</b><button className="close-menu" onClick={()=>setMenu(false)}><X/></button></div><nav><button className="selected"><MessageSquare/> Chat</button><button onClick={()=>setToast('Agent orchestration is powered by LangGraph.')}><Network/> Agents</button><button onClick={()=>setToast('Workflow orchestration is managed by LangGraph.')}><Workflow/> Workflows</button><button onClick={()=>setToast('Your analytics warehouse is powered by DuckDB.')}><Database/> Datasets</button><button onClick={()=>setToast('Ask orka.ai to generate an analytics report.')}><FileText/> Reports</button><button onClick={()=>setToast('Ask orka.ai to discover business insights.')}><Sparkles/> Insights</button></nav><div className="hero-profile"><span>BL</span><b>Basil Laiju</b></div></aside>
  {menu&&<button className="hero-scrim" onClick={()=>setMenu(false)}/>}
  <main className="hero-main"><header className="hero-top"><button className="hamb" onClick={()=>setMenu(true)}><Menu/></button><span className="top-spacer"/><button aria-label="Notifications"><Bell/></button><button aria-label="Profile"><UserCircle/></button></header>
   <section className="hero-content">
    <div className="hero-banner"><div className="hero-wave wave-one"/><div className="hero-wave wave-two"/><div className="hero-copy"><div className="hero-mascot"><Robot mood={busy?'think':'idle'} onClick={()=>input.current?.focus()}/></div><div className="hero-message"><h1>Hi Basil, I’m Orka<br/>Your Enterprise BI Assistant <span>👋</span></h1><p>Ask questions, analyze data, generate reports,<br/>or let me run end-to-end analytics for you.</p><div className="hero-api"><i className={'dot '+health}/>{health==='online'?'Connected and ready':health==='checking'?'Connecting to your API':'API connection unavailable'}</div></div></div>
     <form className="hero-search" onSubmit={e=>{e.preventDefault();ask()}}><Sparkles/><input ref={input} value={q} onChange={e=>setQ(e.target.value)} placeholder="Ask orka.ai anything about your data..." disabled={busy||!!pending}/><button type="submit" disabled={!q.trim()||busy||!!pending}><Send/></button></form>
     <div className="hero-actions">{actions.map(a=><button key={a.label} onClick={()=>ask(a.question)}><span>{a.icon}</span>{a.label}</button>)}</div>
    </div>
    {messages.length>0&&<section className="conversation"><div className="conversation-head"><div><span className="conversation-icon"><MessageSquare/></span><div><b>Conversation</b><small>Your analytics workspace</small></div></div><button onClick={reset}><Plus size={14}/> New chat</button></div>{messages.map(m=><article className="conversation-message" key={m.id}><div className="conversation-question"><span>BL</span><div><small>YOU · {new Date(m.id).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</small><p>{m.question}</p></div></div>{m.error?<div className="warn"><AlertTriangle/>{m.error}</div>:m.answer?<Result data={m.answer} onCsv={csv}/>:<div className="conversation-thinking"><Robot small mood="think"/><div><b>orka.ai is thinking...</b><small>Retrieving context · Generating SQL · Validating query</small><div className="bars"><i/><i/><i/></div></div></div>}</article>)}
     {pending&&<div className="approval"><div><LockKeyhole/><div><b>Human approval required</b><small>This query is paused before execution.</small></div><span>PENDING</span></div><pre>{pending.sql||'SQL preview unavailable'}</pre><footer><button onClick={()=>approve(false)} disabled={busy}>Reject</button><button onClick={()=>approve(true)} disabled={busy}><Check size={14}/> Approve & run</button></footer></div>}
     {busy&&<div className="conversation-running"><i/> Agent workflow running <span>● ● ● ●</span></div>}<div ref={bottom}/></section>}
    <footer className="hero-footer"><span>© 2026 orka.ai</span><span><i className={'dot '+health}/> Secure, API-powered analytics</span></footer>
   </section>
  </main>
  <OrcaWidget thinking={busy} onOpenChat={()=>input.current?.focus()}/>
  {toast&&<div className="toast"><CheckCircle2 size={16}/>{toast}<button onClick={()=>setToast('')}><X size={14}/></button></div>}
 </div>;
}

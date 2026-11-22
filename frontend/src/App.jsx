import React,{useEffect,useRef,useState} from 'react';
import {Activity,ArrowDownToLine,Check,CheckCircle2,ChevronDown,Code2,Database,History,Home,LayoutDashboard,LockKeyhole,Menu,MessageSquare,Plus,Send,ShieldCheck,Sparkles,Table2,Terminal,Workflow,X,AlertTriangle,RefreshCw,Bot,Bell,UserCircle,BarChart3,FileText,Network,Clock3} from 'lucide-react';
const API=(import.meta.env.VITE_API_BASE_URL||'https://enterprise-bi-agent.onrender.com').replace(/\/$/,'');
const SUGGESTIONS=['How many customers are from India?','Show the top 5 customers by order count','What is the average order value for completed orders?','Which products are available in the warehouse?'];
const rowsOf=(data)=>Array.isArray(data)?data.map(r=>Array.isArray(r)?r:(r&&typeof r==='object'?Object.values(r):[r])):[];
const cell=(v)=>v==null?'—':typeof v==='object'?JSON.stringify(v):String(v);

function Orka3D({mood='idle',small=false,onClick,className=''}) {
 const mount=useRef(null);
 useEffect(()=>{
  const host=mount.current;
  if(!host)return;
  let renderer,frame,observer;
  let disposed=false;
  import('three').then(THREE=>{
   if(disposed)return;
   const scene=new THREE.Scene();
   const camera=new THREE.PerspectiveCamera(34,1,.1,100);
   camera.position.set(0,0,6.2);
   renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});
   renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
   renderer.setSize(host.clientWidth||240,host.clientHeight||220,false);
   renderer.outputColorSpace=THREE.SRGBColorSpace;
   renderer.toneMapping=THREE.ACESFilmicToneMapping;
   renderer.toneMappingExposure=1.25;
   host.appendChild(renderer.domElement);
   scene.add(new THREE.HemisphereLight(0xe9e7ff,0x29204b,2.0));
   const key=new THREE.DirectionalLight(0xffffff,3.2);key.position.set(-3,4,5);scene.add(key);
   const rimLight=new THREE.PointLight(0x65efff,16,8);rimLight.position.set(2,1,3);scene.add(rimLight);
   const violet=new THREE.PointLight(0x9b61ff,18,9);violet.position.set(-3,-1,2);scene.add(violet);
   const root=new THREE.Group();scene.add(root);
   const mat=(color,roughness=.28,metalness=.12,emissive=null,intensity=0)=>new THREE.MeshStandardMaterial({color,roughness,metalness,emissive:emissive||color,emissiveIntensity:intensity});
   const pearl=mat(0xf4f1ff,.22,.18);
   const lavender=mat(0xaaa4dc,.3,.22);
   const dark=mat(0x080d20,.12,.35);
   const cyan=mat(0x59f4ff,.18,.12,0x18dfff,2.4);
   const softCyan=mat(0x9afaff,.2,.1,0x38eaff,1.5);
   const body=new THREE.Mesh(new THREE.SphereGeometry(1,48,32),pearl);body.scale.set(.78,.98,.58);body.position.y=-.38;root.add(body);
   const chest=new THREE.Mesh(new THREE.SphereGeometry(1,40,28),lavender);chest.scale.set(.58,.56,.16);chest.position.set(0,-.5,.48);root.add(chest);
   const head=new THREE.Mesh(new THREE.SphereGeometry(1,48,32),pearl);head.scale.set(1.02,.86,.72);head.position.set(0,.55,0);root.add(head);
   const crown=new THREE.Mesh(new THREE.SphereGeometry(1,40,28),lavender);crown.scale.set(.28,.65,.25);crown.position.set(0,1.24,-.12);crown.rotation.z=-.12;root.add(crown);
   const visorRim=new THREE.Mesh(new THREE.SphereGeometry(1,48,32),softCyan);visorRim.scale.set(.87,.58,.18);visorRim.position.set(0,.48,.63);root.add(visorRim);
   const visor=new THREE.Mesh(new THREE.SphereGeometry(1,48,32),dark);visor.scale.set(.82,.53,.19);visor.position.set(0,.49,.69);root.add(visor);
   const eyeGroup=new THREE.Group();eyeGroup.position.set(0,.48,.87);root.add(eyeGroup);
   const eyes=[];
   [-1,1].forEach(side=>{
    const eye=new THREE.Mesh(new THREE.SphereGeometry(.105,24,20),cyan);eye.position.set(side*.29,.015,0);eye.scale.set(1.05,1.22,.55);eyeGroup.add(eye);eyes.push(eye);
    const glint=new THREE.Mesh(new THREE.SphereGeometry(.028,12,10),mat(0xffffff,.1,.05,0xffffff,.8));glint.position.set(side*.29+.025,.055,.055);eyeGroup.add(glint);
   });
   const smileCurve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(-.13,-.18,.89),new THREE.Vector3(0,-.27,.91),new THREE.Vector3(.13,-.18,.89));
   const smile=new THREE.Mesh(new THREE.TubeGeometry(smileCurve,20,.022,8,false),cyan);root.add(smile);
   const finGeo=new THREE.SphereGeometry(1,32,24);
   const fins=[];
   [-1,1].forEach(side=>{
    const fin=new THREE.Mesh(finGeo,pearl);fin.scale.set(.22,.48,.19);fin.position.set(side*.82,-.56,.03);fin.rotation.z=side*-.42;root.add(fin);fins.push(fin);
    const shoulder=new THREE.Mesh(new THREE.SphereGeometry(.2,24,18),lavender);shoulder.position.set(side*.7,-.12,.02);root.add(shoulder);
   });
   const tail=new THREE.Mesh(finGeo,lavender);tail.scale.set(.43,.16,.14);tail.position.set(-.95,-.05,-.3);tail.rotation.z=-.15;root.add(tail);
   const antenna=new THREE.Mesh(new THREE.SphereGeometry(.075,20,16),softCyan);antenna.position.set(0,1.62,0);root.add(antenna);
   const halo=new THREE.Mesh(new THREE.TorusGeometry(.12,.018,8,32),cyan);halo.position.set(0,1.62,0);root.add(halo);
   let targetX=0,targetY=0,lookX=0,lookY=0,lastBlink=0,blink=0;
   const onPointer=e=>{const r=host.getBoundingClientRect();targetY=((e.clientX-r.left)/r.width-.5)*.48;targetX=-((e.clientY-r.top)/r.height-.5)*.35;};
   const onLeave=()=>{targetX=0;targetY=0;};
   host.addEventListener('pointermove',onPointer);host.addEventListener('pointerleave',onLeave);
   const clock=new THREE.Clock();
   const resize=()=>{if(!renderer)return;const w=Math.max(1,host.clientWidth),h=Math.max(1,host.clientHeight);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();};
   observer=new ResizeObserver(resize);observer.observe(host);resize();
   const animate=()=>{
    if(disposed)return;
    frame=requestAnimationFrame(animate);
    const t=clock.getElapsedTime();
    const isThinking=mood==='think',isListening=mood==='listen';
    lookX+=(targetX-lookX)*.055;lookY+=(targetY-lookY)*.055;
    root.rotation.y=lookX+Math.sin(t*.65)*.035;
    root.rotation.x=lookY+(isListening?-.035:0);
    root.position.y=Math.sin(t*(isThinking?2.2:1.05))*(isThinking?.065:.035);
    root.rotation.z=Math.sin(t*.7)*.018;
    fins[0].rotation.z=-.42+Math.sin(t*1.5)*.07;fins[1].rotation.z=.42-Math.sin(t*1.5)*.07;
    tail.rotation.y=Math.sin(t*1.7)*.16;
    antenna.scale.setScalar(1+(isThinking?.18:.07)*(.5+.5*Math.sin(t*4)));
    const elapsed=t-lastBlink;
    if(elapsed>(isThinking?1.8:3.2)+Math.sin(t*.31)*.7){lastBlink=t;blink=.001;}
    if(blink>0){blink=Math.min(1,blink+.18);const sy=Math.max(.08,1-Math.sin(blink*Math.PI)*.94);eyes.forEach(e=>e.scale.y=sy*1.22);if(blink>=1)blink=0;}
    else eyes.forEach(e=>e.scale.y=isListening?1.38:1.22);
    eyeGroup.position.x=lookX*.25;eyeGroup.position.y=.48+lookY*.18;
    renderer.render(scene,camera);
   };
   animate();
   host._cleanup=()=>{host.removeEventListener('pointermove',onPointer);host.removeEventListener('pointerleave',onLeave);observer?.disconnect();cancelAnimationFrame(frame);scene.traverse(o=>{o.geometry?.dispose();if(o.material){if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material.dispose();}});renderer?.dispose();renderer?.domElement.remove();};
  }).catch(err=>console.error('Orka 3D avatar failed to load',err));
  return()=>{disposed=true;host?._cleanup?.();};
 },[mood]);
 return <div ref={mount} className={'orka-scene '+(small?'orka-scene-small ':'')+className} role={onClick?'button':'img'} tabIndex={onClick?0:undefined} aria-label="Orka interactive 3D assistant" onClick={onClick} onKeyDown={e=>{if(onClick&&(e.key==='Enter'||e.key===' ')){e.preventDefault();onClick();}}}/>;
}
function Robot({mood='idle',small=false,onClick}) {return <Orka3D mood={mood} small={small} onClick={onClick}/>;}
function OrcaWidget({thinking,listening,onOpenChat}) {
 const [bubble,setBubble]=useState(false);
 return <div className={'orca-widget '+(thinking?'thinking ':'')+(listening?'listening ':'')+(bubble?'show-bubble':'')}>
  <div className="orca-bubble">{thinking?'Orka is thinking...':listening?'I’m listening.':'Hi! Ask Orka anything.'}</div>
  <div className="orca-float"><button className="orca-tilt" type="button" aria-label="Open Orka AI chat" onClick={()=>{setBubble(v=>!v);onOpenChat?.();}}><Orka3D mood={thinking?'think':listening?'listen':'idle'} small/><span className="orca-shadow"/></button></div>
 </div>;
}

function Result({data,onCsv}){const rows=rowsOf(data.result);return <div className="result-card"><div className="result-head"><div className="bot-avatar"><Bot size={17}/></div><div><b>orka.ai</b><small>ANALYSIS COMPLETE</small></div><span className="done"><CheckCircle2 size={12}/> Returned</span></div>{data.error&&<p className="warn"><AlertTriangle size={14}/>{data.error}</p>}{data.sql&&<details open className="sql"><summary><span><Terminal size={14}/> Generated SQL</span><ChevronDown size={14}/></summary><pre>{data.sql}</pre></details>}<div className="table-head"><div><b><Table2 size={15}/> Query results</b><small>{rows.length} rows returned</small></div>{rows.length>0&&<button onClick={()=>onCsv(data)}><ArrowDownToLine size={13}/> CSV</button>}</div>{rows.length?<div className="table-scroll"><table><thead><tr>{rows[0].map((_,i)=><th key={i}>Column {i+1}</th>)}</tr></thead><tbody>{rows.slice(0,100).map((r,i)=><tr key={i}>{r.map((v,j)=><td key={j}>{cell(v)}</td>)}</tr>)}</tbody></table></div>:<div className="empty">No rows returned.</div>}<div className="result-meta"><span><CheckCircle2 size={12}/> Workflow finished</span><span>{data.retries||0} retries</span><span>{data.cache_hit?'Cache hit':'Fresh query'}</span></div></div>}

export default function App(){
 const [q,setQ]=useState(''),[role,setRole]=useState('analyst'),[messages,setMessages]=useState([]),[busy,setBusy]=useState(false),[listening,setListening]=useState(false),[health,setHealth]=useState('checking'),[pending,setPending]=useState(null),[toast,setToast]=useState(''),[menu,setMenu]=useState(false);
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
    <div className="hero-banner"><div className="hero-wave wave-one"/><div className="hero-wave wave-two"/><div className="hero-copy"><div className="hero-mascot"><Robot mood={busy?'think':listening?'listen':'idle'} onClick={()=>input.current?.focus()}/></div><div className="hero-message"><h1>Hi Basil, I’m Orka<br/>Your Enterprise BI Assistant <span>👋</span></h1><p>Ask questions, analyze data, generate reports,<br/>or let me run end-to-end analytics for you.</p><div className="hero-api"><i className={'dot '+health}/>{health==='online'?'Connected and ready':health==='checking'?'Connecting to your API':'API connection unavailable'}</div></div></div>
     <form className="hero-search" onSubmit={e=>{e.preventDefault();ask()}}><Sparkles/><input ref={input} value={q} onChange={e=>setQ(e.target.value)} onFocus={()=>setListening(true)} onBlur={()=>setListening(false)} placeholder="Ask orka.ai anything about your data..." disabled={busy||!!pending}/><button type="submit" disabled={!q.trim()||busy||!!pending}><Send/></button></form>
     <div className="hero-actions">{actions.map(a=><button key={a.label} onClick={()=>ask(a.question)}><span>{a.icon}</span>{a.label}</button>)}</div>
    </div>
    {messages.length>0&&<section className="conversation"><div className="conversation-head"><div><span className="conversation-icon"><MessageSquare/></span><div><b>Conversation</b><small>Your analytics workspace</small></div></div><button onClick={reset}><Plus size={14}/> New chat</button></div>{messages.map(m=><article className="conversation-message" key={m.id}><div className="conversation-question"><span>BL</span><div><small>YOU · {new Date(m.id).toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</small><p>{m.question}</p></div></div>{m.error?<div className="warn"><AlertTriangle/>{m.error}</div>:m.answer?<Result data={m.answer} onCsv={csv}/>:<div className="conversation-thinking"><Robot small mood="think"/><div><b>orka.ai is thinking...</b><small>Retrieving context · Generating SQL · Validating query</small><div className="bars"><i/><i/><i/></div></div></div>}</article>)}
     {pending&&<div className="approval"><div><LockKeyhole/><div><b>Human approval required</b><small>This query is paused before execution.</small></div><span>PENDING</span></div><pre>{pending.sql||'SQL preview unavailable'}</pre><footer><button onClick={()=>approve(false)} disabled={busy}>Reject</button><button onClick={()=>approve(true)} disabled={busy}><Check size={14}/> Approve & run</button></footer></div>}
     {busy&&<div className="conversation-running"><i/> Agent workflow running <span>● ● ● ●</span></div>}<div ref={bottom}/></section>}
    <footer className="hero-footer"><span>© 2026 orka.ai</span><span><i className={'dot '+health}/> Secure, API-powered analytics</span></footer>
   </section>
  </main>
  <OrcaWidget thinking={busy} listening={listening} onOpenChat={()=>input.current?.focus()}/>
  {toast&&<div className="toast"><CheckCircle2 size={16}/>{toast}<button onClick={()=>setToast('')}><X size={14}/></button></div>}
 </div>;
}

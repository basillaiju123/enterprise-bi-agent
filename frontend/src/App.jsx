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
  let renderer,frame,observer,cleanup;
  let disposed=false;
  import('three').then(THREE=>{
   if(disposed)return;
   const scene=new THREE.Scene();
   const camera=new THREE.PerspectiveCamera(34,1,.1,100);
   camera.position.set(0,0,6.4);
   renderer=new THREE.WebGLRenderer({alpha:true,antialias:true,powerPreference:'low-power'});
   renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));
   renderer.setSize(host.clientWidth||240,host.clientHeight||220,false);
   renderer.outputColorSpace=THREE.SRGBColorSpace;
   renderer.toneMapping=THREE.ACESFilmicToneMapping;
   renderer.toneMappingExposure=1.2;
   host.appendChild(renderer.domElement);
   scene.add(new THREE.HemisphereLight(0xf2f0ff,0x17152f,2.1));
   const key=new THREE.DirectionalLight(0xffffff,3.4);key.position.set(-3,4,5);scene.add(key);
   const rim=new THREE.PointLight(0x61efff,15,9);rim.position.set(2,1,3);scene.add(rim);
   const violet=new THREE.PointLight(0x9b61ff,13,9);violet.position.set(-3,-1,2);scene.add(violet);
   const root=new THREE.Group();scene.add(root);
   const material=(color,roughness=.25,metalness=.12,emissive=null,intensity=0)=>new THREE.MeshStandardMaterial({color,roughness,metalness,emissive:emissive||color,emissiveIntensity:intensity});
   const midnight=material(0x171b35,.24,.22);
   const black=material(0x070b18,.12,.3);
   const white=material(0xf5f3ff,.22,.16);
   const pale=material(0xd8d7f4,.28,.18);
   const cyan=material(0x63f4ff,.16,.12,0x16dfff,2.5);
   const glow=material(0xa5fbff,.18,.1,0x42eaff,1.5);
   const sphere=new THREE.SphereGeometry(1,48,32);
   const make=(geo,mat,pos,scale,rot)=>{const m=new THREE.Mesh(geo,mat);m.position.set(...pos);m.scale.set(...scale);if(rot)m.rotation.set(...rot);root.add(m);return m;};

   // A whale-shaped silhouette: broad streamlined body, dorsal fin, flippers and tail flukes.
   const body=make(sphere,midnight,[0,-.12,0],[1.42,.68,.62]);
   const belly=make(sphere,white,[.02,-.43,.31],[1.13,.36,.39]);
   const muzzle=make(sphere,midnight,[.78,-.02,.26],[.55,.43,.48]);
   // White eye patches on the characteristic black-and-white orca head.
   make(sphere,white,[.57,.38,.43],[.3,.23,.12],[0,0,-.22]);
   make(sphere,white,[-.57,.38,.43],[.3,.23,.12],[0,0,.22]);
   // Glossy face screen sits forward on the whale's head.
   const visorRim=make(sphere,glow,[0,.22,.59],[.67,.43,.17]);
   const visor=make(sphere,black,[0,.22,.70],[.625,.385,.15]);
   const eyeGroup=new THREE.Group();eyeGroup.position.set(0,.24,.84);root.add(eyeGroup);
   const eyes=[];
   [-1,1].forEach(side=>{
    const eye=new THREE.Mesh(new THREE.SphereGeometry(.105,24,20),cyan);
    eye.position.set(side*.22,.025,0);eye.scale.set(1.05,1.2,.55);eyeGroup.add(eye);eyes.push(eye);
    const glint=new THREE.Mesh(new THREE.SphereGeometry(.026,12,10),material(0xffffff,.08,.02,0xffffff,.9));
    glint.position.set(side*.22+.025,.065,.055);eyeGroup.add(glint);
   });
   const smileCurve=new THREE.QuadraticBezierCurve3(new THREE.Vector3(-.12,-.12,.855),new THREE.Vector3(0,-.19,.87),new THREE.Vector3(.12,-.12,.855));
   root.add(new THREE.Mesh(new THREE.TubeGeometry(smileCurve,20,.018,8,false),cyan));

   // Dorsal fin: custom rounded triangular fin along the whale's back.
   const finShape=new THREE.Shape();
   finShape.moveTo(-.25,0);finShape.quadraticCurveTo(-.18,.38,-.02,.58);finShape.quadraticCurveTo(.12,.62,.18,.42);finShape.lineTo(.28,0);finShape.closePath();
   const dorsalGeo=new THREE.ExtrudeGeometry(finShape,{depth:.12,bevelEnabled:true,bevelSegments:4,steps:1,bevelSize:.045,bevelThickness:.04});
   const dorsal=new THREE.Mesh(dorsalGeo,midnight);dorsal.position.set(-.35,.47,-.2);root.add(dorsal);
   const flippers=[];
   [-1,1].forEach(side=>{
    const fin=make(sphere,midnight,[-.18+side*.55,-.53,.02],[.22,.5,.16],[0,0,side*.48]);
    flippers.push(fin);
    make(sphere,white,[-.18+side*.55,-.57,.13],[.13,.31,.055],[0,0,side*.48]);
   });
   // Tail stock and two lobes visible behind the body.
   const tailStock=make(sphere,midnight,[-1.35,-.12,-.06],[.48,.19,.22],[0,0,-.08]);
   const tailGroup=new THREE.Group();tailGroup.position.set(-1.63,-.1,-.08);root.add(tailGroup);
   const lobe1=new THREE.Mesh(sphere,midnight);lobe1.scale.set(.48,.17,.12);lobe1.position.set(-.28,.19,0);lobe1.rotation.z=.3;tailGroup.add(lobe1);
   const lobe2=new THREE.Mesh(sphere,midnight);lobe2.scale.set(.48,.17,.12);lobe2.position.set(-.28,-.19,0);lobe2.rotation.z=-.3;tailGroup.add(lobe2);
   // Subtle cyan gill/energy accents.
   for(let i=0;i<3;i++){
    const gill=make(new THREE.TorusGeometry(.07,.012,8,20),glow,[-.83+i*.09,-.1,.55],[1,1,1],[0,0,Math.PI/2]);
   }

   let targetX=0,targetY=0,lookX=0,lookY=0,lastBlink=0,blink=0;
   const onPointer=e=>{const r=host.getBoundingClientRect();targetY=((e.clientX-r.left)/r.width-.5)*.42;targetX=-((e.clientY-r.top)/r.height-.5)*.3;};
   const onLeave=()=>{targetX=0;targetY=0;};
   host.addEventListener('pointermove',onPointer);host.addEventListener('pointerleave',onLeave);
   const clock=new THREE.Clock();
   const resize=()=>{if(!renderer)return;const w=Math.max(1,host.clientWidth),h=Math.max(1,host.clientHeight);renderer.setSize(w,h,false);camera.aspect=w/h;camera.updateProjectionMatrix();};
   observer=new ResizeObserver(resize);observer.observe(host);resize();
   const animate=()=>{
    if(disposed)return;
    frame=requestAnimationFrame(animate);
    const t=clock.getElapsedTime();
    const thinking=mood==='think',listening=mood==='listen';
    lookX+=(targetX-lookX)*.055;lookY+=(targetY-lookY)*.055;
    root.rotation.y=lookX+Math.sin(t*.45)*.045;
    root.rotation.x=lookY+(listening?-.025:0);
    root.position.y=Math.sin(t*(thinking?2.1:.85))*(thinking?.055:.028);
    root.rotation.z=Math.sin(t*.55)*.012;
    tailGroup.rotation.y=Math.sin(t*1.45)*.3;
    tailGroup.rotation.z=Math.sin(t*1.45)*.09;
    flippers[0].rotation.z=-.48+Math.sin(t*1.2)*.045;
    flippers[1].rotation.z=.48-Math.sin(t*1.2)*.045;
    eyeGroup.position.x=lookX*.22;eyeGroup.position.y=.24+lookY*.16;
    const elapsed=t-lastBlink;
    if(elapsed>(thinking?1.9:3.4)+Math.sin(t*.27)*.8){lastBlink=t;blink=.001;}
    if(blink>0){blink=Math.min(1,blink+.18);const sy=Math.max(.08,1-Math.sin(blink*Math.PI)*.94);eyes.forEach(e=>e.scale.y=sy*1.2);if(blink>=1)blink=0;}
    else eyes.forEach(e=>e.scale.y=listening?1.32:1.2);
    visorRim.material.emissiveIntensity=thinking?3.4:listening?2.8:1.5;
    renderer.render(scene,camera);
   };
   animate();
   cleanup=()=>{host.removeEventListener('pointermove',onPointer);host.removeEventListener('pointerleave',onLeave);observer?.disconnect();cancelAnimationFrame(frame);scene.traverse(o=>{o.geometry?.dispose();if(o.material){if(Array.isArray(o.material))o.material.forEach(m=>m.dispose());else o.material.dispose();}});renderer?.dispose();renderer?.domElement.remove();};
   host._cleanup=cleanup;
  }).catch(err=>console.error('Orka 3D avatar failed to load',err));
  return()=>{disposed=true;host?._cleanup?.();};
 },[mood]);
 return <div ref={mount} className={'orka-scene '+(small?'orka-scene-small ':'')+className} role={onClick?'button':'img'} tabIndex={onClick?0:undefined} aria-label="Orka whale-inspired interactive 3D assistant" onClick={onClick} onKeyDown={e=>{if(onClick&&(e.key==='Enter'||e.key===' ')){e.preventDefault();onClick();}}}/>;
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

const $=s=>document.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const fmt=b=>b>=1e9?(b/1e9).toFixed(1)+" GB":b>=1e6?(b/1e6).toFixed(0)+" MB":Math.max(1,Math.round(b/1e3))+" KB";
const KIND={loose:["Loose files to sort into folders","Moved into tidy sub-folders"],dup:["Duplicate files","Identical copies; the oldest stays"],old:["Old, large files","Untouched for over a year"],cache:["Cache folders","Apps rebuild these on their own"]};
let S={},plan=null,sel=new Set(),tab="dash",busy=false;
async function api(p,b){let r;try{r=await fetch(p,b===undefined?{}:{method:"POST",headers:{"X-LD":"1","Content-Type":"application/json"},body:JSON.stringify(b)})}catch(e){throw new Error("Lost connection to the app's background service. Close the window and reopen Laptop Doctor.")}const j=await r.json();if(!r.ok)throw new Error(j.error||r.status);return j}
function toast(t){const e=$("#toast");e.textContent=t;e.style.display="block";setTimeout(()=>e.style.display="none",3500)}
const ask=t=>new Promise(res=>{const d=$("#dlg");$("#dtxt").textContent=t;d.returnValue="";d.onclose=()=>res(d.returnValue==="ok");d.showModal()});
const go=t=>{tab=t;draw()};
async function load(){try{S=await api("/api/state");draw()}catch(e){const v=$("#view");if(v)v.innerHTML=`<section><h2>Laptop Doctor could not start</h2><p>${esc(e.message)}</p><p>Close and reopen the app. If it keeps happening, check <code>%USERPROFILE%\.laptop_doctor\log.txt</code>.</p></section>`;toast(e.message)}}
function draw(){document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("on",b.dataset.t===tab));({dash,plan:planV,hist,set:setV})[tab]()}

function dash(){const m=S.config.model,a=plan?plan.ai:{},st=plan&&plan.stats;
$("#view").innerHTML=`${m?"":`<div class="note">No model chosen yet. <a href="#" onclick="go('set');return false">Open Settings</a> to connect Ollama.</div>`}
<section class="hero"><div><h2>Check my laptop</h2><div class="mute">Scans your allowed folders, then asks <b>${esc(m||"your model")}</b> for advice. Nothing changes until you approve it.</div></div>
<button class="btn" ${busy?"disabled":""} onclick="analyze()">${busy?"Analyzing, this can take a minute":"Run analysis"}</button></section>
${plan?`${plan.error?`<div class="note">The AI step failed (${esc(plan.error)}). Showing rule-based suggestions only.</div>`:""}
<div class="stats"><div><div class="mute sm">Health score</div><div class="num">${esc(a.score??"-")}</div></div>
<div><div class="mute sm">Disk used</div><div class="num">${Math.round(st.disk_used*100/st.disk_total)}%</div><div class="meter"><i style="width:${st.disk_used*100/st.disk_total}%"></i></div>${st.ram!=null?`<div class="sm mute">RAM ${st.ram}%, CPU ${st.cpu}%</div>`:""}</div>
<div><div class="mute sm">Proposed changes</div><div class="num">${plan.items.length}</div><a href="#" onclick="go('plan');return false">Review them</a></div></div>
<section><h3>Diagnosis</h3><p>${esc(a.diagnosis||"No AI diagnosis available.")}</p>${a.tips.length?`<h3>Advice</h3><ul>${a.tips.map(t=>`<li>${esc(t)}</li>`).join("")}</ul>`:""}</section>`:""}`}
async function analyze(){busy=true;draw();try{await api("/api/analyze",{});let j;do{await new Promise(r=>setTimeout(r,1500));j=await api("/api/job")}while(j.state==="running");if(j.state==="error")throw new Error(j.error);plan=j.result;sel.clear()}catch(e){toast(e.message)}busy=false;draw()}

function planV(){if(!plan||!plan.items.length){$("#view").innerHTML=`<div class="box empty">${plan?"Nothing to clean up. Your folders look tidy.":"Run an analysis to get a list of proposed changes."}</div>`;return}
let h="";for(const k in KIND){const it=plan.items.filter(i=>i.kind===k);if(!it.length)continue;
h+=`<section><div class="gh"><label><input type="checkbox" onchange="all_('${k}',this.checked)"> <b>${KIND[k][0]}</b></label><span class="mute sm">${it.length} items, ${fmt(it.reduce((s,i)=>s+i.size,0))}. ${KIND[k][1]}.</span></div>
${it.map(i=>`<label class="row" title="${esc(i.path)}"><input type="checkbox" ${sel.has(i.id)?"checked":""} onchange="tog('${i.id}',this.checked)"><div><div class="nm">${esc(i.name)}</div>
<div class="mute sm">${fmt(i.size)}, last changed ${i.age} days ago</div><div class="to">${i.action==="move"?"move to "+esc(i.dest)+"/":"move to quarantine (recoverable)"}</div>${i.note?`<div class="sm ai">AI: ${esc(i.note)}</div>`:""}</div></label>`).join("")}</section>`}
$("#view").innerHTML=h+`<div class="bar2"><span id="cnt"></span><button class="btn" onclick="applySel()">Apply selected</button></div>`;cnt()}
function cnt(){const e=$("#cnt");if(!e)return;const l=plan.items.filter(i=>sel.has(i.id));e.textContent=l.length?`${l.length} selected, ${fmt(l.reduce((s,i)=>s+i.size,0))}`:"Nothing selected. Hover a name to see its full path."}
function tog(id,v){v?sel.add(id):sel.delete(id);cnt()}
function all_(k,v){plan.items.filter(i=>i.kind===k).forEach(i=>v?sel.add(i.id):sel.delete(i.id));planV()}
async function applySel(){const ids=[...sel];if(!ids.length)return toast("Tick at least one change first.");
const mv=plan.items.filter(i=>sel.has(i.id)&&i.action==="move").length;
if(!await ask(`Apply ${ids.length} change(s)?\n\n${mv} will be moved into folders and ${ids.length-mv} into the quarantine folder.\nNothing is permanently deleted, and every batch can be undone from History.`))return;
try{const r=await api("/api/apply",{ids});toast(`${r.done} changed`+(r.skipped.length?`, ${r.skipped.length} skipped`:""));plan=null;sel.clear();tab="hist";await load()}catch(e){toast(e.message)}}

function hist(){$("#view").innerHTML=S.history.length?S.history.map(b=>`<section><div class="gh" style="border:0;margin:0;padding:0"><b>${esc(b.ts)}, ${b.moves.length} change(s)</b>${b.undone?`<span class="mute">Undone</span>`:`<button class="btn ghost" onclick="undo('${b.id}')">Undo batch</button>`}</div>
<div class="mute sm">${b.moves.slice(0,6).map(m=>esc(m.name)).join(", ")}${b.moves.length>6?" and more":""}</div></section>`).join(""):`<div class="box empty">No changes applied yet.</div>`}
async function undo(id){try{const r=await api("/api/undo",{id});toast(`${r.restored} restored`);await load()}catch(e){toast(e.message)}}

function setV(){const c=S.config;$("#view").innerHTML=`
<section><h3>1. Connect to Ollama</h3><div class="row2"><input type="text" id="url" value="${esc(c.ollama_url)}"><button class="btn ghost" onclick="connect()">Connect</button></div>
${S.ollama_error?`<div class="sm bad">${esc(S.ollama_error)}. Start it with <code>ollama serve</code>.</div>`:`<div class="sm ok">Connected, ${S.models.length} model(s) found.</div>`}
<h3>2. Choose a model</h3><div class="row2"><select id="mdl">${S.models.length?S.models.map(m=>`<option ${m===c.model?"selected":""}>${esc(m)}</option>`).join(""):`<option value="">No models found</option>`}</select></div>
<div class="sm mute">A 3B to 8B model such as llama3.2 or qwen2.5 is enough. Install one with <code>ollama pull llama3.2</code>.</div></section>
<section><h3>3. Folders this app may change</h3><div class="sm mute">Only folders inside your home folder are accepted. Everything else is off limits.</div>
${c.folders.map((f,i)=>`<div class="row2"><code>${esc(f)}</code><button class="btn ghost" onclick="rmf(${i})">Remove</button></div>`).join("")||`<div class="sm bad">No folders yet. Add one below.</div>`}
<div class="row2"><input type="text" id="nf" placeholder="~/Documents/Projects"><button class="btn ghost" onclick="addf()">Add folder</button></div>
<label class="row"><input type="checkbox" id="cache" ${c.include_cache?"checked":""}><div>Also allow cleaning user cache folders<div class="sm mute">Covers ~/.cache, ~/Library/Caches and Windows Temp. Items are quarantined, not deleted.</div></div></label></section>
<section><h3>Quarantine folder</h3><div class="sm mute">Removed items wait here (${fmt(S.quarantine_size)}) until you empty it yourself.<br><code>${esc(S.quarantine)}</code></div><div class="row2"><button class="btn ghost" onclick="api('/api/open',{}).catch(e=>toast(e.message))">Open folder</button></div></section>
<button class="btn" onclick="save()">Save settings</button>`}
function draft(){const c=S.config;c.ollama_url=$("#url").value;c.model=$("#mdl").value;c.include_cache=$("#cache").checked}
function rmf(i){draft();S.config.folders.splice(i,1);setV()}
function addf(){draft();const v=$("#nf").value.trim();if(v)S.config.folders.push(v);setV()}
async function connect(){draft();await api("/api/config",S.config);await load()}
async function save(){draft();const r=await api("/api/config",S.config);toast(r.rejected.length?"Rejected (must be inside your home folder): "+r.rejected.join(", "):"Settings saved");await load()}
load();

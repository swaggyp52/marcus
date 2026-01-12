const API = (path)=>`http://127.0.0.1:8000${path}`

// Simple neon globe fallback: draw circle + nodes orbiting
const canvas = document.getElementById('globe')
const ctx = canvas.getContext('2d')
let W, H, cx, cy, R
const nodes = []

function resize(){
  W = canvas.width = canvas.clientWidth
  H = canvas.height = canvas.clientHeight
  cx = W/2; cy = H/2; R = Math.min(W,H)*0.36
}
window.addEventListener('resize', resize)
resize()

function fetchGraph(){
  fetch(API('/api/graph'))
    .then(r=>r.json())
    .then(j=>{
      // convert nodes to simple positions
      nodes.length=0
      for(let n of j.nodes){
        nodes.push({id:n.id,label:n.label,type:n.type,angle:Math.random()*Math.PI*2,dist: R*(0.6+Math.random()*0.4),speed:0.001+Math.random()*0.004})
      }
      document.getElementById('status-text').innerText = 'ready'
    }).catch(e=>{document.getElementById('status-text').innerText='backend offline'})
}
fetchGraph()

function draw(){
  ctx.clearRect(0,0,W,H)
  // background stars
  for(let i=0;i<40;i++){
    ctx.fillStyle='rgba(255,255,255,0.02)'; ctx.fillRect(Math.random()*W,Math.random()*H,1,1)
  }
  // globe
  const grd = ctx.createRadialGradient(cx,cy,R*0.1,cx,cy,R)
  grd.addColorStop(0,'rgba(124,0,255,0.08)'); grd.addColorStop(1,'rgba(0,0,0,0.2)')
  ctx.beginPath(); ctx.arc(cx,cy,R,0,Math.PI*2); ctx.fillStyle=grd; ctx.fill()
  // equator glow
  ctx.beginPath(); ctx.ellipse(cx,cy,R,R*0.28,0,0,Math.PI*2); ctx.strokeStyle='rgba(0,230,255,0.06)'; ctx.lineWidth=2; ctx.stroke()

  // nodes
  for(let n of nodes){
    n.angle += n.speed
    const x = cx + Math.cos(n.angle)*n.dist
    const y = cy + Math.sin(n.angle)*n.dist*0.6
    // glow
    ctx.beginPath(); ctx.fillStyle='rgba(0,230,255,0.12)'; ctx.arc(x,y,8,0,Math.PI*2); ctx.fill()
    ctx.beginPath(); ctx.fillStyle='rgba(124,0,255,0.9)'; ctx.arc(x,y,3,0,Math.PI*2); ctx.fill()
  }
  requestAnimationFrame(draw)
}
requestAnimationFrame(draw)

// Chat handlers
const log = document.getElementById('chat-log')
const form = document.getElementById('chat-form')
form.addEventListener('submit', async (e)=>{
  e.preventDefault(); const v = document.getElementById('chat-input').value
  if(!v) return
  appendMessage('you',v)
  document.getElementById('chat-input').value=''
  appendMessage('system','Thinking...')
  try{
    const res = await fetch(API('/api/chat'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v})})
    const j = await res.json()
    // remove last Thinking
    const last = log.lastElementChild; if(last && last.dataset?.role=='system'){ last.remove() }
    appendMessage('bot', JSON.stringify(j.results || j, null, 2))
    // refresh graph
    fetchGraph()
  }catch(err){
    appendMessage('bot','Error talking to backend')
  }
})

function appendMessage(who, text){
  const el = document.createElement('div'); el.className='msg '+who; el.textContent = (who== 'you' ? 'You: ' : who=='bot'? 'Marcus: ' : '') + text; el.dataset.role = who
  log.appendChild(el); log.scrollTop = log.scrollHeight
}

// upload
document.getElementById('uploadBtn').addEventListener('click', async ()=>{
  const f = document.getElementById('fileInput').files[0]; if(!f) return alert('Choose a file')
  const fd = new FormData(); fd.append('file',f)
  appendMessage('you','Uploading '+f.name)
  const r = await fetch(API('/api/upload'),{method:'POST',body:fd})
  const j = await r.json(); appendMessage('bot','Uploaded: '+(j.file_id||'ok')+' Tasks created: '+(j.created_tasks.length))
  fetchGraph()
})

// simple click hit test
canvas.addEventListener('click',(e)=>{
  const rect = canvas.getBoundingClientRect(); const x = e.clientX-rect.left; const y = e.clientY-rect.top
  for(let n of nodes){
    const nx = cx + Math.cos(n.angle)*n.dist
    const ny = cy + Math.sin(n.angle)*n.dist*0.6
    const d = Math.hypot(x-nx,y-ny)
    if(d<12){ appendMessage('bot','Clicked: '+n.label); break }
  }
})

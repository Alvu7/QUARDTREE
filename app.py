from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "0.0.0.0"
PORT = 8000

HTML = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Quadtree Lab en Python</title>
  <style>
    :root { --bg:#0a1020; --panel:#121c33; --text:#e7eeff; --muted:#9bb0d8; --a:#4fd1ff; --b:#8b7cff; }
    *{box-sizing:border-box} body{margin:0;font-family:Inter,system-ui,sans-serif;background:radial-gradient(circle at top,#13203d,var(--bg));color:var(--text)}
    .wrap{width:min(1200px,94vw);margin:auto;padding:1.2rem 0 2rem;display:grid;gap:1rem}
    .card{background:linear-gradient(170deg,var(--panel),#0d152a);border:1px solid #27385f;border-radius:16px;padding:1rem}
    h1{margin:.2rem 0 0} p,li{color:var(--muted)}
    .controls{display:flex;flex-wrap:wrap;gap:.6rem;align-items:center}
    button{background:linear-gradient(135deg,var(--a),var(--b));border:0;padding:.55rem .8rem;border-radius:10px;font-weight:700;cursor:pointer}
    .grid{display:grid;grid-template-columns:2fr 1fr;gap:1rem}
    @media(max-width:900px){.grid{grid-template-columns:1fr}}
    canvas{width:100%;background:#050a15;border:1px solid #23345a;border-radius:10px}
    .tree{max-height:460px;overflow:auto;font-family:ui-monospace,monospace;font-size:.85rem;color:#bfd0f7;white-space:pre}
    .stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.7rem;margin-top:.7rem}
    .stat{background:#0c1427;border:1px solid #22345d;border-radius:10px;padding:.6rem}
    .stat span{color:var(--muted);font-size:.8rem;display:block}
  </style>
</head>
<body>
  <main class="wrap">
    <section class="card"><h1>Quadtree Lab Interactivo</h1><p>Implementación servida por <strong>Python</strong>. Haz clic en el canvas para insertar puntos y observar subdivisiones.</p></section>
    <section class="card">
      <h2>Teoría rápida</h2>
      <ul>
        <li>Un Quadtree divide el espacio 2D en 4 subregiones: NW, NE, SW, SE.</li>
        <li>Cuando un nodo supera su capacidad, se subdivide recursivamente.</li>
        <li>Se usa en videojuegos, GIS/GPS, compresión de imágenes e IA espacial.</li>
      </ul>
    </section>
    <section class="card">
      <div class="controls">
        <button id="randomBtn">Insertar aleatorios</button>
        <button id="resetBtn">Reiniciar</button>
        <button id="stepBtn">Paso a paso: OFF</button>
        <label>Capacidad: <input id="cap" type="range" min="1" max="8" value="4"> <span id="capV">4</span></label>
      </div>
      <div class="grid">
        <div>
          <canvas id="cv" width="760" height="460"></canvas>
          <p id="msg">Listo para insertar puntos.</p>
          <div class="stats">
            <div class="stat"><span>Nodos</span><strong id="nodes">1</strong></div>
            <div class="stat"><span>Profundidad</span><strong id="depth">0</strong></div>
            <div class="stat"><span>Subdivisiones</span><strong id="subs">0</strong></div>
            <div class="stat"><span>Puntos</span><strong id="pts">0</strong></div>
          </div>
        </div>
        <aside class="card"><h3>Árbol jerárquico</h3><div id="tree" class="tree"></div></aside>
      </div>
    </section>
  </main>

<script>
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const msg = document.getElementById('msg'), tree = document.getElementById('tree');
const nodesEl = document.getElementById('nodes'), depthEl = document.getElementById('depth');
const subsEl = document.getElementById('subs'), ptsEl = document.getElementById('pts');
const cap = document.getElementById('cap'), capV = document.getElementById('capV');
const randomBtn = document.getElementById('randomBtn'), resetBtn = document.getElementById('resetBtn'), stepBtn = document.getElementById('stepBtn');
let capacity = +cap.value, points=[], subs=0, anim=[], queue=[], step=false;
const colors=['#7dd3fc','#60a5fa','#818cf8','#a78bfa','#f472b6','#fb7185','#f59e0b'];

class Node {
  constructor(x,y,w,h,d=0,l='ROOT'){ this.x=x; this.y=y; this.w=w; this.h=h; this.d=d; this.l=l; this.points=[]; this.div=false; }
  has(p){ return p.x>=this.x&&p.x<this.x+this.w&&p.y>=this.y&&p.y<this.y+this.h; }
  split(){ const hw=this.w/2, hh=this.h/2, d=this.d+1; this.nw=new Node(this.x,this.y,hw,hh,d,'NW'); this.ne=new Node(this.x+hw,this.y,hw,hh,d,'NE'); this.sw=new Node(this.x,this.y+hh,hw,hh,d,'SW'); this.se=new Node(this.x+hw,this.y+hh,hw,hh,d,'SE'); this.div=true; subs++; anim.push({n:this,t:0}); }
  insert(p,trail=[]){ if(!this.has(p)) return false; trail.push(this.l); if(!this.div && this.points.length<capacity){ this.points.push(p); return true; }
    if(!this.div){ this.split(); const old=[...this.points]; this.points=[]; old.forEach(op=>this.insert(op,[])); }
    return this.nw.insert(p,trail)||this.ne.insert(p,trail)||this.sw.insert(p,trail)||this.se.insert(p,trail);
  }
  collect(out=[]){ out.push(this); if(this.div)[this.nw,this.ne,this.sw,this.se].forEach(c=>c.collect(out)); return out; }
}
let root = new Node(0,0,cv.width,cv.height);

function ins(x,y){ const t=[]; points.push({x,y}); root.insert({x,y},t); msg.textContent=`Insertado (${x.toFixed(0)}, ${y.toFixed(0)}). Ruta: ${t.join(' → ')}`; refresh(); }
function drawNode(n){ ctx.strokeStyle=colors[n.d%colors.length]; ctx.strokeRect(n.x,n.y,n.w,n.h); if(n.div){ [n.nw,n.ne,n.sw,n.se].forEach(drawNode); ctx.fillStyle='rgba(190,210,255,.7)'; ctx.font='10px sans-serif'; ctx.fillText('NW',n.nw.x+3,n.nw.y+12); ctx.fillText('NE',n.ne.x+3,n.ne.y+12); ctx.fillText('SW',n.sw.x+3,n.sw.y+12); ctx.fillText('SE',n.se.x+3,n.se.y+12);} }
function drawPts(){ points.forEach(p=>{ctx.beginPath();ctx.arc(p.x,p.y,4,0,Math.PI*2);ctx.fillStyle='#fff';ctx.fill();}); }
function drawAnim(dt){ anim=anim.filter(a=>{a.t+=dt; const k=Math.min(1,a.t/380), n=a.n; ctx.strokeStyle=`rgba(255,120,120,${1-k*.2})`; ctx.lineWidth=2.3; ctx.strokeRect(n.x,n.y,n.w,n.h); ctx.beginPath(); ctx.moveTo(n.x+n.w/2,n.y+n.h/2); ctx.lineTo(n.x+n.w/2,n.y+n.h/2+n.h*(k-.5)); ctx.moveTo(n.x+n.w/2,n.y+n.h/2); ctx.lineTo(n.x+n.w/2+n.w*(k-.5),n.y+n.h/2); ctx.stroke(); return k<1;}); }
function treeText(n,p=''){ let s=`${p}${n.l} d=${n.d} pts=${n.points.length}\n`; if(n.div)s+=treeText(n.nw,p+'  ')+treeText(n.ne,p+'  ')+treeText(n.sw,p+'  ')+treeText(n.se,p+'  '); return s; }
function refresh(){ const all=root.collect([]); nodesEl.textContent=all.length; depthEl.textContent=Math.max(...all.map(n=>n.d)); subsEl.textContent=subs; ptsEl.textContent=points.length; tree.textContent=treeText(root); }
function reset(){ points=[]; subs=0; queue=[]; root=new Node(0,0,cv.width,cv.height); msg.textContent='Reiniciado.'; refresh(); }
let last=performance.now(); (function loop(now){ const dt=now-last; last=now; ctx.clearRect(0,0,cv.width,cv.height); drawNode(root); drawPts(); drawAnim(dt); requestAnimationFrame(loop); })(last);
cv.addEventListener('click',(e)=>{ const r=cv.getBoundingClientRect(); const x=(e.clientX-r.left)*(cv.width/r.width); const y=(e.clientY-r.top)*(cv.height/r.height); if(step){ queue.push([x,y]); msg.textContent=`En cola: ${queue.length}. Pulsa Paso a paso para insertar uno.`; } else ins(x,y); });
stepBtn.addEventListener('click',()=>{ step=!step; stepBtn.textContent=`Paso a paso: ${step?'ON':'OFF'}`; if(step&&queue.length){ const [x,y]=queue.shift(); ins(x,y);} });
randomBtn.addEventListener('click',()=>{ for(let i=0;i<20;i++) ins(Math.random()*cv.width,Math.random()*cv.height); });
resetBtn.addEventListener('click',reset);
cap.addEventListener('input',()=>{ capacity=+cap.value; capV.textContent=String(capacity); msg.textContent=`Capacidad=${capacity}. Reinicia para aplicarlo completamente.`; });
refresh();
</script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"404 - Not Found")


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), Handler)
    print(f"Servidor Quadtree en http://{HOST}:{PORT}")
    server.serve_forever()

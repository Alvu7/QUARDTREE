const canvas = document.getElementById('quadCanvas');
const ctx = canvas.getContext('2d');
const randomBtn = document.getElementById('randomBtn');
const resetBtn = document.getElementById('resetBtn');
const stepBtn = document.getElementById('stepBtn');
const searchBtn = document.getElementById('searchBtn');
const capSlider = document.getElementById('capacitySlider');
const capValue = document.getElementById('capacityValue');
const dynamicExplanation = document.getElementById('dynamicExplanation');
const treeView = document.getElementById('treeView');
const statsEl = {
  totalNodes: document.getElementById('totalNodes'),
  maxDepth: document.getElementById('maxDepth'),
  subdivisions: document.getElementById('subdivisions'),
  points: document.getElementById('pointsCount'),
};

const depthColors = ['#7dd3fc', '#60a5fa', '#818cf8', '#a78bfa', '#f472b6', '#fb7185', '#f59e0b'];
let capacity = Number(capSlider.value);
let points = [];
let subdivisions = 0;
let animations = [];
let stepMode = false;
let searchMode = false;
let queue = [];

class QuadNode {
  constructor(x, y, w, h, depth = 0, label = 'ROOT') {
    this.x = x; this.y = y; this.w = w; this.h = h; this.depth = depth; this.label = label;
    this.points = []; this.divided = false;
  }
  contains(p){ return p.x >= this.x && p.x < this.x + this.w && p.y >= this.y && p.y < this.y + this.h; }
  subdivide() {
    const hw = this.w / 2, hh = this.h / 2, d = this.depth + 1;
    this.nw = new QuadNode(this.x, this.y, hw, hh, d, 'NW');
    this.ne = new QuadNode(this.x + hw, this.y, hw, hh, d, 'NE');
    this.sw = new QuadNode(this.x, this.y + hh, hw, hh, d, 'SW');
    this.se = new QuadNode(this.x + hw, this.y + hh, hw, hh, d, 'SE');
    this.divided = true;
    subdivisions++;
    animateSubdivision(this);
  }
  insert(p, trail = []) {
    if (!this.contains(p)) return false;
    trail.push(this);
    if (!this.divided && this.points.length < capacity) {
      this.points.push(p);
      return true;
    }
    if (!this.divided) {
      this.subdivide();
      const oldPoints = [...this.points];
      this.points = [];
      oldPoints.forEach(op => this.insert(op, []));
    }
    return this.nw.insert(p, trail) || this.ne.insert(p, trail) || this.sw.insert(p, trail) || this.se.insert(p, trail);
  }
  collect(list = []) {
    list.push(this);
    if (this.divided) [this.nw, this.ne, this.sw, this.se].forEach(c => c.collect(list));
    return list;
  }
}

let root = new QuadNode(0, 0, canvas.width, canvas.height);

function animateSubdivision(node) { animations.push({ node, t: 0, dur: 380 }); }
function insertPoint(x,y){
  const p={x,y}; points.push(p);
  const trail=[];
  root.insert(p, trail);
  dynamicExplanation.textContent = `Insertado punto (${x.toFixed(0)}, ${y.toFixed(0)}). Recorrido: ${trail.map(n=>n.label).join(' → ')}.`;
  refresh();
}
function buildTreeText(node, pre=''){
  let txt = `${pre}${node.label} d=${node.depth} pts=${node.points.length}\n`;
  if(node.divided){ txt += buildTreeText(node.nw, pre+'  ') + buildTreeText(node.ne, pre+'  ') + buildTreeText(node.sw, pre+'  ') + buildTreeText(node.se, pre+'  '); }
  return txt;
}
function drawNode(n){
  const color = depthColors[n.depth % depthColors.length];
  ctx.strokeStyle = color;
  ctx.lineWidth = 1;
  ctx.strokeRect(n.x, n.y, n.w, n.h);
  if(n.divided){ [n.nw,n.ne,n.sw,n.se].forEach(drawNode); }
  if(n.divided){
    ctx.fillStyle = 'rgba(180,200,255,.65)';
    ctx.font = '10px Inter';
    ctx.fillText('NW', n.nw.x+4, n.nw.y+12);
    ctx.fillText('NE', n.ne.x+4, n.ne.y+12);
    ctx.fillText('SW', n.sw.x+4, n.sw.y+12);
    ctx.fillText('SE', n.se.x+4, n.se.y+12);
  }
}
function drawPoints(){
  points.forEach(p=>{
    ctx.beginPath(); ctx.arc(p.x,p.y,4,0,Math.PI*2); ctx.fillStyle='#f9fafb'; ctx.fill();
  });
}
function drawAnimations(dt){
  animations = animations.filter(a => {
    a.t += dt;
    const k = Math.min(1, a.t / a.dur);
    const n = a.node;
    ctx.save();
    ctx.strokeStyle = `rgba(255,130,130,${1-k*0.2})`;
    ctx.lineWidth = 2.5;
    ctx.strokeRect(n.x, n.y, n.w, n.h);
    ctx.beginPath();
    ctx.moveTo(n.x + n.w/2, n.y + n.h/2);
    ctx.lineTo(n.x + n.w/2, n.y + n.h/2 + n.h*(k-.5));
    ctx.moveTo(n.x + n.w/2, n.y + n.h/2);
    ctx.lineTo(n.x + n.w/2 + n.w*(k-.5), n.y + n.h/2);
    ctx.stroke();
    ctx.restore();
    return k < 1;
  });
}
let last = performance.now();
function loop(now){
  const dt = now-last; last=now;
  ctx.clearRect(0,0,canvas.width,canvas.height);
  drawNode(root); drawPoints(); drawAnimations(dt);
  requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

function refresh(){
  const all = root.collect([]);
  statsEl.totalNodes.textContent = all.length;
  statsEl.maxDepth.textContent = Math.max(...all.map(n=>n.depth));
  statsEl.subdivisions.textContent = subdivisions;
  statsEl.points.textContent = points.length;
  treeView.textContent = buildTreeText(root);
}

function reset(){
  points=[]; subdivisions=0; queue=[]; root = new QuadNode(0,0,canvas.width,canvas.height);
  dynamicExplanation.textContent='Simulación reiniciada. Inserta puntos para observar subdivisiones.';
  refresh();
}

canvas.addEventListener('click', e => {
  const rect = canvas.getBoundingClientRect();
  const x = (e.clientX - rect.left) * (canvas.width / rect.width);
  const y = (e.clientY - rect.top) * (canvas.height / rect.height);
  if (searchMode) {
    dynamicExplanation.textContent = `Búsqueda de punto objetivo en (${x.toFixed(0)}, ${y.toFixed(0)}): se recorre desde ROOT hasta la hoja que lo contiene.`;
    return;
  }
  if(stepMode){ queue.push([x,y]); dynamicExplanation.textContent = `Punto en cola (${queue.length}). Pulsa "Modo paso a paso" para insertar uno.`; }
  else insertPoint(x,y);
});

stepBtn.addEventListener('click', ()=>{
  stepMode = !stepMode;
  stepBtn.textContent = `Modo paso a paso: ${stepMode ? 'ON' : 'OFF'}`;
  if(stepMode && queue.length){ const [x,y] = queue.shift(); insertPoint(x,y); }
});
searchBtn.addEventListener('click', ()=>{
  searchMode = !searchMode;
  searchBtn.textContent = `Buscar punto: ${searchMode ? 'ON' : 'OFF'}`;
});
randomBtn.addEventListener('click', ()=>{
  for(let i=0;i<20;i++) insertPoint(Math.random()*canvas.width, Math.random()*canvas.height);
});
resetBtn.addEventListener('click', reset);
capSlider.addEventListener('input', ()=>{
  capacity = Number(capSlider.value);
  capValue.textContent = String(capacity);
  dynamicExplanation.textContent = `Capacidad actual por nodo: ${capacity}. Reinicia para aplicar en todo el árbol.`;
});

refresh();

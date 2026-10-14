#!/usr/bin/env python3
"""BrickForge AI host: HTTP + exporters + memory. Cognition lives in brain.py."""
import base64, json, math, os, time, io, zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import brain

ROOT=os.path.dirname(os.path.abspath(__file__)); WEB=os.path.join(ROOT,"web")
MEM=os.path.join(ROOT,"memory"); SNAP=os.path.join(MEM,"snaps"); os.makedirs(SNAP,exist_ok=True)
MEMF=os.path.join(MEM,"memory.json")
def load_mem():
    if os.path.exists(MEMF):
        try: return json.load(open(MEMF,encoding="utf-8"))
        except Exception: pass
    return {"bias":{},"palette_prior":[],"entries":[]}
def save_mem(m): json.dump(m,open(MEMF,"w",encoding="utf-8"),indent=1)

def ident(): return [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
def mul(a,b):
    r=[0]*16
    for i in range(4):
        for j in range(4): r[i*4+j]=sum(a[i*4+k]*b[k*4+j] for k in range(4))
    return r
def trans(x,y,z): m=ident(); m[3],m[7],m[11]=x,y,z; return m
def rot(ax,d):
    t=math.radians(d); c,s=math.cos(t),math.sin(t); m=ident()
    if ax==0: m[5],m[6],m[9],m[10]=c,-s,s,c
    if ax==1: m[0],m[2],m[8],m[10]=c,s,-s,c
    if ax==2: m[0],m[1],m[4],m[5]=c,-s,s,c
    return m
def apply(m,v):
    x,y,z=v; return [m[0]*x+m[1]*y+m[2]*z+m[3],m[4]*x+m[5]*y+m[6]*z+m[7],m[8]*x+m[9]*y+m[10]*z+m[11]]
SHAPES={"box":([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5),(-.5,.5,-.5),(.5,.5,-.5),(.5,.5,.5),(-.5,.5,.5)],
 [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]),
 "wedge":([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5),(-.5,.5,.5),(.5,.5,.5)],
 [(0,1,5,4),(2,3,4,5),(0,3,2,1),(0,4,3),(1,2,5)]),
 "pyramid":([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,-.5,.5),(-.5,-.5,.5),(0,.5,0)],
 [(0,3,2,1),(0,1,4),(1,2,4),(2,3,4),(3,0,4)]),
 "gem":([(.5,0,0),(-.5,0,0),(0,.5,0),(0,-.5,0),(0,0,.5),(0,0,-.5)],
 [(0,2,4),(2,1,4),(1,3,4),(3,0,4),(2,0,5),(1,2,5),(3,1,5),(0,3,5)]),
 "cylinder":([(.5*math.cos(i*math.pi/4),-.5,.5*math.sin(i*math.pi/4)) for i in range(8)]+
 [(.5*math.cos(i*math.pi/4),.5,.5*math.sin(i*math.pi/4)) for i in range(8)],
 [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]+[(0,1,2,3,4,5,6,7),(15,14,13,12,11,10,9,8)])}
def world_matrices(spec):
    M={}
    for q in spec["parts"]:
        ax=[i for i,v in enumerate(q["ro"]) if v]; m=trans(*q["po"])
        if ax: m=mul(m,rot(ax[0],q["ro"][ax[0]]))
        M[q["n"]]=mul(M[q["p"]],m) if q["p"] else m
    return M
def build_obj(spec):
    M=world_matrices(spec); lines=[]; mlines=[]; vi=1; seen=set()
    for q in spec["parts"]:
        V,F=SHAPES[q["s"]]; m=M[q["n"]]
        for v in V:
            w=apply(m,[v[0]*q["sz"][0],v[1]*q["sz"][1],v[2]*q["sz"][2]]); lines.append("v %.4f %.4f %.4f"%tuple(w))
        mk="mat_"+q["c"]
        if mk not in seen:
            seen.add(mk); hx=spec["palette"][q["c"]].lstrip("#")
            r,g,b=[int(hx[i:i+2],16)/255 for i in (0,2,4)]; mlines.append("newmtl %s\nKd %.3f %.3f %.3f"%(mk,r,g,b))
        lines.append("usemtl "+mk)
        for f in F:
            idx=[vi+i for i in f]
            for kk in range(1,len(f)-1): lines.append("f %d %d %d"%(idx[0],idx[kk],idx[kk+1]))
            if len(f)==3: lines.append("f %d %d %d"%tuple(idx))
        vi+=len(V)
    return "\n".join(lines)+"\n","\n".join(mlines)+"\n"
def build_lua(spec):
    L=[]; a=L.append
    a("-- %s | BrickForge AI | score %s/100"%(spec["name"],spec.get("score","?")))
    a("-- Motor6D rig. Run as Script in ServerScriptService.")
    a("local model=Instance.new('Model'); model.Name='%s'; local parts={}; local cf={}"%spec["name"])
    for q in spec["parts"]:
        cls={"wedge":"WedgePart","pyramid":"WedgePart"}.get(q["s"],"Part")
        hx=spec["palette"][q["c"]].lstrip("#"); r,g,b=[int(hx[i:i+2],16) for i in (0,2,4)]
        a("do local p=Instance.new('%s'); p.Name='%s'; p.Size=Vector3.new(%f,%f,%f)"%(cls,q["n"],*q["sz"]))
        a(" p.Color=Color3.fromRGB(%d,%d,%d); p.TopSurface='Smooth'; p.BottomSurface='Smooth'"%(r,g,b))
        a(" p.CFrame=(%s)*CFrame.new(%f,%f,%f)*CFrame.Angles(math.rad(%f),math.rad(%f),math.rad(%f))"%(
            ("cf['%s']"%q["p"]) if q["p"] else "CFrame.new(0,2,0)",*q["po"],*q["ro"]))
        a(" p.Massless=true; p.Parent=model; parts['%s']=p; cf['%s']=p.CFrame end"%(q["n"],q["n"]))
    for q in spec["parts"]:
        if q["p"]:
            a("do local m=Instance.new('Motor6D'); m.Name='J_%s'; m.Part0=parts['%s']; m.Part1=parts['%s']; m.C0=cf['%s']:Inverse()*cf['%s']; m.C1=CFrame.new(); m.Parent=parts['%s'] end"%(
                q["n"],q["p"],q["n"],q["p"],q["n"],q["p"]))
    a("local hum=Instance.new('Humanoid'); hum.Parent=model; model.PrimaryPart=parts['%s']; model.Parent=workspace"%spec["root"])
    return "\n".join(L)+"\n"
def make_zip(spec,snap):
    buf=io.BytesIO(); obj,mtl=build_obj(spec)
    with zipfile.ZipFile(buf,"w",zipfile.ZIP_DEFLATED) as z:
        z.writestr(spec["name"]+"_rig.lua",build_lua(spec)); z.writestr(spec["name"]+".obj",obj)
        z.writestr(spec["name"]+".mtl",mtl); z.writestr("spec.json",json.dumps(spec,indent=1))
        if snap:
            try: z.writestr("preview.png",base64.b64decode(snap.split(",",1)[1]))
            except Exception: pass
        z.writestr("HOW_TO_IMPORT.txt","Run the .lua in Roblox Studio for the rigged model; import .obj for static mesh.\n")
    return buf.getvalue()

CT={".html":"text/html",".css":"text/css",".js":"application/javascript",".png":"image/png"}
class H(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def _send(self,d,ct="application/json",code=200,extra=None):
        self.send_response(code); self.send_header("Content-Type",ct); self.send_header("Content-Length",str(len(d)))
        for k,v in (extra or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(d)
    def do_GET(self):
        p=self.path.split("?")[0]
        if p=="/api/memory":
            m=load_mem()
            return self._send(json.dumps({"entries":[{k:e.get(k) for k in
                ("id","name","prompt","archetype","ts","snap","spec","style")} for e in m["entries"]][::-1],
                "stats":{"liked":len(m["entries"]),"bias":m["bias"]}}).encode())
        if p.startswith("/memory/snaps/"):
            fp=os.path.join(SNAP,os.path.basename(p))
            return self._send(open(fp,"rb").read(),"image/png") if os.path.exists(fp) else self._send(b"",404 and "text/plain",404)
        fp=os.path.join(WEB,"index.html" if p in ("/","") else p.lstrip("/"))
        if os.path.isfile(fp): return self._send(open(fp,"rb").read(),CT.get(os.path.splitext(fp)[1],"application/octet-stream"))
        self._send(b"not found","text/plain",404)
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); body=json.loads(self.rfile.read(n) or b"{}")
        if self.path=="/api/generate": return self._send(json.dumps(brain.generate(body,load_mem())).encode())
        if self.path=="/api/vote":
            m=load_mem(); spec=body.get("spec",{}); arch=spec.get("archetype","?")
            if body.get("vote")=="yes":
                sid=spec.get("id","m%x"%int(time.time())); fn=sid+".png"
                if body.get("snapshot"):
                    try: open(os.path.join(SNAP,fn),"wb").write(base64.b64decode(body["snapshot"].split(",",1)[1]))
                    except Exception: fn=None
                m["entries"].append({"id":sid,"ts":int(time.time()),"prompt":body.get("prompt",""),"name":spec.get("name"),
                    "archetype":arch,"snap":("/memory/snaps/"+fn) if fn else None,"palette":spec.get("palette"),
                    "style":brain.style_vector(spec),"spec":spec})
                m["bias"][arch]=m["bias"].get(arch,0)+2; save_mem(m)
                return self._send(json.dumps({"ok":True,"saved":True}).encode())
            m["bias"][arch]=max(-4,m["bias"].get(arch,0)-1); save_mem(m)
            return self._send(json.dumps({"ok":True,"saved":False}).encode())
        if self.path=="/api/export":
            return self._send(make_zip(body.get("spec",{}),body.get("snapshot")),"application/zip",200,
                              {"Content-Disposition":"attachment; filename=BrickForge_model.zip"})
        self._send(b"{}","application/json",404)
if __name__=="__main__":
    port=int(os.environ.get("PORT",8000)); print("BrickForge AI brain online → http://localhost:%d"%port)
    ThreadingHTTPServer(("127.0.0.1",port),H).serve_forever()

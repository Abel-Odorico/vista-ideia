import numpy as np, subprocess, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W,H,FPS = 1080,1920,30
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UP=os.path.join(ROOT,'assets','fotos')+'/'; F=os.path.join(ROOT,'assets','fonts')+'/'
NAVY=(12,27,54); CREAM=(244,239,228); TEXT=(248,244,236)

def ease(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def eio(t): t=max(0,min(1,t)); return 4*t**3 if t<.5 else 1-(-2*t+2)**3/2
def eout(t): t=max(0,min(1,t)); return 1-(1-t)**3
def font(w,s): return ImageFont.truetype(F+f'Montserrat-{w}.ttf',s)

def tracked(draw,xy,txt,fnt,fill,track,anchor_center=True):
    widths=[draw.textlength(c,font=fnt) for c in txt]
    total=sum(widths)+track*(len(txt)-1)
    x=xy[0]-total/2 if anchor_center else xy[0]
    for c,w in zip(txt,widths):
        draw.text((x,xy[1]),c,font=fnt,fill=fill); x+=w+track
    return total

# ---------- logo ----------
MARK=Image.open(os.path.join(ROOT,'assets','logo','mark.png')); WORD=Image.open(os.path.join(ROOT,'assets','logo','word.png'))
def logo_layer(color, mark_w, reveal=1.0, word_op=1.0, word_track=0.0):
    """RGBA full-frame with Vi mark revealed bottom->top and wordmark."""
    lay=Image.new('RGBA',(W,H),(0,0,0,0))
    mh=int(MARK.height*mark_w/MARK.width)
    m=np.asarray(MARK.resize((mark_w,mh),Image.LANCZOS)).astype(float)/255
    # soft wipe from bottom
    edge=60; y=np.arange(mh)[:,None]
    cut=mh-(mh+edge)*reveal
    g=np.clip((y-cut)/edge,0,1)
    a=(m*g*255).astype('uint8')
    mk=Image.new('RGBA',(mark_w,mh),color+(0,)); mk.putalpha(Image.fromarray(a))
    top=int(H*0.40-mh/2)-60
    lay.alpha_composite(mk,((W-mark_w)//2,top))
    ww=int(mark_w*1.05*(1+word_track)); wh=int(WORD.height*ww/WORD.width)
    wm=WORD.resize((ww,wh),Image.LANCZOS).point(lambda v:int(v*word_op))
    wl=Image.new('RGBA',(ww,wh),color+(0,)); wl.putalpha(wm)
    lay.alpha_composite(wl,((W-ww)//2, top+mh+70))
    return lay, top+mh+70+wh

# ---------- scenes ----------
def load(n): return Image.open(UP+n).convert('RGB')
class Shot:
    def __init__(s,img,z0,z1,c0,c1):
        s.im=load(img); s.k=max(W/s.im.width,H/s.im.height)
        s.z0,s.z1,s.c0,s.c1=z0,z1,c0,c1
    def frame(s,t):
        e=eio(t); z=s.z0+(s.z1-s.z0)*e
        cx=s.c0[0]+(s.c1[0]-s.c0[0])*e; cy=s.c0[1]+(s.c1[1]-s.c0[1])*e
        sc=1/(s.k*z); hw,hh=W/2*sc,H/2*sc
        cx=min(max(cx,hw),s.im.width-hw); cy=min(max(cy,hh),s.im.height-hh)
        return s.im.transform((W,H),Image.AFFINE,(sc,0,cx-hw,0,sc,cy-hh),resample=Image.BICUBIC)

shots={
 'dark':Shot('IMG_3239.jpeg',1.00,1.14,(760,1000),(560,980)),
 'light':Shot('IMG_3241.jpeg',1.10,1.00,(540,1080),(700,1050)),
 'open':Shot('IMG_3243.jpeg',1.05,1.18,(1100,1200),(1620,1180)),
 'roll':Shot('IMG_3244.jpeg',1.00,1.14,(820,1150),(1050,980)),
 'shirt':Shot('IMG_3246.jpeg',1.08,1.00,(830,1150),(860,1250)),
 'wear':Shot('IMG_0567.jpeg',1.75,1.00,(830,840),(840,1195)),
}
# timeline: (name, start, end)
TL=[('dark',1.9,4.1),('light',3.8,6.2),('open',5.9,8.5),('roll',8.2,10.4),('shirt',10.1,12.9),('wear',12.6,15.9)]
CAPS=[('01','A chegada',2.2,5.9),('02','O cuidado',6.2,8.2),('03','Os detalhes',8.5,10.1),('04','A peça',10.4,12.6),('05','Vestida de verdade',12.9,15.4)]
DUR=19.0; XF=0.3

# bottom gradient for legibility
gy=np.linspace(0,1,H)[:,None]
grad_a=(np.clip((gy-0.6)/0.4,0,1)**1.6*120).astype('uint8')
GRAD=Image.new('RGBA',(W,H),(8,12,22,0)); GRAD.putalpha(Image.fromarray(np.repeat(grad_a,W,1)))
# vignette
yy,xx=np.mgrid[0:H,0:W]; r=np.sqrt(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)
VIG=Image.new('RGBA',(W,H),(0,0,0,0)); VIG.putalpha(Image.fromarray((np.clip((r-0.75)/0.6,0,1)*110).astype('uint8')))
rng=np.random.default_rng(7)
GRAINS=[Image.fromarray(np.clip(128+rng.normal(0,30,(H//2,W//2)),0,255).astype('uint8')).resize((W,H)).convert('RGB') for _ in range(6)]

# caption layers
def cap_layer(num,txt,y0=1290):
    lay=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(lay)
    fb=font('Medium',56); fs=font('SemiBold',24)
    tw=sum(d.textlength(c,font=fb) for c in txt)+3*(len(txt)-1)
    cw=int(max(tw,180)+120); ch=170; x0=(W-cw)//2
    sh=Image.new('RGBA',(W,H),(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle([x0,y0+12,x0+cw,y0+ch+12],radius=34,fill=(0,0,0,110))
    lay.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d.rounded_rectangle([x0,y0,x0+cw,y0+ch],radius=34,fill=CREAM+(246,))
    tracked(d,(W/2,y0+30),f'{num}  /  05',fs,NAVY+(150,),9)
    tracked(d,(W/2,y0+66),txt,fb,NAVY+(255,),3)
    return lay
CAPL=[cap_layer(n,t,330 if n=='02' else 1290) for n,t,_,_ in CAPS]

def with_op(rgba,op):
    o=rgba.copy(); o.putalpha(rgba.getchannel('A').point(lambda v:int(v*op))); return o

intro_word_tag=None
def intro(t):  # 0..2.2 cream with logo reveal
    bg=Image.new('RGBA',(W,H),CREAM+(255,))
    lay,yb=logo_layer(NAVY,520,reveal=eout((t-0.15)/0.9),word_op=ease((t-0.7)/0.5),word_track=0.25*(1-eout((t-0.7)/0.9)))
    bg.alpha_composite(lay)
    tl=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(tl); op=ease((t-1.0)/0.4)
    tracked(d,(W/2,yb+90),'UNBOXING',font('Medium',30),NAVY+(int(180*op),),14)
    bg.alpha_composite(tl); return bg

def outro(t):
    bg=Image.new('RGBA',(W,H),NAVY+(255,))
    lay,yb=logo_layer(CREAM,440,reveal=eout((t-0.2)/0.9),word_op=ease((t-0.8)/0.5),word_track=0.25*(1-eout((t-0.8)/0.9)))
    bg.alpha_composite(lay)
    tl=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(tl); op=ease((t-1.3)/0.5)
    tracked(d,(W/2,yb+110),'Obrigado por escolher',font('Light',40),CREAM+(int(235*op),),3)
    tracked(d,(W/2,yb+165),'a Vista Ideia.',font('Light',40),CREAM+(int(235*op),),3)
    bg.alpha_composite(tl); return bg

def scene_at(t):
    frame=None
    for name,s,e in TL:
        if s<=t<=e:
            img=shots[name].frame((t-s)/(e-s)).convert('RGBA')
            if name=='dark':  # lights-on bloom into next shot
                pass
            a=ease((t-s)/XF) if s>TL[0][1] else 1.0
            if frame is None: frame=img
            else: frame=Image.blend(frame,img,a)
    return frame

proc=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-',
    '-c:v','libx264','-preset','slow','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',
    os.path.join(ROOT,'output','vista_ideia_unboxing.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
N=int(DUR*FPS)
for i in range(N):
    t=i/FPS
    if t<1.9: fr=intro(t)
    else:
        fr=scene_at(min(t,15.9))
        # warm flash at dark->light
        fl=max(0,1-abs(t-3.95)/0.28)
        if fl>0: fr=Image.blend(fr,Image.new('RGBA',(W,H),(255,246,228,255)),0.55*fl)
        fr.alpha_composite(GRAD); fr.alpha_composite(VIG)
        for L,(_,_,cs,ce) in zip(CAPL,CAPS):
            if cs<=t<=ce:
                op=min(ease((t-cs)/0.35),ease((ce-t)/0.3))
                dy=int(30*(1-eout((t-cs)/0.5)))
                lay=with_op(L,op)
                if dy: lay=lay.transform((W,H),Image.AFFINE,(1,0,0,0,1,-dy))
                fr.alpha_composite(lay)
        # intro curtain: cream panel slides up off screen
        if t<2.55:
            p=eio((t-1.9)/0.65); off=int(-H*p)
            ip=intro(1.9+ (t-1.9)*0.3)
            fr.alpha_composite(ip,(0,off)) if off>-H else None
        # outro curtain: navy panel rises from bottom
        if t>=15.6:
            p=eio((t-15.6)/0.6); off=int(H*(1-p))
            fr.alpha_composite(outro(max(0,t-16.0)),(0,off))
    fr=fr.convert('RGB')
    fr=Image.blend(fr,GRAINS[i%6],0.035)
    proc.stdin.write(fr.tobytes())
    if i==int(2.0*FPS) and False: pass
    if i==50: fr.save(os.path.join(ROOT,'output','capa_reels.jpg'),quality=92)
proc.stdin.close(); proc.wait(); print('done')

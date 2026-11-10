import numpy as np, sys
SONIC = len(sys.argv) > 1 and sys.argv[1] == 'sonic'
from PIL import Image, ImageDraw, ImageFilter
from scipy.ndimage import distance_transform_edt, gaussian_filter, label
S=1024; rng=np.random.default_rng(7)
y,x=np.mgrid[0:S,0:S]/S
n=gaussian_filter(rng.normal(0,1,(S,S)),40); n=(n+n[:,::-1])/2; n/=np.abs(n).max()
core=(np.hypot(x-.5,y-.5)<0.2) if SONIC else (np.hypot((x-.5)*1.15,(y-.5))+0.06*n<0.27)
d=distance_transform_edt(~core)
SAGE=np.array([0x73,0xAE,0x8A],float)
lvl=np.zeros((S,S))
for i,t in enumerate([0,14,30,48,68,90,114,140,168,198]): lvl[d>t]=i+1
img=SAGE[None,None,:]*np.clip(1-0.085*lvl,0.12,1)[...,None]*1.08
g=gaussian_filter(lvl,1.2); gy,gx=np.gradient(g); img+=(-(gx+gy)*55)[...,None]
im=Image.fromarray(np.clip(img,0,255).astype(np.uint8),'RGB').convert('RGBA')
m=Image.new('L',(S,S),0); ImageDraw.Draw(m).rounded_rectangle((100,100,924,924),185,fill=255)
sh=Image.new('L',(S,S),0); ImageDraw.Draw(sh).rounded_rectangle((100,112,924,936),185,fill=120)
out=Image.new('RGBA',(S,S),(0,0,0,0)); out.paste((0,0,0,255),(0,0),sh.filter(ImageFilter.GaussianBlur(14)))
body=Image.new('RGBA',(S,S),(0,0,0,0)); body.paste(im,(0,0),m); out=Image.alpha_composite(out,body)
ImageDraw.Draw(out).rounded_rectangle((100,100,924,924),185,outline=(20,40,28,255),width=4)
logo=Image.open('src/oblq_logo.png').convert('RGBA')
a=np.asarray(logo.crop((179,0,224,logo.size[1]))).copy()
lab,k=label(a[...,3]>20); big=1+int(np.argmax([(lab==i).sum() for i in range(1,k+1)]))
a[...,3]=np.where(lab==big,a[...,3],0)
s=Image.fromarray(a); s=s.crop(s.getbbox())
sc=520/s.size[1]; s=s.resize((int(s.size[0]*sc),520),Image.NEAREST)
px,py=(S-s.size[0])//2,(S-520)//2
shadow=Image.new('RGBA',out.size,(0,0,0,0)); shadow.paste((0,0,0,255),(px+10,py+14),s.split()[3].point(lambda v:int(v*.6)))
out=Image.alpha_composite(out,shadow.filter(ImageFilter.GaussianBlur(8))); out.alpha_composite(s,(px,py))
if SONIC:                                               # points flying round the listener
    d=ImageDraw.Draw(out)
    import math
    for k,(rr,a) in enumerate([(300,20),(330,95),(270,160),(345,215),(295,290),(320,340)]):
        cx,cy=512+rr*math.cos(math.radians(a)),512-rr*math.sin(math.radians(a))
        col=[(170,255,190),(255,90,70),(255,200,90)][k%3]
        d.ellipse((cx-17,cy-17,cx+17,cy+17),fill=(0,0,0,150)); d.ellipse((cx-13,cy-14,cx+13,cy+12),fill=col+(255,))
out.save('app/icon_sonic.png' if SONIC else 'app/icon.png')

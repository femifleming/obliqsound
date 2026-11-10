# 8 s seamless stereo loops (16-bit, 44.1k) cut from the middle of each recording
import sys, os, subprocess, numpy as np, re
SRC = os.path.expanduser('~/Desktop/Folders/Realmorereal/Campbinet_NewSamples')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'samples')
SR, LEN, XF = 44100, 8.0, 0.5
RENAME = {'202610251258Recordingw':'recording_oct25','embodieslisteningexper':'embodied_listening','somethingtosampleyeste':'show_sample',
          'oneofthebitchesjun10':'oneofthebitches','Tent_Talk22':'Tent_Talk3','hydrophone22':'hydrophone3','wingieintoNorns_drone':'wingie_into_norns'}
names = []
for f in sorted(os.listdir(SRC)):
    if not f.lower().endswith('.wav'): continue
    dur = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',os.path.join(SRC,f)]))
    seg = min(LEN + XF, dur)
    start = max(0, dur/2 - seg/2)
    raw = subprocess.check_output(['ffmpeg','-v','error','-ss',str(start),'-t',str(seg),'-i',os.path.join(SRC,f),
                                   '-ac','2','-ar',str(SR),'-f','f32le','-'])
    x = np.frombuffer(raw, np.float32).reshape(-1,2).astype(np.float64)
    n = int(min(LEN, len(x)/SR - XF) * SR); xf = int(XF*SR)
    y = x[:n].copy()
    t = np.linspace(0, np.pi/2, xf)[:,None]
    y[:xf] = x[:xf]*np.sin(t) + x[n:n+xf]*np.cos(t)      # equal-power loop crossfade
    y /= max(1e-9, np.abs(y).max()) / 0.89                 # normalise to -1 dBFS
    base = re.sub(r'(jun|june)?2026.*|\.wav', '', f, flags=re.I).strip(' _').replace(' ', '_') or f
    name = re.sub(r'[^A-Za-z0-9_]', '', base)[:22]
    while name in names: name += '2'
    name = RENAME.get(name, name)
    names.append(name)
    pcm = (np.clip(y, -1, 1) * 32767).astype('<i2').tobytes()
    subprocess.run(['ffmpeg','-v','error','-y','-f','s16le','-ar',str(SR),'-ac','2','-i','-','-c:a','pcm_s16le',
                    os.path.join(OUT, name + '.wav')], input=pcm, check=True)
    print(f'{name:24} <- {f}  ({start:.1f}s..{start+n/SR:.1f}s)')
open(os.path.join(OUT,'index.txt'),'w').write('\n'.join(names))

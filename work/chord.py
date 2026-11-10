import sys, numpy as np, warnings; warnings.filterwarnings('ignore'); from scipy.io import wavfile
sr,x=wavfile.read(sys.argv[1]); t0=float(sys.argv[2]) if len(sys.argv)>2 else 0.6; t1=float(sys.argv[3]) if len(sys.argv)>3 else 1.4
m=x[int(t0*sr):int(t1*sr)].astype(float).mean(axis=1)
S=np.abs(np.fft.rfft(m*np.hanning(len(m)))); f=np.fft.rfftfreq(len(m),1/sr)
def pk(fr): return S[(abs(f-fr)<3)].max()
ref=S[(f>150)&(f<500)].max()
out=[]
for nm,fr in (('C',261.63),('E',329.63),('G',392.0)):
    out.append(f'{nm}:{20*np.log10(pk(fr)/ref+1e-9):5.1f}dB')
print(' '.join(out), ' rms %.4f'%np.sqrt(np.mean(m**2)))

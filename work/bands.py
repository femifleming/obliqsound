import sys, numpy as np, warnings; warnings.filterwarnings('ignore'); from scipy.io import wavfile
sr,x=wavfile.read(sys.argv[1]); x=x.astype(float); m=x[int(.4*sr):int(1.4*sr),0]
S=np.abs(np.fft.rfft(m))**2; f=np.fft.rfftfreq(len(m),1/sr)
cs=[100,250,500,800,1000,1250,2000,4000,8000]
e=[S[(f>c/1.15)&(f<c*1.15)].mean() for c in cs]; ref=max(e)
print(' '.join(f'{c}:{10*np.log10(v/ref+1e-12):4.0f}' for c,v in zip(cs,e)))

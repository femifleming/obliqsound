import sys, numpy as np, warnings; warnings.filterwarnings('ignore'); from scipy.io import wavfile
sr,x=wavfile.read(sys.argv[1]); f0=float(sys.argv[2]); ch=int(sys.argv[3]) if len(sys.argv)>3 else 0
x=x.astype(float); m=x[int(.6*sr):int(1.3*sr),ch]
S=np.abs(np.fft.rfft(m*np.hanning(len(m)))); f=np.fft.rfftfreq(len(m),1/sr)
h=np.array([S[(abs(f-f0*k)<4)].max() for k in range(1,17)])
d=20*np.log10(h/h[0]+1e-9)
print(' '.join(f'{v:4.0f}' for v in d))

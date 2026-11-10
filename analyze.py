import sys, numpy as np
from scipy.io import wavfile
sr, x = wavfile.read(sys.argv[1]); x = x.astype(float)/2**31
m = x.mean(axis=1)
t0, t1 = float(sys.argv[2]) if len(sys.argv)>2 else 0.6, float(sys.argv[3]) if len(sys.argv)>3 else 1.4
seg = m[int(t0*sr):int(t1*sr)] * np.hanning(int(t1*sr)-int(t0*sr))
S = np.abs(np.fft.rfft(seg, 1<<18)); f = np.fft.rfftfreq(1<<18, 1/sr)
band = (f>float(sys.argv[4]) if len(sys.argv)>4 else f>25)&(f<1500)
idx = np.argsort(S[band])[::-1]
fb = f[band]; Sb = S[band]
peaks=[]
for i in idx:
    if all(abs(fb[i]-p)>8 for p,_ in peaks): peaks.append((fb[i],Sb[i]))
    if len(peaks)>=8: break
print("peaks:", ", ".join(f"{p:.1f}Hz({a/peaks[0][1]:.2f})" for p,a in sorted(peaks)))
# envelope per 100ms
env = [np.sqrt(np.mean(m[i:i+sr//10]**2)) for i in range(0,len(m),sr//10)]
print("env:", " ".join(f"{e*1000:.0f}" for e in env))

import sys,numpy as np; from scipy.io import wavfile
sr,x=wavfile.read(sys.argv[1]); m=x.mean(1)/2**31
print(' '.join(f'{np.sqrt(np.mean(m[i:i+sr//20]**2))*1000:.0f}' for i in range(0,len(m),sr//20)))

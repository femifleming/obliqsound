import sys, numpy as np; from scipy.io import wavfile
import warnings; warnings.filterwarnings('ignore')
sr,x=wavfile.read(sys.argv[1]); x=x.astype(float)
print('rms %.5f peak %.4f' % (np.sqrt(np.mean(x**2)), np.abs(x).max()))

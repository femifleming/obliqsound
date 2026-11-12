import subprocess, sys, time
host, plug = sys.argv[1], sys.argv[2]
notes = ','.join(f'{40+(i*5)%40}:{0.5+i/16:.3f}:0.4:100' for i in range(160))
def run(secs):
    t = time.time(); subprocess.run([host, plug, '--wav', '/tmp/obliq_flood.wav', '--secs', str(secs), '--notes', notes], capture_output=True); return time.time() - t
a = min(run(2), run(2)); b = min(run(12), run(12))
print(f'{plug.split("/")[-1]}: 16 notes/s flood = {(b - a) / 10 * 100:.1f}% of real time  (start-up {a:.1f} s)')

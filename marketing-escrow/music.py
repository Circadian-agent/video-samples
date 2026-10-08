# Original warm ambient bed: soft pad chords + sparse pentatonic plucks. Pure Python, 44.1 kHz mono.
import math, wave, struct, random
SR, DUR = 44100, 36.0
N = int(SR*DUR); out = [0.0]*N
def f(n): return 440*2**((n-69)/12)
chords = [[48,55,64,67],[45,52,60,64],[41,48,57,60],[43,50,59,62],[48,55,64,72],[48,55,64,67]]
seg = 7.0
for ci, ch in enumerate(chords):
    t0 = ci*seg; t1 = min(DUR, t0+seg+1.5)
    for n in ch:
        fr = f(n); a = 0.045
        for i in range(int(t0*SR), int(t1*SR)):
            t = i/SR - t0; L = t1-t0
            env = min(1, t/1.8) * min(1, max(0,(L-t))/1.8)
            s = math.sin(2*math.pi*fr*i/SR) + 0.25*math.sin(2*math.pi*2*fr*i/SR + 0.3)
            out[i] += a*env*s*(0.85+0.15*math.sin(2*math.pi*0.2*t+n))
random.seed(7)
penta = [60,62,64,67,69,72,74,76]
t = 2.0
while t < DUR-3:
    n = random.choice(penta); fr = f(n)
    for i in range(int(t*SR), min(N, int((t+2.5)*SR))):
        u = i/SR - t
        out[i] += 0.09*math.exp(-u*2.2)*min(1,u*200)*(math.sin(2*math.pi*fr*u)+0.3*math.sin(2*math.pi*3*fr*u)*math.exp(-u*6))
    t += random.choice([0.875,1.75,1.75,2.625])
# simple echo for space
d = int(0.32*SR)
for i in range(d, N): out[i] += 0.28*out[i-d]
fade = int(2.5*SR)
for i in range(fade): out[N-1-i] *= i/fade
pk = max(abs(x) for x in out)
w = wave.open("music.wav","wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
w.writeframes(b"".join(struct.pack("<h", int(x/pk*0.8*32767)) for x in out)); w.close()

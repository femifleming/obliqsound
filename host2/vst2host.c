// minimal VST2 host: load, print id/params, play a chord, report output level
#include <dlfcn.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <CoreFoundation/CoreFoundation.h>
typedef struct AEffect AEffect;
typedef intptr_t (*Disp)(AEffect*, int32_t, int32_t, intptr_t, void*, float);
typedef void (*Proc)(AEffect*, float**, float**, int32_t);
struct AEffect { int32_t magic; Disp dispatcher; void* process; void* setParameter; void* getParameter;
  int32_t numPrograms, numParams, numInputs, numOutputs, flags; intptr_t r1, r2; int32_t initialDelay, rq, oq; float ioRatio;
  void* object; void* user; int32_t uniqueID, version; Proc processReplacing; };
typedef struct { int32_t type, byteSize, deltaFrames, flags, noteLength, noteOffset; char midiData[4]; char detune, noteOffVelocity, r1, r2; } VstMidiEvent;
typedef struct { int32_t numEvents; intptr_t reserved; void* events[8]; } VstEvents;
static intptr_t host(AEffect* e, int32_t op, int32_t idx, intptr_t v, void* p, float o) { return op == 1 ? 2400 : 0; }
int main(int argc, char** argv) {
  CFURLRef url = CFURLCreateFromFileSystemRepresentation(NULL, (const UInt8*)argv[1], strlen(argv[1]), true);
  CFBundleRef b = CFBundleCreate(NULL, url);
  if (!b || !CFBundleLoadExecutable(b)) { printf("load failed\n"); return 1; }
  AEffect* (*main_)(void*) = CFBundleGetFunctionPointerForName(b, CFSTR("VSTPluginMain"));
  if (!main_) { printf("no VSTPluginMain\n"); return 1; }
  AEffect* e = main_(host);
  if (!e || e->magic != 0x56737450) { printf("bad effect\n"); return 1; }
  uint32_t id = (uint32_t)e->uniqueID;
  printf("uniqueID=%u ('%c%c%c%c') params=%d outs=%d flags=0x%x\n", id, id>>24, (id>>16)&255, (id>>8)&255, id&255, e->numParams, e->numOutputs, e->flags);
  char name[256] = {0}; e->dispatcher(e, 45, 0, 0, name, 0); printf("effectName=%s\n", name);
  e->dispatcher(e, 0, 0, 0, 0, 0); e->dispatcher(e, 10, 0, 0, 0, 48000.f); e->dispatcher(e, 11, 0, 512, 0, 0); e->dispatcher(e, 12, 0, 1, 0, 0);
  float l[512], r[512], *outs[2] = {l, r}, inb[512] = {0}, *ins[2] = {inb, inb};
  double sum = 0, peak = 0; int n = 0;
  for (int blk = 0; blk < 94 * 4; blk++) {           // ~4 s
    if (blk == 94) {                                  // chord after 1 s of warm-up
      static VstMidiEvent ev[3]; static VstEvents evs; evs.numEvents = 3;
      int notes[3] = {60, 64, 67};
      for (int i = 0; i < 3; i++) { memset(&ev[i], 0, sizeof ev[i]); ev[i].type = 1; ev[i].byteSize = sizeof ev[i];
        ev[i].midiData[0] = 0x90; ev[i].midiData[1] = notes[i]; ev[i].midiData[2] = 100; evs.events[i] = &ev[i]; }
      e->dispatcher(e, 25, 0, 0, &evs, 0);
    }
    memset(l, 0, sizeof l); memset(r, 0, sizeof r);
    e->processReplacing(e, ins, outs, 512);
    if (blk > 100) for (int i = 0; i < 512; i++) { sum += l[i] * l[i] + r[i] * r[i]; n += 2; peak = fmax(peak, fabs(l[i])); }
    usleep(2000);
  }
  printf("chord: rms=%.4f peak=%.4f\n", sqrt(sum / n), peak);
  e->dispatcher(e, 12, 0, 0, 0, 0); e->dispatcher(e, 1, 0, 0, 0, 0);
  return 0;
}

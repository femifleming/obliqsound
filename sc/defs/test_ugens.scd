var out = thisProcess.argv[0];
SynthDef(\tfilt, { |freq = 110, cut = 800, res = 0.5, mode = 0, gain = 0.5| Out.ar(0, OblqFilter.ar(Saw.ar(freq), cut, res, mode, gain) * 0.2 ! 2) }).writeDefFile(out);
SynthDef(\tpoly, { |freq = 110, order = 5| Out.ar(0, OblqPoly.ar(freq, order, 0.2, 0, 2, 0.3, 0, 0) * 0.2) }).writeDefFile(out);
SynthDef(\tadd, { |freq = 110, partials = 64| Out.ar(0, OblqAdd.ar(freq, partials, 0.5, 0.2, 0.3, 0.2, 0.5, 2, 1, 255) * 0.2) }).writeDefFile(out);
SynthDef(\tenc, { |freq = 220, x = 0, y = 2, z = 0| Out.ar(0, OblqEncode.ar(SinOsc.ar(freq) * 0.3, x, y, z, 0, 0, 0, 2)) }).writeDefFile(out);
"ok".postln; 0.exit;

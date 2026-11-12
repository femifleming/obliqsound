// compiled headless by sclang: writes .scsyndef files next to this script's "out" dir (first argument)
var out = thisProcess.argv[0];
SynthDef(\spike, { |freq = 440, amp = 0.2, gate = 1|
    var e = EnvGen.kr(Env.adsr(0.01, 0.2, 0.7, 0.3), gate, doneAction: 2);
    var s = RLPF.ar(Saw.ar(freq * [1, 1.005]), freq * 6, 0.3);
    Out.ar(0, s * e * amp);
}).writeDefFile(out);
"wrote spike".postln;
0.exit;

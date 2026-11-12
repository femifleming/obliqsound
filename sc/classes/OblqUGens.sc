// sclang declarations of the ObliqSound UGens (see ugens/OblqUGens.cpp)
OblqFilter : UGen {
    *ar { |in, freq = 1000, res = 0.1, mode = 0, gain = 0.5| ^this.multiNew('audio', in, freq, res, mode, gain) }
}
OblqPoly : MultiOutUGen {
    *ar { |freq = 110, order = 4, teeth = 0, roll = 0, ratio = 1, amt = 0, cycle = 0, skew = 0|
        ^this.multiNew('audio', freq, order, teeth, roll, ratio, amt, cycle, skew) }
    init { |... theInputs| inputs = theInputs; ^this.initOutputs(2, rate) }
}
OblqAdd : MultiOutUGen {
    *ar { |freq = 110, partials = 32, tilt = 0.5, tension = 0, density = 0, warp = 0, peaking = 0.5, bank = 0, factor = 0, gates = 255|
        ^this.multiNew('audio', freq, partials, tilt, tension, density, warp, peaking, bank, factor, gates) }
    init { |... theInputs| inputs = theInputs; ^this.initOutputs(2, rate) }
}
OblqEncode : MultiOutUGen {
    *ar { |in, x = 1, y = 0, z = 0, spread = 0, air = 0.4, doppler = 0.5, ref = 2|
        ^this.multiNew('audio', in, x, y, z, spread, air, doppler, ref) }
    init { |... theInputs| inputs = theInputs; ^this.initOutputs(16, rate) }
}

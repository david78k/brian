from brian2 import *

N = 40
El = -49*mV # default -60
psp = 0.5*mV

taum = 20*ms
taue = 1*ms
taui = 10*ms
vt = 10*mV
vr = 0*mV
eqs = '''dv/dt = (-v + ge - gi)/taum : volt
        dge/dt = -ge/taue : volt
        dgi/dt = -gi/taui : volt
        '''
spikeindices = [0, 0, 1, 0, 0]
spiketimes = [1*ms, 10*ms, 40*ms, 50*ms, 55*ms]
G1 = SpikeGeneratorGroup(2, spikeindices, spiketimes)
G2 = NeuronGroup(1, eqs, threshold = 'v>vt', reset = 'v=vr')

C1 = Synapses(G1, G2, pre='ge')
C2 = Synapses(G1, G2, pre='gi')
#C1[0,0] = 3*mV
#C2[1,0] = 3*mV
C1.w = 3
C2.w = 3

Mv = StateMonitor(G2, 'v', record = True)
Mge = StateMonitor(G2, 'ge', record = True)
Mgi = StateMonitor(G2, 'gi', record = True)

#mon = SpikeMonitor(G)

run(100 * ms)

figure()
subplot(211)
plot(Mv.times, Mv[0])
subplot(212)
plot(Mge.times, Mge[0])
plot(Mgi.times, Mgi[0])
#plot(mon.t/ms, mon.i, '.k')
show()

#print mon.num_spikes


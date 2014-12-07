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

C1 = Synapses(G1, G2, pre='ge += 3*mV')
C2 = Synapses(G1, G2, pre='gi += 3*mV')
#C1[0,0] = 3*mV
#C2[1,0] = 3*mV
C1.connect('i==0')
C2.connect('i==1')

Mv = StateMonitor(G2, 'v', record = True)
Mge = StateMonitor(G2, 'ge', record = True)
Mgi = StateMonitor(G2, 'gi', record = True)

#mon = SpikeMonitor(G)

run(100 * ms)

figure()
subplot(211)
plot(Mv.t/ms, Mv[0].v.T)
subplot(212)
plot(Mge.t/ms, Mge[0].ge.T)
plot(Mgi.t/ms, Mgi[0].gi.T)
#plot(mon.t/ms, mon.i, '.k')
show()

#print mon.num_spikes


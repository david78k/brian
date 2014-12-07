from brian2 import *

tau_a = 1*ms
tau_b = 10*ms
vt = 10*mV
vr = 0*mV
eqs = '''
        dva/dt = -va/tau_a : volt
        dvb/dt = -vb/tau_b : volt
        '''
spikeindices = [0, 1, 1, 0]
spiketimes = [1*ms, 2*ms, 3*ms, 4*ms]
G1 = SpikeGeneratorGroup(2, spikeindices, spiketimes)
G2 = NeuronGroup(1, eqs, threshold = 'vb>vt', reset = 'vb=vr')

C1 = Synapses(G1, G2)
C2 = Synapses(G1, G2)

Ma = StateMonitor(G2, 'va', record = True)
Mb = StateMonitor(G2, 'vb', record = True)

run(100 * ms)

figure()
plot(Ma.t/ms, Ma[0].va.T)
plot(Mb.t/ms, Mb[0].vb.T)
#plot(mon.t/ms, mon.i, '.k')
show()

#print mon.num_spikes


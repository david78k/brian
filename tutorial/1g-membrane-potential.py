from brian2 import *

N = 40
tau = 20 * ms
vt = -50*mV
vr = -60*mV
El = -49*mV # default -60
psp = 0.5*mV
                    
G = NeuronGroup (N, model = 'dv/dt = - (v - El) / tau : volt', 
                 threshold = 'v > vt', reset = 'v = vr')

G.v = 'vr + rand() * (vt - vr)'

#C = Synapses(G,G, pre='v+=psp')
C = Synapses(G,G, post='v+=psp')
C.connect('i==j', p=0.1)

mon = StateMonitor(G, 'v', record = True)
#mon = SpikeMonitor(G, 'v', record=True)
#G.v = 'vr + rand() * (vt - vr)'

run(200*ms)

plot(mon.t/ms, mon[0].v.T/mV)

xlabel('Time (in ms)')
ylabel('Membrane potential (in mV)')
title('Membrane potential for neuron 0')
show()

#print mon.num_spikes

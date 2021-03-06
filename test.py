#import brian2
from brian2 import *

#print ("hello, brian2")

#print (1000*mV)

#brian2.test()

N = 40
tau = 20 * ms
vt = -50*mV
vr = -60*mV
El = -49*mV # default -60
psp = 0.5*mV

eqs = '''
dv/dt = (v0 - v) / tau : volt (unless refractory)
v0 : volt
'''

#group = NeuronGroup(n, eqs, threshold='v > 10*mV', reset='v = 0*mV',
#                    refractory=5*ms)
                    
G = NeuronGroup (N, model = 'dv/dt = - (v - El) / tau : volt', 
threshold = 'v > vt', reset = 'v = vr')
#G.v = 'vr + rand() * (vt - vr)'
#C = Synapses(G,G, sparseness=0.1, weight=psp)
mon = SpikeMonitor(G)

run(1 * second)
plot(mon.t/ms, mon.i, '.k')
show()

print mon.num_spikes

# add randomness 
G.v = 'vr + rand() * (vt - vr)'
#C = Synapses(G,G, sparseness=0.1, weight=psp)
mon = SpikeMonitor(G)

#net = Network(collect())
#net.add(mon)
run(1 * second)
#run(10*ms)
plot(mon.t/ms, mon.i, '.k')
show()

print mon.num_spikes


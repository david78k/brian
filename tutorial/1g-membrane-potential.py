from brian2 import *

N = 40
tau = 20 * ms
vt = -50*mV
vr = -60*mV
El = -49*mV # default -60
psp = 0.5*mV

G = NeuronGroup (N, model = 'dv/dt = - (v - El) / tau : volt', 
                 threshold = 'v > vt', reset = 'v = vr')
#G.v = 'vr + rand() * (vt - vr)'

C = Synapses(G,G, post='v+=psp')
C.connect('i==j', p=0.1)

mon = StateMonitor(G, 'v', record = True)
s_mon = SpikeMonitor(G) # for taster plot

# poisson input stimuli
P = PoissonGroup(N, np.arange(N)*Hz + 10*Hz)
G2 = NeuronGroup (N, model = 'dv/dt = - (v - El) / tau : volt', 
                  threshold = 'v > vt', reset = 'v = vr')
S = Synapses(P,G2, pre='v+=1*mV', connect='i==j')
#G2.v = 'vr + rand() * (vt - vr)'
C2 = Synapses(G2,G2, post='v+=psp')
C2.connect('i==j', p=0.1)

mon2 = StateMonitor(G2, 'v', record = True)
s_mon2 = SpikeMonitor(G2) # for taster plot

run(200*ms)

figure()
subplot(211)
# rastor plot
plot(s_mon.t/ms, s_mon.i, '.')
plot(s_mon2.t/ms, s_mon2.i, '.')

subplot(212)
plot(mon.t/ms, mon[0].v.T/mV)
plot(mon2.t/ms, mon2[0].v.T/mV)

xlabel('Time (in ms)')
ylabel('Membrane potential (in mV)')
#title('Membrane potential for neuron 0')
legend(('normal','poisson'), 'upper left')

show()

#print mon.num_spikes


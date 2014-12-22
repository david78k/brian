#!/usr/bin/env python
'''
Spike-timing dependent plasticity
Adapted from Song, Miller and Abbott (2000) and Song and Abbott (2001)
'''
from brian2 import *

N = 100
taum = 10*ms
taupre = 20*ms
taupost = taupre
Ee = 0*mV
vt = -54*mV
vr = -60*mV
El = -74*mV
taue = 5*ms
F = 15*Hz
gmax = .01
dApre = .01
dApost = -dApre * taupre / taupost * 1.05
dApost *= gmax
dApre *= gmax

eqs_neurons = '''
dv/dt = (ge * (Ee-vr) + El - v) / taum : volt
dge/dt = -ge / taue : 1
'''

input = PoissonGroup(N, rates=F)
output = NeuronGroup(1, eqs_neurons, threshold='v>vt', reset='v = vr')
S = Synapses(input, output,
             '''w : 1
                dApre/dt = -Apre / taupre : 1 (event-driven)
                dApost/dt = -Apost / taupost : 1 (event-driven)''',
             pre='''ge += w
                    Apre += dApre
                    w = clip(w + Apost, 0, gmax)''',
             post='''Apost += dApost
                     w = clip(w + Apre, 0, gmax)''',
             connect=True,
             )
S.w = 'rand() * gmax'
mon = StateMonitor(S, 'w', record=[0, 1])
is_mon = SpikeMonitor(input)
ir_mon = PopulationRateMonitor(input)

# record output neuron membrane potential
o_mon = StateMonitor(output, 'v', record = True)
os_mon = SpikeMonitor(output)
or_mon = PopulationRateMonitor(output)

# plot befre training
subplot(311)
plot(S.w / gmax, '.k')
ylabel('Weight / gmax')
xlabel('Synapse index')
subplot(312)
hist(S.w / gmax, 20)
xlabel('Weight / gmax')
subplot(313)
plot(mon.t/second, mon.w.T/gmax)
xlabel('Time (s)')
ylabel('Weight / gmax')
#subplot(312)
#plot(o_mon.t/second, o_mon[0].v.T, '.')
#xlabel('Time (s)')
#ylabel('Potential (mV)')
##plot(os_mon.t/second, os_mon.i)
##xlabel('Time (s)')
##ylabel('Neuron Output Index')
#subplot(313)
#plot(or_mon.t/second, or_mon.rate/Hz)
#xlabel('Time (s)')
#ylabel('rate (Hz)')
tight_layout()
show()

# train the network: takes about 1min
run(1*second, report='text')

# plot befre training
subplot(511)
plot(S.w / gmax, '.k')
#ylabel('Weight / gmax')
#xlabel('Synapse index')
subplot(512)
hist(S.w / gmax, 20)
#xlabel('Weight / gmax')
subplot(513)
plot(mon.t/second, mon.w.T/gmax)
#xlabel('Time (s)')
#ylabel('Weight / gmax')
subplot(514)
plot(ir_mon.t/second, ir_mon.rate/Hz)
#xlabel('Time (s)')
#ylabel('rate (Hz)')
subplot(515)
# output neuron membrane potential
plot(o_mon.t/second, o_mon[0].v.T/mV, '.')
#xlabel('Time (s)')
#ylabel('Potential (mV)')
#ylabel('Neuron Output Membrane Potential (mV)')

tight_layout()
show()

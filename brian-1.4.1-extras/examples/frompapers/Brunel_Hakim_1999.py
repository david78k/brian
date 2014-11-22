#!/usr/bin/env python
"""
Dynamics of a network of sparsely connected inhibitory current-based 
integrate-and-fire neurons. Individual neurons fire irregularly at 
low rate but the network is in an oscillatory global activity regime 
where neurons are weakly synchronized.

Reference:
    "Fast Global Oscillations in Networks of Integrate-and-Fire
    Neurons with Low Firing Rates"
    Nicolas Brunel & Vincent Hakim
    Neural Computation 11, 1621-1671 (1999)
"""

from brian import *

N = 5000
Vr = 10 * mV
theta = 20 * mV
tau = 20 * ms
delta = 2 * ms
taurefr = 2 * ms
duration = .1 * second
C = 1000
sparseness = float(C)/N
J = .1 * mV
muext = 25 * mV
sigmaext = 1 * mV

eqs = """
dV/dt = (-V+muext + sigmaext * sqrt(tau) * xi)/tau : volt
"""

group = NeuronGroup(N, eqs, threshold=theta,
                    reset=Vr, refractory=taurefr)
group.V = Vr
conn = Connection(group, group, state='V', delay=delta,
                  weight = -J,
                  sparseness=sparseness)
M = SpikeMonitor(group)
LFP = PopulationRateMonitor(group, bin=0.4 * ms)

run(duration)

subplot(211)
raster_plot(M)
xlim(0, duration/ms)

subplot(212)
plot(LFP.times_/ms, LFP.rate)
xlim(0, duration/ms)

show()

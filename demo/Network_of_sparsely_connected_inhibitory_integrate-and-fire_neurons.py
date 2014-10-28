from brian import *
# Network parameters
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
# Neuron model
eqs = "dV/dt=(-V+muext+sigmaext*sqrt(tau)*xi)/tau : volt"
group = NeuronGroup(N, eqs, threshold=theta,
reset=Vr, refractory=taurefr)
group.V = Vr
# Connections
conn = Connection(group, group, state='V', delay=delta,
weight=-J, sparseness=sparseness)
# Monitors
M = SpikeMonitor(group)
# Run
run(duration)
# Plot
raster_plot(M)
show()


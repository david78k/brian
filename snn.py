from brian2 import *

'''
input: distance for ultrasonic or angular velocity for gyroscope (integer) 
- single value or coding to multiple values
- distance in cm: 1-250cm or 1-100inch + infinity
- angular velocity: 0-440 degrees/sec
output: motor power 0-100% (integer)
- left motor power (signed): 101
- right motor power (signed): 101
'''

#inN = 251
inN = 10
#outN = 8 # 202=101*2
outN = 202
tau = 20 * ms
vt = -50*mV
vr = -60*mV
El = -49*mV # default -60
w = 50*mV
psp = 0.5*mV

def snn(sensor_value): 
#    index = encode(sensor_value)
    index = 5
    I = NeuronGroup (inN, model = 'dv/dt = - (v - El)/tau : volt', 
                     threshold = 'v > vt', reset = 'v = vr')
#    I.v[index] = El
    I.v = 'vr + rand() * (vt - vr)'
    O = NeuronGroup (outN, model = 'dv/dt = - (v - El) / tau : volt', 
                     threshold = 'v > vt', reset = 'v = vr')
#    O.v = 'vr + rand() * (vt - vr)'
    
    C = Synapses(I,O, pre='v+=w', post='v+=psp', connect=True)
#    C = Synapses(I,O, post='v+=psp', connect=True)
    #C.connect('i==j', p=0.1)
    
    mon = StateMonitor(O, 'v', record = True)
    is_mon = SpikeMonitor(I) # for taster plot
    s_mon = SpikeMonitor(O) # for taster plot
    
    '''
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
    '''
    run(200*ms)
    
    figure()
    subplot(311)
    # rastor plot
    plot(is_mon.t/ms, is_mon.i, '.')
        
    subplot(312)
    # rastor plot
    plot(s_mon.t/ms, s_mon.i, '.')
    #plot(s_mon2.t/ms, s_mon2.i, '.')
    
    subplot(313)
    plot(mon.t/ms, mon[0].v.T/mV)
    #plot(mon2.t/ms, mon2[0].v.T/mV)
    
    xlabel('Time (in ms)')
    ylabel('Membrane potential (in mV)')
    #title('Membrane potential for neuron 0')
    #legend(('normal','poisson'), 'upper left')
    
    show()
    
    #print mon.t
    #print mon[0].v.T
#    power = np.array(filter(None,mon[0].v.T),dtype='|S10').astype(np.longdouble)
    power = mon[0].v.T
    return power

if __name__ == '__main__':
    sensor_value = 35    
    power = snn(sensor_value)
#    print power
    print np.round(power, 5)
#    print np.around(power, 4)
    
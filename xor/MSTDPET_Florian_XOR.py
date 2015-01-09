'''
Florian rate coded xor
60 inputs divided into two groups to form patterns
frequency 40Hz is logical 1 and 0Hz is logical 0
half of input neurons are inhibitory
60 hidden neurons
1 output
'''

from brian import *

#global clock
defaultclock.dt = 1*ms
dt = defaultclock.dt

wmax = 5*mV
wmin = -5*mV
Ap = 1
Am = -1
tauP = 20*ms
beta = 0.9
dtbeta = beta*dt
learnRate = 0.01
tau=20*ms
Vr=-70*mV
Vl=-70*mV
Vt=-55*mV
lif_eqs = '''
dVm/dt=(Vl-Vm)/tau : volt
K : 1
'''

#input
groupi=PoissonGroup(60,rates=40*Hz)
groupi_A=groupi[0:30]
groupi_B=groupi[30:60]
groupi_in = groupi[15:45]
groupi_ex1 = groupi[0:15]
groupi_ex2 = groupi[45:60]

#hidden
group_hid = NeuronGroup(60, model=lif_eqs, threshold=-55*mV, reset=Vr)

#output
group_out = NeuronGroup(1, model=lif_eqs, threshold=-55*mV, reset=Vr)

#initialize neuron potential
groupi.Vm = Vr
group_hid.Vm = Vr
group_out.Vm = Vr

#connections
link_in_hid_in  = Connection(groupi_in,group_hid, 'Vm', weight=rand(len(groupi_in),len(group_hid))*-5*mV,sparseness=1)
link_in_hid_ex1  = Connection(groupi_ex1,group_hid, 'Vm', weight=rand(len(groupi_ex1),len(group_hid))*5*mV, sparseness=1)
link_in_hid_ex2  = Connection(groupi_ex2,group_hid, 'Vm', weight=rand(len(groupi_ex2),len(group_hid))*5*mV, sparseness=1)

link_hid_out = Connection(group_hid,group_out, 'Vm', weight=rand(len(group_hid),len(group_out))*5*mV, sparseness=1)

#trace
trace_in_hid_in = Connection(groupi_in,group_hid, 'K', weight= 0.0000001, sparseness=1,structure='sparse')
trace_in_hid_ex1 = Connection(groupi_ex1,group_hid, 'K', weight= 0.0000001, sparseness=1,structure='sparse')
trace_in_hid_ex2 = Connection(groupi_ex2,group_hid, 'K', weight= 0.0000001, sparseness=1,structure='sparse')
trace_hid_out = Connection(group_hid, group_out, 'K', weight= 0.0000001, sparseness=1,structure='sparse')

#P functions
Pp_in_hid_in = NeuronGroup(30, 'dPp/dt=-Pp/tauP:1')
Pm_in_hid_in = NeuronGroup(60, 'dPm/dt=-Pm/tauP:1')

Pp_in_hid_ex1 = NeuronGroup(15, 'dPp/dt=-Pp/tauP:1')
Pm_in_hid_ex1 = NeuronGroup(60, 'dPm/dt=-Pm/tauP:1')

Pp_in_hid_ex2 = NeuronGroup(15, 'dPp/dt=-Pp/tauP:1')
Pm_in_hid_ex2 = NeuronGroup(60, 'dPm/dt=-Pm/tauP:1')

Pp_hid_out = NeuronGroup(60, 'dPp/dt=-Pp/tauP:1')
Pm_hid_out = NeuronGroup(1, 'dPm/dt=-Pm/tauP:1')

#monitors that update P and trace functions on spikes
def update_on_pre_spikes_in_hid_in(spikes):
    if len(spikes):
        Pp_in_hid_in.Pp[spikes] += Ap
        for i in spikes:
            trace_in_hid_in.W[i, :] += Pm_in_hid_in.Pm
def update_on_post_spikes_in_hid_in(spikes):
    if len(spikes):
        Pm_in_hid_in.Pm[spikes] += Am
        for i in spikes:
            trace_in_hid_in.W[:, i] += Pp_in_hid_in.Pp
SM_in_hid_in_Pp = SpikeMonitor(groupi_in, function=update_on_pre_spikes_in_hid_in)
SM_in_hid_in_Pm = SpikeMonitor(group_hid, function=update_on_post_spikes_in_hid_in)
###################################################
def update_on_pre_spikes_in_hid_ex1(spikes):
    if len(spikes):
        Pp_in_hid_ex1.Pp[spikes] += Ap
        for i in spikes:
            trace_in_hid_ex1.W[i, :] += Pm_in_hid_ex1.Pm
def update_on_post_spikes_in_hid_ex1(spikes):
    if len(spikes):
        Pm_in_hid_ex1.Pm[spikes] += Am
        for i in spikes:
            trace_in_hid_ex1.W[:, i] += Pp_in_hid_ex1.Pp
SM_in_hid_ex1_Pp = SpikeMonitor(groupi_ex1, function=update_on_pre_spikes_in_hid_ex1)
SM_in_hid_ex1_Pm = SpikeMonitor(group_hid, function=update_on_post_spikes_in_hid_ex1)
##################################################
def update_on_pre_spikes_in_hid_ex2(spikes):
    if len(spikes):
        Pp_in_hid_ex2.Pp[spikes] += Ap
        for i in spikes:
            trace_in_hid_ex2.W[i, :] += Pm_in_hid_ex2.Pm
def update_on_post_spikes_in_hid_ex2(spikes):
    if len(spikes):
        Pm_in_hid_ex2.Pm[spikes] += Am
        for i in spikes:
            trace_in_hid_ex2.W[:, i] += Pp_in_hid_ex2.Pp
SM_in_hid_ex2_Pp = SpikeMonitor(groupi_ex2, function=update_on_pre_spikes_in_hid_ex2)
SM_in_hid_ex2_Pm = SpikeMonitor(group_hid, function=update_on_post_spikes_in_hid_ex2)
##################################################
def update_on_pre_spikes_in_hid_out(spikes):
    if len(spikes):
        Pp_hid_out.Pp[spikes] += Ap
        for i in spikes:
            trace_hid_out.W[i, :] += Pm_hid_out.Pm
def update_on_post_spikes_in_hid_out(spikes):
    if len(spikes):
        Pm_hid_out.Pm[spikes] += Am
        for i in spikes:
            trace_hid_out.W[:, i] += Pp_hid_out.Pp
SM_in_hid_out_Pp = SpikeMonitor(group_hid, function=update_on_pre_spikes_in_hid_out)
SM_in_hid_out_Pm = SpikeMonitor(group_out, function=update_on_post_spikes_in_hid_out)

#continious decay of trace functions
#and update of real weights
@network_operation() 
def reduce_trace(): 
    for value in trace_in_hid_in.W:
        value*=beta
    for value in trace_in_hid_ex1.W:
        value*=beta
    for value in trace_in_hid_ex2.W:
        value*=beta
    for value in trace_hid_out.W:
        value*=beta
    
    clip(link_in_hid_in.W.alldata + trace_in_hid_in.W.alldata*reward[-1]*dt*learnRate, -5*mV, 0*mV, link_in_hid_in.W.alldata)
    clip(link_in_hid_ex1.W.alldata + trace_in_hid_ex1.W.alldata*reward[-1]*dt*learnRate, 0*mV, 5*mV, link_in_hid_ex1.W.alldata)
    clip(link_in_hid_ex2.W.alldata + trace_in_hid_ex2.W.alldata*reward[-1]*dt*learnRate, 0*mV, 5*mV, link_in_hid_ex2.W.alldata)
    clip(link_hid_out.W.alldata + trace_hid_out.W.alldata*reward[-1]*dt*learnRate, 0*mV, 5*mV, link_hid_out.W.alldata)
    
#set the reward
def f(spikes):
    if 0 in spikes:
        reward.append(rw)
    else:
        reward.append(0)
    
rewardMonitor=SpikeMonitor(group_out,function=f)    
    
#monitores, your cap.
mGpre=SpikeMonitor(group_hid[0])
mGpost=SpikeMonitor(group_out)

monitor_v_out = StateMonitor(group_out, 'Vm', record=0)

Pp0=[]
Pm0=[]
zet=[]
w=[]
reward=[]
rewardPC=[]

@network_operation()
def monitor(): 
#    Pp0.append(Pp_hid_out.Pp[0])
#    Pm0.append(Pm_hid_out.Pm[0])
#    zet.append(trace_hid_out.W[0][0])
    w.append(link_hid_out.W[0][0])

#learning cycle for 300 epochs
for x in range (0,300):
    
    #(0,0)
    groupi_A.rate = 0*Hz
    groupi_B.rate = 0*Hz
    rw = -1
    run(500*ms) 
    
    #(1,0)
    groupi_A.rate = 40*Hz
    groupi_B.rate = 0*Hz
    rw = 1
    run(500*ms) 

    #(0,1)
    groupi_A.rate = 0*Hz
    groupi_B.rate = 40*Hz
    rw = 1
    run(500*ms) 

    #(1,1)
    groupi_A.rate = 40*Hz
    groupi_B.rate = 40*Hz
    rw = -1
    run(500*ms) 
    
    rewardPC.append(sum(reward[-2000:]))
    print 'last step reward is:',rewardPC[-1]
    print '0,0 rate is:',-sum(reward[-2000:-1500])
    print '0,1 rate is:',sum(reward[-1500:-1000])
    print '1,0 rate is:',sum(reward[-1000:-500])
    print '1,1 rate is:',-sum(reward[-500:])
 
#test after learning on 10 epoch
a=[]
b=[]
c=[]
d=[]
for x in range (0,10):
    #learning is turned off
    learnRate = 0
    
    #(0,0)
    groupi_A.rate = 0*Hz
    groupi_B.rate = 0*Hz
    rw = -1
    run(500*ms) 
    
    #(1,0)
    groupi_A.rate = 40*Hz
    groupi_B.rate = 0*Hz
    rw = 1
    run(500*ms) 

    #(0,1)
    groupi_A.rate = 0*Hz
    groupi_B.rate = 40*Hz
    rw = 1
    run(500*ms) 

    #(1,1)
    groupi_A.rate = 40*Hz
    groupi_B.rate = 40*Hz
    rw = -1
    run(500*ms) 
    
    rewardPC.append(sum(reward[-2000:]))
    print 'last step reward is:',rewardPC[-1]
    print '0,0 rate is:',-sum(reward[-2000:-1500])
    print '0,1 rate is:',sum(reward[-1500:-1000])
    print '1,0 rate is:',sum(reward[-1000:-500])
    print '1,1 rate is:',-sum(reward[-500:])
    
    
    a.append(-sum(reward[-2000:-1500]))
    b.append(sum(reward[-1500:-1000]))
    c.append(sum(reward[-1000:-500]))
    d.append(-sum(reward[-500:]))


print 'average reward after learning:', sum(rewardPC[-10:])   
print 'average number of spikes for (0,0)', sum(a)
print 'average number of spikes for (0,1)',sum(b)
print 'average number of spikes for (1,0)',sum(c)
print 'average number of spikes for (1,1)',sum(d)

subplot(311)
plot(rewardPC)
#subplot(612)
#plot(Pp0)
#subplot(613)
#plot(Pm0)
#subplot(614)
#plot(zet)
subplot(312)
plot(w)
subplot(313)
monitor_v_out.plot()
show()
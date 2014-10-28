"""
Spike queues following BEP-21.

The spike queue class stores future synaptic events
produced by a given presynaptic neuron group (or postsynaptic for backward
propagation in STDP).

The structure X is a 2D array, where row is the time bin and column
is the position in that bin (each row is a stack) .
The array is circular in the time dimension. There is a 1D array (n) giving the
position of the last added event in each time bin.
The 2D array is dynamic in the column direction.
The row corresponding to current time is stored in currenttime.
X_flat is a flattened view of X.

Main methods:
* peek()
    Outputs the current events: we simply get the row corresponding to
    currenttime, so this is fast. We then shift the cursor of the circular
    array by one row: next().
* insert(delay, target, offset=None)
    Insert events in the queue. Each presynaptic neuron has a corresponding
    array of target synapses and corresponding delays. We must push each target
    synapse (index) on top of the stack (row) corresponding to the delay. If all synapses
    have different delays, this is relatively easy to vectorise. It is a bit
    more difficult if there are synapses with the same delays.
    For a given presynaptic neuron, each synaptic delay corresponds to coordinates
    (i,j) in the circular array of stacks, where i is the delay (stack index and
    j is index relative to the top of the stack (0=top, 1=1 above top).
    The absolute location in the structure is then calculated as n[i]+j, where
    n[i] is the location of the top of stack i. The only difficulty is to calculate
    j, and in Python this requires sorting (see development mailing list).
    It can be preprocessed if event feeding involves a loop over presynaptic spikes
    (if it's vectorised then it's not possible anymore). In this case it takes K*4
    bytes.
* offsets(delay)
    This calculates the offsets j mentionned above, for a given array of delays.
* precompute_offsets()
    This precomputes all offsets for all presynaptic neurons.
* propagate()
    The class is implemented as a SpikeMonitor, which means the propagate() function is
    called at each timestep with the spikes produced by the neuron group.
    The function executes different codes (different strategies) depending on whether
    offsets are precomputed or not, and on whether delays are heterogeneous or
    homogeneous.
"""
import numpy as np
try:
    import pylab
except:
    pass
from scipy import weave

from brian.globalprefs import get_global_preference, exists_global_preference, define_global_preference
from brian.monitor import SpikeMonitor
from brian.stdunits import ms
import warnings

__all__=['SpikeQueue']

INITIAL_MAXSPIKESPER_DT = 1

class SpikeQueue(SpikeMonitor):
    '''Spike queue
    
    Initialised with arguments:

    ``source``
        The neuron group that sends spikes.
    ``synapses``
        A list of synapses (synapses[i]=array of synapse indices for neuron i).
    ``delays``
        An array of delays (delays[k]=delay of synapse k).  
    ``max_delay=0*ms``
        The maximum delay (in second) of synaptic events. At run time, the
        structure is resized to the maximum delay in ``delays``, and thus
        the ``max_delay`` should only be specified if delays can change
        during the simulation (in which case offsets should not be
        precomputed).
    ``maxevents = INITIAL_MAXSPIKESPER_DT``
        The initial size of the queue for each timestep. Note that the data
        structure automatically grows to the required size, and therefore this
        option is generally not useful.
    ``precompute_offsets = True``
        A flag to precompute offsets. By default, offsets (an internal array
        derived from ``delays``, used to insert events in the data structure,
        see below)
        are precomputed for all neurons, the first time the object is run.
        This usually results in a speed up but takes memory, which is why it
        can be disabled.

    **Data structure** 
    
    A spike queue is implemented as a 2D array ``X`` that is circular in the time
    direction (rows) and dynamic in the events direction (columns). The
    row index corresponding to the current timestep is ``currentime``.
    Each element contains the target synapse index.

    The class is implemented as a :class:`SpikeMonitor`, so that the propagate()
    method is called at each timestep (of the monitored group).
    
    **Methods**
            
    .. method:: next()
    
        Advances by one timestep.
        
    .. method:: peek()
    
        Returns the all the synaptic events corresponding to the current time,
        as an array of synapse indexes.
        
    .. method:: precompute_offsets()
    
        Precompute all offsets corresponding to delays. This assumes that
        delays will not change during the simulation. If they do (between two
        runs for example), then this method can be called.
    
    **Offsets**
    
    Offsets are used to solve the problem of inserting multiple synaptic events with the
    same delay. This is difficult to vectorise. If there are n synaptic events with the same
    delay, these events are given an offset between 0 and n-1, corresponding to their
    relative position in the data structure.
    They can be either precalculated
    (faster), or determined at run time (saves memory). Note that if they
    are determined at run time, then it is possible to also vectorise over
    presynaptic spikes.
    '''
    def __init__(self, source, synapses, delays,
                 max_delay = 0*ms, maxevents = INITIAL_MAXSPIKESPER_DT,
                 precompute_offsets = True):
        self.source = source #NeuronGroup
        self.delays = delays
        self.synapses = synapses
        self._precompute_offsets=precompute_offsets

        self._max_delay=max_delay
        if max_delay>0: # do not precompute offsets if delays can change
            self._precompute_offsets=False
        
        # number of time steps, maximum number of spikes per time step
        nsteps = int(np.floor((max_delay)/(self.source.clock.dt)))+1
        self.X = np.zeros((nsteps, maxevents), dtype = self.synapses[0].dtype) # target synapses
        self.X_flat = self.X.reshape(nsteps*maxevents,)
        self.currenttime = 0
        self.n = np.zeros(nsteps, dtype = int) # number of events in each time step
        
        self._offsets = None # precalculated offsets
        
        # Compiled version
        self._useweave = get_global_preference('useweave')
        self._cpp_compiler = get_global_preference('weavecompiler')
        self._extra_compile_args = ['-O3']
        if self._cpp_compiler == 'gcc':
            self._extra_compile_args += get_global_preference('gcc_options') # ['-march=native', '-ffast-math']
        if self._useweave: # no need to precompute offsets if weave is used
            self._precompute_offsets=False

        super(SpikeQueue, self).__init__(source, 
                                         record = False)
        
        #useweave=get_global_preference('useweave')
        #compiler=get_global_preference('weavecompiler')

    def compress(self):
        '''
        This is called the first time the network is run. The size of the
        of the data structure (number of rows) is adjusted to fit the maximum
        delay in ``delays'', if necessary. Offsets are calculated, unless
        the option ``precompute_offsets'' is set to False. A flag is set if
        delays are homogeneous, in which case insertion will use a faster method.
        '''
        nsteps=max(self.delays)+1
        # Check whether some delays are too long
        if (self._max_delay>0) and (nsteps>self.X.shape[0]):
            raise ValueError,"Synaptic delays exceed maximum delay"
        
        if hasattr(self, '_iscompressed') and self._iscompressed:
            return
        self._iscompressed = True
        # Adjust the maximum delay and number of events per timestep if necessary
        maxevents=self.X.shape[1]
        if maxevents==INITIAL_MAXSPIKESPER_DT: # automatic resize
            maxevents=max(INITIAL_MAXSPIKESPER_DT,max([len(targets) for targets in self.synapses]))
        # Check if homogeneous delays
        if self._max_delay>0:
            self._homogeneous=False
        else:
            self._homogeneous=(nsteps==min(self.delays)+1)
        # Resize
        if (nsteps>self.X.shape[0]) or (maxevents>self.X.shape[1]): # Resize
            nsteps=max(nsteps,self.X.shape[0]) # Choose max_delay if is is larger than the maximum delay
            maxevents=max(maxevents,self.X.shape[1])
            self.X = np.zeros((nsteps, maxevents), dtype = self.synapses[0].dtype) # target synapses
            self.X_flat = self.X.reshape(nsteps*maxevents,)
            self.n = np.zeros(nsteps, dtype = int) # number of events in each time step

        # Precompute offsets
        if (self._offsets is None) and self._precompute_offsets:
            self.precompute_offsets()

    ################################ SPIKE QUEUE DATASTRUCTURE ######################
    def next(self):
        '''
        Advances by one timestep
        '''
        self.n[self.currenttime]=0 # erase
        self.currenttime=(self.currenttime+1) % len(self.n)
        
    def peek(self):
        '''
        Returns the all the synaptic events corresponding to the current time,
        as an array of synapse indexes.
        '''      
        return self.X[self.currenttime,:self.n[self.currenttime]]
    
    def _update_delays(self, delays):
        '''
        Internal method to update the delays, used by the Synapses class when the delays are dynamically varied.
        Delays are assumed to be represented as floating values in second, hence the conversion to "timestep delays" is handled here.
        '''
        #log_debug('brian.synapses.spikequeue', 'Updating delays...')
        self.delays = np.array(np.floor(delays/self.source.clock.dt), dtype = int)+1
    
    def precompute_offsets(self):
        '''
        Precompute all offsets corresponding to delays. This assumes that
        delays will not change during the simulation. If they do (between two
        runs for example), then this method can be called.
        '''
        self._offsets=[]
        for i in range(len(self.synapses)):
            delays=self.delays[self.synapses[i].data]
            self._offsets.append(self.offsets(delays))
    
    def offsets(self, delay):
        '''
        Calculates offsets corresponding to a delay array.
        If there n identical delays, there are given offsets between
        0 and n-1.
        Example:
        
            [7,5,7,3,7,5] -> [0,0,1,0,2,1]
            
        The code is complex because tricks are needed for vectorisation.
        '''
        if self._useweave:
            return self.offsets_C(delay)
        # We use merge sort because it preserves the input order of equal
        # elements in the sorted output
        I = np.argsort(delay,kind='mergesort')
        xs = delay[I]
        J = xs[1:]!=xs[:-1]
        #K = xs[1:]==xs[:-1]
        A = np.hstack((0, np.cumsum(J)))
        #B = np.hstack((0, np.cumsum(K)))
        B = np.hstack((0, np.cumsum(-J)))
        BJ = np.hstack((0, B[J]))
        ei = B-BJ[A]
        ofs = np.zeros_like(delay)
        ofs[I] = np.array(ei,dtype=ofs.dtype) # maybe types should be signed?
        return ofs
           
    def insert(self, delay, target, offset=None):
        '''
        Vectorised insertion of spike events.
        
        ``delay``
            Delays in timesteps (array).
            
        ``target``
            Target synaptic indexes (array).
            
        ``offset``
            Offsets within timestep (array). If unspecified, they are calculated
            from the delay array.
        '''
        delay=np.array(delay,dtype=int)
        if self._useweave: # C-optimised insertion (minor speed up)
            self.insert_C(delay,target)
            return
        if offset is None:
            offset=self.offsets(delay)
        
        # Calculate row indexes in the data structure
        timesteps = (self.currenttime + delay) % len(self.n)
        # (Over)estimate the number of events to be stored, to resize the array
        # It's an overestimation for the current time, but I believe a good one
        # for future events
        m=max(self.n)+len(target)
        if (m >= self.X.shape[1]): # overflow
            self.resize(m+1)
        
        self.X_flat[timesteps*self.X.shape[1]+offset+self.n[timesteps]]=target
        self.n[timesteps] += offset+1 # that's a trick (to update stack size)
        # Note: the trick can only work if offsets are ordered in the right way
        
    def insert_homogeneous(self,delay,target):
        '''
        Inserts events at a fixed delay.
        
        ``delay``
            Delay in timesteps (scalar).
            
        ``target``
            Target synaptic indexes (array).
        '''
        timestep = (self.currenttime + delay) % len(self.n)
        nevents=len(target)
        m = self.n[timestep]+nevents+1 # If overflow, then at least one self.n is bigger than the size
        if (m >= self.X.shape[1]):
            self.resize(m+1) # was m previously (not enough)
        k=timestep*self.X.shape[1]+self.n[timestep]
        self.X_flat[k:k+nevents]=target
        self.n[timestep]+=nevents
        
    def resize(self, maxevents):
        '''
        Resizes the underlying data structure (number of columns = spikes per dt).
        
        ``maxevents``
            The new number of columns.It will be rounded to the closest power of 2.
        '''
        # old and new sizes
        old_maxevents = self.X.shape[1]
        new_maxevents = int(2**np.ceil(np.log2(maxevents))) # maybe 2 is too large
        # new array
        newX = np.zeros((self.X.shape[0], new_maxevents), dtype = self.X.dtype)
        newX[:, :old_maxevents] = self.X[:, :old_maxevents] # copy old data
        
        self.X = newX
        self.X_flat = self.X.reshape(self.X.shape[0]*new_maxevents,)
        
    def propagate(self, spikes):
        '''
        Called by the network object at every timestep.
        Spikes produce synaptic events that are inserted in the queue. 
        '''
        if len(spikes):
#            print '(Python) In propagate: spikes = ', spikes
            if self._homogeneous: # homogeneous delays
                synaptic_events=np.hstack([self.synapses[i].data for i in spikes]) # could be not efficient
                self.insert_homogeneous(self.delays[0],synaptic_events)
            elif self._offsets is None: # vectorise over synaptic events
                # there are no precomputed offsets, this is the case (in particular) when there are dynamic delays
                synaptic_events=np.hstack([self.synapses[i].data for i in spikes])
                if len(synaptic_events):
                    delay = self.delays[synaptic_events]
                    self.insert(delay, synaptic_events)
            else: # offsets are precomputed
                for i in spikes:
                    synaptic_events=self.synapses[i].data # assuming a dynamic array: could change at run time?    
                    if len(synaptic_events):
                        delay = self.delays[synaptic_events]
                        offsets = self._offsets[i]
                        self.insert(delay, synaptic_events, offsets)

    ######################################## C optimised versions
    def insert_C(self,delay,target):
        '''
        Insertion of events using weave.

        ``delay``
            Delays in timesteps (array).
            
        ``target``
            Target synaptic indexes (array).
        '''
        # Check if we can fit the events (crude check)
        nevents=len(target)
        m=max(self.n)+nevents
        if m>self.X.shape[1]:
            self.resize(m)
        Xflat=self.X_flat
        n=self.n
        ncols=self.X.shape[1]
        currentt=self.currenttime
        ndelays=len(self.n)
        code='''
        for(int k=0;k<nevents;k++) {
            const int d = (currentt+delay[k]) % ndelays;
            Xflat[d*ncols+n[d]] = target[k];
            n[d]++;
        }
        '''
        weave.inline(code, ['nevents','n','delay','Xflat','target','ncols','currentt','ndelays'], \
             compiler=self._cpp_compiler,
             extra_compile_args=self._extra_compile_args)

    def offsets_C(self, delay):
        '''
        Calculates offsets corresponding to a delay array, optimised C version.
        This function is normally not used (since insert_C does not need it).
        '''
        nevents=len(delay)
        x=np.zeros(self.X.shape[0],dtype=int) # a counter for each delay
        ofs=np.zeros(nevents,dtype=int)
        code='''
        int d;
        for(int i=0;i<nevents;i++) {
            d=delay[i];
            ofs[i]=x[d];
            x[d]++;
        }
        '''
        weave.inline(code, ['nevents','x','ofs','delay'], \
             compiler=self._cpp_compiler,
             extra_compile_args=self._extra_compile_args)
        return ofs

    def __repr__(self):
        res = 'SpikeQueue(shape = (%d, %d), ' % (self.X.shape)
        res += 'max_delay = %.1f ms)' % (self._max_delay/ms)
        return res
        
    

    ######################################## UTILS    
    def plot(self, display = True):
        '''
        Plots the events stored in the spike queue.
        '''
        for i in range(self.X.shape[0]):
            idx = (i + self.currenttime ) % self.X.shape[0]
            data = self.X[idx, :self.n[idx]]
            pylab.plot(idx * np.ones(len(data)), data, '.')
        if display:
            pylab.show()

try:
    ## CSpikeQueue support!
    # replaces the SpikeQueue object by a wrapper for the C++ version
    # this is only if the import statement below doesn't fail (i.e. the c version is compiled)

    ## try to import the CSpikeQueue
    import brian.experimental.cspikequeue.cspikequeue as _cspikequeue
    has_cspikequeue = True

    ## OK, now replace SpikeQueue by a wrapper to the C version
    # this adds compatibility easily to all usual the arguments of SpikeQueue
    # hence the arguments should match those of the class above
    class SpikeQueue(_cspikequeue.SpikeQueue, SpikeMonitor):
        def __init__(self, source, synapses, delays,
                     max_delay = 60*ms, maxevents = INITIAL_MAXSPIKESPER_DT,
                     precompute_offsets = True):
            self._precompute_offsets = precompute_offsets
            SpikeMonitor.__init__(self, source, record = False)

            nsteps = int(np.floor(max_delay/self.source.clock.dt))+1

            self._max_delay = max_delay

            self.synapses = synapses
            self.delays = delays # Delay handling should also be in C

            _cspikequeue.SpikeQueue.__init__(self, nsteps, int(maxevents))

#            self._spikequeue = _cspikequeue.SpikeQueue(nsteps, int(maxevents))

        def compress(self):
            nsteps=max(self.delays)+1

            # Check whether some delays are too long
            if (nsteps>self.n_delays):
                desired_max_delay = nsteps * self.source.clock.dt
                raise ValueError,"Synaptic delays exceed maximum delay, set max_delay to %.1f ms" % (desired_max_delay/ms)

            if hasattr(self, '_iscompressed') and self._iscompressed:
                return

            self._iscompressed = True

            # Adjust the maximum delay and number of events per timestep if necessary
            maxevents=self.n_maxevents
            if maxevents==INITIAL_MAXSPIKESPER_DT: # automatic resize
                maxevents=max(INITIAL_MAXSPIKESPER_DT, max([len(targets) for targets in self.synapses]))

            # Resize

            self.expand(int(maxevents))
        def propagate(self, spikes):
            '''
            Called by the network object at every timestep.
            Spikes produce synaptic events that are inserted in the queue. 
            '''
            if len(spikes):
                synaptic_events=np.hstack([self.synapses[i].data for i in spikes]) # could be not efficient
                self.insert(synaptic_events, self.delays[synaptic_events])   
        warnings.warn('Using C++ SpikeQueue')
except ImportError:
    has_cspikequeue = False

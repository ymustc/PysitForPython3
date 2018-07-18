import copy
import numpy as np
import scipy.sparse as spsp
from scipy.interpolate import interp1d
from pysit.core.sources import *

# The names from this namespace that we wish to expose globally go here.
__all__ = ['Shot', 'SourceEncodedSupershot']

__docformat__ = "restructuredtext en"

class Shot(object):
    """ Container class for a seismic shot.

    The `Shot` class provides a logical grouping of seismic sources with
    receivers.  This class may be refactored so that it is a base class for
    subclasses like SuperShot, SyntheticShot, SegyShot, ProductionShot, etc.

    Attributes
    ----------
    sources : subclass of SourceBase
        Source or set of source objects.
    receivers : subclass of ReceiverBase
        Receiver or set of receiver objects.

    """

    def __init__(self, sources, receivers):
        """Constructor for the Shot class.

        Parameters
        ----------
        source : SeismicSource
            Object representing the source emitter.
        receiver_list : list of SeismicReceiver, optional
            Initial list of receivers.

        Examples
        --------
        >>> from pysit import *
        >>> d = Domain()
        >>> S = Shot(SeismicSource(d, (0.5,0.5)))

        """

        self.receivers = receivers
        receivers.set_shot(self)

        self.sources = sources
        sources.set_shot(self)

        # # This is a function/function object, not an attribute.
        # self._interpolator = None
        # self._ts = None


    # def add_receiver(self, r):
        # """Wrapper for list.append.

        # Parameters
        # ----------
        # r : SeismicReceiver
            # r is appended to self.receiver_list.
        # """

        # self.receiver_list.append(r)
        # r.set_shot(self)

    def initialize(self, data_length):
        """Clear the data from each receiver in the list of receivers.

        Parameters
        ----------
        data_length : int
            Length of the desired data array.
        """

        self.receivers.clear_data(data_length)

    def reset_time_series(self, ts):
        self.sources.reset_time_series(ts)
        self.receivers.reset_time_series(ts)

    def compute_data_dft(self, frequencies, force_computation=False):
        """ Precompute the DFT of the data at the given list of frequencies.

        Parameters
        ----------
        frequencies : float, iterable
            The frequency or frequencies for which to compute the DFT.
        force_computation : bool {optional}
            Force computation of DFT.  By default already computed frequencies are not recomputed.

        """

        self.receivers.compute_data_dft(frequencies)

    def gather(self, as_array=False, offset=None):
        """Collect a sub list of receivers or an array of the data from those
        receivers.

        Parameters
        ----------
        as_array : bool, optional
            Return the data from the selected receivers as an array, rather than
            returning a list of selected receivers.
        offset : float or int, optional
            Not implemented.  Will eventually allow an offset to be passed so
            that reduced sized gathers can be collected.

        Returns
        -------
        sublist : list of SeismicReceiver
            If as_array is False, list of references to the selected receivers.
        A : numpy.ndarray
            If as_array is True, an array of the data from the selected
            receivers.

        """

        if offset is not None:
            # sublist = something that sublists by offset
            raise NotImplementedError('Gather by offset not yet implemented.')
        else:
            sublist = self.receivers

        if as_array:
            A = sublist.data #np.array([r.data for r in sublist])
            return A
        else:
            return sublist

    def serialize_dict(self):

        ret = dict()

        ret['dt'] = self.dt
        ret['t_start'] = self.trange[0]
        ret['t_end'] = self.trange[1]

        ret['sources'] = self.sources.serialize_dict()
        ret['receivers'] = self.receivers.serialize_dict()

        return ret

    def unserialize_dict(self, d):
        raise NotImplementedError()

class SourceEncodedSupershot(Shot):
    """ A source encoded supershot.

    The `SourceEncodedSupershot` class handles the encoding of the 
    sources of each shot and the recorded 'real data'. Each time
    the weight_vector is regenerated, this supershot generates a 
    new encoded SourceSet from the sources of the member shots. 
    A new ReceiverSet is also generated and its recordings are
    generated by encoding the receiver recordings of each shot.
    

    Attributes
    ----------
    shots : subclass of Shot
        A shot with a PointSource source
    """
    def __init__(self, shots, weight_type = 'gaussian'):
        #Set the shots to 'self.sequential_shots'. This will invoke the setter, which will generate the first weight vector.
        self.weight_type = weight_type       
        self.sequential_shots = shots

    def generate_weight_vector(self):
        if self.weight_type == "gaussian":
            weight_vector = np.random.randn(self._nshots)
    
        elif self.weight_type == "krebs":
            weight_vector = 2*np.random.random_integers(0,1,self._nshots) - 1 #values that are either -1 or 1 with equal likelihood.

        else:
            raise Exception("Incorrect weight type supplied.")

        return weight_vector

    def encode(self): 
        """ Do a new encoding.
        
        Calling this function will generate a new random vector
        of weight_type. It then encodes the shots and data
        according to these new weights.
        """
        
        class EncodedSourceSet(SourceSet):
            """ A SourceSet that encodes the member sources. 
            
            """
            def __init__(self, mesh, sources, time_coded=True, **kwargs):
                """ Creates a SourceSet the normal way, but also indicates whether coding is happening on time or frequency basis. 
                
                """
                
                super(EncodedSourceSet, self).__init__(mesh, sources, **kwargs)
                self.time_coded = time_coded
                
                if not time_coded:
                    self.codes = dict() #To allow for a different code at every frequency
            
            def f(self, t=0.0, nu=None, **kwargs):
                #Decorate here
                
                ret = None
                if self.time_coded and nu == None: 
                    #We already set the codes in encode(). They have not changed, so no need to reapply.
                    ret = super(EncodedSourceSet, self ).f(t, nu, **kwargs )
                elif not self.time_coded and nu != None:
                    #Set the codes for this frequency. Not much of an overhead since no timestepping.
                    #In contrast to a time simulation, the intensity (used for code) has to be set again each time frequencies are varied. Each frequency can have a different code.
                    
                    for source_nr in range(self.source_count):
                        source = self.source_list[source_nr]
                        source.intensity = self.codes[nu][source_nr]                        
                        
                    ret = super(EncodedSourceSet, self ).f(t, nu, **kwargs )
                    
                else:
                    raise Exception("Something strange happened")
        
                return ret 
            
            def encode(self, codes, nu=None):
                """ If no nu applied, code is interpreted as time code
                
                codes: An ndarray with length equal to the number of sources.
                nu:    The frequency at which the codes are applied, in case of a frequency domain simulation.
                
                """
                if self.time_coded and nu == None:  #Time domain.
                    #self.codes is an ndarray or list with length equal to the number of sources
                    self.codes = codes      
                    
                    #Set the codes here already. Applying them at each time step when f() is called is an overhead.
                    
                    for source_nr in range(self.source_count):
                        source = self.source_list[source_nr]
                        source.intensity = self.codes[source_nr]
                        
                elif not self.time_coded and nu != None:    #Freq domain.
                    #self.codes is a dict. At every frequency it has an ndarray or list with length equal to the number of sources
                    self.codes[nu] = codes   
                else:   #Some inconsistency
                    raise Exception("Something strange happened")
        
        #In the future it should be possible to select a random shot to fire (so weight vector has one single '1' location and the rest is '0'. This would implement randomized shot in an easy way.
        #See the paper "Fast waveform inversion without source-encoding" by Van Leeuwen and Herrmann, 2013, and "A new optimization approach for source-encoding full-waveform inversion" by moghaddam et al, 2013        
        #Even though the methods are very similar, the randomized shot allows for non-fixed-spread acquisition as well. So a different method should probably be written. 

        shots = self._sequential_shots
        
        #Prepare the source list which will be used to make the encoded SourceSet
        sources = []
        for shot in shots:
            source = copy.deepcopy(shot.sources)
            source.set_shot(None)
            sources.append(source)
        
        #Generate the encoded SourceSet. The actual encoding weights are supplied in the loop below.
        mesh = shots[0].sources.mesh
        enc_sourceset = EncodedSourceSet(mesh, sources, time_coded = self.is_time_simulation)
        enc_sourceset.set_shot(self)
        
        #Make the encoded ReceiverSet by encoding the data in each ReceiverSet.
        #We already verified that each ReceiverSet has the same sampling operator.
        #Encode both SourceSets and receivers in loop
        
        receiver_set = copy.deepcopy(shots[0].receivers) #Initialize by copying one, then reset data.
        receiver_set.set_shot(self)

        if self.is_time_simulation:
            receiver_set.data*=0.0 #clear time data
            codes = self.generate_weight_vector() #generate encoding 
            
            #now encode and add contributions from each receiver set
            for shot, code in zip(shots,codes.tolist()):
                ### ENCODE RECEIVERS ###
                receiver_set.data += code*shot.receivers.data
                
            enc_sourceset.encode(codes)
        else:
            
            for freq in shots[0].receivers.data_dft: #Encode every frequency the same way. Perhaps I should encode each frequency differently to increase randomness?
                receiver_set.data_dft[freq]*= 0 #clear frequency data
                codes = self.generate_weight_vector() #generate different encoding for each frequency
                
                #now encode and add contributions from each receiver set
                for shot, code in zip(shots,codes.tolist()):
                    ### ENCODE RECEIVERS ###
                    receiver_set.data_dft[freq] += code*shot.receivers.data_dft[freq]
                    
                enc_sourceset.encode(codes, nu=freq)
                
        #Now make the SourceSet from the list of sources:
        self.sources = enc_sourceset
        self.receivers = receiver_set

    @property
    def sequential_shots(self): return self._sequential_shots
    @sequential_shots.setter
    def sequential_shots(self, shots): 
        """ Set a list of sequential shots.
        
        The list of sequential shots is used to create an
        encoded simultaneous source.
        """
        
        #Verify that each shot has a 'PointSource' source 
        for shot in shots:
            if type(shot.sources) != PointSource:
                raise Exception("The shots have to have a PointSource as source.")

        #Verify that we have a fixed-spread acquisition (Receiver locations are the same for each shot in 'shots') 
        #Also verify they have the same grid representation (delta, gaussian etc).
        receiverset_sampling_operator = shots[0].receivers.sampling_operator
        receiver_approximation_type = shots[0].receivers.receiver_list[0].approximation #'gaussian' or 'delta' for instance.
        for shot in shots:
            if np.abs(shot.receivers.sampling_operator - receiverset_sampling_operator).nnz != 0: #Inequality check sparse matrix not implemented. This is workaround.
                raise Exception("The receiver acquisition has to be the same for each shot in order to construct a supershot.")
            
            for receiver in shot.receivers.receiver_list: #assuming we have a ReceiverSet and not a single PointReceiver. I think this check is redundant when the sampling operators are identical.
                if receiver.approximation != receiver_approximation_type:
                    raise Exception("The receiver approximations are not the same. An encoded stack would make no sense.")
        
        
        self._sequential_shots = shots
        self._fixed_spread_sampling_operator = receiverset_sampling_operator #Can be used for verification when we construct the ReceiverSet with encoded data. Should have same sampling operator.
        self._receiver_approximation = receiver_approximation_type
        self._nshots = len(shots)

        #See if time or frequency data has been recorded by the ReceiverSets. Do this by checking one receiver set
        self.is_time_simulation = True #Initialize:
        if shots[0].receivers.data is None:
            if shots[0].receivers.data_dft == {}:
                raise Exception("No time or frequency data recorded yet.")
        
            self.is_time_simulation = False


        self.encode() #This will generate a randomized weighting vector. When setting this vector an encoded SourceSet and ReceiverSet are created.


                
#if __name__ == '__main__':
#
#   from pysit import * #Domain, PML, RickerWavelet, ReceiverSet, PointReceiver, PointSource, WaveSolverAcousticSecondOrder2D, generate_seismic_data
#   from pysit.gallery import horizontal_reflector
#   import time
#
#   pmlx = PML(0.1, 100)
#   pmlz = PML(0.1, 100)
#
#   x_config = (0.1, 1.0, 90, pmlx, pmlx)
#   z_config = (0.1, 0.8, 70, pmlz, pmlz)
#
#   d = Domain( (x_config, z_config) )
#
#   M, C0, C = horizontal_reflector(d)
#
#   xmax = d.x.rbound_true
#   nx   = d.x.n_true
#   zmin = d.z.lbound_true
#   zmax = d.z.rbound_true
#
#   f = RickerWavelet(25.0)
#
#   ws = PointSource(d, (0.5, 0.5), f)
#   ws2 = PointSource(d, (0.5, 0.5), f, source_approximation='delta')
#
#   Nshots = 1
#   shots = []
#
#   for i in xrange(Nshots):
#
#       # Define source location and type
#       source = PointSource(d, (xmax*(i+1.0)/(Nshots+1.0), 0.1), RickerWavelet(25.0))
#
#       # Define set of receivers
#       zpos = zmin + (1./9.)*zmax
#       xpos = np.reshape(d.generate_grid(sparse=True,exclude_pml=True)[0], (nx,))
#       receivers = [PointReceiver(d, (x, zpos)) for x in xpos[::3]] #receivers every 3 nodes
#
#       # Create and store the shot
#       shot = Shot(source, ReceiverSet(d, receivers))
#       shots.append(shot)
#
#   solver_fd_cpp = WaveSolverAcousticSecondOrder2D(d, (0.,0.3), model_parameters={'C': C}, gradient_method='fd', time_step_implementation='c++')
#
#   print('Generating data FD C++...')
#   tt = time.time()
#   # ps_fd_cpp = None
#   ps_fd_cpp = []
#   generate_seismic_data(shots, solver_fd_cpp, ps=ps_fd_cpp)
#   print 'Data generation: {0}s'.format(time.time()-tt)
#
#   import pickle
#
#   with open('foo.pkl','w') as output:
##      pickle.dump(receivers, output)
#       pickle.dump(source, output)
#




import sys
import time
import copy
import tensorflow as tf

import numpy as np
import scipy.io as sio

__all__=['pCN']

__docformat__ = "restructuredtext en"

class pCN(object):
    """ Class of pCN type MCMC method for UQ and optimization for CNN type variables
    ----------
    solver : pysit wave solver object
        A wave solver that inherits from pysit.solvers.WaveSolverBase
    ivnersion_methods : class
        A class containing all of the methods required to compute the inversion steps.
    verbose : bool
        Verbosity flag.
    xi : solver.WaveSolverParameters
        Current state of the unknowns.
    i : float
        Current iteration index.
    <blank>_history : list of tuples
        History of property (e.g., step length) with entries like the tuple (i, step_length_i) for index i.
    <blank>_frequency : int
        Iteration frequency at which to store a particular property.

    """

    def __init__(self, objective):
        """Constructor for the BasicDescentAlgorithm class.

        Parameters
        ----------
        solver : pysit wave solver object
            A wave solver that inherits from pysit.solvers.WaveSolverBase
        inversion_methods : class
            A class containing all of the methods required to compute the inversion steps.

        Notes
        -----
        * InversionMethodsType is a data type that takes a wave solver object
          as a construction argument.  The collection of inversion methods will
          depend on the solver.
        * InversionMethodsType must have member functions that implement the
          basic wave imaging procedures, e.g., forward modeling,
          adjoint modeling, demigration, etc.

        """
        self.objective_function = objective
        self.solver = objective.solver
        self.verbose = False

        self.use_parallel = objective.use_parallel()

        self.max_linesearch_iterations = 10

        self.logfile = sys.stdout
        self.proj_op = None

        self.write = False

    def __call__(self,
                 shots,
                 initial_model,
                 n_cnn_para,
                 nsmps,
                 beta,
                 noise_sigma=1.0,
                 isuq=False,
                 print_interval=10,
                 initial_value_cnn=None,
                 verbose=False,
                 append=False,
                 write=False,
                 **kwargs):
        """The main function for executing a number of steps of the descent
        algorith.

        Most things can be done without directly overriding this function.

        Parameters
        ----------
        shots : list of pysit.Shot
            List of Shots for which to compute on.
        initial_value : solver.WaveParameters
            Initial guess for the iteration.
        iteration_parameters : int, iterable
            Loop iteration parameters, like number of steps or frequency sets.
        <blank>_frequency : int, optional kwarg
            Frequency with which to store histories.  Detailed in reset method.
        verbose : bool
            Verbosity flag.
        linesearch_configuration : dictionary
            Possible parameters for linesearch, for more details, please check the introduction of the function set_linesearch_configuration

        """
        if initial_value_cnn is None:
            m0_cnn = tf.random.uniform([1, n_cnn_para])
        else:
            m0_cnn = initial_value_cnn

        phi0 = self.objective_function.evaluate(shots, initial_model, m0_cnn) / noise_sigma**2.0
        Ms = []
        A_accept = []
        Phi = []
        Ms.append(m0_cnn)
        r_probs = np.random.uniform(0.0, 1.0, nsmps)
        m_min_cnn = m0_cnn
        phi_min = phi0
        

        for i in range(nsmps):
            # mtmp_cnn = tf.random.uniform([1, n_cnn_para])
            mtmp_cnn = tf.random.normal([1, n_cnn_para])
            m1_cnn = np.sqrt(1-beta**2.0)*m0_cnn + beta*mtmp_cnn
            phi1 = self.objective_function.evaluate(shots, initial_model, m1_cnn) / noise_sigma**2.0

            if phi1 < phi_min:
                phi_min = phi1
                m_min_cnn = m1_cnn

            a_accept = np.min((np.exp(phi0-phi1), 1))
            A_accept.append(a_accept)
            Phi.append(phi1)
            # print('Accept probability:', a_accept)
            if np.mod(i,print_interval) == 0:
                print('Iteration:', i)
                print('f: ', phi_min)

            if a_accept > r_probs[i]:
                Ms.append(m1_cnn)
                m0_cnn = m1_cnn
                phi0 = phi1
            else:
                Ms.append(m0_cnn)

            

        result = dict()
        result['MAP'] = m_min_cnn
        result['samples'] = Ms
        result['accept_prob'] = A_accept
        result['Phi'] = Phi

        return result

            


            






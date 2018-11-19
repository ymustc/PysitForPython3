# Std import block
import time
import copy

import numpy as np
import matplotlib.pyplot as plt

from pysit import *
from pysit.gallery import horizontal_reflector

from GradientTest import GradientTest

if __name__ == '__main__':
    # Setup

    #   Define Domain
    pmlx = PML(0.1, 1)
    pmlz = PML(0.1, 1)


    x_config = (0.1, 1.0, pmlx, pmlx)
    z_config = (0.1, 0.8, pmlz, pmlz)

    d = RectangularDomain(x_config, z_config)

    m = CartesianMesh(d, 91, 71)

    #   Generate true wave speed
    C, C0, m, d = horizontal_reflector(m)

    # Set up shots
    zmin = d.z.lbound
    zmax = d.z.rbound
    zpos = zmin + (1./9.)*zmax

    shots = equispaced_acquisition(m,
                                   RickerWavelet(10.0),
                                   sources=1,
                                   source_depth=zpos,
                                   source_kwargs={},
                                   receivers='max',
                                   receiver_depth=zpos,
                                   receiver_kwargs={},
                                   )

    # Define and configure the wave solver
    trange = (0.0, 3)

    solver = ConstantDensityAcousticWave(m,
                                         spatial_accuracy_order=2,
                                         trange=trange,
                                         kernel_implementation='cpp',
                                         mac_C=3.0)

    # Generate synthetic Seismic data
    tt = time.time()
    wavefields = []
    base_model = solver.ModelParameters(m, {'C': C})
    generate_seismic_data(shots, solver, base_model, wavefields=wavefields)

    print('Data generation: {0}s'.format(time.time()-tt))

    objective = TemporalLeastSquares(solver)

    # Define the inversion algorithm
    grad_test = GradientTest(objective)
    grad_test.base_model = solver.ModelParameters(m, {'C': C0})
    grad_test.length_ratio = np.power(5.0, range(-8, -0))

    # Set up the perturbation direction
    dC_vec = copy.deepcopy(grad_test.base_model)
    m_size = m._shapes[(False, True)]
    tmp = np.random.normal(0, 1, m_size)
    # tmp = np.ones(m_size)
    tmp[0:3, :] = 0.0
    tmp[m_size[0]-3:m_size[0], :] = 0.0
    tmp[:, 0:3] = 0.0
    tmp[:, m_size[1]-3:m_size[1]] = 0.0
    tmp = np.reshape(tmp, grad_test.base_model.data.shape)
    dC_vec.data = tmp
    norm_dC_vec = np.linalg.norm(dC_vec.data)
    norm_base_model = np.linalg.norm(grad_test.base_model.data)
    dC_vec.data = dC_vec.data * 0.1 * (norm_base_model / norm_dC_vec)
    grad_test.model_perturbation = dC_vec
    # Execute inversion algorithm
    print('Gradient test ...')
    tt = time.time()

    result = grad_test(shots)

    print('...run time:  {0}s'.format(time.time()-tt))

    print(grad_test.objective_value)

    plt.figure()
    plt.loglog(grad_test.length_ratio, grad_test.zero_order_difference, 'b',
               grad_test.length_ratio, grad_test.length_ratio, 'r')
    plt.title('Zero order difference')
    plt.gca().legend(('df_0', 'h'))

    plt.figure()
    plt.loglog(grad_test.length_ratio, grad_test.first_order_difference, 'b',
               grad_test.length_ratio, np.power(grad_test.length_ratio, 1.0), 'y',
               grad_test.length_ratio, np.power(grad_test.length_ratio, 2.0), 'r')
    plt.title('First order difference')
    plt.gca().legend(('df_1', 'h', 'h^2'))

    plt.show()


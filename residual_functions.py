# This file contains the function definitions that calculate the residuals and
# their associated gradients.

import numpy as np
from Trajectory import Trajectory
import trajectory_functions as traj_funcs

def resolvent_inv(no_modes, freq, jac_at_mean):
    """
        This function calculates the resolvent operator for a given mode number
        n, system, and fundamental frequency.

        Parameters
        ----------
        n: positive integer
            mode number for the resolvent operator
        sys: System object
            the dynamical system required to calculate the Jacobian matrix
        freq: float
            the frequency of the trajectory
        dim: positive integer
            dimension of the dynamical system
        mean: vector
            the mean of the state-space trajectory
        
        Returns
        -------
        resolvent: numpy array
            the resolvent operator for the given mode number, system, and
            frequency
    """
    # evaluate the number of dimensions using the size of the jacobian
    dim = np.shape(jac_at_mean)[0]

    # initialise the resolvent list
    resolvent_inv = [None]*no_modes

    # loop over calculating the value at each wavenumber
    for n in range(no_modes):
        # resolvent[n] = np.linalg.inv((1j*n*freq*np.identity(dim)) - jac_at_mean)
        resolvent_inv[n] = (1j*n*freq*np.identity(dim)) - jac_at_mean

    # set mean mode resolvent to array of zeros
    resolvent_inv[0] = np.zeros_like(resolvent_inv[1])

    return Trajectory(resolvent_inv)

def local_residual(traj, sys, freq, mean):
    """
        This function calculates the local residual of a trajectory through a
        state-space defined by a given dynamical system.

        Parameters
        ----------
        traj: Trajectory object
            the trajectory through state-space
        sys: System object
            the dynamical system defining the state-space
        freq: float
            the fundamental frequency of the trajectory
        mean: vector
            the mean of the state-space trajectory
        
        Returns
        -------
        residual_traj: Trajectory object
            the local residual of the trajectory with respect to the dynamical
            system, given as an instance of the Trajectory class
    """
    # evaluate jacobian at the mean
    jac_at_mean = sys.jacobian(mean)

    # evaluate the inverse resolvents
    H_n_inv = resolvent_inv(traj.shape[0], freq, jac_at_mean)

    # evaluate response and multiply by resolvent at every mode
    resp = traj_funcs.traj_response(traj, sys.nl_factor)

    # evaluate local residual trajectory for all modes
    H_inv_traj_mult = H_n_inv @ traj
    local_res = H_inv_traj_mult - resp

    # reassign the mean mode to the second constraint
    local_res[0] = -sys.response(mean) - resp[0]

    return local_res

def global_residual(traj, sys, freq, mean):
    """
        This function calculates the global residual of a trajectory through a
        state-space defined by a given dynamical system.

        Parameters
        ----------
        traj: Trajectory object
            the trajectory through state-space
        sys: System object
            the dynamical system defining the state-space
        freq: float
            the fundamental frequency of the trajectory
        
        Returns
        -------
        global_res: float
            the global residual of the trajectory-system pair
    """
    # calcualte the local residual
    local_res = local_residual(traj, sys, freq, mean)

    # initialise and sum the norms of the complex residual vectors
    sum = 0
    for n in range(1, local_res.shape[0]):
        sum += np.dot(np.conj(local_res[n]), local_res[n])

    # add the zero mode for the mean constraint
    sum += 0.5*np.dot(np.conj(local_res[0]), local_res[0])

    return np.real(sum)

def gr_traj_grad(traj, sys, freq, mean, conv_method = 'fft'):
    """
        This function calculates the gradient of the global residual with
        respect to the trajectory and the associated fundamental frequency for
        a trajectory through a state-space defined by a given dynamical system.

        Parameters
        ----------
        traj: Trajectory object
            the trajectory through state-space
        sys: System object
            the dynamical system defining the state-space
        freq: float
            the fundamental frequency of the trajectory
        
        Returns
        -------
        d_gr_wrt_traj: Trajectory object
            the gradient of the global residual with respect to the trajectory,
            given as an instance of the Trajectory class
        d_gr_wrt_freq: float
            the gradient of the global residual with respect to the trajectory
    """
    # calculate local residual trajectory
    local_res = local_residual(traj, sys, freq, mean)

    # calculate trajectory gradients
    res_grad = traj_funcs.traj_grad(local_res)

    # initialise jacobian function and take transpose
    traj[0] = np.array(mean, dtype = complex)
    jac = traj_funcs.traj_response(traj, sys.jacobian)
    traj[0] = np.zeros_like(traj[1])
    jac = traj_funcs.transpose(jac)

    # perform convolution
    jac_res_conv = traj_funcs.traj_conv(jac, local_res, method = conv_method)

    # calculate and return gradients w.r.t trajectory and frequency respectively
    # return 2*((-freq*res_grad) - jac_res_conv)
    return (-freq*res_grad) - jac_res_conv

def gr_freq_grad(traj, sys, freq, mean):
    # calculate local residual
    local_res = local_residual(traj, sys, freq, mean)

    # initialise sum and loop over modes
    sum = 0
    for n in range(1, traj.shape[0]):
        sum += n*np.imag(np.dot(np.conj(traj[n]), local_res[n]))
    sum = 2*sum

    # return sum
    # return 0.001*sum
    return 0

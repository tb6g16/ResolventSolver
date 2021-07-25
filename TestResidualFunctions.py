# This file contains the tests for the residual calculation functions defined
# in the residual_functions file.

import unittest
import numpy as np
import scipy.integrate as integ
import random as rand

from Trajectory import Trajectory
import residual_functions as res_funcs
from my_fft import my_rfft, my_irfft
from trajectory_definitions import unit_circle as uc
from trajectory_definitions import ellipse as elps
from trajectory_definitions import unit_circle_3d as uc3
from systems import van_der_pol as vpd
from systems import viswanath as vis
from systems import lorenz

import matplotlib.pyplot as plt

class TestResidualFunctions(unittest.TestCase):

    def setUp(self):
        self.traj1 = Trajectory(uc.x)
        # self.freq1 = 1
        self.traj2 = Trajectory(elps.x)
        # self.freq2 = 1
        self.traj3 = Trajectory(uc3.x)
        self.sys1 = vpd
        self.sys2 = vis
        self.sys3 = lorenz

    def tearDown(self):
        del self.traj1
        del self.traj2
        del self.traj3
        del self.sys1
        del self.sys2
        del self.sys3

    def test_resolvent_inv(self):
        rho = rand.uniform(0, 30)
        beta = rand.uniform(0, 10)
        sigma = rand.uniform(0, 30)
        z_mean = rand.uniform(0, 50)
        freq = rand.uniform(0, 10)
        self.sys3.parameters['sigma'] = sigma
        self.sys3.parameters['beta'] = beta
        self.sys3.parameters['rho'] = rho
        jac_at_mean_sys3 = self.sys3.jacobian([0, 0, z_mean])
        H_sys3 = res_funcs.resolvent_inv(self.traj3.shape[0], freq, jac_at_mean_sys3)
        resolvent_true = Trajectory(np.zeros([self.traj3.shape[0], 3, 3], dtype = complex))
        for n in range(1, self.traj3.shape[0]):
            D_n = ((1j*n*freq) + sigma)*((1j*n*freq) + 1) + sigma*(z_mean - rho)
            resolvent_true[n, 0, 0] = ((1j*n*freq) + 1)/D_n
            resolvent_true[n, 1, 0] = (rho - z_mean)/D_n
            resolvent_true[n, 0, 1] = sigma/D_n
            resolvent_true[n, 1, 1] = ((1j*n*freq) + sigma)/D_n
            resolvent_true[n, 2, 2] = 1/((1j*n*freq) + beta)
            resolvent_true[n] = np.linalg.inv(np.copy(resolvent_true[n]))
        self.assertEqual(H_sys3, resolvent_true)

    def test_local_residual(self):
        # generating random frequencies and system parameters
        freq1 = rand.uniform(-10, 10)
        freq2 = rand.uniform(-10, 10)
        mu1 = rand.uniform(0, 10)
        mu2 = rand.uniform(0, 10)
        r = rand.uniform(0, 10)

        # apply parameters
        self.sys1.parameters['mu'] = mu1
        self.sys2.parameters['mu'] = mu2
        self.sys2.parameters['r'] = r

        # generate local residual trajectories
        lr_traj1_sys1 = res_funcs.local_residual(self.traj1, self.sys1, freq1, np.zeros([2]))
        lr_traj2_sys1 = res_funcs.local_residual(self.traj2, self.sys1, freq2, np.zeros([2]))

        # output is of Trajectory class
        self.assertIsInstance(lr_traj1_sys1, Trajectory)
        self.assertIsInstance(lr_traj2_sys1, Trajectory)

        # output is of correct shape
        self.assertEqual(lr_traj1_sys1.shape, self.traj1.shape)
        self.assertEqual(lr_traj2_sys1.shape, self.traj2.shape)

        # outputs are numbers
        temp = True
        if lr_traj1_sys1.modes.dtype != np.complex128:
            temp = False
        if lr_traj2_sys1.modes.dtype != np.complex128:
            temp = False
        self.assertTrue(temp)

        # correct values
        lr_traj1_sys1_true = np.zeros_like(my_irfft(self.traj1.modes))
        lr_traj2_sys1_true = np.zeros_like(my_irfft(self.traj2.modes))
        for i in range(np.shape(lr_traj1_sys1_true)[0]):
            s = ((2*np.pi)/np.shape(lr_traj1_sys1_true)[0])*i
            lr_traj1_sys1_true[i, 0] = (1 - freq1)*np.sin(s)
            lr_traj1_sys1_true[i, 1] = (mu1*(1 - (np.cos(s)**2))*np.sin(s)) + ((1 - freq1)*np.cos(s))
        lr_traj1_sys1_true = Trajectory(my_rfft(lr_traj1_sys1_true))
        for i in range(np.shape(lr_traj2_sys1_true)[0]):
            s = ((2*np.pi)/np.shape(lr_traj2_sys1_true)[0])*i
            lr_traj2_sys1_true[i, 0] = (1 - (2*freq2))*np.sin(s)
            lr_traj2_sys1_true[i, 1] = ((2 - freq2)*np.cos(s)) + (mu1*(1 - (4*(np.cos(s)**2)))*np.sin(s))
        lr_traj2_sys1_true = Trajectory(my_rfft(lr_traj2_sys1_true))
        self.assertEqual(lr_traj1_sys1, lr_traj1_sys1_true)
        self.assertEqual(lr_traj2_sys1, lr_traj2_sys1_true)

    def test_global_residual(self):
        # generating random frequencies and system parameters
        freq1 = rand.uniform(-10, 10)
        freq2 = rand.uniform(-10, 10)
        mu1 = rand.uniform(0, 10)
        mu2 = rand.uniform(0, 10)
        r = rand.uniform(0, 10)

        # apply parameters
        self.sys1.parameters['mu'] = mu1
        self.sys2.parameters['mu'] = mu2
        self.sys2.parameters['r'] = r

        # calculate global residuals
        lr_t1s1 = res_funcs.local_residual(self.traj1, self.sys1, freq1, np.zeros([2]))
        lr_t2s1 = res_funcs.local_residual(self.traj2, self.sys1, freq2, np.zeros([2]))
        gr_traj1_sys1 = res_funcs.global_residual(lr_t1s1)
        gr_traj2_sys1 = res_funcs.global_residual(lr_t2s1)

        # output is a positive number
        temp = True
        if type(gr_traj1_sys1) != np.int64 and type(gr_traj1_sys1) != np.float64:
            temp = False
        if type(gr_traj2_sys1) != np.int64 and type(gr_traj2_sys1) != np.float64:
            temp = False
        self.assertTrue(temp)

        # correct values
        gr_traj1_sys1_true = ((5*(mu1**2))/32) + (((freq1 - 1)**2)/2)
        gr_traj2_sys1_true = (1/4)*((((2*freq2) - 1)**2) + ((2 - freq2)**2) + mu1**2)
        self.assertAlmostEqual(gr_traj1_sys1, gr_traj1_sys1_true, places = 6)
        self.assertAlmostEqual(gr_traj2_sys1, gr_traj2_sys1_true, places = 6)

    def est_global_residual_grad(self):
        # generating random frequencies and system parameters
        freq1 = rand.uniform(-10, 10)
        freq2 = rand.uniform(-10, 10)
        mu1 = rand.uniform(0, 10)
        mu2 = rand.uniform(0, 10)
        r = rand.uniform(0, 10)

        # apply parameters
        self.sys1.parameters['mu'] = mu1
        self.sys2.parameters['mu'] = mu2
        self.sys2.parameters['r'] = r

        # calculate global residual gradients
        gr_grad_traj_traj1_sys1, gr_grad_freq_traj1_sys1 = res_funcs.global_residual_grad(self.traj1, self.sys1, freq1)
        gr_grad_traj_traj2_sys1, gr_grad_freq_traj2_sys1 = res_funcs.global_residual_grad(self.traj2, self.sys1, freq2)
        gr_grad_traj_traj1_sys2, gr_grad_freq_traj1_sys2 = res_funcs.global_residual_grad(self.traj1, self.sys2, freq1)
        gr_grad_traj_traj2_sys2, gr_grad_freq_traj2_sys2 = res_funcs.global_residual_grad(self.traj2, self.sys2, freq2)

        # outputs are numbers
        temp_traj = True
        temp_freq = True
        if gr_grad_traj_traj1_sys1.curve_array.dtype != np.int64 and gr_grad_traj_traj1_sys1.curve_array.dtype != np.float64:
            temp_traj = False
        if gr_grad_traj_traj2_sys1.curve_array.dtype != np.int64 and gr_grad_traj_traj2_sys1.curve_array.dtype != np.float64:
            temp_traj = False
        if gr_grad_traj_traj1_sys2.curve_array.dtype != np.int64 and gr_grad_traj_traj1_sys2.curve_array.dtype != np.float64:
            temp_traj = False
        if gr_grad_traj_traj2_sys2.curve_array.dtype != np.int64 and gr_grad_traj_traj2_sys2.curve_array.dtype != np.float64:
            temp_traj = False
        if type(gr_grad_freq_traj1_sys1) != np.int64 != type(gr_grad_freq_traj1_sys1) != np.float64:
            temp_freq = False
        if type(gr_grad_freq_traj2_sys1) != np.int64 != type(gr_grad_freq_traj2_sys1) != np.float64:
            temp_freq = False
        if type(gr_grad_freq_traj1_sys2) != np.int64 != type(gr_grad_freq_traj1_sys2) != np.float64:
            temp_freq = False
        if type(gr_grad_freq_traj2_sys2) != np.int64 != type(gr_grad_freq_traj2_sys2) != np.float64:
            temp_freq = False
        self.assertTrue(temp_traj)
        self.assertTrue(temp_freq)

        # correct values (compared with FD approximation)
        gr_grad_traj_traj1_sys1_FD, gr_grad_freq_traj1_sys1_FD = self.gen_gr_grad_FD(self.traj1, self.sys1, freq1)
        gr_grad_traj_traj2_sys1_FD, gr_grad_freq_traj2_sys1_FD = self.gen_gr_grad_FD(self.traj2, self.sys1, freq2)
        gr_grad_traj_traj1_sys2_FD, gr_grad_freq_traj1_sys2_FD = self.gen_gr_grad_FD(self.traj1, self.sys2, freq1)
        gr_grad_traj_traj2_sys2_FD, gr_grad_freq_traj2_sys2_FD = self.gen_gr_grad_FD(self.traj2, self.sys2, freq2)

        # fig, (ax1, ax2, ax3) = plt.subplots(figsize = (12, 5), nrows = 3)
        # pos1 = ax1.matshow(gr_grad_traj_traj2_sys2.curve_array)
        # pos2 = ax2.matshow(gr_grad_traj_traj2_sys2_FD.curve_array)
        # pos3 = ax3.matshow(abs(gr_grad_traj_traj2_sys2.curve_array - gr_grad_traj_traj2_sys2_FD.curve_array))
        # fig.colorbar(pos1, ax = ax1)
        # fig.colorbar(pos2, ax = ax2)
        # fig.colorbar(pos3, ax = ax3)
        # plt.show()

        # LARGEST ERRORS AT POINTS OF EXTREMA IN MATRIX ALONG TIME DIMENSION

        # Passes consistently with rtol, atol = 1e-2
        self.assertEqual(gr_grad_traj_traj1_sys1, gr_grad_traj_traj1_sys1_FD)
        # Mostly passes with rtol, atol = 1e-2
        self.assertEqual(gr_grad_traj_traj2_sys1, gr_grad_traj_traj2_sys1_FD)
        # Passes consistently with rtol, atol = 5e-1
        self.assertEqual(gr_grad_traj_traj1_sys2, gr_grad_traj_traj1_sys2_FD)
        # Passes consistently with rtol, atol = 5e-1
        self.assertEqual(gr_grad_traj_traj2_sys2, gr_grad_traj_traj2_sys2_FD)
        self.assertAlmostEqual(gr_grad_freq_traj1_sys1, gr_grad_freq_traj1_sys1_FD, places = 6)
        self.assertAlmostEqual(gr_grad_freq_traj2_sys1, gr_grad_freq_traj2_sys1_FD, places = 6)
        self.assertAlmostEqual(gr_grad_freq_traj1_sys2, gr_grad_freq_traj1_sys2_FD, places = 6)
        self.assertAlmostEqual(gr_grad_freq_traj2_sys2, gr_grad_freq_traj2_sys2_FD, places = 6)

    @staticmethod
    def gen_gr_grad_FD(traj, sys, freq, step = 1e-6):
        """
            This function uses finite differencing to compute the gradients of
            the global residual for all the DoFs (the discrete time coordinated
            and the frequency).
        """
        # initialise arrays
        gr_grad_FD_traj = np.zeros(traj.shape)

        # loop over trajectory DoFs and use CD scheme
        for i in range(traj.shape[0]):
            for j in range(traj.shape[1]):
                traj_for = traj
                traj_for[i, j] = traj[i, j] + step
                gr_traj_for = res_funcs.global_residual(traj_for, sys, freq)
                traj_back = traj
                traj_back[i, j] = traj[i, j] - step
                gr_traj_back = res_funcs.global_residual(traj_back, sys, freq)
                gr_grad_FD_traj[i, j] = (gr_traj_for - gr_traj_back)/(2*step)
        gr_grad_FD_traj = Trajectory(gr_grad_FD_traj)

        # calculate gradient w.r.t frequency
        gr_freq_for = res_funcs.global_residual(traj, sys, freq + step)
        gr_freq_back = res_funcs.global_residual(traj, sys, freq - step)
        gr_grad_FD_freq = (gr_freq_for - gr_freq_back)/(2*step)

        return gr_grad_FD_traj, gr_grad_FD_freq


if __name__ == "__main__":
    unittest.main()

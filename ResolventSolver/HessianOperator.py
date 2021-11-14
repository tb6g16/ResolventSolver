# This file contains the definition of the Hessian operator class as a subclass
# of the LinearOperator abstract class given by the SciPy sparse linear algebra
# library.

import numpy as np
from scipy.sparse.linalg import LinearOperator

from ResolventSolver.traj2vec import traj2vec, vec2traj
from ResolventSolver.my_min import init_opt_funcs

class HessianOperator(LinearOperator):

    def __init__(self, traj, sys, freq, mean):
        self.state = traj2vec(traj)
        self.dim = traj.shape[1]
        _, self.grad_func = init_opt_funcs(traj.shape[0], freq, sys, traj.shape[1], mean)
        self.shape = (np.shape(self.state)[0], np.shape(self.state)[0])
        self.dtype = np.dtype('float64')

    def _matvec(self, v):
        """
            Return the Hessian-vector product by taking the difference of the
            gradients.
        """
        return self.grad_func(self.state + v) - self.grad_func(self.state)

    def _rmatvec(self, v):
        """
            Return the matrix-vector product of an arbitrary vector and the
            adjoint of the Hessian (equivalent to left multiplication of a
            row vector).
        """
        return self.grad_func(self.state + v) - self.grad_func(self.state)

    @property
    def traj(self):
        return vec2traj(self.state, self.dim)

    @traj.setter
    def traj(self, new_traj):
        self.dim = new_traj.shape[1]
        self.state = traj2vec(new_traj)
        self.shape = (np.shape(self.state)[0], np.shape(self.state)[0])

    @property
    def hess_matrix(self, eps = 1e-6):
        # intialise hessian matrix
        hessian = np.zeros(self.shape)

        # precompute the gradient for the given trajectory
        grad_at_min = self.grad_func(self.state)

        # loop over columns of hessian matrix
        for j in range(self.shape[0] - 1):
            # define unit basis in j-th direction
            unit_basis_j = np.zeros(self.shape[0])
            unit_basis_j[j] = 1.0

            # calculate gradient at two close states at minimum
            grad_off_min = self.grad_func(self.state + eps*unit_basis_j)

            # evaluate hessian column
            hessian[:, j] = (grad_at_min - grad_off_min)/eps

        return hessian[:-1, :-1]

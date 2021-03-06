"""
Filename: oligopoly.py
Authors: Chase Coleman

This is an example for the lecture dyn_stack.rst from the QuantEcon
series of lectures by Tom Sargent and John Stachurski.

We deal with a large monopolistic firm who faces costs:

C_t = e Q_t + .5 g Q_t^2 + .5 c (Q_{t+1} - Q_t)^2

where the fringe firms face:

sigma_t = d q_t + .5 h q_t^2 + .5 c (q_{t+1} - q_t)^2

Additionally, there is a linear inverse demand curve of the form:

p_t = A_0 - A_1 (Q_t + \bar{q_t}) + \eta_t,

where:

.. math
    \eta_{t+1} = \rho \eta_t + C_{\varepsilon} \varepsilon_{t+1};
    \varepsilon_{t+1} \sim N(0, 1)

For more details, see the lecture.
"""
import numpy as np
import scipy.linalg as la
from quantecon import LQ
from quantecon.matrix_eqn import solve_discrete_lyapunov
from scipy.optimize import root


def setup_matrices(params):
    """
    This function sets up the A, B, R, Q for the oligopoly problem
    described in the lecture.

    Parameters
    ----------
    params : Array(Float, ndim=1)
        Contains the parameters that describe the problem in the order
        [a0, a1, rho, c_eps, c, d, e, g, h, beta]

    Returns
    -------
    (A, B, Q, R) : Array(Float, ndim=2)
        These matrices describe the oligopoly problem.
    """

    # Left hand side of (37)
    Alhs = np.eye(5)
    Alhs[4, :] = np.array([a0-d, 1., -a1, -a1-h, c])
    Alhsinv = la.inv(Alhs)

    # Right hand side of (37)
    Brhs = np.array([[0., 0., 1., 0., 0.]]).T
    Arhs = np.eye(5)
    Arhs[1, 1] = rho
    Arhs[3, 4] = 1.
    Arhs[4, 4] = c / beta

    # R from equation (40)
    R = np.array([[0., 0., (a0-e)/2., 0., 0.],
                  [0., 0., 1./2., 0., 0.],
                  [(a0-e)/2., 1./2, -a1 - .5*g, -a1/2, 0.],
                  [0., 0., -a1/2, 0., 0.],
                  [0., 0., 0., 0., 0.]])
    Q = np.array([[c/2]])

    A = Alhsinv.dot(Arhs)
    B = Alhsinv.dot(Brhs)

    return A, B, Q, R


def find_PFd(A, B, Q, R, beta=.95):
    """
    Taking the parameters A, B, Q, R as found in the `setup_matrices`,
    we find the value function of the optimal linear regulator problem.
    This is steps 2 and 3 in the lecture notes.

    Parameters
    ----------
    (A, B, Q, R) : Array(Float, ndim=2)
        The matrices that describe the oligopoly problem

    Returns
    -------
    (P, F, d) : Array(Float, ndim=2)
        The matrix that describes the value function of the optimal
        linear regulator problem.

    """

    lq = LQ(Q, -R, A, B, beta=beta)
    P, F, d = lq.stationary_values()

    return P, F, d


def solve_for_opt_policy(params, eta0=0., Q0=0., q0=0.):
    """
    Taking the parameters as given, solve for the optimal decision rules
    for the firm.

    Parameters
    ----------
    params : Array(Float, ndim=1)
        This holds all of the model parameters in an array

    Returns
    -------
    out :

    """
    # Step 1/2: Formulate/Solve the optimal linear regulator
    (A, B, Q, R) = setup_matrices(params)
    (P, F, d) = find_PFd(A, B, Q, R, beta=beta)

    # Step 3: Convert implementation into state variables (Find coeffs)
    P22 = P[-1, -1]
    P21 = P[-1, :-1]
    P22inv = P22**(-1)
    dotmat = np.empty((5, 5))
    upper = np.eye(4, 5)  # Gives me 4x4 identity with a column of 0s
    lower = np.hstack([-P22inv*P21, P22inv])
    dotmat[:-1, :] = upper
    dotmat[-1, :] = lower

    coeffs = np.dot(-F, dotmat)

    # Step 4: Find optimal x_0 and \mu_{x, 0}
    z0 = np.array([1., eta0, Q0, q0])
    x0 = -P22inv*np.dot(P21, z0)
    D0 = -np.dot(P22inv, P21)

    # Do some rearranging for convenient representation of policy
    # TODO: Finish getting the equations into the from
    # u_t = rho u_{t-1} + gamma_1 z_t + gamma_2 z_{t-1}

    part1 = np.vstack([np.eye(4, 5), P[-1, :]])
    part2 = A - np.dot(B, F)
    part3 = dotmat
    m = np.dot(part1, part2).dot(part3)
    m12 = m[-1, :-1]
    m22 = m[-1, -1]

    f = np.dot(-F, dotmat)
    f11 = f[-1, :-1]
    f12 = f[-1, -1]

    coeff_utm1 = f12*m22*f12**(-1)
    coeff_zt = coeffs[0, :-1]
    coeff_ztm1 = f12*(m12 - f12**(-1)*m22*f11)

    return P, F, D0


# Parameter values
a0 = 100.
a1 = 1.
rho = .8
c_eps = .2
c = 1.
d = 20.
e = 20.
g = .2
h = .2
beta = .95
params = np.array([a0, a1, rho, c_eps, c, d, e, g, h, beta])


P, F, D0  = solve_for_opt_policy(params)

print("P = "), P
print("F = "), F
print("D0 = "), D0


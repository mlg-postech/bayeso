# bo
# author: Jungtaek Kim (jtkim@postech.ac.kr)
# last updated: June 23, 2018

import numpy as np
from scipy.optimize import minimize
import sobol_seq

from bayeso import gp
from bayeso import acquisition
from bayeso.utils import utils_common
from bayeso.utils import utils_bo
from bayeso import constants


# TODO: I am not sure, but flatten() should be replaced.
class BO():
    def __init__(self, arr_range,
        str_cov=constants.STR_GP_COV,
        str_acq=constants.STR_BO_ACQ,
        is_ard=True,
        prior_mu=None,
        verbose=False,
        debug=False,
    ):
        # TODO: use is_ard.
        # TODO: add debug cases.
        assert isinstance(arr_range, np.ndarray)
        assert isinstance(str_cov, str)
        assert isinstance(str_acq, str)
        assert isinstance(is_ard, bool)
        assert isinstance(verbose, bool)
        assert isinstance(debug, bool)
        assert callable(prior_mu) or prior_mu is None
        assert len(arr_range.shape) == 2
        assert arr_range.shape[1] == 2
        assert (arr_range[:, 0] <= arr_range[:, 1]).all()

        self.arr_range = arr_range
        self.num_dim = arr_range.shape[0]
        self.str_cov = str_cov
        self.str_acq = str_acq
        self.is_ard = is_ard
        self.verbose = verbose
        self.debug = debug
        self.prior_mu = prior_mu

    def _get_initial_grid(self, int_grid=constants.NUM_BO_GRID):
        assert isinstance(int_grid, int)

        arr_initials = utils_bo.get_grid(self.arr_range, int_grid)
        return arr_initials

    def _get_initial_uniform(self, int_samples, int_seed=None):
        assert isinstance(int_seed, int) or int_seed is None
        
        if int_seed is not None:
            np.random.seed(int_seed)
        list_initials = []
        for _ in range(0, int_samples):
            list_initial = []
            for elem in self.arr_range:
                list_initial.append(np.random.uniform(elem[0], elem[1]))
            list_initials.append(np.array(list_initial))
        arr_initials = np.array(list_initials)
        return arr_initials

    # TODO: I am not sure, but noise can be added.
    def _get_initial_sobol(self, int_samples, int_seed=None):
        assert isinstance(int_seed, int) or int_seed is None

        if int_seed is None:
            int_seed = np.random.randint(0, 10000)
        if self.debug:
            print('DEBUG: _get_initial_sobol: int_seed')
            print(int_seed)
        arr_samples = sobol_seq.i4_sobol_generate(self.num_dim, int_samples, int_seed)
        arr_samples = arr_samples * (self.arr_range[:, 1].flatten() - self.arr_range[:, 0].flatten()) + self.arr_range[:, 0].flatten()
        return arr_samples

    def _get_initial_latin(self, int_samples):
        pass

    def get_initial(self, str_initial_method,
        fun_objective=None,
        int_samples=constants.NUM_ACQ_SAMPLES,
        int_seed=None,
    ):
        assert isinstance(str_initial_method, str)
        assert callable(fun_objective) or fun_objective is None
        assert isinstance(int_samples, int)
        assert isinstance(int_seed, int) or int_seed is None

        if str_initial_method == 'grid':
            assert fun_objective is not None
            arr_initials = self._get_initial_grid()
            arr_initials = utils_bo.get_best_acquisition(arr_initials, fun_objective)
        elif str_initial_method == 'uniform':
            arr_initials = self._get_initial_uniform(int_samples, int_seed=int_seed)
        elif str_initial_method == 'sobol':
            arr_initials = self._get_initial_sobol(int_samples, int_seed=int_seed)
        elif str_initial_method == 'latin':
            raise NotImplementedError('get_initial: latin')
        else:
            raise ValueError('get_initial: missing condition for str_initial_method')
        if self.debug:
            print('DEBUG: get_initial: arr_initials')
            print(arr_initials)
        return arr_initials

    def _optimize_objective(self, fun_acquisition, X_train, Y_train, X_test, cov_X_X, inv_cov_X_X, hyps):
        X_test = np.atleast_2d(X_test)
        pred_mean, pred_std = gp.predict_test_(X_train, Y_train, X_test, cov_X_X, inv_cov_X_X, hyps, self.str_cov, self.prior_mu)
        acquisitions = fun_acquisition(pred_mean.flatten(), pred_std.flatten(), Y_train=Y_train)
        return acquisitions

    def _optimize(self, fun_objective, str_initial_method):
        assert str_initial_method in constants.ALLOWED_INITIALIZATIONS_OPTIMIZER
        list_bounds = []
        for elem in self.arr_range:
            list_bounds.append(tuple(elem))
        arr_initials = self.get_initial(str_initial_method, fun_objective=fun_objective)
        list_next_point = []
        for arr_initial in arr_initials:
            next_point = minimize(
                fun_objective,
                x0=arr_initial,
                bounds=list_bounds,
                method=constants.STR_OPTIMIZER_METHOD_BO,
                options={'disp': self.verbose}
            )
            list_next_point.append(next_point.x)
            if self.verbose:
                print('INFORM: _optimize: optimized result for acq. ', next_point.x)
        next_point = utils_bo.get_best_acquisition(np.array(list_next_point), fun_objective)
        return next_point.flatten()

    def optimize(self, X_train, Y_train, str_initial_method=constants.STR_OPTIMIZER_INITIALIZATION):
        assert isinstance(X_train, np.ndarray)
        assert isinstance(Y_train, np.ndarray)
        assert isinstance(str_initial_method, str)
        assert len(X_train.shape) == 2
        assert len(Y_train.shape) == 2
        assert Y_train.shape[1] == 1
        assert X_train.shape[0] == Y_train.shape[0]
        assert X_train.shape[1] == self.num_dim

        cov_X_X, inv_cov_X_X, hyps = gp.get_optimized_kernel(X_train, Y_train, self.prior_mu, self.str_cov, verbose=self.verbose)

        if self.str_acq == 'pi':
            fun_acquisition = acquisition.pi
        elif self.str_acq == 'ei':
            fun_acquisition = acquisition.ei
        elif self.str_acq == 'ucb':
            fun_acquisition = acquisition.ucb
        else:
            raise ValueError('optimize: missing condition for self.str_acq.')
      
        fun_objective = lambda X_test: -1.0 * constants.MULTIPLIER_ACQ * self._optimize_objective(fun_acquisition, X_train, Y_train, X_test, cov_X_X, inv_cov_X_X, hyps)
        next_point = self._optimize(fun_objective, str_initial_method=str_initial_method)
        return next_point, cov_X_X, inv_cov_X_X, hyps

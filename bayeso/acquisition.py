# acquisition
# author: Jungtaek Kim (jtkim@postech.ac.kr)
# last updated: June 12, 2018

import numpy as np
import scipy.stats

from bayeso import constants


def pi(pred_mean, pred_std, Y_train, jitter=constants.JITTER_ACQ):
    assert isinstance(pred_mean, np.ndarray)
    assert isinstance(pred_std, np.ndarray)
    assert isinstance(Y_train, np.ndarray)
    assert isinstance(jitter, float)
    assert len(pred_mean.shape) == 1
    assert len(pred_std.shape) == 1
    assert len(Y_train.shape) == 2
    assert pred_mean.shape[0] == pred_std.shape[0]

    with np.errstate(divide='ignore'):
        val_z = (np.min(Y_train) - pred_mean) / (pred_std + jitter)
    return scipy.stats.norm.cdf(val_z)

def ei(pred_mean, pred_std, Y_train, jitter=constants.JITTER_ACQ):
    assert isinstance(pred_mean, np.ndarray)
    assert isinstance(pred_std, np.ndarray)
    assert isinstance(Y_train, np.ndarray)
    assert isinstance(jitter, float)
    assert len(pred_mean.shape) == 1
    assert len(pred_std.shape) == 1
    assert len(Y_train.shape) == 2
    assert pred_mean.shape[0] == pred_std.shape[0]

    with np.errstate(divide='ignore'):
        val_z = (np.min(Y_train) - pred_mean) / (pred_std + jitter)
    return (np.min(Y_train) - pred_mean) * scipy.stats.norm.cdf(val_z) + pred_std * scipy.stats.norm.pdf(val_z)

def ucb(pred_mean, pred_std, kappa=2.0, Y_train=None, is_increased=True):
    assert isinstance(pred_mean, np.ndarray)
    assert isinstance(pred_std, np.ndarray)
    assert isinstance(Y_train, np.ndarray)
    assert isinstance(kappa, float)
    assert isinstance(is_increased, bool)
    assert len(pred_mean.shape) == 1
    assert len(pred_std.shape) == 1
    assert len(Y_train.shape) == 2
    assert pred_mean.shape[0] == pred_std.shape[0]

    if is_increased and Y_train is not None:
        kappa_ = kappa * np.log(Y_train.shape[0])
    else:
        kappa_ = kappa
    return -pred_mean + kappa_ * pred_std

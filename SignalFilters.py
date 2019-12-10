import numpy as np
from scipy.signal import butter, lfilter

class BaseFilter:
    def apply(self, chunk: np.ndarray):
        '''
        :param chunk:
        :return:
        '''
        raise NotImplementedError

class NotchFilter(BaseFilter):
    def __init__(self, f0, fs, n_channels, mu=0.05):
        self.n_channels = n_channels
        w0 = 2*np.pi*f0/fs
        self.a = np.array([1., 2 * (mu - 1) * np.cos(w0), (1 - 2 * mu)])
        self.b = np.array([1., -2 * np.cos(w0), 1.]) * (1 - mu)
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, n_channels))

    def apply(self, chunk: np.ndarray):
        y, self.zi = lfilter(self.b, self.a, chunk, axis=0, zi=self.zi)
        return y

    def reset(self):
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, self.n_channels))

class ButterFilter(BaseFilter):
    def __init__(self, band, fs, n_channels, order=4):
        self.n_channels = n_channels
        low, high = band
        if low is None and high is None:
            raise ValueError('band should involve one or two not None values')
        elif low is None:
            self.b, self.a = butter(order, high/fs*2, btype='low')
        elif high is None:
            self.b, self.a = butter(order, low/fs*2, btype='high')
        else:
            self.b, self.a = butter(order, [low/fs*2, high/fs*2], btype='band')
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, n_channels))

    def apply(self, chunk: np.ndarray):
        y, self.zi = lfilter(self.b, self.a, chunk, axis=0, zi=self.zi)
        return y

    def reset(self):
        self.zi = np.zeros((max(len(self.b), len(self.a)) - 1, self.n_channels))
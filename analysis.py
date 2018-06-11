"""The functions in this module are made for peak detection.
Currently it consists of one function, this should be refactored.
This is very hackish and will likely change
"""
# todo create class which can then be subclassed

__author__ = "Gerald Ebberink"
__copyright__ = "Copyright 2016-2017"
__license__ = "GPLv2"
__version__ = "2.0.0"
__maintainer__ = "Gerald Ebberink"
__email__ = "g.h.p.ebberink@saxion.nl"
__status__ = "Prototype"

import peakutils
import numpy
import numpy.fft.fftpack
import scipy.signal
from scipy import optimize


# noinspection PyAttributeOutsideInit
class Analysis:
    """In this class the main MRR analysis is done"""
    def __init__(self, step_rejection=None):
        self.reference_data = None
        self.k_factor = 5
        self.jump_compensation = 0
        self.step_rejection = 20
        if step_rejection is not None:
            self.step_rejection = step_rejection
        self.previous_data = 0

    @staticmethod
    def simple_peak_find(data, min_distance):
        """"This function is an implementation of the peakutils peak find"""
        all_peaks = peakutils.indexes(data[1:],
                                      thres=0.1 / numpy.max(data[1:]),
                                      min_dist=min_distance)
        # return the last peak, unless there is no peak then return NaN
        try:
            peak = all_peaks[-1]
        except IndexError:
            peak = numpy.nan
        return peak

    def simple_shift_find(self, data):
        """"This function uses the simple peak find to find the shift.
        The first data given is made the reference"""
        shift = 0
        peak = self.simple_peak_find(data=data)
        if self.reference_data is None:
            self.reference_data = peak
        else:
            shift = peak - self.reference_data

        return shift

    def correlate_find(self, data):
        """This function uses a very naive correlation to estimate the shift
        Please note 2 things:
        1) It is still experimental and not guaranteed to work at all
        2) It does not return peak positions"""

        if self.reference_data is None:
            number_of_samples = len(data)
            self.zero_index = int(number_of_samples/2)-1
            self.number_of_samples = number_of_samples
            self.cosine_window = numpy.cos(
                    numpy.arange(-numpy.pi/2,
                                 numpy.pi/2,
                                 numpy.pi / number_of_samples))

        data = data * self.cosine_window

        if self.reference_data is None:
            self.reference_data = data
        shift = numpy.correlate(data, self.reference_data, 'same')
        shift = numpy.argmax(shift)

        return shift

    def fft_shift_find(self, data):
        """This function use the more complex FFT shift find.
        Please note 2 things:
        currently only the full sample shift is calculated
        1) It is still experimental and not guaranteed to work at all
        2) It does not return peak positions

        The inspiration is taken from https://dsp.stackexchange.com/a/2336
        for the subsample part.
        """
        # todo implement the sub sample shift
        # shift, first is sample second is fraction of the sample
        shift = [0, 0.0]

        # If there is no reference setup the various values

        if self.reference_data is None:
            self.number_of_samples = len(data)
            self.zero_index = int(self.number_of_samples/2)-1
            self.number_of_samples = self.number_of_samples
            self.cosine_window = numpy.cos(
                    numpy.arange(-numpy.pi/2,
                                 numpy.pi/2,
                                 numpy.pi / self.number_of_samples))
            self.omega = (2 * numpy.pi * numpy.arange(
                    (self.number_of_samples / 2)+1)) / self.number_of_samples

        # Apply cosine window
        s_sig = data * self.cosine_window
        # s_sig = data
        # do the fourrier transform
        fft_sig = numpy.fft.fft(s_sig)
        # fft_sig = numpy.fft.fftshift(fft_sig)

        # If this is the first calculation store reference otherwise continue
        # calculating. The reference is the angles.
        if self.reference_data is None:
            self.reference_data = numpy.conjugate(fft_sig)

        # Take the difference in angles
        phase_diff = fft_sig * self.reference_data

        n = numpy.fft.ifft(phase_diff)
        shift[0] = numpy.argmax(n)

        rotated_phase = phase_diff * numpy.exp(
                -1j*2*numpy.pi*shift[0]*numpy.arange(len(n))/len(n))

        shift[1] = numpy.angle(rotated_phase)*numpy.abs(rotated_phase)**1

        result = shift[0]

        return result

    def convolve_shift_find(self, data):
        shift = [0, 0.0]
        number_of_samples = len(data)

        if self.reference_data is None:
            self.number_of_samples = number_of_samples
            self.cosine_window = numpy.cos(
                    numpy.arange(-numpy.pi/2,
                                 numpy.pi/2,
                                 numpy.pi / number_of_samples))

        # Apply cosine window
        s_sig = data * self.cosine_window

        # If this is the first calculation store reference otherwise continue
        # calculating. The reference is the angles.
        if self.reference_data is None:
            self.reference_data = s_sig

        shift[0] = numpy.argmax(scipy.signal.fftconvolve(s_sig,
                                                         self.reference_data,
                                                         mode='full'))

        return sum(shift)

    def quadratic_fit(self, data, window=150):
        if self.reference_data is None:
            # first inital guess
            self.previous_window = None
            guess = peakutils.indexes(data[1:],
                                      thres=0.1 / numpy.max(data[1:]),
                                      min_dist=1000)
            if len(guess) == 0:
                self.x_max = 5000 + window
                self.x_min = 5000 - window
            else:
                guess = guess[guess < 9000][-2]
                self.x_min = guess - window
                self.x_max = guess + window

        if self.previous_window != window:
            # pre calculate the x values
            self.x = numpy.arange(0, 2 * window + 1, dtype=numpy.float64)
            self.x2 = self.x ** 2
            self.n = len(self.x)
            self.sumx = numpy.sum(self.x)
            self.sumx2 = numpy.sum(self.x ** 2)
            self.sumx3 = numpy.sum(self.x ** 3)
            self.sumx4 = numpy.sum(self.x ** 4)
            self.D = self.n * self.sumx2 * self.sumx4 + 2 * self.sumx * self.sumx2 * self.sumx3 - self.sumx2 ** 3 - \
                     (self.sumx ** 2) * self.sumx4 - self.n * (self.sumx3 ** 2)

        y = 1 / data[self.x_min:self.x_max+1]

        sumxxy = numpy.sum(self.x2 * y)
        sumy = numpy.sum(y)
        sumxy = numpy.sum(self.x * y)

        a = (self.n*self.sumx2*sumxxy + self.sumx*self.sumx3*sumy + self.sumx*self.sumx2*sumxy - (self.sumx2**2)*sumy - (self.sumx**2)*sumxxy - self.n*self.sumx3*sumxy)/self.D
        b = (self.n*self.sumx4*sumxy + self.sumx*self.sumx2*sumxxy + self.sumx2*self.sumx3*sumy - (self.sumx2**2)*sumxy - self.sumx*self.sumx4*sumy - self.n*self.sumx3*sumxxy)/self.D
        x_pos = -b/(2*a)
        x_pos += float(self.x_min)

        if self.reference_data is None:
            self.reference_data = x_pos

        shift = x_pos - self.reference_data
        self.x_min_new = numpy.int(x_pos - window)

        # check for strange values
        if self.x_min_new < len(data) and self.x_min_new > 0:
            self.x_min = self.x_min_new
        self.x_max = self.x_min + self.n-1

        return shift

    def center_of_mass(self, data, window=100):
        if self.reference_data is None:
            # first inital guess
            self.previous_window = None
            guess = peakutils.indexes(data[1:],
                                      thres=0.1 / numpy.max(data[1:]),
                                      min_dist=1000)
            if len(guess) == 0:
                self.x_max = 5000 + window
                self.x_min = 5000 - window
            else:
                guess = guess[guess < 9000][-2]
                self.x_min = guess - window
                self.x_max = guess + window
        if self.previous_window != window:
            # pre calculate the x values
            self.x = numpy.arange(0, 2 * window + 1, dtype=numpy.float64)
            self.n = len(self.x)

        y = data[self.x_min:self.x_max+1]

        total = numpy.sum(self.x * y)
        x_pos = total / numpy.sum(y)
        x_pos += float(self.x_min)

        if self.reference_data is None:
            self.reference_data = x_pos

        shift = x_pos - self.reference_data

        self.x_min_new = numpy.int(x_pos - window)

        # check for strange values
        if self.x_min_new < len(data) and self.x_min_new > 0:
            self.x_min = self.x_min_new
        self.x_max = self.x_min + self.n - 1

        return shift

    def remove_step(self, result):
        """This function compares the current value the previous one. """
        result += self.jump_compensation
        if numpy.abs(self.previous_data - result) > self.step_rejection:
            self.jump_compensation += self.previous_data - result
            result = self.previous_data
        self.previous_data = result

        return result

    def moving_avarage(self, data, window_width=12):
        cumsum_vec = numpy.cumsum(numpy.insert(data, 0, 0))
        data = (cumsum_vec[window_width:] - cumsum_vec[:-window_width]) / window_width

        return data

    def find_shift(self, algorithm=0, data=None, filter=None, **kwargs):
        """This function is made to easily select the shift find method
        to use.
        """
        if filter is None:
            pass
        elif filter == 1:
            data = self.moving_avarage(data, **kwargs)



        val = None
        # Simple peak utils peak find.
        if algorithm == 0:
            val = self.simple_shift_find(data=data)

        elif algorithm == 1:
            val = self.fft_shift_find(data=data)

        elif algorithm == 2:
            val = self.correlate_find(data=data)

        elif algorithm == 3:
            val = self.convolve_shift_find(data=data)

        elif algorithm == 4:
            val = self.center_of_mass(data=data)

        elif algorithm == 5:
            val = self.quadratic_fit(data=data)

        val = self.remove_step(val)
        return val

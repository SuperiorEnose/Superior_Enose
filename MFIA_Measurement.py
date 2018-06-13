""" This code will aqcuire data from the MFIA and process the data to show
the resanance peak of the E-nose chip"""

# For all the daq functions please refer to the Zurich Instruments
# LabOne programming manual

__author__ = "Mika Uytdewilligen, Zhi Jan Bai"
__version__ = "1.0.0"
__maintainer__ = " SSS project E-nose group"
__status__ = "Prototype"

import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
from analysis import Analysis
from collections import defaultdict


def get_value():
    """ This function calls the poll function of the Zurich instruments API to
    gather data for X time and average the value of the samples gathered in this
    time frame and returns these values in a dictionary"""
    # Initialize the dictionary
    data = defaultdict(dict)
    # Create the variables
    RealZ = 0
    ImagZ = 0
    frequency = 0
    # Call the poll function
    value = daq.poll(0.1, 500, 0, True)
    # Collect the data and average them
    for i in range(0, len(value['/dev3481/imps/0/sample']['z'])):
        RealZ += value['/dev3481/imps/0/sample']['z'][i].real
        ImagZ += value['/dev3481/imps/0/sample']['z'][i].imag
        frequency += value['/dev3481/imps/0/sample']['frequency'][i]
    RealZ = RealZ/len(value['/dev3481/imps/0/sample']['z'])
    ImagZ = ImagZ/len(value['/dev3481/imps/0/sample']['z'])
    frequency = frequency/len(value['/dev3481/imps/0/sample']['frequency'])
    # Put the data in the dictionary and return the data
    data['RealZ'] = RealZ
    data['ImagZ'] = ImagZ
    data['frequency'] = frequency
    return data


def start_impedance_sweep(start_freq, stop_freq, samples):
    """ In this function the impedance sweep is initialized. First the step_size
    for the frequency is calculated with the start and stop frequency and the
    amount of samples. Second the get_value function is called for samples
    amoun of times. The first call of get_value is ignored since the data is not
    usable and we give the filters some time to settle when it is enabled for
    the first time. Third the data from the get_value function is put in a
    double layer dictionary and returned"""
    # Initialize the dictionary
    data = defaultdict(dict)
    settle_turn_on = 0
    # Calculate the step_size of the frequency
    step_size = (stop_freq-start_freq)/samples
    for dataindex in range(0, samples):
        fprop = start_freq + dataindex*step_size
        daq.set([['/%s/imps/%d/freq' % (device, imp_index), fprop]])
        daq.sync()
        if settle_turn_on == 0:     # Wait for the demodulator filter to settle
            time.sleep(2)           # and ignore the first get_value
            get_value()
            settle_turn_on = 1
        time.sleep(0.001)
        data_get_value = get_value()
        # Transfer the data to the dictionary and return it
        data['RealZ'][dataindex] = data_get_value['RealZ']
        data['ImagZ'][dataindex] = data_get_value['ImagZ']
        data['frequency'][dataindex] = data_get_value['frequency']
    return data


def plot_result(RealZ, ImagZ, frequency):
    """This function plots the results in 2 plots, the real and imaginary
    impedance, against the frequency. The graph will be autoranged on the
    X and Y axis"""
    _, (ax1, ax2) = plt.subplots(2, 1)
    ax2.plot(frequency, ImagZ)
    ax1.plot(frequency, RealZ)
    ax1.grid(True)
    ax1.set_ylabel('R')
    ax1.autoscale()

    ax2.grid(True)
    ax2.set_xlabel('Frequency ($Hz$)')
    ax2.set_ylabel('ImagZ ohm')
    ax2.autoscale()

    plt.draw()
    return


"""The main loop initializes the MFIA, subscribes to the impedance sample node
and calls the start_impedance_sweep function with the initial values defined
in the code"""
# The name of the MFIA
device_id = 'dev3481'

# The apilevel of this program
apilevel_MFIA = 6

err_msg = "We fucked up. beep boop - Dr. Prof. Boii"

# The api session is created te connect to the MFIA and communicate with it
# to set the settings and read the data
(daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_MFIA,
                                                       required_devtype='.*IA',
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)

# The outputs are all set to aff
general_setting = [['/%s/demods/*/enable' % device, 0],
                   ['/%s/demods/*/trigger' % device, 0],
                   ['/%s/sigouts/*/enables/*' % device, 0],
                   ['/%s/scopes/*/enable' % device, 0],
                   ['/%s/imps/*/enable' % device, 0]]
daq.set(general_setting)
daq.sync()

# The impedance channel that is used(LabOne counts starting at 1, the cade at 0)
imp_index = 0

# Enabling all the settings for the use of the impdance measurement in MFIA
exp_setting = [['/%s/imps/%d/enable' % (device, imp_index), 1],
               ['/%s/imps/%d/mode' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 1]]
daq.set(exp_setting)

# Unsubscribe any streaming data.
daq.unsubscribe('*')
daq.sync()

# The path to the impedance sample and subscribing to it
path = '/dev3481/IMPS/0/SAMPLE'
daq.subscribe(path)

# Initial values for the start_impedance_sweep
start = 135000
stop = 150000
n = 500

# Start the start_impedance_sweep with a certain omount of sweeps
for i in range(0, 100):
    # Store the returned data in data
    data = start_impedance_sweep(start, stop, n)
    # Create empty numpy arrays
    # ("empty" since they are filled with random volues)
    frequency = np.empty(shape=(len(data['RealZ'])))
    RealZ = np.empty(shape=(len(data['RealZ'])))
    ImagZ = np.empty(shape=(len(data['RealZ'])))

    for j in range(0, len(data['RealZ'])):
        # Transfer the data from the dictionary to the numpy arrays
        frequency[j] = data['frequency'][j]
        RealZ[j] = data['RealZ'][j]
        ImagZ[j] = data['ImagZ'][j]
    # Plot the results in graphs
    plot_result(RealZ, ImagZ, frequency)

    # Initialize the peak_finder class
    peak_finder = Analysis()

    # Fit the window to 1 kHz around the resonance peak
    # peak_finder.simple_peak_find(RealZ, n) find the peak of the RealZ in
    # the amount of samples defined for the sweep
    start = frequency[peak_finder.simple_peak_find(RealZ, n)] - 500
    stop = frequency[peak_finder.simple_peak_find(RealZ, n)] + 500

    # Print the resonance frequency
    print("%d hz " % frequency[peak_finder.simple_peak_find(RealZ, n)])

# Redraw the plots to show them
plt.draw()

# Clear the subscription and turn the measurement off
daq.unsubscribe('*')
daq.set([['/%s/imps/*/enable' % device, 0]])

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
    data = defaultdict(dict)
    RealZ = 0
    ImagZ = 0
    frequency = 0
    value = daq.poll(0.1, 500, 0, True)
    for i in range(0, len(value['/dev3481/imps/0/sample']['z'])):
        RealZ += value['/dev3481/imps/0/sample']['z'][i].real
        ImagZ += value['/dev3481/imps/0/sample']['z'][i].imag
        frequency += value['/dev3481/imps/0/sample']['frequency'][i]
    RealZ = RealZ/len(value['/dev3481/imps/0/sample']['z'])
    ImagZ = ImagZ/len(value['/dev3481/imps/0/sample']['z'])
    frequency = frequency/len(value['/dev3481/imps/0/sample']['frequency'])
    data['RealZ'] = RealZ
    data['ImagZ'] = ImagZ
    data['frequency'] = frequency
    return data


def start_impedance_sweep(start_freq, stop_freq, samples):
    data = defaultdict(dict)
    settle_turn_on = 0
    step_size = (stop_freq-start_freq)/samples
    for dataindex in range(0, samples):
        fprop = start_freq + dataindex*step_size
        daq.set([['/%s/imps/%d/freq' % (device, imp_index), fprop]])
        daq.sync()
        if settle_turn_on == 0:     # Wait for the demodulator filter to settle.
            time.sleep(2)
            get_value()
            settle_turn_on = 1
        time.sleep(0.001)
        data_get_value = get_value()
        data['RealZ'][dataindex] = data_get_value['RealZ']
        data['ImagZ'][dataindex] = data_get_value['ImagZ']
        data['frequency'][dataindex] = data_get_value['frequency']
    return data


def plot_result(RealZ, ImagZ, frequency):
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


# The name of the MFIA
device_id = 'dev3481'

# The apilevel of this program
apilevel_MFIA = 6

err_msg = "We fucked up. beep boop - Dr. Prof. Boii"

(daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_MFIA,
                                                       required_devtype='.*IA',
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)

general_setting = [['/%s/demods/*/enable' % device, 0],
                   ['/%s/demods/*/trigger' % device, 0],
                   ['/%s/sigouts/*/enables/*' % device, 0],
                   ['/%s/scopes/*/enable' % device, 0],
                   ['/%s/imps/*/enable' % device, 0]]
daq.set(general_setting)
daq.sync()

imp_index = 0

exp_setting = [['/%s/imps/%d/enable' % (device, imp_index), 1],
               ['/%s/imps/%d/mode' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 1]]
daq.set(exp_setting)

# Unsubscribe any streaming data.
daq.unsubscribe('*')
daq.sync()

path = '/dev3481/IMPS/0/SAMPLE'
daq.subscribe(path)
start = 100000
stop = 200000
n = 500
for i in range(0, 3):

    data = start_impedance_sweep(start, stop, n)
    frequency = np.empty(shape=(len(data['RealZ'])))
    RealZ = np.empty(shape=(len(data['RealZ'])))
    ImagZ = np.empty(shape=(len(data['RealZ'])))

    for i in range(0, len(data['RealZ'])):
        frequency[i] = data['frequency'][i]
        RealZ[i] = data['RealZ'][i]
        ImagZ[i] = data['ImagZ'][i]
    plot_result(RealZ, ImagZ, frequency)

    k = Analysis()
    start = data['frequency'][k.simple_peak_find(RealZ, n)] - 500
    stop = data['frequency'][k.simple_peak_find(RealZ, n)] + 500
    print("%d hz " % frequency[k.simple_peak_find(RealZ, n)])

plt.draw()
daq.unsubscribe('*')
daq.set([['/%s/imps/*/enable' % device, 0]])

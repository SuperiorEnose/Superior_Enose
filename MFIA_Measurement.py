import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
from collections import defaultdict


def get_value():
    RealZ = 0
    ImagZ = 0
    frequency = 0
    data = defaultdict(dict)
    for dataindex in range(0, 10):
        fprop = 500 + dataindex*1000
        daq.set([['/%s/imps/%d/freq' % (device, imp_index), fprop]])
        daq.sync()
        time.sleep(0.5)
        value = daq.poll(0.1, 500, 0, True)
        for i in range(0, len(value['/dev3481/imps/0/sample']['z'])):
            RealZ += value['/dev3481/imps/0/sample']['z'][i].real
            ImagZ += value['/dev3481/imps/0/sample']['z'][i].imag
            frequency += value['/dev3481/imps/0/sample']['frequency'][i]
        RealZ = RealZ/len(value['/dev3481/imps/0/sample']['z'])
        ImagZ = ImagZ/len(value['/dev3481/imps/0/sample']['z'])
        frequency = frequency/len(value['/dev3481/imps/0/sample']['frequency'])
        data['RealZ'][dataindex] = RealZ
        data['ImagZ'][dataindex] = ImagZ
        data['frequency'][dataindex] = frequency
        print('The real part of the impedance %.8f ohm' % RealZ)
        print('The imaginary part of the impedance %.9fj ohm' % ImagZ)
        print('Frequency is %d' % frequency)
    return data


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

amplitude = 0.1
out_channel = 0
out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
in_channel = 0
demod_index = 0
osc_index = 0
demod_rate = 10e3
time_constant = 0.01
frequency = 400e3  # This must variable to measure multiple frequency points
imp_index = 0

exp_setting = [['/%s/imps/%d/enable' % (device, imp_index), 1],
               ['/%s/imps/%d/mode' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
               ['/%s/imps/%d/freq' % (device, imp_index), 500],
               ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 1]]
daq.set(exp_setting)

# Unsubscribe any streaming data.
daq.unsubscribe('*')

# Wait for the demodulator filter to settle.
time.sleep(10*time_constant)

daq.sync()

path = '/dev3481/IMPS/0/SAMPLE'
daq.subscribe(path)

# data = zhinst.examples.common.example_poll.run_example('dev3481', 0.1, True)
data = get_value()
print(len(data['RealZ']))


daq.unsubscribe('*')

frequency = np.empty(shape=(len(data['RealZ']), 1))
RealZ = np.empty(shape=(len(data['RealZ']), 1))
ImagZ = np.empty(shape=(len(data['RealZ']), 1))
_, (ax1, ax2) = plt.subplots(2, 1)

for i in range(0, len(data['RealZ'])):
    frequency[i] = data['frequency'][i]
    RealZ[i] = data['RealZ'][i]
    ImagZ[i] = data['ImagZ'][i]
ax2.plot(frequency, ImagZ)
ax1.plot(frequency, RealZ)
ax1.grid(True)
ax1.set_ylabel('R')
ax1.autoscale()

ax2.grid()
ax2.set_xlabel('Frequency ($Hz$)')
ax2.set_ylabel('ImagZ ohm')
ax2.autoscale()

plt.draw()
plt.show()

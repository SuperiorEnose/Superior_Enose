import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
from collections import defaultdict
# data = zhinst.examples.common.example_sweeper.run_example('dev3481', 0.1, True)


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
daq.sync()

daq.subscribe('/dev3481/IMPS/0/SAMPLE')
data = get_value()
_, (ax1, ax2) = plt.subplots(2, 1)

for i in range(0, len(data['RealZ'])):
    frequency = data['frequency'][i]
    RealZ = data['RealZ'][i]
    ImagZ = data['ImagZ'][i]
ax1.plot(frequency, RealZ, 'b-')
ax2.plot(frequency, ImagZ, 'ro')
ax1.grid()
ax1.set_ylabel('R')
ax1.autoscale()

ax2.grid()
ax2.set_xlabel('Frequency ($Hz$)')
ax2.set_ylabel('ImagZ ohm')
ax2.autoscale()

plt.draw()
plt.show()

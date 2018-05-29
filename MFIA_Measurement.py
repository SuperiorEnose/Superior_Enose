import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
# data = zhinst.examples.common.example_sweeper.run_example('dev3481', 0.1, True)


def get_value():
    for i in range(0, 5):
        fprop = 500 + i*100
        daq.set([['/%s/imps/%d/freq' % (device, imp_index), fprop]])
        time.sleep(0.001)
        RealZ = 0
        ImagZ = 0
        value = daq.poll(0.1, 500, 0, True)
        for i in range(0, len(value['/dev3481/imps/0/sample']['param0'])):
            RealZ += value['/dev3481/imps/0/sample']['param0'][i]
            ImagZ += value['/dev3481/imps/0/sample']['param1'][i]
        RealZ = RealZ/len(value['/dev3481/imps/0/sample']['param0'])
        ImagZ = ImagZ/len(value['/dev3481/imps/0/sample']['param0'])
        print('The real part of the impedance %.8f ohm' % RealZ)
        print('The imaginary part of the impedance %.9fj ohm' % ImagZ)
    return len(value['/dev3481/imps/0/sample']['param0'])


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
curr_index = daq.getInt('/%s/imps/%d/current/inputselect' % (device, imp_index))
volt_index = daq.getInt('/%s/imps/%d/voltage/inputselect' % (device, imp_index))
man_curr_range = 10e-3
man_volt_range = 10e-3

exp_setting = [['/%s/imps/%d/enable' % (device, imp_index), 1],
               ['/%s/imps/%d/mode' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/output' % (device, imp_index), 1],
               ['/%s/imps/%d/auto/bw' % (device, imp_index), 1],
               ['/%s/imps/%d/freq' % (device, imp_index), 500],
               ['/%s/imps/%d/auto/inputrange' % (device, imp_index), 0],
               ['/%s/currins/%d/range' % (device, curr_index), man_curr_range],
               ['/%s/sigins/%d/range' % (device, volt_index), man_volt_range]]
daq.set(exp_setting)
daq.sync()

trigger_auto_ranging = [['/%s/currins/%d/autorange' % (device, curr_index), 1],
                        ['/%s/sigins/%d/autorange' % (device, volt_index), 1]]
print('Start auto ranging. This takes a few seconds.')
# daq.set(trigger_auto_ranging)

daq.subscribe('/dev3481/IMPS/0/SAMPLE')

get_value()

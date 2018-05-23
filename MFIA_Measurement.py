import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
zhinst.examples.common.example_data_acquisition_edge.run_example('dev3481', True)
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
                   ['/%s/imps/*/enable' % device, 1]]
daq.set(general_setting)

amplitude = 0.1
out_channel = 0
out_mixer_channel = zhinst.utils.default_output_mixer_channel(props)
in_channel = 0
demod_index = 0
osc_index = 0
demod_rate = 10e3
time_constant = 0.01
frequency = 400e3  # This must variable to measure multiple frequency points

exp_setting = [['/%s/sigins/%d/ac'             % (device, in_channel), 0],
               ['/%s/sigins/%d/range'          % (device, in_channel), 2*amplitude],
               ['/%s/demods/%d/enable'         % (device, demod_index), 1],
               ['/%s/demods/%d/rate'           % (device, demod_index), demod_rate],
               ['/%s/demods/%d/adcselect'      % (device, demod_index), in_channel],
               ['/%s/demods/%d/order'          % (device, demod_index), 6],
               ['/%s/demods/%d/timeconstant'   % (device, demod_index), time_constant],
               ['/%s/demods/%d/oscselect'      % (device, demod_index), osc_index],
               ['/%s/demods/%d/harmonic'       % (device, demod_index), 1],
               ['/%s/sigouts/%d/on'            % (device, out_channel), 1],
               ['/%s/sigouts/%d/enables/%d'    % (device, out_channel, out_mixer_channel), 1],
               ['/%s/sigouts/%d/range'         % (device, out_channel), 1],
               ['/%s/sigouts/%d/amplitudes/%d' % (device, out_channel, out_mixer_channel), amplitude]]
daq.set(exp_setting)

# Wait for the demodulator filter to settle.
# time.sleep(10*time_constant)
trigger = daq.dataAcquisitionModule()
signal_path = '/%s/demods/%d/sample' % (device, demod_index)
#value = daq.getDouble('/%s/demods/%d/sample' % (device, demod_index))

# daq.listNodes('/*',3)
# print(value)

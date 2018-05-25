import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils
import zhinst.examples
zhinst.examples.common.example_sweeper.run_example('dev3481', 0.1, True)
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
               ['/%s/imps/%d/mode' % (device, imp_index), 0],
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

# Wait for the demodulator filter to settle.
#time.sleep(1)
#imp = daq.impedanceModule()
#imp.subscribe('/dev3481/IMPS/0/SAMPLE')
#imp.execute()
#time.sleep(3)
#imp.finish()
#value = imp.read(True)
#imp.unsubscribe('*')
# signal_path = '/%s/demods/%d/sample' % (device, demod_index)
# value = imp.getDouble('/dev3481/IMPS/0/SAMPLE')
#p = value[1][0]['x']

# imp.listNodes('/dev3481/imps/', 3)
#print(p)

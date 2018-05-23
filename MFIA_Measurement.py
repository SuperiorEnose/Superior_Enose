import zhinst.ziPython as ziPython
from scipy.integrate import odeint
import numpy as np
import time
import matplotlib.pyplot as plt
import zhinst.utils

# The name of the MFIA
device_id = 'dev3481'


# The apilevel of this program
apilevel_MFIA = 6

err_msg = "This should not be seen"

(daq, device, props) = zhinst.utils.create_api_session(device_id, apilevel_MFIA,
                                                       required_devtype='.*IA',
                                                       required_err_msg=err_msg)
zhinst.utils.api_server_version_check(daq)

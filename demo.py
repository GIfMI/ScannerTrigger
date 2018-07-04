"""Demo of the ScannerTrigger module.

Idea
====
This program, written in Python using PsychoPy demonstrates the use of the
ScannerTrigger module.

Input
=====
    Triggering - device to receive triggers from
    Scans to skip - number of triggers to skip before continuing

To adjust device specific parameters, edit the appropriate MR_settings
dictionary below.

Output
======
The program will detect triggers received from the selected device and displays
some data:
    Trigger number - number of received trigger (zero based, it's Python!)
                     if scans to skip is greater than 0, the first shown
                     trigger is trigger <scans to skip>
    Onset time - time elapsed since the first triggered
    Delta time - time between last and one-but-last triggered
    Skip scans - number of scans to skip
The program will loop until the escape key has been pressed or after 100s have
elapsed (can be adjusted).

After finishing the loop, a histogram is displayed from the delta times.
The program also prints out the mean, standard deviation, maximum and minimum
of the delta times.

Remark
======
This program was developed in PsychoPy 1.90.2 and runs in the Python2 and
Python3 version.

Copyright (C) 2018 Pieter Vandemaele
Distributed under the terms of the GNU General Public License (GPL).
"""

from psychopy import sound
from psychopy import core, visual, logging, event, parallel, gui
import scannertrigger as s
import serial
from psychopy.hardware.emulator import SyncGenerator
import matplotlib.pyplot as plt
import numpy as np

# ######################################################################
# EXPERIMENT INFO
# ######################################################################
# select the device to trigger from
# select the number of scans to skip

expName = "Demo ScannerTrigger"
expInfo = {'triggering': ['keyboard',
                          'serial',
                          'parallel',
                          'cedrus',
                          'launchscan',
                          'dummy'],
           'skip scans': 0}

dlg = gui.DlgFromDict(dictionary=expInfo, title=expName, sort_keys=False)

if dlg.OK is False:
    core.quit()

# ######################################################################
# STIMULI
# ######################################################################

# Setup the Window
win = visual.Window(
        size=(800, 600),
        fullscr=False,
        screen=0,
        allowGUI=True,
        allowStencil=False,
        monitor='testMonitor',
        color=[0, 0, 0],
        colorSpace='rgb',
        blendMode='avg',
        useFBO=True)

# Wait for scanner text
stimScanner = visual.TextStim(
    win=win,
    name='text',
    text='Wait for trigger...',
    font='Arial',
    pos=(0, 0),
    height=0.1,
    wrapWidth=None,
    ori=0,
    color='white',
    colorSpace='rgb',
    opacity=1,
    depth=0.0
    )

# Fixation text
stimTrigger = visual.TextStim(
    win=win,
    name='text',
    text='TRIGGER',
    font='Arial',
    pos=(0, 0),
    height=0.1,
    wrapWidth=None,
    ori=0,
    color='white',
    colorSpace='rgb',
    opacity=1,
    depth=0.0
    )

# ######################################################################
# SCANNER TRIGGER
# ######################################################################

portType = expInfo['triggering']
dummyScans = int(expInfo['skip scans'])

if portType == "keyboard":
    # Keyboard specific settings
    MR_settings = {
        'keyList': 't',
        'maxWait': 9999999,
        }
elif portType == "dummy":
    # Dummy specific settings
    MR_settings = {
        'tr': 1,
        }
elif portType == "serial":
    # Serial port specific settings
    MR_settings = {
        'port': 'COM5',
        'baudrate': 9600,
        'sync': '5'
        }
elif portType == "parallel":
    # Parallelport specific settings
    MR_settings = {
        'address': '0x0378',
        'pin': 10,
        'edge': s.RISING
        }
elif portType == "cedrus":
    # Cedrus specific settings
    MR_settings = {
        'devicenr': 0,
        'sync': 4,
        }
elif portType == "launchscan":
    # launchScan specific settings
    MR_settings = {
        'wait_msg': 'Waiting for scanner',
        'esc_key': 'escape',
        'log': True,
        'wait_timeout': 100,
        'settings': {
            'TR': 1,
            'volumes': 100,
            'sync': 't',
            'skip': dummyScans,
            'sound': False,
            }
        }
else:
    raise ValueError("The selected Port type does not exist!")

# ######################################################################
# OTHER INITIALIZATION
# ######################################################################

# Clocks
timeOutClock = core.Clock()
globalClock = core.Clock()

# Logging
logging.setDefaultClock(globalClock)
logging.console.setLevel(logging.DATA)

# Data
deltaTriggerTimeArray = []

try:
    # Open scanner trigger
    st = s.ScannerTrigger.create(
            win,
            globalClock,
            portType,
            portConfig=MR_settings,
            timeout=99999,
            logLevel=logging.DATA,
            esc_key='escape')
    st.open()
except Exception as e:
    # In case of errors
    logging.flush()
    print("ScannerTrigger Error: {0}".format(e))
    core.quit()

msg = 'TRIGGER {}\nonset time: {:.3f}\ndelta time: {:.3f}\nskip scans: {}'

# ######################################################################
# RUN EXPERIMENT
# ######################################################################

stimScanner.draw()
win.flip()

try:
    # Comment this out of you would like to generate emulated keyboard presses.
    # syncPulse = SyncGenerator(TR=1, volumes=100, sync='t', skip=0)
    # syncPulse.start()  # start emitting sync pulses
    # core.runningThreads.append(syncPulse)
    # event.clearEvents()
    print("Waiting for the Trigger")
    triggered = st.waitForTrigger(skip=dummyScans)
    logging.flush()
except Exception as e:
    # In case of errors
    logging.flush()
    print("ScannerTrigger Error: {0}".format(e))
    core.quit()

prevTriggerTime = st.triggerTime
timeOutClock.reset()

while (not event.getKeys(keyList=['escape']) and timeOutClock.getTime() < 100):
    if triggered:
        logging.flush()
        deltaTriggerTime = st.triggerTime - prevTriggerTime
        deltaTriggerTimeArray.append(deltaTriggerTime)
        txt = msg.format(st.triggerCnt,
                         st.triggerTime,
                         deltaTriggerTime,
                         dummyScans)
        prevTriggerTime = st.triggerTime
        stimTrigger.setText(txt)
        stimTrigger.draw()
        win.flip()
    triggered = st.getTrigger()

# ######################################################################
# DATA OUTPUT
# ######################################################################
# Calculate values
delta = np.array(deltaTriggerTimeArray[1:])
logging.data('Mean deltaTime: {:0.3f}s'.format(delta.mean()))
logging.data('Stdev deltaTime: {:0.3f}s'.format(delta.std()))
logging.data('Max deltaTime: {:0.3f}s'.format(delta.max()))
logging.data('Min deltaTime: {:0.3f}s'.format(delta.min()))
logging.flush()

# Plot delta time histogram
binWidth = np.ceil(4 * len(deltaTriggerTimeArray) ** (1.0/3))
fig = plt.figure()
plt.hist(delta, int(binWidth))
plt.title("Delta time - mean: {:0.3f}s - stdev: {:0.3f}s".format(delta.mean(),
                                                                 delta.std())                                                                 )
plt.xlabel("delta time")
plt.ylabel("frequency")
plt.show()

st.close()
win.close()
core.quit()

__author__ = 'Mauricio Merino, UTSA, June 2015'

# SSVEP Presentation program.

# ----------------------------------------------------------------------------------------------------------------------
# 0.) Import required packages, modules, libraries, etc.
from psychopy import visual, core, logging
from pylsl import StreamInfo, StreamOutlet
import time
import numpy

# ----------------------------------------------------------------------------------------------------------------------
# 1.) Program Configuration

# --- Configure duration
frame_rate_cycles = 1000

# --- Window properties
window_size = [1920, 1200]
window_background_color = [-1, -1, -1]   # White is represented by 1 and black by -1, RGB.
window_monitor = 1                       # 0 corresponds to main display
window_units = 'norm'                    # Independent of monitor size

# --- Stimulus frequencies and number of ON/OFF frames. 8 flickers on screen corners and each side's mid point.
number_stimulus = 8
stimulus_frequencies = [30, 12, 15, 20, 10, 8.57, 6, 7.55]
stimulus_frame_activations = [[1, 1], [3, 2], [2, 2], [2, 1], [3, 3], [4, 3], [5, 5], [4, 4]]
stimulus_frame_sequence_length = 60

stimulus_size = 7
position_offset = 3
x_limit = 28
y_limit = 16
stimulus_screen_positions = [[(-x_limit + position_offset), (y_limit - position_offset)],   # Top-left
                             [0, (y_limit - position_offset)],                  # Top-middle
                             [(x_limit - position_offset), (y_limit - position_offset)],    # Top-right
                             [(-x_limit + position_offset), 0],                 # Middle-left
                             [(x_limit - position_offset), 0],                  # Middle-right
                             [(-x_limit + position_offset), (-y_limit + position_offset)],  # Bottom-left
                             [0, (-y_limit + position_offset)],                 # Bottom-center
                             [(x_limit - position_offset), (-y_limit + position_offset)]]   # Bottom-right

# ----------------------------------------------------------------------------------------------------------------------
# 2.) Compute a 60-Frame/Color sequence for each frequency

# --- Pre-allocate all stimulus sequences as a matrix, the color matrix and a frame counter
stimulus_frame_sequence = numpy.zeros([number_stimulus, stimulus_frame_sequence_length])
stimulus_color_sequence = numpy.zeros([number_stimulus, 3, stimulus_frame_sequence_length])
frame_counter = 0

# --- Loop to fill sequence and colors matrix (per stimulus)
for stimulus in range(number_stimulus):

    # All stimulus begins on ON state, reset frame counter
    frame_state_switch = True
    frame_counter = 0

    for frame in range(stimulus_frame_sequence_length):

        # Check for ON frames
        if frame_state_switch:

            # Count ON frames, save it on matrix
            frame_counter += 1
            stimulus_frame_sequence[stimulus, frame] = 1

            # Save WHITE color on matrix (current stimulus and frame)
            stimulus_color_sequence[stimulus, 0, frame] = 1
            stimulus_color_sequence[stimulus, 1, frame] = 1
            stimulus_color_sequence[stimulus, 2, frame] = 1

            # Reset counter and flip switch when number of ON frames is reached
            if frame_counter == stimulus_frame_activations[stimulus][0]:
                frame_counter = 0
                frame_state_switch = False

        else:
            # Count OFF frames (already saved on matrix), and check for switching flag
            frame_counter += 1

            # Save BLACK color on matrix (current stimulus and frame)
            stimulus_color_sequence[stimulus, 0, frame] = -1
            stimulus_color_sequence[stimulus, 1, frame] = -1
            stimulus_color_sequence[stimulus, 2, frame] = -1

            if frame_counter == stimulus_frame_activations[stimulus][1]:
                frame_counter = 0
                frame_state_switch = True

print('Process Completed!')

# ----------------------------------------------------------------------------------------------------------------------
# 3.) Create OpenGL window and stimulus arrays
window_handle = visual.Window(size=[1920, 1200], fullscr=False, monitor='testMonitor', units='deg',
                              screen=window_monitor, winType='pyglet', color=[-1, -1, -1], colorSpace='rgb')

stimulus_array = visual.ElementArrayStim(window_handle, units='deg', nElements=number_stimulus, colors=[1, 1, 1],
                                         colorSpace='rgb', elementMask=None, autoLog=None, sfs=0, sizes=stimulus_size,
                                         xys=stimulus_screen_positions, fieldShape='sqr', maskParams=None)

fixation_array = visual.ElementArrayStim(window_handle, units='deg', nElements=number_stimulus, colors=[-1, -1, -1],
                                         colorSpace='rgb', elementMask=None, autoLog=None, sfs=0, sizes=0.2,
                                         xys=stimulus_screen_positions, fieldShape='sqr', maskParams=None)



# ----------------------------------------------------------------------------------------------------------------------
# 4.) Setup frame recording and other properties

# --- Obtain frame rate and enable frame time recording
monitor_frame_rate = int(window_handle.getActualFrameRate())
print(monitor_frame_rate)
window_handle.setRecordFrameIntervals(True)

# --- Configure frame delay tolerance (ms) and enable warning
frame_delay_tolerance = 3  # In milliseconds
window_handle._refreshThreshold = (1.0/monitor_frame_rate) + (frame_delay_tolerance / 1000)
logging.console.setLevel(logging.WARNING)

# ----------------------------------------------------------------------------------------------------------------------
# 5.) Perform stimulus flickering

# --- Enable constant drawing of fixation array
fixation_array.setAutoDraw(True)

# --- loop through frames and create the flicker effect
for cycle in range(frame_rate_cycles):
    window_handle.flip()
    for frame in range(stimulus_frame_sequence_length):
        stimulus_current_frame_colors = stimulus_color_sequence[:, :, frame]       # Obtain the colors for current frame
        stimulus_array.setColors(stimulus_current_frame_colors, colorSpace='rgb')  # Set new array of colors
        stimulus_array.draw()                                                      # Changes will be drawn on next flip
        window_handle.flip()


# --- Close window
window_handle.close()
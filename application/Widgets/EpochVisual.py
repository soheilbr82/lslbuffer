import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import pylsl
from lslringbuffer_multithreaded import LSLRINGBUFFER
import sys


channels = int(sys.argv[1])
maxView = channels*5
fs = np.linspace(-0.2, 0.8,128)
colors = ['g', 'b', 'r', 'k', 'c']

streams = pylsl.resolve_streams(wait_time=1.0) # Contains information about all available lsl inlets

for s in streams:
    lsl_inlet = pylsl.StreamInlet(s, max_buflen=4)
    lsl_inlet.open_stream()
    lsl = LSLRINGBUFFER(lsl_type=lsl_inlet.info().type(), name=lsl_inlet.info().name(), inlet=lsl_inlet,\
            fs=lsl_inlet.info().nominal_srate(), buffer_duration=4.0, \
            num_channels=lsl_inlet.info().channel_count(), uid=lsl_inlet.info().uid(),\
            hostname=lsl_inlet.info().hostname(), channel_format='float64')

chunk = None
buffer = np.empty([0,channels])
tmp_buffer = np.empty([0,channels])

# Create figure for plotting
fig, axs = plt.subplots(2)
for i in range(len(axs)):
    axs[i].set_xlim(-0.3, 0.9)
    axs[i].set_ylim(-2, 2)

lines = [[None for j in range(5)] for i in range(channels)]
line = 0
alphas = [0.2, 0.4, 0.6, 0.8, 1.0]


# This function is called periodically from FuncAnimation
def animate(i):
    global buffer, tmp_buffer, chunk, lsl, lines, line, colors, alphas, fs, channels, maxView, axs


    while buffer.shape[0] < 128:
        while chunk is None:
            chunk, timestamp = lsl.get_next_chunk()

        buffer = np.concatenate((buffer, chunk), axis=0)

    
    if buffer.shape[0] > 128:
        tmp_buffer  = np.concatenate((tmp_buffer, buffer[128:]), axis=0)
        buffer = np.delete(buffer, np.s_[128:], axis=0)
        


    for channel in range(channels):
        lines[channel][line] = Line2D(fs, buffer[:, channel], c=colors[channel])
        if len(axs[channel].get_lines()) >= 5:
            axs[channel].lines.pop(0)
        axs[channel].add_line(lines[channel][line])

    for channel in range(channels):
        for li in range(len(lines[channel])):
            l = axs[channel].lines.pop(0)
            c = l.get_c()
            x = l.get_xdata()
            y = l.get_ydata()
            lines[channel][li] = Line2D(x, y, c=c, alpha=alphas[li])
            axs[channel].add_line(lines[channel][li])

    
    if line < 4:
        line += 1
    else:
        line = 0
                    
    buffer = tmp_buffer
    tmp_buffer = np.empty([0,channels])

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, interval=1000)
plt.show()
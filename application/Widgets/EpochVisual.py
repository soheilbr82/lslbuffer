import numpy as np
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import pylsl
from lslringbuffer_multithreaded import LSLRINGBUFFER


fs = np.linspace(-0.2, 0.8,128)
colors = ['g', 'b', 'r', 'k', 'c']
colorIndex = 0

streams = pylsl.resolve_streams(wait_time=1.0) # Contains information about all available lsl inlets

for s in streams:
    lsl_inlet = pylsl.StreamInlet(s, max_buflen=4)
    lsl_inlet.open_stream()
    lsl = LSLRINGBUFFER(lsl_type=lsl_inlet.info().type(), name=lsl_inlet.info().name(), inlet=lsl_inlet,\
            fs=lsl_inlet.info().nominal_srate(), buffer_duration=4.0, \
            num_channels=lsl_inlet.info().channel_count(), uid=lsl_inlet.info().uid(),\
            hostname=lsl_inlet.info().hostname(), channel_format='float64')

chunk = None
buffer = np.empty([0,1])
tmp_buffer = np.empty([0,1])

# Create figure for plotting
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)
ax.set_xlim(-0.3, 0.9)
xs = []
ys = []
lines = [None for i in range(5)]
line = 0
alphas = [0.2, 0.4, 0.6, 0.8, 1.0]


# This function is called periodically from FuncAnimation
def animate(i, xs, ys):
    global buffer, tmp_buffer, chunk, lsl, lines, line, colors, alphas, fs


    while buffer.size < 128:

        while chunk is None:
            chunk, timestamp = lsl.get_next_chunk()

        buffer = np.concatenate((buffer, chunk), axis=0)

    if buffer.size > 128:
        tmp_buffer  = np.concatenate((tmp_buffer, buffer[128:]), axis=0)
        buffer = np.delete(buffer, np.s_[128:], 0)

    lines[line] = Line2D(fs, buffer, c='b')
    if len(ax.get_lines()) >= 5:
        ax.lines.pop(0)
    ax.add_line(lines[line])

    numLine = len(ax.get_lines())
    for i in range(numLine):
        l = ax.lines.pop(0)
        c = l.get_c()
        x = l.get_xdata()
        y = l.get_ydata()
        lines[i] = Line2D(x, y, c=c, alpha=alphas[i])
        ax.add_line(lines[i])

    
    if line < 4:
        line += 1
    else:
        line = 0
                    
    buffer = tmp_buffer
    tmp_buffer = np.empty([0,1])

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    print(len(ax.get_lines()))

# Set up plot to call animate() function periodically
ani = animation.FuncAnimation(fig, animate, fargs=(xs, ys), interval=1000)
plt.show()
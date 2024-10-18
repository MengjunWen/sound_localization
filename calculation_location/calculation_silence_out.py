import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
import numpy as np
import torch
from scipy.io import wavfile
from matplotlib import pyplot as plt
import random
from model import GCC, NGCCPHAT
from scipy.optimize import minimize
from IPython.display import clear_output
import matplotlib
matplotlib.use('TKAgg')
plt.ion()  # Enable interactive mode

# For reproducibility
torch.manual_seed(42)
random.seed(42)
np.random.seed(42)

def is_silent(audio, threshold=1):
    return torch.sqrt(torch.mean(audio**2)) < threshold

# 3D room dimensions
room_dim = [3.5, 6.0, 2.65]  # width, length, height
mic_locs = np.array([[1.55, 5.45, 1.80], [0.25, 0.05, 1.80], [3.30, 0.05, 1.8]]).T
print(mic_locs)
source_loc_1 = [2.6, 1, 0.45]
source_loc_2 = [2.6, 2.5, 0.45]
source_loc_3 = [2.6, 4, 0.45]
source_loc = source_loc_3
filename1 = "D:/MOOD-SENSE/ngcc-main/dataset/wav/room3_audio4_mic1.wav"
filename2 = "D:/MOOD-SENSE/ngcc-main/dataset/wav/room3_audio4_mic2.wav"
filename3 = "D:/MOOD-SENSE/ngcc-main/dataset/wav/room3_audio4_mic3.wav"

# Microphone recording in Techhub:
# source_loc_1 RMSE: 1.5430925156627695
# source_loc_2 RMSE: 1.289486590666066
# source_loc_3 RMSE: 1.3750886632855917

fs, signal_1 = wavfile.read(filename1)
fs, signal_2 = wavfile.read(filename2)
fs, signal_3 = wavfile.read(filename3)

y = [np.array(signal_1), np.array(signal_2), np.array(signal_3)]

fig1, ax1 = plt.subplots()
fig, ax = plt.subplots()

predicted_coords = []
true_coords = []

# Pick a 2048-sample long snippet
sig_len = 1024  # Roughly 0.3 ms, # 2048

# Load the GCC-PHAT and PGCC-PHAT modules for TDOA estimation
max_distance = max(np.linalg.norm(mic_locs[:, 0] - mic_locs[:, 1]),
                   np.linalg.norm(mic_locs[:, 0] - mic_locs[:, 2]),
                   np.linalg.norm(mic_locs[:, 1] - mic_locs[:, 2]))
max_tau_gcc = int(np.floor(max_distance * fs / 343))

print('max_tau_gcc:', max_tau_gcc)

max_tau = max_tau_gcc
max_tau = int(max_tau)
gcc = GCC(max_tau)
ngcc = NGCCPHAT(max_tau)

# Load the model weights
ngcc.load_state_dict(torch.load(
    "experiments/ngccphat/model.pth", map_location=torch.device('cpu')))
ngcc.eval()

def loss(x, mic_locs, tdoas):
    return sum([(np.linalg.norm(x - mic_locs[:, pairs[0]]) - np.linalg.norm(x - mic_locs[:, pairs[1]]) - tdoas[i] / fs * 340) ** 2 for i, pairs in enumerate([[0, 1], [0, 2], [1, 2]])])

for start_idx in range(0, min(len(signal_1), len(signal_2), len(signal_3)) - sig_len, 1000):
    end_idx = start_idx + sig_len
    x = torch.Tensor([yi[start_idx:end_idx] for yi in y])

    # Clear and update the first plot
    ax1.clear()
    ax1.plot(range(start_idx, end_idx), x[0], label='Signal 1')
    ax1.plot(range(start_idx, end_idx), x[1], label='Signal 2')
    ax1.plot(range(start_idx, end_idx), x[2], label='Signal 3')
    ax1.legend()
    ax1.set_title('Three Signals')
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Amplitude')
    ax1.set_ylim(min(np.min(yi) for yi in y), max(np.max(yi) for yi in y))
    fig1.canvas.draw()

    # Check if all channels are silent
    if all(is_silent(x[i]) for i in range(x.shape[0])):
        print("Silent frame detected, skipping calculations.")
        continue

    gcc_delays = []
    ngcc_delays = []
    for i, pairs in enumerate([[0, 1], [0, 2], [1, 2]]):
        x1 = x[pairs[0]].unsqueeze(0)
        x2 = x[pairs[1]].unsqueeze(0)

        if is_silent(x1) or is_silent(x2):
            print(f"Pair {pairs}: One or both signals are too quiet, skipping GCC calculation.")
            continue

        # Original GCC and NGCC calculation code
        print('gcc start')
        cc = gcc(x1, x2).squeeze()
        print('size cc = gcc(x1, x2).squeeze()', cc.shape)
        cc = cc / torch.max(cc)
        print('size cc = cc / torch.max(cc)', cc.shape)
        print('ngcc start')
        p = ngcc(x1, x2).squeeze()
        print('size p = ngcc(x1, x2).squeeze()', p.shape)
        p = p.detach()
        print('size p = p.detach()', p.shape)
        p = p / torch.max(p)
        print('size p = p / torch.max(p)', p.shape)

        shift_gcc = float(torch.argmax(cc, dim=-1)) - max_tau
        shift_ngcc = float(torch.argmax(p, dim=-1)) - max_tau
        gcc_delays.append(shift_gcc)
        ngcc_delays.append(shift_ngcc)

    # Only localize if we have enough delay estimates
    if len(gcc_delays) == 3 and len(ngcc_delays) == 3:
        guess = [0, 0]
        bounds = ((0, room_dim[0]), (0, room_dim[1]))
        xhat_gcc = minimize(loss, guess, args=(mic_locs[:2], gcc_delays), bounds=bounds).x
        xhat_ngcc = minimize(loss, guess, args=(mic_locs[:2], ngcc_delays), bounds=bounds).x
        predicted_coords.append(xhat_ngcc)
        true_coords.append(source_loc[:2])

        # Plot estimated positions
        ax.clear()
        ax.plot(xhat_gcc[0], xhat_gcc[1], 'go', markersize=10, label='GCC estimate')
        ax.plot(xhat_ngcc[0], xhat_ngcc[1], 'mo', markersize=10, label='NGCC estimate')
        # Plot reference point (source location)
        ax.plot(source_loc[0], source_loc[1], 'rx', markersize=6, label='Source')
        # Plot microphone locations
        ax.plot(mic_locs[0], mic_locs[1], 'bx', markersize=6, label='Microphones')
    else:
        ax.clear()
        # Plot reference point (source location)
        ax.plot(source_loc[0], source_loc[1], 'rx', markersize=10, label='Source')
        # Plot microphone locations
        ax.plot(mic_locs[0], mic_locs[1], 'bx', markersize=10, label='Microphones')

    ax.set_xlim(0, room_dim[0])
    ax.set_ylim(0, room_dim[1])
    ax.set_aspect('equal')  # Keep aspect ratio

    ax.set_title('Room Layout (2D projection)')
    ax.set_xlabel('Width (m)')
    ax.set_ylabel('Length (m)')

    # Place the legend outside the plot
    ax.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
    # Update the plot
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.1)

print(predicted_coords)
print(true_coords)

if predicted_coords and true_coords:
    predicted_coords = np.array(predicted_coords)
    true_coords = np.array(true_coords)

    # Ensure both are 2D arrays
    if predicted_coords.ndim == 1:
        predicted_coords = predicted_coords.reshape(-1, 2)
    if true_coords.ndim == 1:
        true_coords = true_coords.reshape(-1, 2)

mse = np.mean((predicted_coords - true_coords) ** 2)
print("RMSE:", np.sqrt(mse))
print("done.")

plt.ioff()  # Turn off interactive mode
plt.show()  # Show the last frame

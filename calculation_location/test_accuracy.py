import os
import numpy as np
import torch
from scipy.io import wavfile
from matplotlib import pyplot as plt
import random
import librosa
import librosa.display
from model import GCC
from scipy.optimize import minimize  # Missing import added

# Set random seed
torch.manual_seed(42)
random.seed(42)
np.random.seed(42)

def is_silent(audio, threshold=1):
    return torch.sqrt(torch.mean(audio**2)) < threshold

room_dim = [500, 500, 500]
mic_locs = np.array([[-165, -125, 30], [165, -125, 30], [165, 125, 30], [-165, 125, 30]]).T
print(mic_locs)

denoised_signals = []

# Microphone file paths
path_folder = "D:/MOOD-SENSE/sound_localization-no_multicast_to_esp32/experiments/exp_1/aligned/"
filenames = [os.path.join(path_folder, f"aligned_mic_{i}.wav") for i in range(1, 5)]

# Set up subplots
fig, axs = plt.subplots(2, 2, figsize=(8, 6))
axs = axs.ravel()

# Compute and plot simple spectrograms
for i, filename in enumerate(filenames):
    fs, signal = wavfile.read(filename)
    n_fft = 1024
    hop_length = 256
    Sxx = np.abs(librosa.stft(signal.astype(np.float32), n_fft=n_fft, hop_length=hop_length))
    axs[i].imshow(Sxx, aspect='auto', origin='lower', cmap='magma')
    axs[i].set_title(f"Mic {i+1}")
    axs[i].set_xlabel("Time")
    axs[i].set_ylabel("Frequency")

plt.tight_layout()
plt.show()
plt.pause(1)
plt.close()

# Dynamic noise estimation for spectral subtraction
def estimate_noise_dynamic(signal_stft, percentile=10):
    noise_magnitude = np.percentile(np.abs(signal_stft), percentile, axis=1, keepdims=True)
    return noise_magnitude

def spectral_subtraction_denoise(noisy_signal, fs, n_fft=2048, hop_length=512):
    stft_signal = librosa.stft(noisy_signal.astype(np.float32), n_fft=n_fft, hop_length=hop_length)
    magnitude, phase = np.abs(stft_signal), np.angle(stft_signal)
    noise_magnitude = estimate_noise_dynamic(magnitude)
    magnitude_denoised = np.maximum(magnitude - noise_magnitude, 0)
    stft_denoised = magnitude_denoised * np.exp(1j * phase)
    denoised_signal = librosa.istft(stft_denoised, hop_length=hop_length)
    return np.clip(denoised_signal, -32768, 32767).astype(np.int16)

# Process all audio files
for filename in filenames:
    fs, signal = wavfile.read(filename)
    denoised_signal = spectral_subtraction_denoise(signal, fs)
    output_filename = filename.replace("aligned_", "denoised_")
    wavfile.write(output_filename, fs, denoised_signal)
    print(f"Denoised file saved: {output_filename}")
    denoised_signals.append(denoised_signal)

# Plot spectrograms of denoised audio
fig, axs = plt.subplots(2, 2, figsize=(10, 8))
axs = axs.ravel()

for i, filename in enumerate(filenames):
    fs, signal = wavfile.read(filename.replace("aligned_", "denoised_"))
    Sxx = librosa.amplitude_to_db(np.abs(librosa.stft(signal.astype(np.float32))), ref=np.max)
    librosa.display.specshow(Sxx, sr=fs, hop_length=512, x_axis='time', y_axis='log', ax=axs[i])
    axs[i].set_title(f"Denoised Spectrogram of Mic {i+1}")

plt.show(block=False)
plt.pause(1)
plt.close()

y = [np.array(signal) for signal in denoised_signals]

# Visualization and processing variables
fig1, ax1 = plt.subplots()
fig, ax = plt.subplots()
fig2, ax2 = plt.subplots()
predicted_coords = []
true_coords = []

# Pick a 2048-sample long snippet
sig_len = 1024  # Roughly 0.3 ms

# Load the GCC-PHAT module for TDOA estimation
mic_distance = (np.linalg.norm(mic_locs[:, i] - mic_locs[:, j])
                for i in range(mic_locs.shape[1])
                for j in range(i + 1, mic_locs.shape[1]))

max_distance = max(mic_distance)
print("max_distance=", max_distance)
max_tau_gcc = int(np.floor(max_distance * fs / (343 * 100)))

print('max_tau_gcc:', max_tau_gcc)

max_tau = max_tau_gcc
max_tau = int(max_tau)
gcc = GCC(max_tau)

# Loss function for optimization
def loss(x, mic_locs, tdoas):
    pairs = [(i, j) for i in range(mic_locs.shape[1]) for j in range(i + 1, mic_locs.shape[1])]
    return sum(
        [
            (np.linalg.norm(x - mic_locs[:, pair[0]]) - np.linalg.norm(x - mic_locs[:, pair[1]]) - tdoas[i] / fs * 34000) ** 2
            for i, pair in enumerate(pairs)
        ]
    )

for start_idx in range(0, min(len(y[0]), len(y[1]), len(y[2]), len(y[3])) - sig_len, 1000):
    end_idx = start_idx + sig_len
    x = torch.Tensor([yi[start_idx:end_idx] for yi in y])

    # Clear and update the first plot
    ax1.clear()
    ax1.plot(range(start_idx, end_idx), x[0], label='Signal 1')
    ax1.plot(range(start_idx, end_idx), x[1], label='Signal 2')
    ax1.plot(range(start_idx, end_idx), x[2], label='Signal 3')
    ax1.plot(range(start_idx, end_idx), x[3], label='Signal 4')
    ax1.legend()
    ax1.set_title('Four Signals')
    ax1.set_xlabel('Sample Index')
    ax1.set_ylabel('Amplitude')
    ax1.set_ylim(min(np.min(yi) for yi in y), max(np.max(yi) for yi in y))
    fig1.canvas.draw()

    # Check if all channels are silent
    if all(is_silent(x[i]) for i in range(x.shape[0])):
        print("Silent frame detected, skipping calculations.")
        continue

    gcc_delays = []
    mic_pairs = [(i, j) for i in range(mic_locs.shape[1]) for j in range(i + 1, mic_locs.shape[1])]

    for i, pair in enumerate(mic_pairs):
        x1 = x[pair[0]].unsqueeze(0)
        x2 = x[pair[1]].unsqueeze(0)

        if is_silent(x1) or is_silent(x2):
            print(f"Pair {pair}: One or both signals are too quiet, skipping GCC calculation.")
            continue

        cc = gcc(x1, x2).squeeze()
        cc = cc / torch.max(cc)
        shift_gcc = float(torch.argmax(cc, dim=-1)) - max_tau
        gcc_delays.append(shift_gcc)

    if len(gcc_delays) == len(mic_pairs):
        guess = [np.mean(mic_locs[0]), np.mean(mic_locs[1])]
        bounds = ((-room_dim[0]/2, room_dim[0]/2), (-room_dim[1]/2, room_dim[1]/2))
        xhat_gcc = minimize(loss, guess, args=(mic_locs[:2], gcc_delays), bounds=bounds).x

        ax.clear()
        ax.plot(xhat_gcc[0], xhat_gcc[1], 'go', markersize=10, label='GCC estimate')
        ax.plot(mic_locs[0], mic_locs[1], 'bx', markersize=10, label='Microphones')
    else:
        ax.clear()
        ax.plot(mic_locs[0], mic_locs[1], 'bx', markersize=10, label='Microphones')

    ax.set_xlim(-room_dim[0]/2, room_dim[0]/2)
    ax.set_ylim(-room_dim[1]/2, room_dim[1]/2)
    ax.set_aspect('equal')
    ax.set_title('Layout (2D projection)')
    ax.set_xlabel('Width (cm)')
    ax.set_ylabel('Length (cm)')
    ax.legend(loc='center left', bbox_to_anchor=(1.1, 0.5))
    fig.canvas.draw()
    fig.canvas.flush_events()
    plt.pause(0.001)

plt.ioff()
plt.show()

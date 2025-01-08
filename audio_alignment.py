# %pip install tqdm
import wave
from tqdm import tqdm
import numpy as np
import cupy as cp
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

def calculate_audio_error(signal1, signal2, start_time, stop_time, sample_rate):
    """
    Calculate the squared error between two audio signals within a specified time window.

    Parameters:
    signal1 (cupy array): The first audio signal.
    signal2 (cupy array): The second audio signal.
    start_time (float): The start time in seconds.
    stop_time (float): The stop time in seconds.
    sample_rate (int): The sample rate of the audio signals.

    Returns:
    float: The squared error between the two signals within the time window.
    """

    start_sample = int(start_time * sample_rate)
    end_sample = int(stop_time * sample_rate)

    signal1_sliced = signal1[start_sample:end_sample]
    signal2_sliced = signal2[start_sample:end_sample]

    if len(signal1_sliced) != len(signal2_sliced):
        raise ValueError("The sliced audio signals must have the same length.")

    error = cp.sum((signal1_sliced - signal2_sliced) ** 2)
    return error


def shift_audio(signal, shift_amount):
    """
    Shifts an audio signal by a given number of samples, padding with zeros.

    Parameters:
    signal (cupy array): The audio signal to shift.
    shift_amount (int): The number of samples to shift. 
                        Positive values shift to the right (delay), 
                        negative values shift to the left (advance).

    Returns:
    cupy array: The shifted audio signal with the same length as the input.
    """

    shifted_signal = cp.zeros_like(signal)

    if shift_amount > 0:  # Shift right (delay)
        shifted_signal[shift_amount:] = signal[:-shift_amount]
    elif shift_amount < 0:  # Shift left (advance)
        shifted_signal[:shift_amount] = signal[-shift_amount:]
    else:  # No shift
        shifted_signal = signal.copy()

    return shifted_signal


def find_best_shift(signal1, signal2, start_time, stop_time, sample_rate, max_shift_seconds=3, sample_size=20):
    """
    Finds the best shift (in samples) for signal2 that minimizes the 
    squared error with signal1 within the specified time window.

    Parameters:
    signal1 (cupy array): The first audio signal.
    signal2 (cupy array): The second audio signal.
    start_time (float): The start time in seconds.
    stop_time (float): The stop time in seconds.
    sample_rate (int): The sample rate of the audio signals.
    max_shift_seconds (float): The maximum shift allowed in seconds (default: 3).

    Returns:
    tuple: (best_shift_amount, min_error) 
           - best_shift_amount (int): The shift amount in samples that resulted in the minimum error.
           - min_error (float): The minimum squared error achieved.
    """

    min_error = float('inf')
    best_shift_amount = 0
    max_shift_samples = int(max_shift_seconds * sample_rate)
    
    threshold = 0.0
    
    # signal1 *= 1
    # signal2 *= 1.8
    # signal1 = cp.clip(signal1, -1, 1)
    # signal2 = cp.clip(signal2, -1, 1)
    # Normalize signals so that the max value is always 1 or -1
    start_sample = int(start_time * sample_rate)
    stop_sample = int(stop_time * sample_rate)
    signal1 = signal1 / cp.max(cp.abs(signal1[start_sample:stop_sample]))
    signal2 = signal2 / cp.max(cp.abs(signal2[start_sample:stop_sample]))
    # signal1 = cp.where(cp.abs(signal1) < threshold, 0, signal1)
    # signal2 = cp.where(cp.abs(signal2) < threshold, 0, signal2)
    signal1 = cp.abs(signal1)
    signal2 = cp.abs(signal2)

    # Calculate the derivative (dy/dx) of the signals
    # signal1_derivative = cp.gradient(signal1)
    # signal2_derivative = cp.gradient(signal2)
    # Calculate running average of signal1 and signal2
    window_size = sample_size
    signal1_running_avg = cp.convolve(signal1, cp.ones(window_size)/window_size, mode='valid')
    signal2_running_avg = cp.convolve(signal2, cp.ones(window_size)/window_size, mode='valid')

    # Adjust start and stop samples for running average
    start_sample += window_size // 2
    stop_sample -= window_size // 2
    for shift_amount in tqdm(range(0, max_shift_samples + 1), desc="Finding best shift"):
        shifted_running_avg_signal2 = shift_audio(signal2_running_avg, shift_amount)
        error = calculate_audio_error(signal1_running_avg, shifted_running_avg_signal2, start_time, stop_time, sample_rate)
        
        if error < min_error:
            min_error = error
            best_shift_amount = shift_amount

    return best_shift_amount, min_error

# file_1 = 'experiments/experiments/exp_1/audio_raw_files/17221159_ESP32_Audio_Device_1734631034.bin'
# file_2 = 'experiments/experiments/exp_1/audio_raw_files/17221170_ESP32_Audio_Device_1734631035.bin'
# file_3 = 'experiments/experiments/exp_1/audio_raw_files/17221157_ESP32_Audio_Device_1734631035.bin'
# file_4 = 'experiments/experiments/exp_1/audio_raw_files/17221172_ESP32_Audio_Device_1734631035.bin'
file_1 = 'experiments/experiments/exp_1/aligned/aligned_mic_1.wav'
file_2 = 'experiments/experiments/exp_1/aligned/aligned_mic_2.wav'
file_3 = 'experiments/experiments/exp_1/aligned/aligned_mic_3.wav'
file_4 = 'experiments/experiments/exp_1/aligned/aligned_mic_4.wav'
# Function to read audio file
def read_audio(file_path):
    with wave.open(file_path, 'r') as wf:
        num_channels = wf.getnchannels()
        framerate = wf.getframerate()
        num_frames = wf.getnframes()
        frames = wf.readframes(num_frames)
        if wf.getsampwidth() == 2:
            audio_data = np.frombuffer(frames, dtype=np.int16)
        elif wf.getsampwidth() == 1:
            audio_data = np.frombuffer(frames, dtype=np.int8)
        else:
            raise ValueError("Unsupported sample width. Only 8-bit and 16-bit are currently supported.")
        audio_data = audio_data / np.max(np.abs(audio_data))
        if num_channels > 1:
            audio_data = audio_data[::num_channels]  # Take only the left channel
    return audio_data, framerate, num_channels

def read_binary_audio(file_path, channels=2, sample_width=2, frame_rate=44100):
    """
    Reads a binary audio file (.bin) and returns the audio data as a NumPy array.

    Parameters:
    file_path (str): Path to the binary audio file.
    channels (int): Number of channels in the audio data (default: 2).
    sample_width (int): Number of bytes per sample (default: 2).
    frame_rate (int): Sampling rate of the audio data (default: 44100).

    Returns:
    tuple: (audio_data, frame_rate, num_channels)
           - audio_data (numpy array): The audio data as a NumPy array.
           - frame_rate (int): The frame rate of the audio data.
           - num_channels (int): The number of channels in the audio data.
    """

    with open(file_path, 'rb') as f:
        binary_data = f.read()

    # Determine the appropriate data type based on sample_width
    if sample_width == 2:
        dtype = np.int16
    elif sample_width == 1:
        dtype = np.int8
    else:
        raise ValueError("Unsupported sample width. Only 8-bit and 16-bit are currently supported.")

    # Convert binary data to NumPy array
    audio_data = np.frombuffer(binary_data, dtype=dtype)
    audio_data = audio_data / np.max(np.abs(audio_data))  # Normalize

    # If stereo, take only the left channel
    if channels > 1:
        audio_data = audio_data[::channels]

    return audio_data, frame_rate, channels

# Read audio files
audio_data_1, framerate_1, num_channels_1 = read_audio(file_1)
audio_data_2, framerate_2, num_channels_2 = read_audio(file_3)

# Define start and stop times for plotting
plot_start_time = 4  # in seconds
plot_stop_time = 10  # in seconds

# Convert times to sample indices
plot_start_sample_1 = int(plot_start_time * framerate_1)
plot_stop_sample_1 = int(plot_stop_time * framerate_1)
plot_start_sample_2 = int(plot_start_time * framerate_2)
plot_stop_sample_2 = int(plot_stop_time * framerate_2)

# Plot waveforms within the specified time window
# plt.figure(figsize=(14, 6))
# time_axis_1 = np.linspace(plot_start_time, plot_stop_time, num=(plot_stop_sample_1 - plot_start_sample_1))
# time_axis_2 = np.linspace(plot_start_time, plot_stop_time, num=(plot_stop_sample_2 - plot_start_sample_2))

# plt.subplot(2, 1, 1)
# plt.plot(time_axis_1, audio_data_1[plot_start_sample_1:plot_stop_sample_1])
# plt.title('Waveform of File 1')
# plt.xlabel('Time (seconds)')
# plt.ylabel('Amplitude')

# plt.subplot(2, 1, 2)
# plt.plot(time_axis_2, audio_data_2[plot_start_sample_2:plot_stop_sample_2])
# plt.title('Waveform of File 2')
# plt.xlabel('Time (seconds)')
# plt.ylabel('Amplitude')

# plt.tight_layout()
# plt.show()

# Move data to GPU
audio_data_1_gpu = cp.asarray(audio_data_1)
audio_data_2_gpu = cp.asarray(audio_data_2)

# Find the best shift on the GPU
start_time = 6
stop_time = 8
sample_size = 4000
# best_shift, min_error = find_best_shift(audio_data_1_gpu, audio_data_2_gpu, start_time, stop_time, framerate_1, 1, sample_size)
best_shift = 0
min_error = 0
print(f"Best shift: {best_shift} samples")
print(f"Minimum error: {min_error}")
# best_shift = 15188
# Define start and stop times for plotting

# plot_start_time = 7.425  # in seconds
# plot_stop_time = 7.43  # in seconds
# plot_start_time = 7.4
# plot_stop_time = 7.5
plot_start_time = 6
plot_stop_time = 9
# Convert times to sample indices
plot_start_sample_1 = int(plot_start_time * framerate_1)
plot_stop_sample_1 = int(plot_stop_time * framerate_1)
plot_start_sample_2 = int(plot_start_time * framerate_2)
plot_stop_sample_2 = int(plot_stop_time * framerate_2)

# Plot waveforms within the specified time window
# plt.figure(figsize=(14, 6))
time_axis_1 = np.linspace(plot_start_time, plot_stop_time, num=(plot_stop_sample_1 - plot_start_sample_1))
time_axis_2 = np.linspace(plot_start_time, plot_stop_time, num=(plot_stop_sample_2 - plot_start_sample_2))

# threshold = 0.0
# new_signal1 = np.where(np.abs(audio_data_1) < threshold, 0,  audio_data_1)
# new_signal2 = np.where(np.abs(audio_data_2) < threshold, 0, audio_data_2)
# new_signal1 *= 1
# new_signal2 *= 1.8
# new_signal1 = np.clip(new_signal1, -1, 1)
# new_signal2 = np.clip(new_signal2, -1, 1)

new_signal1 = (audio_data_1 / np.max(np.abs(audio_data_1[plot_start_sample_1:plot_stop_sample_1])))
new_signal2 = (audio_data_2 / np.max(np.abs(audio_data_2[plot_start_sample_1:plot_stop_sample_1])))
new_signal1_avg = new_signal1
new_signal2_avg = new_signal2

# new_signal1_avg = np.convolve(new_signal1, np.ones(sample_size)/sample_size, mode='valid')
# new_signal2_avg = np.convolve(new_signal2, np.ones(sample_size)/sample_size, mode='valid')

fig, ax = plt.subplots(figsize=(7, 4))
plt.subplots_adjust(left=0.1, bottom=0.25)

# Shift audio_data_2 by best_shift amount
addition = 0
shifted_audio_data_2 = np.roll(new_signal2_avg, best_shift + addition)

# error = calculate_audio_error(new_signal1_avg, shifted_audio_data_2, start_time, stop_time, framerate_1)

# Plot the waveforms
line1, = ax.plot(time_axis_1, new_signal1_avg[plot_start_sample_1:plot_stop_sample_1], label='File 1')
line2, = ax.plot(time_axis_2, shifted_audio_data_2[plot_start_sample_2:plot_stop_sample_2], label='Shifted File 2')

ax.set_title('Waveforms of File 1 and Shifted File 2')
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Amplitude')
ax.legend()

multiplier = 1
def key_press(event):
    global addition, shifted_audio_data_2, line2, multiplier  # Access global variables
    changed =False
    if event.key == 'shift':
        multiplier *=10
        print(f"Multiplier: {multiplier}")
    if event.key == 'control':
        multiplier /=10
        print(f"Multiplier: {multiplier}")
    
    if event.key == '+':    
        addition += int(1 * multiplier)
        changed = True
    elif event.key == '-':
        addition -= int(1 * multiplier)
        changed = True

    if changed:
        # Update the shifted audio data
        shifted_audio_data_2 = np.roll(new_signal2_avg, best_shift + addition)

        # Update the plot
        line2.set_ydata(shifted_audio_data_2[plot_start_sample_2:plot_stop_sample_2])
        fig.canvas.draw_idle()

        # Calculate the error between the signals (optional)
        # error = np.sum((new_signal1_avg[plot_start_sample_1:plot_stop_sample_1] - shifted_audio_data_2[plot_start_sample_2:plot_stop_sample_2]) ** 2)
        print(f"Current shift: {best_shift + addition} samples")
# Connect the key press event to the figure
fig.canvas.mpl_connect('key_press_event', key_press)

plt.tight_layout()
plt.show()

import librosa
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import soundfile as sf
import glob
import os

# Sound speed and 3D coordinates of microphones and source
sound_speed = 343  # in m/s
source_coords = np.array([125, 25, 30])  # Source coordinates (cm)
mic_coords = [
    np.array([-165, -125, 30]),
    np.array([165, -125, 30]),
    np.array([165, 125, 30]),
    np.array([-165, 125, 30])
]  # Microphone coordinates (cm)

# Calculate the delay times from the source to each microphone (in seconds)
mic_delays = [
    np.linalg.norm(source_coords - mic_coord) / 100 / sound_speed for mic_coord in mic_coords
]
print(mic_delays)

# Global variable to store the selected peak times for each microphone
selected_times = {}

def on_click(event, mic_id, peak_times):
    """
    Mouse click event to record the selected peak times (start and end).
    """
    if mic_id not in selected_times:
        selected_times[mic_id] = []

    if len(selected_times[mic_id]) < 2:
        clicked_time = event.xdata
        # Find the nearest peak time to the clicked point
        nearest_peak_time = min(peak_times, key=lambda x: abs(x - clicked_time))
        selected_times[mic_id].append(nearest_peak_time)  # Add to the selected times list
        print(f"Selected peak time for mic {mic_id}: {nearest_peak_time:.2f} seconds")
        if len(selected_times[mic_id]) == 2:
            print(f"Mic {mic_id}: Both start and end points selected.")
            if len(selected_times) == 4:  # If all microphones have selected their points
                plt.close()  # Close the plot

# Function to visualize and allow the user to select pulse start and end times
def select_pulse_times(y, sr, mic_id):
    """
    Display the waveform of the audio and allow the user to manually select the start and end times for the pulse.
    """
    print(f"Processing microphone {mic_id}")
    amplitude_envelope = np.abs(y)

    # Calculate the envelope of the audio signal (absolute value)
    threshold = 0.5 * np.max(amplitude_envelope)  # Set to 50% of the max amplitude
    peaks, _ = find_peaks(amplitude_envelope, height=threshold, distance=sr // 2)  # Ensure at least 0.5 second distance
    peak_times = peaks / sr  # Convert peak indices to time (seconds)

    plt.plot(np.arange(len(y)) / sr, amplitude_envelope, label=f"Mic {mic_id}")
    plt.scatter(peak_times, amplitude_envelope[peaks], color="red", label=f"Detected Peaks Mic {mic_id}")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title("Click near peaks to select start and end points")
    plt.grid()

    # Bind the mouse click event
    plt.gcf().canvas.mpl_connect('button_press_event', lambda event: on_click(event, mic_id, peak_times))

    plt.legend()
    plt.show()

    if mic_id not in selected_times or len(selected_times[mic_id]) < 2:
        raise ValueError(f"Error: Mic {mic_id} must select exactly two peaks.")
    
    return sorted(selected_times[mic_id])

# Function to process and align audio files
def process_audio(file_path, mic_delay, mic_id, output_folder):
    """
    Load the audio file, allow the user to select start and end peaks, and align the audio based on propagation delay.
    """
    y, sr = librosa.load(file_path, sr=None)
    pulse_times = select_pulse_times(y, sr, mic_id)

    # Subtract the delay from the selected start time to get the aligned start point
    start_time_aligned = pulse_times[0] - mic_delay
    end_time_aligned = pulse_times[1] - mic_delay

    # Ensure the start and end points are within the audio range
    start_sample = max(0, int(start_time_aligned * sr))
    end_sample = min(len(y), int(end_time_aligned * sr))

    # Clip the audio
    aligned_audio = y[start_sample:end_sample]

    # Save the aligned audio file
    output_path = os.path.join(output_folder, f"aligned_mic_{mic_id}.wav")
    sf.write(output_path, aligned_audio, sr)
    print(f"Aligned audio saved for microphone {mic_id}: {output_path}")

# Main program
def main():
    # Define the main folder
    main_folder = "./experiments/exp_1/"
    
    # Input and output folder paths
    folder_path = os.path.join(main_folder, "audio_wav_files/")
    output_folder = os.path.join(main_folder, "aligned/")
    
    # Create the output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    plt.figure(figsize=(12, 6))

    for mic_id in range(1, 5):  # Process each microphone file
        file_paths = glob.glob(f"{folder_path}{mic_id}_*.wav")

        for file_path in file_paths:  # Process all matching file paths
            print(f"Processing {file_path}")
            process_audio(file_path, mic_delays[mic_id - 1], mic_id, output_folder)
    
    print("All microphones processed and aligned.")
    plt.show()

if __name__ == "__main__":
    main()

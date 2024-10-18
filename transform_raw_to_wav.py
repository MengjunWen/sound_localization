import wave

def convert_text_to_wav(input_file, output_file, channels, sampwidth, framerate):
    # Prepare to read the text file and collect data
    data = []
    with open(input_file, 'r') as file:
        for line in file:
            if line.strip():  # Ensure the line has content
                # Convert the line to an integer and pack it into binary format
                # Adjust the format '<h' as per your data range and endianess
                # also add AMPLIFY with '*5'
                sample = int(float(line.strip())*5)
                # Check sample width to determine packing format
                if sampwidth == 2:
                    data.append(sample.to_bytes(2, byteorder='little', signed=True))
                elif sampwidth == 1:
                    data.append(sample.to_bytes(1, byteorder='little', signed=True))
    # Convert the list of bytes into a bytes object
    data_bytes = b''.join(data)

    # Write the data to a WAV file
    with wave.open(output_file, 'w') as wavfile:
        wavfile.setnchannels(channels)
        wavfile.setsampwidth(sampwidth)
        wavfile.setframerate(framerate)
        wavfile.writeframes(data_bytes)

# Example usage:
input_file = 'recording1.txt'  # Path to your raw text file
output_file = 'a_test_1_amplified2.wav'  # Desired path for the output WAV file
channels = 1  # Mono audio
sampwidth = 2  # 2 bytes per sample (16-bit audio)
framerate = int(20000)  # Sample rate in Hz

convert_text_to_wav(input_file, output_file, channels, sampwidth, framerate)

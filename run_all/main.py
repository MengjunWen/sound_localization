import asyncio
import csv
from datetime import datetime
import numpy as np
from zeroconf import ServiceBrowser, Zeroconf, ServiceStateChange
from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, Root

robot = Root(Bluetooth('Robot 10'))

from experiment_manager import ExperimentManager
from video_recorder import VideoRecorder
from audio_recorder import AudioRecorders
from logger import Logger
import threading
import soundfile as sf
import matplotlib.pyplot as plt

csv_file = "D:/MOOD-SENSE/sound_localization-no_multicast_to_esp32/action_sequences/4.csv"

expected_device_count=4

def load_actions_from_csv(file_path):
    """Load actions from a CSV file."""
    actions = []
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            action_type = row[0]
            if action_type == 'move':
                distance = int(row[1])
                if len(row) == 2:
                    actions.append((row[0], int(row[1])))
                elif len(row) == 4:  # move, Distance, frequency, and duration
                    actions.append((action_type, distance, int(row[2]), float(row[3])))
            elif action_type in ['turn_left', 'turn_right']:
                degrees = int(row[1])
                if len(row) == 2:
                    actions.append((row[0], int(row[1])))
                elif len(row) == 4:  # turn, angel, frequency, duration
                    actions.append((action_type, degrees, int(row[2]), float(row[3])))
            elif action_type == 'wait':
                duration = float(row[1])
                if len(row) == 2:
                    actions.append((action_type, duration))
                elif len(row) == 3:
                    actions.append((action_type, duration, int(row[2])))
    print(f"Loaded actions: {actions}")  # Debug loaded actions
    return actions

@event(robot.when_play)
async def perform_actions(robot):
    sequence = load_actions_from_csv(csv_file)
    exp_manager = ExperimentManager()  # 创建实验文件夹管理器
    exp_folder = exp_manager.get_exp_folder()
    logger = Logger(exp_folder)

    video_recorder = VideoRecorder(calibration_file="calibration_data.npz", output_directory=exp_folder, logger=logger)
    audio_recorder = AudioRecorders(exp_folder, logger)
    
    # 启动视频录制
    if video_recorder.start():
        # 在后台异步运行捕获视频帧的方法
        video_task = asyncio.create_task(video_recorder.capture_frames())

    await audio_recorder.discover_devices(expected_device_count)
    # hardcoded ip addresses
    # audio_recorder.list_of_esp32 = ["172.21.1.59", "172.21.1.70", "172.21.1.57", "172.21.1.72"]

    if len(audio_recorder.list_of_esp32) == expected_device_count:
        print("All devices discovered, starting audio recording...")
        # await asyncio.sleep(2)
        await audio_recorder.start_tcp()

        logger.log_timestamp('Actions Start')
        async def execute_actions():
            for action in sequence:
                if action[0] == 'move':
                    distance = action[1]
                    print(f"Moving {distance} cm")
                    move_task = asyncio.create_task(robot.move(distance))
                    if len(action) > 2:
                        note_task = asyncio.create_task(robot.play_note(action[2], action[3]))
                    
                    await move_task
                    if len(action) > 2:
                        await note_task

                elif action[0] in ['turn_left', 'turn_right']:
                    direction = 'left' if action[0] == 'turn_left' else 'right'
                    print(f"Rotating {action[1]} degrees to the {direction}")

                    turn_task = asyncio.create_task(
                        robot.turn_left(action[1]) if action[0] == 'turn_left' else robot.turn_right(action[1])
                    )
                    if len(action) > 2:
                        note_task = asyncio.create_task(robot.play_note(action[2], action[3]))

                    await turn_task
                    if len(action) > 2:
                        await note_task
                
                elif action[0] == 'wait':
                    # 如果有3个参数，播放音符但不等待
                    if len(action) == 3:
                        print(f"Playing note with frequency {action[2]} for {action[1]} seconds")
                        await robot.play_note(action[2], action[1])
                    # 如果参数少于3个，执行等待
                    elif len(action) < 3:
                        print(f"Waiting for {action[1]} seconds")
                        await robot.wait(action[1])

        await execute_actions()
        logger.log_timestamp('Actions End')

        audio_recorder.stop_tcp()

        video_recorder.stop_video()

        logger.save_timestamps_to_csv()
        await robot.disconnect()

        print("Downloading audio files...")

        threads = []
        results = []
        for i, ip in enumerate(audio_recorder.list_of_esp32):
            thread = threading.Thread(target=lambda q, arg1: q.append(audio_recorder.download_latest_recording(arg1)), args=(results, ip,))
            threads.append(thread)  # Store the thread objects
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Print the results
        fig, axs = plt.subplots(len(results), 2, figsize=(10, 2 * len(results)))

        for i, (result, ip) in enumerate(results):
            data, samplerate = sf.read(result)
                # Separate channels
            if len(data.shape) > 1:  # Check if stereo
                left_channel = data[:, 0]
                right_channel = data[:, 1]
            else:
                left_channel = data
                right_channel = data  # If mono, duplicate the data

            # Plot left channel
            time_axis = np.linspace(0, len(left_channel) / samplerate, num=len(left_channel))

            axs[i, 0].plot(time_axis, left_channel)
            axs[i, 0].set_title(f'Waveform {i+1} - {ip} - Left Channel')
            axs[i, 0].set_xlabel('Time (s)')
            axs[i, 0].set_ylabel('Amplitude')
            axs[i, 0].set_ylim([-1, 1])  # Set y-axis limits

            # Plot right channel
            axs[i, 1].plot(time_axis, right_channel)
            axs[i, 1].set_title(f'Waveform {i+1} - {ip} - Right Channel')
            axs[i, 1].set_xlabel('Time (s)')
            axs[i, 1].set_ylabel('Amplitude')
            axs[i, 1].set_ylim([-1, 1])  # Set y-axis limits


        plt.tight_layout()
        plt.show()

        
        print("Actions completed.")

robot.play()

print('Finished')
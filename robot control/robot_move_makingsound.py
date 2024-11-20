from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, Robot, Root, Create3
from irobot_edu_sdk.music import Note

import asyncio
from bleak import BleakScanner, BleakClient

# Bluetooth connection code
async def run():
    # 扫描附近的蓝牙设备
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Device found: {device.name}, {device.address}")
        if device.name == "Robot 10":  # 根据设备名称连接
            async with BleakClient(device.address) as client:
                print(f"Connected to {device.name}")
                break

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

# Robot setup
robot = Root(Bluetooth())

@event(robot.when_play)
async def draw_square(robot):
    # Step 1: Play starting sound
    print("Playing starting sound...")
    await robot.play_note(150, 2.0)
    await robot.wait(0.1)
    await robot.play_note(300, 2.0)

    # Step 2: Draw square while playing variable sound
    async def play_variable_sound():
        frequency = 100  # Start frequency at 100Hz
        while True:
            await robot.play_note(frequency, 1)  # Play note with current frequency
            frequency += 100  # Increase frequency by 100Hz
            if frequency > 1000:  # Reset frequency if it exceeds 1000Hz
                frequency = 100
            await asyncio.sleep(1)  # Wait for 1 second before changing frequency

    # Start the sound task in parallel
    sound_task = asyncio.create_task(play_variable_sound())

    # Draw a square (10 sides for demonstration)
    for _ in range(10):
        print("Moving forward")
        await robot.move(10)  # cm
        await robot.turn_left(90)  # degrees

    # Step 3: Stop sound after drawing the square
    sound_task.cancel()  # Stop the sound task
    await robot.stop_sound()

robot.play()

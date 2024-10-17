from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, hand_over, Color, Robot, Root, Create3
from irobot_edu_sdk.music import Note

import asyncio

robot = Root(Bluetooth())

@event(robot.when_play)
async def draw_square(robot):
    await robot.set_marker_down()  # Will have no effect on Create 3.
    print("Event triggered2")

    # Play sound in parallel using a loop for continuous effect
    async def play_variable_sound():
        frequency = 100  # Start at 100Hz
        while True:
            await robot.play_note(frequency, 1)  # Play note with current frequency
            frequency += 100  # Increase frequency by 100Hz
            if frequency > 1000:  # Reset frequency if it exceeds 2000Hz
                frequency = 100
            await asyncio.sleep(1)  # Wait for 1 second before changing frequency

    sound_task = asyncio.create_task(play_variable_sound())

    # Move and draw square
    for _ in range(10):
        print("Moving forward")
        await robot.move(50)  # cm
        await robot.turn_left(90)  # deg

    # Stop sound after drawing the square
    sound_task.cancel()  # Stop the sound task
    await robot.stop_sound()
    await robot.set_marker_and_eraser_up()

robot.play()

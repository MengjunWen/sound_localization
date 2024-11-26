from action_generator import generate_random_action_sequence, save_actions_to_csv

# Bluetooth connection code (assuming this part remains the same)
async def run():
    devices = await BleakScanner.discover()
    for device in devices:
        print(f"Device found: {device.name}, {device.address}")
        if device.name == "Robot 10":  
            async with BleakClient(device.address) as client:
                print(f"Connected to {device.name}")
                break

loop = asyncio.get_event_loop()
loop.run_until_complete(run())

# Assuming robot setup is done the same way as in previous example
robot = Root(Bluetooth())

@event(robot.when_play)
async def perform_actions(robot):
    # Generate a random action sequence
    sequence = generate_random_action_sequence()

    # Save the generated sequence to a CSV file
    save_actions_to_csv(sequence)

    # Execute the action sequence
    for action in sequence:
        if action[0] == 'move':
            print(f"Moving {action[1]} cm")
            await robot.move(action[1])
            if len(action) > 2:  # Check if sound is included in the action (i.e., frequency present)
                await robot.play_note(action[2], 1)  # Play sound with frequency
            await robot.wait(action[3])  # Wait for the move to complete
        elif action[0] == 'wait':
            print(f"Waiting for {action[1]} seconds")
            if len(action) == 2:  # No frequency included for wait
                await robot.wait(action[1])
            elif len(action) == 3:  # Frequency is included for wait
                await robot.play_note(action[0], 1)  # Play sound with frequency
                await robot.wait(action[1])  # Wait for the specified duration
        elif action[0] in ['rotate_left', 'rotate_right']:
            direction = 'left' if action[0] == 'rotate_left' else 'right'
            print(f"Rotating {action[1]} degrees to the {direction}")
            if direction == 'left':
                await robot.turn_left(action[1])
            else:
                await robot.turn_right(action[1])
            if len(action) > 2:  # Check if sound is included in the action (i.e., frequency present)
                await robot.play_note(action[2], 1)  # Play sound with frequency
            await robot.wait(action[3])  # Wait for the rotation to complete

    # Step 3: Stop sound after execution
    await robot.stop_sound()

robot.play()

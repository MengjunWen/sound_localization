import argparse
import asyncio
from bleak import BleakScanner, BleakClient
from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, Root
from irobot_edu_sdk.music import Note
from action_generator import generate_random_action_sequence, save_actions_to_csv


# Bluetooth connection code
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

# Setup robot connection
robot = Root(Bluetooth())

def load_actions_from_csv(file_path):
    """Load actions from a CSV file."""
    actions = []
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row[0] == 'move':
                # If it's a move action, we check if it includes frequency
                if len(row) == 3:
                    actions.append((row[0], int(row[1]), float(row[2])))
                else:
                    actions.append((row[0], int(row[1]), int(row[2]), float(row[3])))
            elif row[0] in ['rotate_left', 'rotate_right']:
                # For rotation, check if it includes frequency
                if len(row) == 3:
                    actions.append((row[0], int(row[1]), float(row[2])))
                else:
                    actions.append((row[0], int(row[1]), int(row[2]), float(row[3])))
            else:
                actions.append((row[0], float(row[1])))
    return actions

@event(robot.when_play)
async def perform_actions(robot, mode='simulate', csv_file=None):
    # Select action sequence generation method
    if mode == 'simulate':
        # Generate a random action sequence
        sequence = generate_random_action_sequence()
        # Save the generated sequence to a CSV file
        save_actions_to_csv(sequence)
    elif mode == 'csv' and csv_file:
        # Load the action sequence from a CSV file
        sequence = load_actions_from_csv(csv_file)

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

def main():
    parser = argparse.ArgumentParser(description="Control the robot.")
    parser.add_argument('--mode', choices=['simulate', 'csv'], required=True, help="Run in simulate or csv mode")
    parser.add_argument('--csv_file', type=str, help="Path to the CSV file containing the action sequence (only for csv mode)")

    args = parser.parse_args()

    # Run the robot actions based on the selected mode
    if args.mode == 'simulate':
        asyncio.run(perform_actions(robot, mode='simulate'))
    elif args.mode == 'csv' and args.csv_file:
        asyncio.run(perform_actions(robot, mode='csv', csv_file=args.csv_file))

if __name__ == "__main__":
    main()

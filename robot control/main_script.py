from irobot_edu_sdk.backend.bluetooth import Bluetooth
from irobot_edu_sdk.robots import event, Root
import csv
import asyncio

robot = Root(Bluetooth())
def load_actions_from_csv(file_path):
    """Load actions from a CSV file."""
    actions = []
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        for row in reader:
            print(f"Loading row: {row}")  # Add this to debug CSV reading
            action_type = row[0]
            if action_type == 'move':
                distance = int(row[1])
                if len(row) == 2:
                    actions.append((row[0], int(row[1])))
                if len(row) == 3:  # Only distance and duration
                    actions.append((action_type, distance, float(row[2])))
                elif len(row) == 4:  # Distance, frequency, and duration
                    actions.append((action_type, distance, int(row[2]), float(row[3])))
            elif action_type in ['turn_left', 'turn_right']:
                degrees = int(row[1])
                if len(row) == 2:
                    actions.append((row[0], int(row[1])))
                if len(row) == 3:  # Only degrees and duration
                    actions.append((action_type, degrees, float(row[2])))
                elif len(row) == 4:  # Degrees, frequency, and duration
                    actions.append((action_type, degrees, int(row[2]), float(row[3])))
            elif action_type == 'wait':
                duration = float(row[1])
                if len(row) == 2:
                    actions.append((action_type, duration))
                elif len(row) == 3:
                    actions.append((action_type, duration, int(row[2])))
    print(f"Loaded actions: {actions}")  # Debug the loaded actions
    return actions

# Play sound in parallel using a loop for continuous effect
async def play_variable_sound():
    frequency = 100  # Start at 100Hz
    while True:
        await robot.play_note(frequency, 1)  # Play note with current frequency
        frequency += 100  # Increase frequency by 100Hz
        if frequency > 1000:  # Reset frequency if it exceeds 2000Hz
            frequency = 100
        await asyncio.sleep(1)  # Wait for 1 second before changing frequency

@event(robot.when_play)
async def perform_actions(robot):
    print("Event triggered2")
    #sound_task = asyncio.create_task(play_variable_sound())

    csv_file = "./action_sequences/actions_1732895967.csv"  
    # Replace with your CSV file path
    sequence = load_actions_from_csv(csv_file)

    for action in sequence:
        print(f"Performing action: {action}")  # Debug each action
        
        if action[0] == 'move':
            print(f"Moving {action[1]} cm")
            await robot.move(action[1])  # Ensure move is awaited properly
            if len(action) > 2 :  # Check if sound frequency is included
                await robot.play_note(action[2], action[3])
        elif action[0] == 'wait':
            print(f"Waiting for {action[1]} seconds")
            if len(action) == 3:
                await robot.play_note(action[2], action[1])
            await robot.wait(action[1])
        elif action[0] in ['turn_left', 'turn_right']:
            direction = 'left' if action[0] == 'turn_left' else 'right'
            print(f"Rotating {action[1]} degrees to the {direction}")
            if direction == 'left':
                await robot.turn_left(action[1])
            else:
                await robot.turn_right(action[1])
            if len(action) > 2:  # Check if sound frequency is included
                await robot.play_note(action[2], action[3])

robot.play()
print('finish')

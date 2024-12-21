import random
import csv
import time
import os
import math
# Please do not change the csv generated manually, otherwise error comes up.

# Constants
ACTION_TYPES = ['move', 'wait', 'turn_left', 'turn_right']
MIN_FREQ = 100
MAX_FREQ = 2000
ROBOT_SPEED_CM_S = 5  # Robot speed in cm per second
ROTATION_SPEED_DEG_S = 90  # Robot rotation speed in degrees per second
MAX_DISTANCE = 50  # Maximum movement in any direction (50 cm)
MAX_ROTATION = 180
ACTION_DURATION = 50  # Action duration in seconds
BOUNDARY = 90  # Square boundary: [-100, -100] to [100, 100]

# Robot's initial position and direction
current_position = [0, 0]  # [x, y]
current_angle = 0  # Angle in degrees, 0 means facing "right"

def is_within_bounds(x, y):
    """Check if the new position is within the boundary [-100, 100]."""
    return -BOUNDARY <= x <= BOUNDARY and -BOUNDARY <= y <= BOUNDARY

def update_position(distance):
    """Update the robot's position based on the current angle and distance."""
    global current_position, current_angle
    dx = round(distance * math.cos(math.radians(current_angle)))
    dy = round(distance * math.sin(math.radians(current_angle)))

    new_x = current_position[0] + dx
    new_y = current_position[1] + dy

    if is_within_bounds(new_x, new_y):
        current_position = [new_x, new_y]
        return True
    return False

def generate_random_action_sequence():
    sequence = []
    elapsed_time = 0

    global current_position, current_angle

    # Add predefined actions at the beginning
    # Wait actions with 500Hz sound
    sequence.append(('wait', 0.2, 880))  # Wait 1 second with 500Hz sound
    sequence.append(('wait', 0.2, 784))
    sequence.append(('wait', 0.2, 659))
    sequence.append(('wait', 0.2, 523))
    sequence.append(('wait', 0.2, 880))
    sequence.append(('wait', 3 ))
    elapsed_time += 4.0  # Update elapsed time for these two actions

    # Move action, 50cm without sound
    predefined_move_distance = 20
    duration = round(predefined_move_distance / ROBOT_SPEED_CM_S, 1)  # Time to move
    if update_position(predefined_move_distance):  # Update position
        sequence.append(('move', predefined_move_distance))
        elapsed_time += duration
    else:
        print("Initial move out of bounds, skipping.")  # This is unlikely since (0,0) is valid.
    last_action = None  # Keep track of the last action

    # Generate random actions
    while elapsed_time < ACTION_DURATION - 5.0:
        action = random.choices(ACTION_TYPES, weights=[65, 10, 5, 20], k=1)[0]

        if action == 'move':
            distance = random.randint(10, MAX_DISTANCE)
            if update_position(distance):
                duration = round(distance / ROBOT_SPEED_CM_S, 1)
                frequency = random.randint(MIN_FREQ, MAX_FREQ)
                sequence.append(('move', distance, frequency, duration))
                elapsed_time += duration
                last_action = 'move'
            else:
                continue

        elif action == 'wait':
            duration = round(random.uniform(0.5, 2.0), 1)
            frequency = random.randint(MIN_FREQ, MAX_FREQ)
            sequence.append(('wait', duration, frequency))
            elapsed_time += duration
            last_action = 'wait'

        elif action in ['turn_left', 'turn_right']:
            if last_action in ['turn_left', 'turn_right']:
                continue  # Skip this action to avoid consecutive turns

            degrees = random.randint(15, MAX_ROTATION)
            duration = round(degrees / ROTATION_SPEED_DEG_S, 1)
            frequency = random.randint(MIN_FREQ, MAX_FREQ)

            # Simulate angle update to ensure it remains within bounds
            test_angle = current_angle + (degrees if action == 'turn_left' else -degrees)
            test_angle %= 360

            if action == 'turn_left':
                current_angle = (current_angle + degrees) % 360
            elif action == 'turn_right':
                current_angle = (current_angle - degrees) % 360

            sequence.append((action, degrees, frequency, duration))
            elapsed_time += duration
            last_action = action

    sequence.append(('wait', 0.2, 880))  
    sequence.append(('wait', 0.2, 784))
    sequence.append(('wait', 0.2, 659))
    sequence.append(('wait', 0.2, 523))
    sequence.append(('wait', 0.2, 880))
    sequence.append(('wait', 5 ))
    return sequence

def save_actions_to_csv(sequence):
    timestamp = int(time.time())
    filename = f"actions_{timestamp}.csv"

    if not os.path.exists('action_sequences'):
        os.makedirs('action_sequences')

    file_path = os.path.join('action_sequences', filename)

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        for action in sequence:
            writer.writerow(action)
    print(f"Action sequence saved to {file_path}")

# Generate the sequence and save it
actions = generate_random_action_sequence()
save_actions_to_csv(actions)

import random
import csv
import time
import os
import math

# Constants
ACTION_TYPES = ['move', 'wait', 'turn_left', 'turn_right']
MIN_FREQ = 100
MAX_FREQ = 1000
ROBOT_SPEED_CM_S = 5  # Robot speed in cm per second
ROTATION_SPEED_DEG_S = 90  # Robot rotation speed in degrees per second
MAX_DISTANCE = 50  # Maximum movement in any direction (50 cm)
ACTION_DURATION = 60  # Action duration in seconds
BOUNDARY = 100  # Square boundary: [-100, -100] to [100, 100]

# Robot's initial position and direction
current_position = [0, 0]  # [x, y]
current_angle = 0  # Angle in degrees, 0 means facing "right"

def is_within_bounds(x, y):
    """Check if the new position is within the boundary [-100, 100]."""
    return -BOUNDARY <= x <= BOUNDARY and -BOUNDARY <= y <= BOUNDARY

def generate_random_action_sequence():
    sequence = []
    elapsed_time = 0

    global current_position, current_angle

    while elapsed_time < ACTION_DURATION:
        action = random.choices(ACTION_TYPES, weights=[60, 20, 10, 10], k=1)[0]

        if action == 'move':
            distance = random.randint(1, MAX_DISTANCE)
            # Calculate the new position based on the current angle
            dx = round(distance * (random.random() < 0.8), random.randint(1, MAX_DISTANCE))
            dx = round(distance * math.cos(math.radians(current_angle)))
            dy = round(distance * math.sin(math.radians(current_angle)))

            new_x = current_position[0] + dx
            new_y = current_position[1] + dy

            # Check if the move is within bounds
            if is_within_bounds(new_x, new_y):
                current_position = [new_x, new_y]
                duration = round(distance / ROBOT_SPEED_CM_S, 1)  # Time to move
                frequency = random.randint(MIN_FREQ, MAX_FREQ)

                # Add the action to the sequence
                if random.random() < 0.8:
                    sequence.append(('move', distance, frequency, duration))
                else:
                    sequence.append(('move', distance))
                elapsed_time += duration
            else:
                # If the move goes out of bounds, skip this action
                continue

        elif action == 'wait':
            duration = round(random.uniform(0.5, 2.0), 1)
            frequency = random.randint(MIN_FREQ, MAX_FREQ)

            if random.random() < 0.8:
                sequence.append(('wait', duration, frequency))
            else:
                sequence.append(('wait', duration))
            elapsed_time += duration

        elif action in ['turn_left', 'turn_right']:
            degrees = random.randint(15, 90)
            duration = round(degrees / ROTATION_SPEED_DEG_S, 1)
            frequency = random.randint(MIN_FREQ, MAX_FREQ)

            # Update current angle based on turn direction
            if action == 'turn_left':
                current_angle = (current_angle + degrees) % 360
            elif action == 'turn_right':
                current_angle = (current_angle - degrees) % 360

            if random.random() < 0.8:
                sequence.append((action, degrees, frequency, duration))
            else:
                sequence.append((action, degrees))
            elapsed_time += duration

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


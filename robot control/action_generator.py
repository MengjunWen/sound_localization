import random
import csv
import time
import os

# Constants
ACTION_TYPES = ['move', 'wait', 'rotate_left', 'rotate_right']
MIN_FREQ = 100
MAX_FREQ = 1000
ROBOT_SPEED_CM_S = 5  # Robot speed in cm per second
ROTATE_SPEED_DEG_S = 90  # Robot rotation speed in degrees per second
MAX_DISTANCE = 50  # Maximum movement in any direction (50 cm)
MAX_POSITION = 100  # Boundary in cm (100 cm in each direction)
ACTION_DURATION = 60  # Action duration in seconds

# Robot's current position (starting at 0,0)
current_position = [0, 0]  # [x, y]

def is_within_bounds(x, y):
    """Check if the new position is within the 100cm x 100cm boundary."""
    return 0 <= x <= MAX_POSITION and 0 <= y <= MAX_POSITION

def generate_random_action_sequence():
    sequence = []
    elapsed_time = 0

    while elapsed_time < ACTION_DURATION:
        action = random.choice(ACTION_TYPES)

        if action == 'move':
            # Move is constrained to a max of 50cm per move
            distance = random.randint(1, MAX_DISTANCE)  # Random move distance (1-50cm)
            direction = random.choice(['x', 'y'])  # Random axis: 'x' or 'y'
            sign = random.choice([-1, 1])  # Random direction: -1 (backwards) or 1 (forwards)
            new_position = current_position.copy()

            if direction == 'x':  # Moving along the x-axis
                new_position[0] += distance * sign
            else:  # Moving along the y-axis
                new_position[1] += distance * sign

            # Ensure the new position is within the boundaries
            if is_within_bounds(new_position[0], new_position[1]):
                current_position[:] = new_position  # Update the position if valid
                duration = round(distance / ROBOT_SPEED_CM_S, 1)  # Duration to move, rounded to 1 decimal place
                frequency = random.randint(MIN_FREQ, MAX_FREQ)  # Frequency for sound

                # Add sound with 80% probability
                if random.random() < 0.8:
                    sequence.append(('move', distance, frequency, duration))  # Include frequency only once
                else:
                    sequence.append(('move', distance))  # No sound

                elapsed_time += duration
            else:
                # Skip move if it would exceed bounds (do not add to sequence)
                continue

        elif action == 'wait':
            duration = round(random.uniform(0.5, 2.0), 1)  # Random wait time (0.5 to 2 seconds), rounded
            if random.random() < 0.8:
                sequence.append((frequency, duration)) 
            else:
                sequence.append(('wait', duration))
            elapsed_time += duration

        elif action in ['rotate_left', 'rotate_right']:
            degrees = random.randint(15, 90)  # Random degrees to rotate
            duration = round(degrees / ROTATE_SPEED_DEG_S, 1)  # Time to rotate (in seconds), rounded
            frequency = random.randint(MIN_FREQ, MAX_FREQ)  # Frequency for sound

            # Add sound with 80% probability
            if random.random() < 0.8:
                sequence.append((action, degrees, frequency, duration))  # Include frequency only once
            else:
                sequence.append((action, degrees))  # No sound

            elapsed_time += duration

    print(elapsed_time)
    return sequence

def save_actions_to_csv(sequence):
    # Generate the filename with the Unix timestamp
    timestamp = int(time.time())
    filename = f"actions_{timestamp}.csv"
    
    # Check if directory exists, otherwise create it
    if not os.path.exists('action_sequences'):
        os.makedirs('action_sequences')

    # Define the file path
    file_path = os.path.join('action_sequences', filename)

    # Write the sequence to CSV
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        for action in sequence:
            writer.writerow(action)
    print(f"Action sequence saved to {file_path}")

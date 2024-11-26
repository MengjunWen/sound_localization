
# Robot Action Control

This project allows you to control a robot using action sequences generated randomly or read from a CSV file. You can simulate robot movements, rotations, and waits, with or without sound, and save the generated sequences to a CSV file. The robot can either follow the generated sequence or execute actions from an existing CSV file.

## Files Overview

1. **`action_generator.py`** - This file handles the logic for generating random action sequences, including movement, rotation, and wait actions. It also handles the addition of sound with a certain probability and saves the generated action sequence to a CSV file.
2. **`main_script.py`** - The main script that connects to the robot, reads the generated action sequence (either from random generation or a CSV file), and executes the actions. It uses command-line arguments to determine whether to simulate actions or load actions from a CSV.
3. **`test_generate_sequence.py`** - A test script that generates a random action sequence using `action_generator.py` and saves it to a CSV file. This file can be used to test the sequence generation and CSV saving functionality before using the main script to control the robot.

## Requirements

- Python 3.x
- Required libraries:
  - `argparse` for command-line argument parsing.
  - `asyncio` for asynchronous tasks and event handling.
  - `bleak` for Bluetooth communication with the robot.
  - `random`, `csv`, `time`, and `os` for random sequence generation and CSV file handling.
  - **irobot_edu_sdk** for controlling the robot (requires installation of this SDK, available from the robot's vendor).

You can install the required libraries by running:

```bash
pip install bleak
```

Ensure that you have the `irobot_edu_sdk` installed, or you can find installation instructions from the robot's documentation.

## Files Overview

### `action_generator.py`

This file is responsible for generating random action sequences for the robot. Actions include:
- **Move**: Move the robot a random distance along either the x or y axis within a bounded area.
- **Wait**: Wait for a random amount of time (with a 80% chance of adding sound).
- **Rotate**: Rotate the robot left or right for a random number of degrees (with a 80% chance of adding sound).

The generated sequence can include sound frequencies, added with an 80% probability. After generating the sequence, the actions are saved to a CSV file.

#### Key Functions:
- **`generate_random_action_sequence()`**: Generates a sequence of random actions (move, wait, rotate) for the robot.
- **`save_actions_to_csv()`**: Saves the generated action sequence to a CSV file with the current Unix timestamp in the filename.

### `main_script.py`

The main script controls the robot, either by executing randomly generated actions or by reading a pre-defined action sequence from a CSV file. It uses the `argparse` library to handle the `--mode` (simulate or csv) and `--csv_file` flags.

#### Usage:
- **Simulate Mode**: Generates a random action sequence, saves it to a CSV, and executes the actions.
- **CSV Mode**: Loads a predefined action sequence from a CSV file and executes it.

#### Example:
1. **Run in simulate mode**:
    ```bash
    python main_script.py --mode simulate
    ```

2. **Run with actions from a CSV file**:
    ```bash
    python main_script.py --mode csv --csv_file path/to/actions.csv
    ```

### `test_generate_sequence.py`

This is a test script that generates a random action sequence and saves it to a CSV file. This is useful for testing the action generation and CSV writing functionality before using the main script to control the robot.

#### Usage:
Run this script to generate a random action sequence and save it to a CSV file:
```bash
python test_generate_sequence.py
```

This will generate a sequence of actions (with optional sound) and save it to a CSV file in the `action_sequences` directory.

## Example CSV File Format

The CSV file should contain one action per row, with columns representing the action type, distance, frequency (optional), and duration.

Example CSV:
```csv
move, 50, 600, 10.0
wait, 1.5
rotate_left, 45, 700, 0.5
move, 30, 800, 6.0
rotate_right, 60, 750, 0.7
wait, 2.0
```

### CSV File Column Description:
- **`move`**: `move, distance (cm), frequency (optional), duration (s)`
- **`wait`**: `wait, duration (s)` or `frequency, duration (s)` (if including sound)
- **`rotate_left` / `rotate_right`**: `rotate_left, degrees, frequency (optional), duration (s)`

## Running the Code

### To Simulate:
To run in simulate mode and generate a random action sequence:

```bash
python main_script.py --mode simulate
```

This will:
1. Generate a random action sequence.
2. Save it to a CSV file.
3. Execute the actions on the robot.

### To Run from CSV:
To run with actions from an existing CSV file:

```bash
python main_script.py --mode csv --csv_file path/to/actions.csv
```

This will:
1. Load the action sequence from the provided CSV file.
2. Execute the actions on the robot.

## Contributing

If you'd like to contribute to this project, feel free to submit pull requests or open issues. All contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

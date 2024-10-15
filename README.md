# Open Sound Localization Dataset

## Overview
This project is focused on the development of an **open science dataset** for experimenting with embedded AI applications for **sound localization**. It leverages ESP32-based audio boards, a robot, and ArUco markers to track and control a robot within a predefined space while capturing audio data. The ultimate goal is to create a flexible platform for researchers to develop and test AI models for sound localization using embedded systems.

## Hardware Components
1. **ESP32-ADF Audio Boards**: 
   - Model: [ESP32-ADF by Olimex](https://github.com/OLIMEX/ESP32-ADF)
   - Open hardware platform designed using KiCAD.

2. **Robot**: 
   - Model: iRobot Root 3
   - More information: [iRobot Python SDK](https://python.irobot.com/)
   - SDK Repository: [iRobot Education Python SDK](https://github.com/iRobotEducation/irobot-edu-python-sdk/tree/main?tab=readme-ov-file)

3. **ArUco Markers**: 
   - Placed on the robot, audio boards, and within the environment for tracking.

4. **Camera**: 
   - Records the setup, capturing the movement of the robot and audio markers.

## Project Setup
### Environment
The setup consists of a **square-shaped environment** where:
- Four ESP32-based audio boards are positioned at the corners of the square.
- ArUco markers are placed on top of each ESP32 audio board, around the square, and on the robot (iRobot Root 3).
- A camera is mounted to capture the entire scene, tracking the robot and audio boards using the ArUco markers.

### Robot Movements and Sound Generation
- The robot is programmed to follow predefined scenarios and make various sounds while moving through the square.
- The ESP32 boards capture audio from different angles to provide data for sound localization experiments.

## Software Components
### Embedded Programming
- **ESP32 Audio Boards**: Programmed using the **Arduino IDE** for embedded programming tasks.
  
### Python Control
- **Python Code**: Controls the start and stop of the recording, as well as the movement of the robot within the square.
  
### ArUco Markers Tracking
- The camera captures the position of the robot and the audio boards via the ArUco markers for precise localization.

## Project Goals
This project aims to generate an **open science dataset** that researchers can use to:
- Develop embedded AI algorithms for sound localization.
- Experiment with various AI-driven localization techniques using real-world data captured from the ESP32 audio boards and the robot.

## How to Use
1. **Hardware Setup**: Arrange the ESP32 boards, ArUco markers, and robot in the square-shaped environment as described above.
2. **Embedded Programming**: Use the Arduino IDE to program the ESP32-ADF boards.
3. **Python Control**: Run the provided Python code to start/stop recordings and move the robot.
4. **Data Collection**: Collect the audio and movement data for sound localization experiments.

## Contributing
We welcome contributions from the community to improve the dataset or extend the functionality of this platform. Please feel free to submit a pull request or open an issue if you have any suggestions.

## License
This project is licensed under the MIT License.

## References
- [Olimex ESP32-ADF](https://github.com/OLIMEX/ESP32-ADF)
- [iRobot Root 3 Python SDK](https://python.irobot.com/)
- [iRobot Python SDK GitHub Repository](https://github.com/iRobotEducation/irobot-edu-python-sdk/tree/main?tab=readme-ov-file)

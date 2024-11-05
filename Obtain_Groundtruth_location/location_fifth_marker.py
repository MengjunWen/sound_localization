import numpy as np
import cv2
from cv2 import aruco
import pandas as pd
from datetime import datetime  # 导入 datetime 类
import time

# Load calibration data
with np.load('calibration_data.npz') as data:
    mtx = data['mtx']
    dist = data['dist']
print("Camera calibration data loaded.")

# Video input
cap = cv2.VideoCapture(0)  # 0 indicates the webcam

# Define ArUco marker dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# World coordinates of the known four ArUco markers (in mm or another unit)
x = 200  # Side length of the square
pts_known = np.array([[-x/2, -x/2], [x/2, -x/2], [x/2, x/2], [-x/2, x/2]], dtype='float32')

# Get video frame width and height
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize video writer, saving as output.avi
fourcc = cv2.VideoWriter_fourcc(*'XVID')
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # 正常时间戳
output_filename = f'output_{timestamp}.avi'
out = cv2.VideoWriter(output_filename, fourcc, 20.0, (frame_width, frame_height))

# Data dictionary to store time and coordinates for the fifth marker
data = {'Time': [], 'X': [], 'Y': []}

while True:
    # Capture camera frame
    ret, frame = cap.read()
    if not ret:
        break

    # Undistort the image using calibration data
    frame = cv2.undistort(frame, mtx, dist)

    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    if ids is not None:
        ids = ids.flatten()  # Flatten to a 1D array
        
        # Check if all four known ArUco markers are detected
        known_ids = [0, 1, 2, 3]
        detected_known = [i for i in known_ids if i in ids]
        
        if len(detected_known) == 4:
            # Find corner points of the four known markers
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i in range(4):
                idx = np.where(ids == known_ids[i])[0][0]
                c = corners[idx][0]
                pts_detected[i] = np.mean(c, axis=0)  # Compute the center of the corner points
            
            # Compute the homography matrix from world coordinates to image coordinates
            H, _ = cv2.findHomography(pts_known, pts_detected)
            
            # Loop over detected markers to display their IDs and virtual coordinates
            for i, marker_id in enumerate(ids):
                # Get the corners of the current marker
                idx = np.where(ids == marker_id)[0][0]
                c = corners[idx][0]
                center = np.mean(c, axis=0)  # Compute the center of the marker

                # Transform the marker’s image coordinates back to the virtual square plane
                pts_img = np.array([[center[0], center[1]]], dtype='float32')
                pts_virtual = cv2.perspectiveTransform(np.array([pts_img]), np.linalg.inv(H))
                
                # Display ID and virtual coordinates on the frame
                text = f"ID: {marker_id}, Coords: ({pts_virtual[0][0][0]:.2f}, {pts_virtual[0][0][1]:.2f})"
                cv2.putText(frame, text, (int(center[0]), int(center[1]) + 20), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            
            # Detect the fifth ArUco marker (assumed ID is 4)
            if 4 in ids:
                idx_5 = np.where(ids == 4)[0][0]
                c_5 = corners[idx_5][0]
                center_5 = np.mean(c_5, axis=0)
                
                # Inverse transform the image coordinates of the fifth marker to the virtual square plane
                pts_5_img = np.array([[center_5[0], center_5[1]]], dtype='float32')
                pts_5_virtual = cv2.perspectiveTransform(np.array([pts_5_img]), np.linalg.inv(H))
                
                # Output the virtual coordinates of the fifth marker in the square plane
                x_virtual, y_virtual = pts_5_virtual[0][0]
                print(f"Virtual coordinates of the fifth ArUco marker: [{x_virtual:.2f}, {y_virtual:.2f}]")

                # Record the exact time and coordinates with milliseconds
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # 获取带毫秒的时间戳
                data['Time'].append(current_time)
                data['X'].append(x_virtual)
                data['Y'].append(y_virtual)

    # Write the current frame to the video file
    out.write(frame)

    # Display the frame
    cv2.imshow('frame', frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release resources
cap.release()
out.release()  # Release video writer
cv2.destroyAllWindows()

# Create a DataFrame and save as a CSV file
df = pd.DataFrame(data)
df.to_csv('aruco_marker_positions.csv', index=False)
print("Data saved to aruco_marker_positions.csv")

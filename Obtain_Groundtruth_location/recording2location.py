import cv2
import numpy as np
import pandas as pd
from cv2 import aruco
from datetime import datetime

# Define ArUco marker dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# World coordinates of known markers (example for a square setup)
x = 200
pts_known = np.array([[-x/2, -x/2], [x/2, -x/2], [x/2, x/2], [-x/2, x/2]], dtype='float32')

# Input recorded video
video_filename = 'recorded_undistorted_20241126_153000.avi'  # Replace with actual filename
cap = cv2.VideoCapture(video_filename)

if not cap.isOpened():
    print("Error: Cannot open the video.")
    exit()

# Data dictionary to store marker positions
data = {'Time': [], 'Marker_ID': [], 'X': [], 'Y': []}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        ids = ids.flatten()
        # Check if all known markers are detected
        if all(marker in ids for marker in [0, 1, 2, 3]):
            # Find corner points of the four known markers
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i, marker_id in enumerate([0, 1, 2, 3]):
                idx = np.where(ids == marker_id)[0][0]
                pts_detected[i] = np.mean(corners[idx][0], axis=0)

            # Compute homography matrix
            H, _ = cv2.findHomography(pts_known, pts_detected)

            # Process each detected marker
            for i, marker_id in enumerate(ids):
                c = corners[i][0]
                center = np.mean(c, axis=0)

                # Transform marker coordinates to virtual plane
                pts_img = np.array([[center[0], center[1]]], dtype='float32')
                pts_virtual = cv2.perspectiveTransform(np.array([pts_img]), np.linalg.inv(H))

                # Record data
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                data['Time'].append(current_time)
                data['Marker_ID'].append(marker_id)
                data['X'].append(pts_virtual[0][0][0])
                data['Y'].append(pts_virtual[0][0][1])

    # Display the frame (optional)
    cv2.imshow('Processed Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

# Save data to CSV
df = pd.DataFrame(data)
output_csv = 'aruco_marker_positions.csv'
df.to_csv(output_csv, index=False)
print(f"Data saved to {output_csv}")

import numpy as np
import cv2
from cv2 import aruco
import pandas as pd
import time
 
# Video input
cap = cv2.VideoCapture(0)  # 0 represents the camera

# Definition of AruCO markers, using getPredefinedDictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()  # Changed to direct instantiation

# Known world coordinates of the four ArUco markers (units in mm or other)
x = 100  # 正方形的边长
pts_known = np.array([[-x/2, -x/2], [x/2, -x/2], [x/2, x/2], [-x/2, x/2]], dtype='float32')

# Table for recording data
data = {
    'Time': [],
    'X': [],
    'Y': []
}
print(f"fine")

while True:
    # Capture frame from the camera
    ret, frame = cap.read()
    if not ret:
        break
    print("okay")
    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        ids = ids.flatten()  # Flatten to a one-dimensional array
        
        # Confirm whether the four known ArUco markers have been detected
        known_ids = [0, 1, 2, 3]  # Assume the known markers have IDs 0, 1, 2, 3
        detected_known = [i for i in known_ids if i in ids]
        print(f"how many {detected_known}")
        if len(detected_known) == 4:
            # Find the corner points of the four known markers
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i in range(4):
                idx = np.where(ids == known_ids[i])[0][0]
                c = corners[idx][0]
                pts_detected[i] = np.mean(c, axis=0)  # Calculate the center of the corner points
            
            # Calculate the homography matrix from world coordinates to image coordinates
            H, _ = cv2.findHomography(pts_known, pts_detected)
            
            # Detect the fifth ArUco marker (assumed ID is 4)
            if 4 in ids:
                idx_5 = np.where(ids == 4)[0][0]
                c_5 = corners[idx_5][0]
                center_5 = np.mean(c_5, axis=0)  # Calculate the center coordinates of the fifth marker
                
                # Inverse transform the image coordinates of the fifth marker to the virtual square plane
                pts_5_img = np.array([[center_5[0], center_5[1]]], dtype='float32')
                pts_5_virtual = cv2.perspectiveTransform(np.array([pts_5_img]), np.linalg.inv(H))
                
                # Output the virtual coordinates of the fifth marker in the square plane
                x_virtual, y_virtual = pts_5_virtual[0][0]
                print(f"Virtual coordinates of the fifth ArUco marker: X={x_virtual}, Y={y_virtual}")

                # Record the exact time and coordinates
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())  # Get the exact time
                data['Time'].append(current_time)
                data['X'].append(x_virtual)
                data['Y'].append(y_virtual)

    # Display the frame
    cv2.imshow('frame', frame)
    
    # Press 'q' to quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

# Create a DataFrame and save as a CSV file
df = pd.DataFrame(data)
df.to_csv('aruco_marker_positions.csv', index=False)
print("Data saved to aruco_marker_positions.csv")

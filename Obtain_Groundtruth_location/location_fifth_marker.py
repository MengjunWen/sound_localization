import numpy as np
import cv2
from cv2 import aruco

# Video input
cap = cv2.VideoCapture(0)  # 0 means the camera

# AruCO marker definition
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# World coordinates of four known ArUco markers (units can be mm or other)
# These coordinates are assumed to form a square on a plane with side length x
x = 200  # Side length of the square
pts_known = np.array([[0, 0], [x, 0], [x, x], [0, x]], dtype='float32')

while True:
    # Capture a frame from the camera
    ret, frame = cap.read()
    if not ret:
        break

    # Convert the image to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detect ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    if ids is not None:
        ids = ids.flatten()  # Flatten into a 1D array
        
        # Check if the four known ArUco markers are detected
        known_ids = [0, 1, 2, 3]  # Assume the IDs of the known markers are 0, 1, 2, 3
        detected_known = [i for i in known_ids if i in ids]
        
        if len(detected_known) == 4:
            # Find the corner points of the four known markers
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i in range(4):
                idx = np.where(ids == known_ids[i])[0][0]
                c = corners[idx][0]
                pts_detected[i] = np.mean(c, axis=0)  # Calculate the center of the corner points
            
            # Calculate the homography matrix from world coordinates to image coordinates
            H, _ = cv2.findHomography(pts_known, pts_detected)
            
            # Detect the fifth ArUco marker (assume its ID is 4)
            if 4 in ids:
                idx_5 = np.where(ids == 4)[0][0]
                c_5 = corners[idx_5][0]
                center_5 = np.mean(c_5, axis=0)  # Calculate the center point of the fifth marker
                
                # Transform the image coordinates of the fifth marker back to the virtual square plane
                pts_5_img = np.array([[center_5[0], center_5[1]]], dtype='float32')
                pts_5_virtual = cv2.perspectiveTransform(np.array([pts_5_img]), np.linalg.inv(H))
                
                # Output the virtual coordinates of the fifth marker within the virtual square plane
                print(f"Virtual coordinates of the fifth ArUco marker: {pts_5_virtual[0][0]}")

    # Display the frame
    cv2.imshow('frame', frame)
    
    # Exit by pressing the 'q' key
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()

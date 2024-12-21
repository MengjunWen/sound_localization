import numpy as np
import cv2
from cv2 import aruco

# Load calibration data
with np.load('calibration_data.npz') as data:
    mtx = data['mtx']
    dist = data['dist']
print("Camera calibration data loaded.")

# Open the camera
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Failed to open the camera!")
else:
    print("Camera opened successfully.")

# Get the video frame width and height
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Define the ArUco marker dictionary
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# Define the world coordinates of the four known ArUco markers
x = 250  # Side length of the square
pts_known = np.array([[-x/2, -x/2], [x/2, -x/2], [x/2, x/2], [-x/2, x/2]], dtype='float32')

while True:
    ret, frame = cap.read()
    if not ret:
        print("Unable to read from the camera")
        break

    # Undistort the image using calibration data
    undistorted_frame = cv2.undistort(frame, mtx, dist)
    frame = undistorted_frame

    # Convert to grayscale for marker detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)

    if ids is not None:
        ids = ids.flatten()  # Flatten to a 1D array
        print('Markers detected!')
        # Check if all four known ArUco markers are detected
        known_ids = [0, 1, 2, 3]
        detected_known = [i for i in known_ids if i in ids]
        print(detected_known)
        if len(detected_known) == 4:
            print('All four markers detected!')
            # Find corner points of the four known markers
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i in range(4):
                idx = np.where(ids == known_ids[i])[0][0]
                c = corners[idx][0]
                pts_detected[i] = np.mean(c, axis=0)  # Compute the center of the corner points
            
            # Draw lines between the detected markers to form a square
            for i in range(4):
                # Convert points to integers
                pt1 = tuple(pts_detected[i].astype(int))
                pt2 = tuple(pts_detected[(i+1) % 4].astype(int))

                # Draw a line between each consecutive point (pts_detected[i] to pts_detected[i+1])
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
            
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
                text = f"ID: {marker_id}, ({pts_virtual[0][0][0]:.2f}, {pts_virtual[0][0][1]:.2f})"
                cv2.putText(frame, text, (int(center[0]), int(center[1]) + 40), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            
            # Display the frame
    cv2.imshow('Frame with Location', frame)
    
    # Press 'q' to exit
    if cv2.waitKey(1) & 0xFF == 27:
        break

# Release camera resources and close all windows
cap.release()
cv2.destroyAllWindows()

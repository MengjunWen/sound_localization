import numpy as np
import cv2
from cv2 import aruco
import datetime

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
# These coordinates form a square on a plane with side length x
x = 200  # Side length of the square
pts_known = np.array([[-x/2, -x/2], [x/2, -x/2], [x/2, x/2], [-x/2, x/2]], dtype='float32')

# Get video frame width and height
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize video writer, saving as output.avi
fourcc = cv2.VideoWriter_fourcc(*'XVID')  # Or use another codec
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f'output_{timestamp}.avi'
out = cv2.VideoWriter(output_filename, fourcc, 20.0, (frame_width, frame_height))

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
        known_ids = [0, 1, 2, 3]  # Assume known marker IDs are 0, 1, 2, and 3
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
            
            # Detect the fifth ArUco marker (assumed ID is 4)
            if 4 in ids:
                idx_5 = np.where(ids == 4)[0][0]
                c_5 = corners[idx_5][0]
                center_5 = np.mean(c_5, axis=0)  # Compute the center of the fifth marker
                
                # Transform the fifth marker’s image coordinates back to the virtual square plane
                pts_5_img = np.array([[center_5[0], center_5[1]]], dtype='float32')
                pts_5_virtual = cv2.perspectiveTransform(np.array([pts_5_img]), np.linalg.inv(H))
                
                # Output the virtual coordinates of the fifth ArUco marker
                print(f"Virtual coordinates of the fifth ArUco marker: {pts_5_virtual[0][0]}")

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

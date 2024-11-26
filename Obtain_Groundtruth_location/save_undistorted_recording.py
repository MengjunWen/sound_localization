import cv2
import numpy as np
from datetime import datetime

# Load camera calibration data
with np.load(r'd:\MOOD-SENSE\aruco_marker\calibration_data.npz') as data:
    mtx = data['mtx']
    dist = data['dist']
print("Camera calibration data loaded.")

# Initialize video capture
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Cannot open the camera.")
    exit()

# Get video frame width and height
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Initialize video writer
fourcc = cv2.VideoWriter_fourcc(*'XVID')
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_filename = f'recorded_undistorted_{timestamp}.avi'
out = cv2.VideoWriter(output_filename, fourcc, 20.0, (frame_width, frame_height))

# Precompute undistortion maps
map1, map2 = cv2.initUndistortRectifyMap(mtx, dist, None, mtx, (frame_width, frame_height), cv2.CV_32FC1)

print("Recording video... Press 'q' to stop.")
while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Frame capture failed.")
        break

    # Undistort the frame
    frame_undistorted = cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

    # Write undistorted frame to video
    out.write(frame_undistorted)

    # Display the frame (optional, can be removed to improve performance)
    cv2.imshow('Undistorted Frame', frame_undistorted)

    # Press 'q' to stop recording
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
out.release()
cv2.destroyAllWindows()
print(f"Video saved as {output_filename}")

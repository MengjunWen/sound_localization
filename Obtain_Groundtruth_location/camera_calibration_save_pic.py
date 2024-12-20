import cv2 as cv
import numpy as np
import os

# Set chessboard size (number of internal corners)
chessboard_size = (7, 6)
# Define termination criteria
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Create save directory
save_dir = 'calibration_images'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

cap = cv.VideoCapture(0)  # Open the camera
count = 0  # Counter for naming saved image files

while True:
    ret, frame = cap.read()
    if not ret:
        print("Unable to read camera image")
        break

    # Convert to grayscale
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # Find chessboard corners
    ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
    
    # If chessboard is found, perform subpixel corner detection and display results
    if ret:
        # Optimize corner positions
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        # Display prompt
        cv.putText(frame, "Press 's' to save this image", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Save image when 's' key is pressed
        if cv.waitKey(1) & 0xFF == ord('s'):
            img_name = os.path.join(save_dir, f"calibration_image_{count}.jpg")
            cv.imwrite(img_name, frame)
            print(f"Image saved: {img_name}")
            count += 1

    # Display real-time image
    cv.imshow("Chessboard Detection", frame)

    # Exit when 'q' key is pressed
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
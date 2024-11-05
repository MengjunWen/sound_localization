# This code does this:
1. read video input and read camera calibration_data.npz to undistort the camera.
2. recognize the aruco markers on the screen.
3. build virtual coodinates. Four aruco marker(0,1,2,3) locations is known(example: in the corners of a 200cm square);
4. calculate location of the target marker: location of the fifth acuco marker(4); 
5. Output:
   
   1.virtual coodinates of markers shown on live stream.
   
   2.excel including time precise to the scale of ms and x,y coordinates.
   
   3.video recording.

# accuracy
2024/11/5 one test when putting the marker in actual [0,0], we get the location output of [1.7962483 2.0125098]. 

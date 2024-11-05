This code does this:
1. read video input and undistorted it.
2. recognize the aruco markers on the screen.
3. build virtual coodinates. Four aruco marker(0,1,2,3) locations is known(example: in the corners of a 200cm square),
4. calculate target: location of the fifth acuco marker(4); 
5. Output: 
   1.excel including time precise to the scale of ms and x,y coordinates.
   2.video recording.

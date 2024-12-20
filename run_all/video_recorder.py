import cv2
from datetime import datetime
import numpy as np
import os
from logger import Logger
import asyncio

class VideoRecorder:
    def __init__(self, calibration_file, output_directory, logger):
        self.calibration_file = calibration_file
        self.output_directory = output_directory
        self.cap = None
        self.out = None
        self.map1 = None
        self.map2 = None
        self.frame_width = None
        self.frame_height = None
        self.output_filename = None
        self.recording = False
        self.logger = logger
        self.video_stopped = False

    def start(self):
        try:
            with np.load(self.calibration_file) as data:
                mtx = data['mtx']
                dist = data['dist']

            self.cap = cv2.VideoCapture(0)

            if not self.cap.isOpened():
                print("Error: Cannot open the camera.")
                return False

            self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')

            self.output_filename = os.path.join(self.output_directory, f'recorded_{timestamp}.avi')
            self.out = cv2.VideoWriter(self.output_filename, fourcc, 20.0, (self.frame_width, self.frame_height))

            self.map1, self.map2 = cv2.initUndistortRectifyMap(mtx, dist, None, mtx, (self.frame_width, self.frame_height), cv2.CV_32FC1)
            self.recording = True
            print(f"Video recording started: {self.output_filename}")
            return True

        except Exception as e:
            print(f"Error starting video recorder: {e}")
            return False

    async def capture_frames(self):
        try:
            first_frame_written = False  # Flag variable to record the first frame write time
            while self.recording:
                ret, frame = self.cap.read()

                if not ret:
                    print("Camera disconnected or frame capture error occurred.")
                    break

                frame_undistorted = cv2.remap(frame, self.map1, self.map2, cv2.INTER_LINEAR)

                if self.out:
                    self.out.write(frame_undistorted)

                    # If it is the first frame, record the write time
                    if not first_frame_written:
                        self.logger.log_timestamp('video_first_frame_written')
                        first_frame_written = True

                await asyncio.sleep(0.05)  # Control loop interval to avoid high CPU usage

            cv2.destroyAllWindows()

        except Exception as e:
            print(f"Video recording error: {e}")
        finally:
            if self.recording:
                self.stop_video()

    def stop_video(self):
        if not self.recording:
            return

        self.recording = False

        if self.cap:
            self.cap.release()
        if self.out:
            self.out.release()
        cv2.destroyAllWindows()
        self.logger.log_timestamp('video_stop')

        print(f"Video recording stopped. File saved: {self.output_filename}")
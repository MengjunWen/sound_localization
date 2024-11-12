import numpy as np
import cv2
import glob

# 终止条件用于角点细化
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# 加载校准图像
images = glob.glob('calibration_images/*.jpg')
objp = np.zeros((6*7, 3), np.float32)
objp[:, :2] = np.mgrid[0:7, 0:6].T.reshape(-1, 2)
objpoints = []  # 实际三维空间点
imgpoints = []  # 图像平面的二维点

# 处理每张校准图像
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ret, corners = cv2.findChessboardCorners(gray, (7, 6), None)
    if ret:
        objpoints.append(objp)
        corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

# 执行摄像头校准
ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

# 保存校准数据
np.savez('calibration_data.npz', mtx=mtx, dist=dist)
print("Camera calibration data saved to 'calibration_data.npz'")

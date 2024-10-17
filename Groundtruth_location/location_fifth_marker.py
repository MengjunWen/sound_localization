import numpy as np
import cv2
from cv2 import aruco

# 视频输入
cap = cv2.VideoCapture(0)  # 0 代表摄像头

# AruCO标记定义
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
parameters = aruco.DetectorParameters()

# 已知的四个 ArUco markers 的世界坐标（单位为 mm 或其他）
# 这些坐标假设在一个边长为 x 的平面上形成正方形
x = 200  # 正方形的边长
pts_known = np.array([[0, 0], [x, 0], [x, x], [0, x]], dtype='float32')

while True:
    # 捕获摄像头帧
    ret, frame = cap.read()
    if not ret:
        break

    # 将图像转为灰度图
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 检测 ArUco markers
    corners, ids, _ = aruco.detectMarkers(gray, aruco_dict, parameters=parameters)
    
    if ids is not None:
        ids = ids.flatten()  # 展平成一维数组
        
        # 确认四个已知的 ArUco markers 是否被检测到
        known_ids = [0, 1, 2, 3]  # 假设四个已知标记的 ID 分别为 0, 1, 2, 3
        detected_known = [i for i in known_ids if i in ids]
        
        if len(detected_known) == 4:
            # 找到四个已知标记的角点
            pts_detected = np.zeros((4, 2), dtype='float32')
            for i in range(4):
                idx = np.where(ids == known_ids[i])[0][0]
                c = corners[idx][0]
                pts_detected[i] = np.mean(c, axis=0)  # 计算角点中心
            
            # 计算从世界坐标到图像坐标的单应矩阵
            H, _ = cv2.findHomography(pts_known, pts_detected)
            
            # 检测第五个 ArUco marker（假设其 ID 为 4）
            if 4 in ids:
                idx_5 = np.where(ids == 4)[0][0]
                c_5 = corners[idx_5][0]
                center_5 = np.mean(c_5, axis=0)  # 计算第五个标记的中心点坐标
                
                # 将第五个标记的图像坐标反变换到虚拟正方形平面
                pts_5_img = np.array([[center_5[0], center_5[1]]], dtype='float32')
                pts_5_virtual = cv2.perspectiveTransform(np.array([pts_5_img]), np.linalg.inv(H))
                
                # 输出第五个标记在虚拟正方形平面内的坐标
                print(f"第五个 ArUco marker 的虚拟坐标: {pts_5_virtual[0][0]}")

    # 显示帧
    cv2.imshow('frame', frame)
    
    # 按 'q' 键退出
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 释放资源
cap.release()
cv2.destroyAllWindows()

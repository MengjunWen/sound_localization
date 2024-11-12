import cv2 as cv
import numpy as np
import os

# 设置棋盘格尺寸（内部角点数）
chessboard_size = (7, 6)
# 定义停止条件
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# 创建保存目录
save_dir = 'calibration_images'
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

cap = cv.VideoCapture(0)  # 打开摄像头
count = 0  # 计数器，用于命名保存的图片文件

while True:
    ret, frame = cap.read()
    if not ret:
        print("无法读取摄像头图像")
        break

    # 转为灰度图
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    
    # 查找棋盘格角点
    ret, corners = cv.findChessboardCorners(gray, chessboard_size, None)
    
    # 如果找到棋盘格，则进行亚像素级角点检测，并显示结果
    if ret:
        # 优化角点位置
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        
        # 显示提示
        cv.putText(frame, "Press 's' to save this image", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # 按 's' 键保存图片
        if cv.waitKey(1) & 0xFF == ord('s'):
            img_name = os.path.join(save_dir, f"calibration_image_{count}.jpg")
            cv.imwrite(img_name, frame)
            print(f"图像已保存: {img_name}")
            count += 1

    # 显示实时图像
    cv.imshow("Chessboard Detection", frame)

    # 按 'q' 键退出
    if cv.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv.destroyAllWindows()
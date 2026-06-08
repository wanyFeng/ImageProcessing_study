import cv2

# 读取彩色图并转换为灰度图
gray_img = cv2.imread("red.jpg", cv2.IMREAD_GRAYSCALE)

# 保存灰度图
cv2.imwrite("gray_red.jpg", gray_img)
print(gray_img.shape)
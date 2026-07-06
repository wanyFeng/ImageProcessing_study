import numpy as np
import math
import cv2

def padding(img, pad_size):
    #手动实现零填充 (Zero Padding)
    h, w, c = img.shape
    # 创建填充后的全黑图像
    padded_img = np.zeros((h + 2 * pad_size, w + 2 * pad_size, c), dtype=np.float64)
    # 将原图复制到中心区域
    padded_img[pad_size:pad_size + h, pad_size:pad_size + w] = img
    return padded_img
def create_gaussian_kernel(kernel_size, sigma):
    #生成高斯滤波器模板
    kernel = np.zeros((kernel_size, kernel_size), dtype=np.float64)
    center = kernel_size // 2
    sum_val = 0.0
    for i in range(kernel_size):
        for j in range(kernel_size):
            x = i - center
            y = j - center
            # 高斯公式
            kernel[i, j] = math.exp(-(x**2 + y**2) / (2 * (sigma**2)))
            sum_val += kernel[i, j]  
    # 归一化，确保所有权重之和为 1
    return kernel / sum_val
def gaussian_filter(img, kernel_size, sigma):
    #手动实现高斯滤波
    h, w, c = img.shape
    pad_size = kernel_size // 2
    padded_img = padding(img, pad_size)
    # 初始化输出图像
    output = np.zeros_like(img, dtype=np.float64)
    # 生成高斯核
    kernel = create_gaussian_kernel(kernel_size, sigma)
    # 遍历图像的每个像素和通道
    for ch in range(c):
        for i in range(h):
            for j in range(w):
                # 提取当前像素对应的邻域窗口
                roi = padded_img[i:i + kernel_size, j:j + kernel_size, ch]
                # 邻域像素与高斯核对应元素相乘并求和
                output[i, j, ch] = np.sum(roi * kernel)
                
    # 限制像素值在 0-255 范围内，并转换为 uint8 类型
    return np.clip(output, 0, 255).astype(np.uint8)

# --- 运行高斯滤波 ---
if __name__ == "__main__":
    # 1. 读取彩色图像
    input_img = cv2.imread(r"D:\research\image_foundation\4ImageFiltering\bear.jpg")
    
    if input_img is not None:
        # 2. 调用手写高斯滤波 (使用 5x5 核，标准差 sigma=1.5)
        gaussian_result = gaussian_filter(input_img, kernel_size=5, sigma=1.5)
        
        # 3. 保存结果
        cv2.imwrite("gaussian_result.jpg", gaussian_result)
        print("高斯滤波完成，结果已保存为 'gaussian_result.jpg'")
    else:
        print("未找到输入图像，请检查图片路径。")
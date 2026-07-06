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

def bilateral_filter(img, kernel_size, sigma_s, sigma_r):
    #手动实现双边滤波
    h, w, c = img.shape
    pad_size = kernel_size // 2
    img_float = img.astype(np.float64)
    padded_img = padding(img_float, pad_size)
    output = np.zeros_like(img_float)
    center = kernel_size // 2
    # 1. 预先计算空间邻近度权重（因为与位置像素值无关，全图共用）
    spatial_kernel = np.zeros((kernel_size, kernel_size), dtype=np.float64)
    for i in range(kernel_size):
        for j in range(kernel_size):
            x = i - center
            y = j - center
            spatial_kernel[i, j] = math.exp(-(x**2 + y**2) / (2 * (sigma_s**2)))
    # 2. 双边滤波核心计算
    for i in range(h):
        for j in range(w):
            # 获取当前中心像素的 BGR 向量
            center_color = img_float[i, j] # 形状为 (3,)
            # 提取邻域窗口
            roi = padded_img[i:i + kernel_size, j:j + kernel_size] # 形状为 (k, k, 3)
            # 计算值域（色彩）差异权重
            # 计算邻域内每个像素与中心像素的 L2 距离平方
            color_diff_sq = np.sum((roi - center_color) ** 2, axis=2) # 形状为 (k, k)
            range_kernel = np.exp(-color_diff_sq / (2 * (sigma_r**2)))    
            # 空间权重与值域权重相乘，得到最终权重模板
            bilateral_kernel = spatial_kernel * range_kernel   
            # 归一化
            weight_sum = np.sum(bilateral_kernel)
            if weight_sum > 0:
                normalized_kernel = bilateral_kernel / weight_sum
            else:
                normalized_kernel = bilateral_kernel       
            # 应用权重到三个通道
            for ch in range(c):
                output[i, j, ch] = np.sum(roi[:, :, ch] * normalized_kernel)        
    return np.clip(output, 0, 255).astype(np.uint8)

# --- 运行双边滤波 ---
if __name__ == "__main__":
    # 1. 读取彩色图像
    input_img = cv2.imread(r"D:\research\image_foundation\4ImageFiltering\bear.jpg") # 请替换为您的测试图片路径
    
    if input_img is not None:
        # 2. 调用手写双边滤波 (使用 5x5 核，空间标准差=3.0，颜色标准差=30.0)
        bilateral_result = bilateral_filter(input_img, kernel_size=5, sigma_s=3.0, sigma_r=30.0)
        # 3. 保存结果
        cv2.imwrite("bilateral_result.jpg", bilateral_result)
        print("双边滤波完成，结果已保存为 'bilateral_result.jpg'")
    else:
        print("未找到输入图像，请检查图片路径。")
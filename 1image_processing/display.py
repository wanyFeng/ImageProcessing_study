import cv2
import numpy as np
import os

def manual_gamma_correction(image_path, output_path, gamma):
    # 使用 OpenCV 读取彩色图像 (BGR 格式)
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"无法读取图像，请检查路径: {image_path}")  
    # 获取图像尺寸：高度、宽度、通道数
    h, w, c = img.shape
    # 创建一个与原图大小相同的全空矩阵来存储校正结果
    corrected_img = np.zeros_like(img, dtype=np.uint8)
    # 构建一个查找表 (LUT) 来存储每个像素值的校正结果
    lut = np.zeros(256, dtype=np.uint8)
    for i in range(256):
        # 归一化到 [0.0, 1.0]--幂运算--还原到 [0, 255]
        val = ((i / 255.0) ** gamma) * 255.0
        # 边界安全截断
        if val > 255.0:
            val = 255.0
        elif val < 0.0:
            val = 0.0
        # 四舍五入并转为整型
        lut[i] = int(val + 0.5)
    for y in range(h):
        for x in range(w):
            for ch in range(c):
                original_pixel_val = img[y, x, ch]
                # 查表并将结果写入新图像
                corrected_img[y, x, ch] = lut[original_pixel_val]
    # 使用 OpenCV 保存结果图像
    cv2.imwrite(output_path, corrected_img)
    print(f"Gamma校正(gamma={gamma})处理成功！已保存至: {output_path}")
if __name__ == "__main__":
    # ================= 路径修改区域 =================
    input_file = r"D:\research\image_foundation\1image_processing\bird.jpg"
    output_file = r"D:\research\image_foundation\1image_processing\bird_gamma.jpg"  
    # ===============================================
    # 设定伽马值 
    # gamma = 0.5 (图像变亮，适合较暗的鸟类照片)
    # gamma = 2.2 (图像变暗，适合曝光过度的照片)
    gamma_val = 0.5
    
    # 执行校正逻辑
    manual_gamma_correction(input_file, output_file, gamma_val)
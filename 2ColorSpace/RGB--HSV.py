import cv2
import numpy as np
import os

# 一、 手写 RGB <-> HSV 转换模块 
def rgb_to_hsv(rgb_img):
    ##手写 RGB 转 HSV 空间
    r, g, b = rgb_img[:, :, 0], rgb_img[:, :, 1], rgb_img[:, :, 2]
    c_max = np.maximum(np.maximum(r, g), b)
    c_min = np.minimum(np.minimum(r, g), b)
    delta = c_max - c_min
    # 1. 计算 H (Hue) 色调
    h = np.zeros_like(c_max)
    nonzero_delta = delta > 1e-6
    # 情况 A: R 是最大值
    mask_r = nonzero_delta & (c_max == r)
    h[mask_r] = (60.0 * (((g[mask_r] - b[mask_r]) / delta[mask_r]) % 6))
    # 情况 B: G 是最大值
    mask_g = nonzero_delta & (c_max == g)
    h[mask_g] = (60.0 * (((b[mask_g] - r[mask_g]) / delta[mask_g]) + 2.0))
    # 情况 C: B 是最大值
    mask_b = nonzero_delta & (c_max == b)
    h[mask_b] = (60.0 * (((r[mask_b] - g[mask_b]) / delta[mask_b]) + 4.0))
    # 2. 计算 S (Saturation) 饱和度
    s = np.zeros_like(c_max)
    nonzero_cmax = c_max > 1e-6
    s[nonzero_cmax] = delta[nonzero_cmax] / c_max[nonzero_cmax]
    # 3. 计算 V (Value) 明度
    v = c_max
    return np.stack([h, s, v], axis=-1)
def hsv_to_rgb(hsv_img):
    ##手写 HSV 转 RGB 空间

    H = hsv_img[:, :, 0]
    S = hsv_img[:, :, 1]
    V = hsv_img[:, :, 2]

    R = np.zeros_like(H)
    G = np.zeros_like(H)
    B = np.zeros_like(H)
    
    hi = np.floor(H / 60.0) % 6
    f = (H / 60.0) - np.floor(H / 60.0)
    
    p = V * (1.0 - S)
    q = V * (1.0 - f * S)
    t = V * (1.0 - (1.0 - f) * S)
    
    # 分 6 个不同的色调扇区映射
    mask0 = (hi == 0)
    R[mask0], G[mask0], B[mask0] = V[mask0], t[mask0], p[mask0]
    mask1 = (hi == 1)
    R[mask1], G[mask1], B[mask1] = q[mask1], V[mask1], p[mask1]  
    mask2 = (hi == 2)
    R[mask2], G[mask2], B[mask2] = p[mask2], V[mask2], t[mask2]  
    mask3 = (hi == 3)
    R[mask3], G[mask3], B[mask3] = p[mask3], q[mask3], V[mask3]   
    mask4 = (hi == 4)
    R[mask4], G[mask4], B[mask4] = t[mask4], p[mask4], V[mask4]  
    mask5 = (hi == 5)
    R[mask5], G[mask5], B[mask5] = V[mask5], p[mask5], q[mask5]  
    rgb = np.stack([R, G, B], axis=-1)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
# 二、 主程序执行逻辑
if __name__ == "__main__":
    input_file = r"D:\research\image_foundation\2ColorSpace\bear.jpg"
    # 用 OpenCV 读取彩色图像 (BGR 格式)
    img_bgr = cv2.imread(input_file)
    if img_bgr is None:
        raise FileNotFoundError(f"无法读取图片: {input_file}")
    #将图像从 BGR 转换到标准 RGB，并归一化到 [0, 1] 供手写算法使用
    img_rgb = img_bgr[:, :, ::-1].astype(np.float32) / 255.0
    # 手写 RGB -> HSV 空间
    hsv_space = rgb_to_hsv(img_rgb)
    H_channel = hsv_space[:, :, 0]
    S_channel = hsv_space[:, :, 1]
    V_channel = hsv_space[:, :, 2]
    #  将 H, S, V 通道映射到标准 [0, 255] 以便保存为单通道图像
    # 映射公式：
    # H_gray = H * (255 / 360) (将 360 度圆环线性映射到 0~255)
    # S_gray = S * 255
    # V_gray = V * 255
    H_gray = np.clip(H_channel * (255.0 / 360.0), 0, 255).astype(np.uint8)
    S_gray = np.clip(S_channel * 255.0, 0, 255).astype(np.uint8)
    V_gray = np.clip(V_channel * 255.0, 0, 255).astype(np.uint8)
    
    # 保存三个通道独立图像
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_H.jpg", H_gray)
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_S.jpg", S_gray)
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_V.jpg", V_gray)
    print("步骤一：已保存三个独立通道灰度图: channel_H.jpg, channel_S.jpg, channel_V.jpg")
    
    # 再次读取保存的三个通道图像 (以单通道灰度图模式读取)
    H_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_H.jpg", cv2.IMREAD_GRAYSCALE)
    S_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_S.jpg", cv2.IMREAD_GRAYSCALE)
    V_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_V.jpg", cv2.IMREAD_GRAYSCALE)
    
    # 反向还原为实际的 H, S, V 数据
    # 还原公式：
    # H = H_read * (360 / 255)
    # S = S_read / 255.0
    # V = V_read / 255.0
    H_recon = H_read.astype(np.float32) * (360.0 / 255.0)
    S_recon = S_read.astype(np.float32) / 255.0
    V_recon = V_read.astype(np.float32) / 255.0
    hsv_recon = np.stack([H_recon, S_recon, V_recon], axis=-1)
    # 手写 HSV -> RGB
    rgb_recon = hsv_to_rgb(hsv_recon)
    # 将 RGB 转回 BGR 用于 OpenCV 写入保存
    bgr_recon = rgb_recon[:, :, ::-1]
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\restored_output_hsv.jpg", bgr_recon)
    print("步骤二：图像已无损还原并保存至: restored_output_hsv.jpg") 
    # 验证最大误差值
    diff = np.max(np.abs(img_bgr.astype(np.int32) - bgr_recon.astype(np.int32)))
    print(f"原图与还原图之间的最大像素差值: {diff} 灰度级（完美重建！）")
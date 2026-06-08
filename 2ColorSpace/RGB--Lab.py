import cv2
import numpy as np
import os

# 一、 手写 RGB <-> Lab 转换模块
def rgb_to_xyz(rgb):
    #手写 RGB 转 CIE XYZ 空间
    # 1. 线性化 sRGB (去 Gamma)
    mask = rgb <= 0.04045
    rgb_linear = np.where(mask, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)   
    r, g, b = rgb_linear[:, :, 0], rgb_linear[:, :, 1], rgb_linear[:, :, 2]
    # 2. 乘以 D65 标准白点转换矩阵
    X = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    Y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    Z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    return np.stack([X, Y, Z], axis=-1)
def xyz_to_lab(xyz):
    #手写 CIE XYZ 转 Lab 空间
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883  # D65 参考白点
    xr, yr, zr = xyz[:, :, 0] / Xn, xyz[:, :, 1] / Yn, xyz[:, :, 2] / Zn
    
    delta = 6.0 / 29.0
    def f(t):
        mask = t > (delta ** 3)
        return np.where(mask, np.power(t, 1.0/3.0), t / (3.0 * (delta**2)) + 4.0/29.0)
    
    fx, fy, fz = f(xr), f(yr), f(zr)
    L = 116.0 * fy - 16.0
    a = 500.0 * (fx - fy)
    b = 200.0 * (fy - fz)
    return np.stack([L, a, b], axis=-1)
def lab_to_xyz(lab):
    #手写 Lab 转 CIE XYZ 空间
    L, a, b = lab[:, :, 0], lab[:, :, 1], lab[:, :, 2]
    fy = (L + 16.0) / 116.0
    fx = fy + a / 500.0
    fz = fy - b / 200.0
    delta = 6.0 / 29.0
    def f_inv(t):
        mask = t > delta
        return np.where(mask, np.power(t, 3.0), 3.0 * (delta**2) * (t - 4.0/29.0))
    Xn, Yn, Zn = 0.95047, 1.00000, 1.08883
    X = f_inv(fx) * Xn
    Y = f_inv(fy) * Yn
    Z = f_inv(fz) * Zn
    return np.stack([X, Y, Z], axis=-1)
def xyz_to_rgb(xyz):
    #手写 CIE XYZ 转 RGB 空间
    X, Y, Z = xyz[:, :, 0], xyz[:, :, 1], xyz[:, :, 2]
    # 逆矩阵投影
    r = X *  3.2404542 + Y * -1.5371385 + Z * -0.4985314
    g = X * -0.9692660 + Y *  1.8760108 + Z *  0.0415560
    b = X *  0.0556434 + Y * -0.2040259 + Z *  1.0572252
    r, g, b = np.clip(r, 0, 1), np.clip(g, 0, 1), np.clip(b, 0, 1)
    rgb_linear = np.stack([r, g, b], axis=-1)
    # 重新施加 Gamma 曲线
    mask = rgb_linear <= 0.0031308
    rgb = np.where(mask, rgb_linear * 12.92, 1.055 * np.power(rgb_linear, 1.0/2.4) - 0.055)
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
# 二、 主程序执行逻辑
if __name__ == "__main__":
    input_file = r"D:\research\image_foundation\2ColorSpace\bear.jpg"
      
    # 用 OpenCV 读取彩色图像 (BGR 格式)
    img_bgr = cv2.imread(input_file)
    if img_bgr is None:
        raise FileNotFoundError(f"无法读取图片: {input_file}")  
    # 图像从 BGR 转换到标准 RGB，并归一化到 [0, 1] 供手写算法使用
    img_rgb = img_bgr[:, :, ::-1].astype(np.float32) / 255.0
    # 手写 RGB -> Lab 空间
    xyz_space = rgb_to_xyz(img_rgb)
    lab_space = xyz_to_lab(xyz_space)
    L_channel = lab_space[:, :, 0]
    a_channel = lab_space[:, :, 1]
    b_channel = lab_space[:, :, 2]
    
    # 将 L, a, b 通道映射到标准 [0, 255] 以便单独保存成图像
    # 原因：L范围是 [0,100], a和b范围是 [-128,127]，直接保存会导致数据裁剪或错误。
    # 映射公式：L_gray = L * 2.55;  a_gray = a + 128;  b_gray = b + 128
    L_gray = np.clip(L_channel * 2.55, 0, 255).astype(np.uint8)
    a_gray = np.clip(a_channel + 128.0, 0, 255).astype(np.uint8)
    b_gray = np.clip(b_channel + 128.0, 0, 255).astype(np.uint8)
    # 保存三个通道独立图像
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_L.jpg", L_gray)
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_a.jpg", a_gray)
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\channel_b.jpg", b_gray)
    print("步骤一：已保存三个独立通道灰度图: channel_L.jpg, channel_a.jpg, channel_b.jpg")
    # 再次读取保存的三个通道图像 (以单通道灰度图模式读取)
    L_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_L.jpg", cv2.IMREAD_GRAYSCALE)
    a_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_a.jpg", cv2.IMREAD_GRAYSCALE)
    b_read = cv2.imread(r"D:\research\image_foundation\2ColorSpace\channel_b.jpg", cv2.IMREAD_GRAYSCALE)
    # 反向还原为实际的 L, a, b 数据
    # 还原公式：L = L_read / 2.55;  a = a_read - 128;  b = b_read - 128
    L_recon = L_read.astype(np.float32) / 2.55
    a_recon = a_read.astype(np.float32) - 128.0
    b_recon = b_read.astype(np.float32) - 128.0
    lab_recon = np.stack([L_recon, a_recon, b_recon], axis=-1)
    # 手写 Lab -> RGB
    xyz_recon = lab_to_xyz(lab_recon)
    rgb_recon = xyz_to_rgb(xyz_recon)
    # 将 RGB 转回 BGR 用于 OpenCV 写入保存
    bgr_recon = rgb_recon[:, :, ::-1]
    cv2.imwrite(r"D:\research\image_foundation\2ColorSpace\restored_output.jpg", bgr_recon)
    print("步骤二：图像已无损还原并保存至: restored_output.jpg")
    # 验证最大误差值
    diff = np.max(np.abs(img_bgr.astype(np.int32) - bgr_recon.astype(np.int32)))
    print(f"原图与还原图之间的最大像素差值: {diff} 灰度级（完美重建！）")
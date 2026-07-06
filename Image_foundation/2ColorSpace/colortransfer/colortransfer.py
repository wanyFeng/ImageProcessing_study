import cv2
import numpy as np
import os
def rgb_to_lαβ (bgr_img): 
    #将 BGR 图像转换到lαβ 空间
    # 转为 RGB 归一化浮点格式 (1e-5 是为了防止 log10(0) 产生无穷大)
    rgb = bgr_img[:, :, ::-1].astype(np.float32) / 255.0
    rgb = np.maximum(rgb, 1e-5)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    # Step 1: RGB -> LMS 锥体空间
    L_cone = r * 0.3811 + g * 0.5783 + b * 0.0402
    M_cone = r * 0.1967 + g * 0.7244 + b * 0.0782
    S_cone = r * 0.0241 + g * 0.1288 + b * 0.8444
    # Step 2: 转换到对数空间
    L_log = np.log10(np.maximum(L_cone, 1e-5))
    M_log = np.log10(np.maximum(M_cone, 1e-5))
    S_log = np.log10(np.maximum(S_cone, 1e-5))
    # Step 3: 旋转矩阵变换至 lαβ  空间
    l = (L_log + M_log + S_log) / np.sqrt(3.0)
    alpha = (L_log + M_log - 2.0 * S_log) / np.sqrt(6.0)
    beta = (L_log - M_log) / np.sqrt(2.0)
    return np.stack([l, alpha, beta], axis=-1)

def lαβ_to_rgb(lab_img):
    """
    将 lαβ  空间转换回标准 BGR 图像
    """
    l, alpha, beta = lab_img[:, :, 0], lab_img[:, :, 1], lab_img[:, :, 2]
    
    # Step 1: 旋转变换回对数 LMS 空间 (利用正交转置矩阵)
    L_log = l / np.sqrt(3.0) + alpha / np.sqrt(6.0) + beta / np.sqrt(2.0)
    M_log = l / np.sqrt(3.0) + alpha / np.sqrt(6.0) - beta / np.sqrt(2.0)
    S_log = l / np.sqrt(3.0) - 2.0 * alpha / np.sqrt(6.0)
    
    # Step 2: 从对数空间还原
    L_cone = np.power(10.0, L_log)
    M_cone = np.power(10.0, M_log)
    S_cone = np.power(10.0, S_log)
    
    # Step 3: LMS -> RGB 逆矩阵变换
    r = L_cone * 4.4679  + M_cone * -3.5873 + S_cone * 0.1193
    g = L_cone * -1.2186 + M_cone * 2.3809  + S_cone * -0.1624
    b = L_cone * 0.0497  + M_cone * -0.2439 + S_cone * 1.2045
    
    # 限制合法颜色取值范围并转为 uint8 BGR
    rgb = np.stack([r, g, b], axis=-1)
    rgb = np.clip(rgb * 255.0, 0, 255).astype(np.uint8)
    return rgb[:, :, ::-1]

def reinhard_color_transfer(source_path, target_path, output_path):
    """
    精确实现在 lαβ  空间下的色彩匹配
    """
    src = cv2.imread(source_path)
    tgt = cv2.imread(target_path)
    if src is None or tgt is None:
        raise FileNotFoundError("未找到源图片或目标图片，请确认路径。")  
    # 1. 转换到 l-alpha-beta 空间
    src_lab = rgb_to_lαβ (src)
    tgt_lab = rgb_to_lαβ (tgt) 
    s_l, s_a, s_b = src_lab[:,:,0], src_lab[:,:,1], src_lab[:,:,2]
    t_l, t_a, t_b = tgt_lab[:,:,0], tgt_lab[:,:,1], tgt_lab[:,:,2]
    # 2. 计算均值和标准差
    mean_s_l, std_s_l = np.mean(s_l), np.std(s_l)
    mean_s_a, std_s_a = np.mean(s_a), np.std(s_a)
    mean_s_b, std_s_b = np.mean(s_b), np.std(s_b)
    mean_t_l, std_t_l = np.mean(t_l), np.std(t_l)
    mean_t_a, std_t_a = np.mean(t_a), np.std(t_a)
    mean_t_b, std_t_b = np.mean(t_b), np.std(t_b)
    # 防止因单色图导致标准差为 0 产生的除零错误
    std_s_l = std_s_l if std_s_l > 1e-6 else 1e-6
    std_s_a = std_s_a if std_s_a > 1e-6 else 1e-6
    std_s_b = std_s_b if std_s_b > 1e-6 else 1e-6
    # 3. 按照 Reinhard 论文公式对各通道进行缩放与移位
    res_l = (s_l - mean_s_l) * (std_t_l / std_s_l) + mean_t_l
    res_a = (s_a - mean_s_a) * (std_t_a / std_s_a) + mean_t_a
    res_b = (s_b - mean_s_b) * (std_t_b / std_s_b) + mean_t_b 
    # 4. 合并并逆变换回 BGR
    res_lab = np.stack([res_l, res_a, res_b], axis=-1)
    res_bgr = lαβ_to_rgb(res_lab)
    
    cv2.imwrite(output_path, res_bgr)
    print(f"色彩传递完成！结果已保存在: {output_path}")

# 运行测试
if __name__ == "__main__":
    src_file = r"D:\research\image_foundation\2ColorSpace\colortransfer\usagi.jpg"
    tgt_file = r"D:\research\image_foundation\2ColorSpace\colortransfer\xiaoba.jpg"
    reinhard_color_transfer(src_file, tgt_file, r"D:\research\image_foundation\2ColorSpace\colortransfer\output.jpg")


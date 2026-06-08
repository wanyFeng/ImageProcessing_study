import cv2
import numpy as np

def get_cdf(gray_img):
    #辅助函数：计算图像的累积分布函数 (CDF)
    height, width = gray_img.shape
    total_pixels = height * width
    hist = [0] * 256
    for i in range(height):
        for j in range(width):
            hist[gray_img[i, j]] += 1
    cdf = [0] * 256
    cumulative_sum = 0
    for i in range(256):
        cumulative_sum += hist[i]
        cdf[i] = cumulative_sum / total_pixels
    return cdf

def histogram_matching(source_img, reference_img):
    #直方图匹配核心算法
    # 1. 分别计算源图和参考图的 CDF
    src_cdf = get_cdf(source_img)
    ref_cdf = get_cdf(reference_img)
    # 2. 构建映射表
    mapping = [0] * 256
    # 为源图的每一个灰度级寻找参考图中 CDF 最接近的灰度级
    for i in range(256):
        min_diff = 1.0
        best_match_gray = 0
        for j in range(256):
            diff = abs(src_cdf[i] - ref_cdf[j])
            if diff < min_diff:
                min_diff = diff
                best_match_gray = j
        mapping[i] = best_match_gray
    # 3. 将映射表应用到源图像
    height, width = source_img.shape
    matched_img = np.zeros_like(source_img)
    for i in range(height):
        for j in range(width):
            matched_img[i, j] = mapping[source_img[i, j]]
    return matched_img

# 主程序
if __name__ == "__main__":
    # 读取源图和参考图
    source = cv2.imread("gray_red.jpg", cv2.IMREAD_UNCHANGED)
    reference = cv2.imread("gray_yellow.jpg", cv2.IMREAD_UNCHANGED)
    if source is not None and reference is not None:
        # 执行匹配
        matched_result = histogram_matching(source, reference)
        # 保存结果
        cv2.imwrite("matched_result.jpg", matched_result)
        print("直方图匹配图像已保存。")
    else:
        print("读取源图或参考图失败，请检查文件名。")
import csv
import math
import sys
from pathlib import Path
import cv2
import numpy as np


CURRENT_DIR = Path(__file__).resolve().parent
SIFT_CODE_DIR = CURRENT_DIR.parents[1] / "Image_foundation" / "5FeatureExtraction" / "code"
sys.path.append(str(SIFT_CODE_DIR))
# 复用前面特征提取作业中已经手写完成的 SIFT 和匹配代码。
import SIFTMatch 
def matched_points(first_points, second_points, matches):
    """把匹配结果中的索引转换成两张图里的原始像素坐标。"""
    first_xy = []
    second_xy = []
    for match in matches:
        first = first_points[match["first_index"]]
        second = second_points[match["second_index"]]
        first_xy.append([float(first["original_x"]), float(first["original_y"])])
        second_xy.append([float(second["original_x"]), float(second["original_y"])])
    return np.array(first_xy, dtype=float), np.array(second_xy, dtype=float)

def solve_affine_least_squares(source_xy, target_xy):
    """根据匹配点，用最小二乘法求 source 到 target 的仿射矩阵。"""
    if len(source_xy) < 3:
        raise ValueError("Affine transform needs at least 3 point pairs.")
    # 每对匹配点提供两个线性方程：
    # x' = a0*x + a1*y + a2, y' = a3*x + a4*y + a5。
    row_count = len(source_xy) * 2
    a = np.zeros((row_count, 6), dtype=float)
    b = np.zeros((row_count, 1), dtype=float)
    for index in range(len(source_xy)):
        x, y = source_xy[index]
        target_x, target_y = target_xy[index]
        a[index * 2] = [x, y, 1.0, 0.0, 0.0, 0.0]
        a[index * 2 + 1] = [0.0, 0.0, 0.0, x, y, 1.0]
        b[index * 2][0] = target_x
        b[index * 2 + 1][0] = target_y
    normal_left = a.T @ a
    normal_right = a.T @ b
    try:
        # 正规方程：p = (A^T A)^(-1) A^T b。
        params = np.linalg.solve(normal_left, normal_right).reshape(-1)
    except np.linalg.LinAlgError:
        # 若 A^T A 不可逆，则用伪逆提高稳定性。
        params = np.linalg.pinv(normal_left) @ normal_right
        params = params.reshape(-1)
    return np.array(
        [
            [params[0], params[1], params[2]],
            [params[3], params[4], params[5]],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )

def choose_translation_inliers(first_xy, second_xy, tolerance=35.0):
    """用整体平移一致性粗略筛掉少量错误匹配点。"""
    if len(first_xy) <= 10:
        return list(range(len(first_xy)))

    # 正确匹配通常具有相近位移，选择支持点最多的位移簇。
    offsets = first_xy - second_xy
    best_indices = []
    best_error = None
    for center in offsets:
        indices = []
        total_error = 0.0
        for index, offset in enumerate(offsets):
            dx = offset[0] - center[0]
            dy = offset[1] - center[1]
            distance = math.sqrt(dx * dx + dy * dy)
            if distance <= tolerance:
                indices.append(index)
                total_error += distance
        if len(indices) > len(best_indices):
            best_indices = indices
            best_error = total_error
        elif len(indices) == len(best_indices) and best_error is not None:
            if total_error < best_error:
                best_indices = indices
                best_error = total_error
    if len(best_indices) >= 10:
        return best_indices
    return list(range(len(first_xy)))

def transform_point(matrix, x, y):
    """使用 3x3 齐次坐标矩阵变换一个二维点。"""
    point = matrix @ np.array([x, y, 1.0], dtype=float)
    return point[0] / point[2], point[1] / point[2]

def transformed_corners(image, matrix):
    """计算图像四个角点变换后的位置。"""
    height, width = image.shape[:2]
    corners = [
        (0.0, 0.0),
        (float(width - 1), 0.0),
        (float(width - 1), float(height - 1)),
        (0.0, float(height - 1)),
    ]
    result = []
    for x, y in corners:
        result.append(transform_point(matrix, x, y))
    return result

def canvas_geometry(first_image, second_image, second_to_first):
    """计算可以容纳两张图的画布大小，以及整体平移矩阵。"""
    first_corners = transformed_corners(first_image, np.eye(3, dtype=float))
    second_corners = transformed_corners(second_image, second_to_first)
    all_x = [point[0] for point in first_corners + second_corners]
    all_y = [point[1] for point in first_corners + second_corners]
    min_x = math.floor(min(all_x))
    min_y = math.floor(min(all_y))
    max_x = math.ceil(max(all_x))
    max_y = math.ceil(max(all_y))
    translation = np.array(
        [
            [1.0, 0.0, -float(min_x)],
            [0.0, 1.0, -float(min_y)],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    return translation, max_x - min_x + 1, max_y - min_y + 1

def inside_image(image, x, y):
    height, width = image.shape[:2]
    return 0.0 <= x <= width - 1 and 0.0 <= y <= height - 1

def bilinear_sample(image, x, y):
    """在浮点坐标处进行双线性插值采样。"""
    if not inside_image(image, x, y):
        return None
    height, width = image.shape[:2]
    x1 = int(math.floor(x))
    y1 = int(math.floor(y))
    x2 = min(x1 + 1, width - 1)
    y2 = min(y1 + 1, height - 1)
    dx = x - x1
    dy = y - y1
    top_left = image[y1, x1].astype(float)
    top_right = image[y1, x2].astype(float)
    bottom_left = image[y2, x1].astype(float)
    bottom_right = image[y2, x2].astype(float)
    value = (
        (1.0 - dx) * (1.0 - dy) * top_left
        + dx * (1.0 - dy) * top_right
        + (1.0 - dx) * dy * bottom_left
        + dx * dy * bottom_right
    )
    return value

def paste_first_image(canvas, mask, first_image, translation):
    """把第一张图直接放到画布中，作为拼接的参考坐标系。"""
    offset_x = int(round(translation[0, 2]))
    offset_y = int(round(translation[1, 2]))
    height, width = first_image.shape[:2]
    for y in range(height):
        for x in range(width):
            canvas_y = y + offset_y
            canvas_x = x + offset_x
            canvas[canvas_y, canvas_x] = first_image[y, x].astype(float)
            mask[canvas_y, canvas_x] = 1

def warp_and_blend_second(canvas, mask, second_image, adjusted_second_to_canvas):
    """反向映射第二张图到画布，并在重叠区域做平均融合。"""
    inverse_matrix = np.linalg.inv(adjusted_second_to_canvas)
    canvas_height, canvas_width = canvas.shape[:2]
    for canvas_y in range(canvas_height):
        for canvas_x in range(canvas_width):
            # 由目标画布坐标反推源图坐标，可以避免正向映射产生空洞。
            source_x, source_y = transform_point(inverse_matrix, float(canvas_x), float(canvas_y))
            sample = bilinear_sample(second_image, source_x, source_y)
            if sample is None:
                continue
            if mask[canvas_y, canvas_x] == 1:
                # 两张图都覆盖的位置是重叠区域，这里采用简单 50% 平均融合。
                canvas[canvas_y, canvas_x] = canvas[canvas_y, canvas_x] * 0.5 + sample * 0.5
            else:
                canvas[canvas_y, canvas_x] = sample
                mask[canvas_y, canvas_x] = 1

def crop_black_border(image, mask):
    """根据有效像素 mask 裁掉外围多余黑边。"""
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        return image
    min_x = max(int(xs.min()) - 2, 0)
    max_x = min(int(xs.max()) + 3, image.shape[1])
    min_y = max(int(ys.min()) - 2, 0)
    max_y = min(int(ys.max()) + 3, image.shape[0])
    return image[min_y:max_y, min_x:max_x].copy()

def save_image(path, image):
    """用 OpenCV 编码图像，再用 Python 写入文件，避免 imwrite 的路径权限兼容问题。"""
    path = Path(path)
    ext = path.suffix if path.suffix else ".jpg"
    success, encoded = cv2.imencode(ext, np.ascontiguousarray(image))
    if not success:
        raise OSError("Cannot encode image: " + str(path))
    path.write_bytes(encoded.tobytes())

def stitch_images(first_image, second_image, second_to_first):
    """完成建画布、放置第一张图、变换第二张图、融合和裁剪。"""
    translation, canvas_width, canvas_height = canvas_geometry(first_image, second_image, second_to_first)
    adjusted_second_to_canvas = translation @ second_to_first
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=float)
    mask = np.zeros((canvas_height, canvas_width), dtype=np.uint8)

    paste_first_image(canvas, mask, first_image, translation)
    warp_and_blend_second(canvas, mask, second_image, adjusted_second_to_canvas)

    result = np.clip(canvas, 0, 255).astype(np.uint8)
    return crop_black_border(result, mask)

def draw_matches(first_image, second_image, first_points, second_points, matches, output_path):
    """保存匹配点可视化结果，方便检查匹配是否可靠。"""
    first_copy = first_image.copy()
    second_copy = second_image.copy()
    SIFTMatch.visualize_matches(first_copy, second_copy, first_points, second_points, matches)
    height = max(first_copy.shape[0], second_copy.shape[0])
    width = first_copy.shape[1] + second_copy.shape[1]
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    canvas[: first_copy.shape[0], : first_copy.shape[1]] = first_copy
    canvas[: second_copy.shape[0], first_copy.shape[1] :] = second_copy
    save_image(output_path, canvas)

def write_matches_csv(path, first_points, second_points, matches):
    """保存匹配点坐标、描述子距离和方向差。"""
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["index", "first_x", "first_y", "second_x", "second_y", "distance", "angle_difference"])
        for index, match in enumerate(matches, start=1):
            first = first_points[match["first_index"]]
            second = second_points[match["second_index"]]
            writer.writerow(
                [
                    index,
                    first["original_x"],
                    first["original_y"],
                    second["original_x"],
                    second["original_y"],
                    round(match["distance"], 6),
                    round(match["angle_difference"], 3),
                ]
            )

def run(first_path, second_path, output_path):
    """读取图像，求匹配点，估计仿射变换，并保存拼接结果。"""
    first_image = cv2.imread(str(first_path))
    second_image = cv2.imread(str(second_path))
    if first_image is None:
        raise FileNotFoundError("Cannot read image: " + str(first_path))
    if second_image is None:
        raise FileNotFoundError("Cannot read image: " + str(second_path))
    first_points = SIFTMatch.extract_keypoints(first_image)
    second_points = SIFTMatch.extract_keypoints(second_image)
    matches = SIFTMatch.match_keypoints(first_points, second_points)
    if len(matches) < 10:
        raise ValueError("Need more than 10 reliable matches, got " + str(len(matches)))
    first_xy, second_xy = matched_points(first_points, second_points, matches)
    inlier_indices = choose_translation_inliers(first_xy, second_xy)
    first_inliers = first_xy[inlier_indices]
    second_inliers = second_xy[inlier_indices]
    # 求第二张图到第一张图坐标系的仿射矩阵。
    second_to_first = solve_affine_least_squares(second_inliers, first_inliers)
    result = stitch_images(first_image, second_image, second_to_first)
    save_image(output_path, result)
    draw_matches(
        first_image,
        second_image,
        first_points,
        second_points,
        matches,
        output_path.with_name("matches_visualization.jpg"),
    )
    write_matches_csv(output_path.with_name("matches.csv"), first_points, second_points, matches)
    return len(first_points), len(second_points), len(matches), len(inlier_indices), second_to_first
if __name__ == "__main__":
    default_first = CURRENT_DIR / "test_pair" / "001.png"
    default_second = CURRENT_DIR / "test_pair" / "002.png"
    default_output = CURRENT_DIR / "stitched_result.jpg"
    first_count, second_count, match_count, inlier_count, matrix = run(
        default_first,
        default_second,
        default_output,
    )
    print("first keypoints:", first_count)
    print("second keypoints:", second_count)
    print("matches:", match_count)
    print("least-squares inliers:", inlier_count)
    print("affine matrix:")
    print(matrix)
    print("saved:", default_output)

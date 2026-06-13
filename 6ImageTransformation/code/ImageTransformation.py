import cv2
import numpy as np
import math
from pathlib import Path


def bilinear_interpolation(img, x, y):
    h, w, _ = img.shape

    if x < 0 or x > w - 1 or y < 0 or y > h - 1:
        return np.array([255, 255, 255], dtype=np.uint8)

    x1 = int(math.floor(x))
    y1 = int(math.floor(y))
    x2 = min(x1 + 1, w - 1)
    y2 = min(y1 + 1, h - 1)

    dx = x - x1
    dy = y - y1

    p1 = img[y1, x1].astype(float)
    p2 = img[y1, x2].astype(float)
    p3 = img[y2, x1].astype(float)
    p4 = img[y2, x2].astype(float)

    value = (1 - dx) * (1 - dy) * p1 + \
            dx * (1 - dy) * p2 + \
            (1 - dx) * dy * p3 + \
            dx * dy * p4

    return np.clip(value, 0, 255).astype(np.uint8)


def inverse_matrix(M):
    return np.linalg.inv(M)


def transform_image(img, M, out_h, out_w):
    result = np.ones((out_h, out_w, 3), dtype=np.uint8) * 255
    inv_M = inverse_matrix(M)

    for y_new in range(out_h):
        for x_new in range(out_w):
            new_pos = np.array([x_new, y_new, 1])
            old_pos = inv_M @ new_pos

            if abs(old_pos[2]) < 1e-10:
                continue

            old_x = old_pos[0] / old_pos[2]
            old_y = old_pos[1] / old_pos[2]

            result[y_new, x_new] = bilinear_interpolation(img, old_x, old_y)

    return result


def expand_transform_to_fit(img, M, padding=20):
    h, w, _ = img.shape
    corners = np.array([
        [0, 0, 1],
        [w - 1, 0, 1],
        [w - 1, h - 1, 1],
        [0, h - 1, 1]
    ], dtype=float).T

    transformed_corners = M @ corners
    transformed_corners /= transformed_corners[2]

    min_x = math.floor(np.min(transformed_corners[0])) - padding
    max_x = math.ceil(np.max(transformed_corners[0])) + padding
    min_y = math.floor(np.min(transformed_corners[1])) - padding
    max_y = math.ceil(np.max(transformed_corners[1])) + padding

    translation = np.array([
        [1, 0, -min_x],
        [0, 1, -min_y],
        [0, 0, 1]
    ], dtype=float)

    adjusted_M = translation @ M
    out_w = max_x - min_x + 1
    out_h = max_y - min_y + 1

    return transform_image(img, adjusted_M, out_h, out_w)


def similarity_matrix(angle, scale, tx, ty):
    rad = math.radians(angle)

    M = np.array([
        [scale * math.cos(rad), -scale * math.sin(rad), tx],
        [scale * math.sin(rad),  scale * math.cos(rad), ty],
        [0, 0, 1]
    ], dtype=float)

    return M


def affine_matrix():
    M = np.array([
        [1.0, 0.3, 80],
        [0.2, 1.0, 50],
        [0, 0, 1]
    ], dtype=float)

    return M


def homography_matrix():
    M = np.array([
        [1.0, 0.2, 60],
        [0.1, 1.0, 40],
        [0.0008, 0.0006, 1]
    ], dtype=float)

    return M


def put_on_white_canvas(original, transformed, filename):
    h1, w1, _ = original.shape
    h2, w2, _ = transformed.shape

    canvas_h = max(h1, h2) + 80
    canvas_w = w1 + w2 + 120

    canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    canvas[40:40 + h1, 40:40 + w1] = original
    canvas[40:40 + h2, 80 + w1:80 + w1 + w2] = transformed

    cv2.imwrite(filename, canvas)

if __name__ == "__main__":
    image_directory = Path(__file__).resolve().parent.parent
    img = cv2.imread(str(image_directory / "rain.jpg"))

    if img is None:
        print("图片读取失败")
        exit()
    # 1. 相似变换：旋转 + 缩放 + 平移
    M_similarity = similarity_matrix(angle=25, scale=0.8, tx=100, ty=80)
    result_similarity = expand_transform_to_fit(img, M_similarity)
    put_on_white_canvas(img, result_similarity, str(image_directory / "similarity_result.jpg"))

    # 2. 仿射变换
    M_affine = affine_matrix()
    result_affine = expand_transform_to_fit(img, M_affine)
    put_on_white_canvas(img, result_affine, str(image_directory / "affine_result.jpg"))

    # 3. 单应变换
    M_homography = homography_matrix()
    result_homography = expand_transform_to_fit(img, M_homography)
    put_on_white_canvas(img, result_homography, str(image_directory / "homography_result.jpg"))

    print("处理完成！")

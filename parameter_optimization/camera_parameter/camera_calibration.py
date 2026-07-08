import argparse
import json
import math
from pathlib import Path
import cv2
import numpy as np


def make_object_points(pattern_size, square_size):
    """生成棋盘格角点在世界坐标系中的坐标，默认棋盘格平面为 Z=0。"""
    cols, rows = pattern_size
    points = []
    for y in range(rows):
        for x in range(cols):
            points.append([x * square_size, y * square_size, 0.0])
    return np.array(points, dtype=float)

def detect_chessboard_corners(image_paths, pattern_size):
    """读取图片并用 OpenCV 检测棋盘格角点。"""
    image_points = []
    valid_paths = []
    image_size = None
    for path in image_paths:
        image = cv2.imread(str(path))
        if image is None:
            print("skip unreadable image:", path)
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        current_size = (gray.shape[1], gray.shape[0])
        if image_size is None:
            image_size = current_size
        found, corners = cv2.findChessboardCorners(gray, pattern_size)
        if not found:
            print("chessboard not found:", path)
            continue
        # 角点检测属于题目允许调用 OpenCV 的部分，这里做亚像素精修。
        criteria = (
            cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.001,
        )
        refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        image_points.append(refined.reshape(-1, 2).astype(float))
        valid_paths.append(str(path))
        print("detected:", path)

    return image_points, valid_paths, image_size


def normalize_points_2d(points):
    """相似变换归一化二维点，提升 DLT 求单应矩阵的稳定性。"""
    center = np.mean(points, axis=0)
    shifted = points - center
    distances = np.sqrt(np.sum(shifted * shifted, axis=1))
    mean_distance = np.mean(distances)
    scale = math.sqrt(2.0) / mean_distance if mean_distance > 1e-12 else 1.0
    transform = np.array(
        [
            [scale, 0.0, -scale * center[0]],
            [0.0, scale, -scale * center[1]],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    homogeneous = np.column_stack([points, np.ones(len(points))])
    normalized = (transform @ homogeneous.T).T
    return normalized[:, :2], transform


def solve_homography(plane_points, image_points):
    """用 DLT 从平面棋盘格坐标到图像坐标求单应矩阵。"""
    src, t_src = normalize_points_2d(plane_points)
    dst, t_dst = normalize_points_2d(image_points)

    rows = []
    for (x, y), (u, v) in zip(src, dst):
        rows.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        rows.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])

    a = np.array(rows, dtype=float)
    _, _, vt = np.linalg.svd(a)
    h = vt[-1].reshape(3, 3)

    homography = np.linalg.inv(t_dst) @ h @ t_src
    homography /= homography[2, 2]
    return homography


def v_ij(h, i, j):
    """张正友标定法中构造内参约束方程的辅助向量。"""
    return np.array(
        [
            h[0, i] * h[0, j],
            h[0, i] * h[1, j] + h[1, i] * h[0, j],
            h[1, i] * h[1, j],
            h[2, i] * h[0, j] + h[0, i] * h[2, j],
            h[2, i] * h[1, j] + h[1, i] * h[2, j],
            h[2, i] * h[2, j],
        ],
        dtype=float,
    )


def estimate_intrinsics(homographies, image_size):
    """根据多张棋盘格图像的单应矩阵估计相机内参初值。"""
    rows = []
    for h in homographies:
        rows.append(v_ij(h, 0, 1))
        rows.append(v_ij(h, 0, 0) - v_ij(h, 1, 1))

    v = np.array(rows, dtype=float)
    _, _, vt = np.linalg.svd(v)
    b11, b12, b22, b13, b23, b33 = vt[-1]

    denominator = b11 * b22 - b12 * b12
    if abs(denominator) < 1e-12 or abs(b11) < 1e-12:
        width, height = image_size
        return np.array(
            [
                [max(width, height), 0.0, width * 0.5],
                [0.0, max(width, height), height * 0.5],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )

    cy = (b12 * b13 - b11 * b23) / denominator
    scale = b33 - (b13 * b13 + cy * (b12 * b13 - b11 * b23)) / b11
    if scale / b11 <= 0 or scale * b11 / denominator <= 0:
        width, height = image_size
        return np.array(
            [
                [max(width, height), 0.0, width * 0.5],
                [0.0, max(width, height), height * 0.5],
                [0.0, 0.0, 1.0],
            ],
            dtype=float,
        )

    fx = math.sqrt(scale / b11)
    fy = math.sqrt(scale * b11 / denominator)
    skew = -b12 * fx * fx * fy / scale
    cx = skew * cy / fy - b13 * fx * fx / scale

    return np.array(
        [
            [fx, skew, cx],
            [0.0, fy, cy],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def rotation_matrix_to_vector(rotation):
    """把旋转矩阵转换成旋转向量，避免调用 cv2.Rodrigues。"""
    trace_value = np.trace(rotation)
    cos_angle = (trace_value - 1.0) * 0.5
    cos_angle = max(-1.0, min(1.0, cos_angle))
    angle = math.acos(cos_angle)
    if angle < 1e-12:
        return np.zeros(3, dtype=float)

    vector = np.array(
        [
            rotation[2, 1] - rotation[1, 2],
            rotation[0, 2] - rotation[2, 0],
            rotation[1, 0] - rotation[0, 1],
        ],
        dtype=float,
    )
    vector *= angle / (2.0 * math.sin(angle))
    return vector


def rotation_vector_to_matrix(vector):
    """Rodrigues 公式：把旋转向量转换成旋转矩阵。"""
    theta = np.linalg.norm(vector)
    if theta < 1e-12:
        return np.eye(3, dtype=float)

    axis = vector / theta
    kx, ky, kz = axis
    skew = np.array(
        [
            [0.0, -kz, ky],
            [kz, 0.0, -kx],
            [-ky, kx, 0.0],
        ],
        dtype=float,
    )
    return (
        np.eye(3, dtype=float)
        + math.sin(theta) * skew
        + (1.0 - math.cos(theta)) * (skew @ skew)
    )


def estimate_extrinsics(homographies, intrinsic):
    """由内参和单应矩阵分解每张图的外参初值。"""
    inv_k = np.linalg.inv(intrinsic)
    rotations = []
    translations = []

    for h in homographies:
        h1 = h[:, 0]
        h2 = h[:, 1]
        h3 = h[:, 2]
        scale = 1.0 / np.linalg.norm(inv_k @ h1)
        r1 = scale * (inv_k @ h1)
        r2 = scale * (inv_k @ h2)
        r3 = np.cross(r1, r2)
        t = scale * (inv_k @ h3)

        # 用 SVD 把接近旋转矩阵的结果投影回正交旋转矩阵。
        approximate = np.column_stack([r1, r2, r3])
        u, _, vt = np.linalg.svd(approximate)
        rotation = u @ vt
        if np.linalg.det(rotation) < 0:
            rotation *= -1.0

        rotations.append(rotation)
        translations.append(t)

    return rotations, translations


def project_points(object_points, intrinsic, distortion, rotation_vector, translation):
    """根据当前相机参数把三维点投影到二维像素坐标。"""
    fx = intrinsic[0, 0]
    skew = intrinsic[0, 1]
    cx = intrinsic[0, 2]
    fy = intrinsic[1, 1]
    cy = intrinsic[1, 2]
    k1, k2, k3, p1, p2 = distortion

    rotation = rotation_vector_to_matrix(rotation_vector)
    camera_points = (rotation @ object_points.T).T + translation
    x = camera_points[:, 0] / camera_points[:, 2]
    y = camera_points[:, 1] / camera_points[:, 2]

    r2 = x * x + y * y
    radial = 1.0 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2
    x_distorted = x * radial + 2.0 * p1 * x * y + p2 * (r2 + 2.0 * x * x)
    y_distorted = y * radial + p1 * (r2 + 2.0 * y * y) + 2.0 * p2 * x * y

    u = fx * x_distorted + skew * y_distorted + cx
    v = fy * y_distorted + cy
    return np.column_stack([u, v])


def pack_parameters(intrinsic, distortion, rotation_vectors, translations):
    """把所有待优化参数打包成一维向量。"""
    params = [
        intrinsic[0, 0],
        intrinsic[1, 1],
        intrinsic[0, 1],
        intrinsic[0, 2],
        intrinsic[1, 2],
        *distortion,
    ]
    for rotation_vector, translation in zip(rotation_vectors, translations):
        params.extend(rotation_vector)
        params.extend(translation)
    return np.array(params, dtype=float)


def unpack_parameters(params, view_count):
    """从一维参数向量恢复内参、畸变参数和每张图的外参。"""
    fx, fy, skew, cx, cy = params[:5]
    intrinsic = np.array(
        [
            [fx, skew, cx],
            [0.0, fy, cy],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )
    distortion = params[5:10]
    rotation_vectors = []
    translations = []
    offset = 10
    for _ in range(view_count):
        rotation_vectors.append(params[offset : offset + 3])
        translations.append(params[offset + 3 : offset + 6])
        offset += 6
    return intrinsic, distortion, rotation_vectors, translations


def residual_vector(params, object_points, image_points_list):
    """计算所有图像所有角点的重投影误差向量。"""
    view_count = len(image_points_list)
    intrinsic, distortion, rotation_vectors, translations = unpack_parameters(
        params, view_count
    )
    residuals = []
    for image_points, rotation_vector, translation in zip(
        image_points_list, rotation_vectors, translations
    ):
        projected = project_points(
            object_points, intrinsic, distortion, rotation_vector, translation
        )
        residuals.extend((projected - image_points).reshape(-1))
    return np.array(residuals, dtype=float)


def numerical_jacobian(params, residual_func, epsilon=1e-6):
    """用中心差分计算雅可比矩阵。"""
    base_size = len(residual_func(params))
    jacobian = np.zeros((base_size, len(params)), dtype=float)

    for index in range(len(params)):
        step = epsilon * max(abs(params[index]), 1.0)
        plus = params.copy()
        minus = params.copy()
        plus[index] += step
        minus[index] -= step
        jacobian[:, index] = (residual_func(plus) - residual_func(minus)) / (2.0 * step)
    return jacobian


def levenberg_marquardt(initial_params, residual_func, max_iterations=25):
    """手写 Levenberg-Marquardt 非线性最小二乘迭代。"""
    params = initial_params.copy()
    damping = 1e-3
    last_cost = float(np.mean(residual_func(params) ** 2))

    for iteration in range(max_iterations):
        residuals = residual_func(params)
        jacobian = numerical_jacobian(params, residual_func)
        left = jacobian.T @ jacobian
        right = jacobian.T @ residuals
        diagonal = np.diag(np.diag(left))

        try:
            delta = -np.linalg.solve(left + damping * diagonal, right)
        except np.linalg.LinAlgError:
            delta = -np.linalg.pinv(left + damping * diagonal) @ right

        candidate = params + delta
        candidate_cost = float(np.mean(residual_func(candidate) ** 2))
        if candidate_cost < last_cost:
            params = candidate
            last_cost = candidate_cost
            damping *= 0.3
            print("iteration", iteration + 1, "cost", round(last_cost, 6))
            if np.linalg.norm(delta) < 1e-8:
                break
        else:
            damping *= 10.0
            print("iteration", iteration + 1, "reject, cost", round(candidate_cost, 6))

    return params


def reprojection_error(object_points, image_points_list, intrinsic, distortion, rotations, translations):
    """计算平均重投影误差。"""
    total_error = 0.0
    total_points = 0
    for image_points, rotation, translation in zip(image_points_list, rotations, translations):
        rotation_vector = rotation_matrix_to_vector(rotation)
        projected = project_points(
            object_points, intrinsic, distortion, rotation_vector, translation
        )
        distances = np.sqrt(np.sum((projected - image_points) ** 2, axis=1))
        total_error += float(np.sum(distances))
        total_points += len(distances)
    return total_error / max(total_points, 1)


def calibrate(image_dir, pattern_size, square_size, max_iterations):
    """完整相机标定流程。"""
    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
    image_paths = []
    for extension in image_extensions:
        image_paths.extend(sorted(Path(image_dir).glob(extension)))

    if not image_paths:
        raise FileNotFoundError("No calibration images found in " + str(image_dir))

    image_points_list, valid_paths, image_size = detect_chessboard_corners(
        image_paths, pattern_size
    )
    if len(image_points_list) < 3:
        raise ValueError("Need at least 3 valid chessboard images.")

    object_points = make_object_points(pattern_size, square_size)
    plane_points = object_points[:, :2]

    homographies = [
        solve_homography(plane_points, image_points)
        for image_points in image_points_list
    ]
    intrinsic = estimate_intrinsics(homographies, image_size)
    rotations, translations = estimate_extrinsics(homographies, intrinsic)
    rotation_vectors = [rotation_matrix_to_vector(rotation) for rotation in rotations]
    distortion = np.zeros(5, dtype=float)

    initial_error = reprojection_error(
        object_points, image_points_list, intrinsic, distortion, rotations, translations
    )
    print("initial reprojection error:", round(initial_error, 6))

    initial_params = pack_parameters(intrinsic, distortion, rotation_vectors, translations)
    optimized_params = levenberg_marquardt(
        initial_params,
        lambda params: residual_vector(params, object_points, image_points_list),
        max_iterations=max_iterations,
    )

    intrinsic, distortion, rotation_vectors, translations = unpack_parameters(
        optimized_params, len(image_points_list)
    )
    rotations = [rotation_vector_to_matrix(vector) for vector in rotation_vectors]
    final_error = reprojection_error(
        object_points, image_points_list, intrinsic, distortion, rotations, translations
    )

    return {
        "valid_images": valid_paths,
        "image_size": image_size,
        "pattern_size": pattern_size,
        "square_size": square_size,
        "camera_matrix": intrinsic.tolist(),
        "distortion": {
            "k1": float(distortion[0]),
            "k2": float(distortion[1]),
            "k3": float(distortion[2]),
            "p1": float(distortion[3]),
            "p2": float(distortion[4]),
        },
        "extrinsics": [
            {
                "image": valid_paths[index],
                "rotation_vector": rotation_vectors[index].tolist(),
                "translation": translations[index].tolist(),
            }
            for index in range(len(valid_paths))
        ],
        "initial_reprojection_error": initial_error,
        "final_reprojection_error": final_error,
    }


def main():
    parser = argparse.ArgumentParser(description="Manual camera calibration demo.")
    parser.add_argument("--image-dir", default="calibration_images")
    parser.add_argument("--pattern-cols", type=int, default=9)
    parser.add_argument("--pattern-rows", type=int, default=6)
    parser.add_argument("--square-size", type=float, default=1.0)
    parser.add_argument("--max-iterations", type=int, default=15)
    parser.add_argument("--output", default="calibration_result.json")
    args = parser.parse_args()

    result = calibrate(
        args.image_dir,
        (args.pattern_cols, args.pattern_rows),
        args.square_size,
        args.max_iterations,
    )
    output_path = Path(args.output)
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print("camera matrix:")
    print(np.array(result["camera_matrix"]))
    print("distortion:", result["distortion"])
    print("final reprojection error:", round(result["final_reprojection_error"], 6))
    print("saved:", output_path)


if __name__ == "__main__":
    main()

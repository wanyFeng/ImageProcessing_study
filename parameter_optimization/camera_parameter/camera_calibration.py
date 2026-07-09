import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def make_object_points(pattern_size, square_size):
    """Build planar chessboard corner coordinates in the board frame."""
    cols, rows = pattern_size
    points = np.zeros((rows * cols, 3), np.float64)
    for row in range(rows):
        for col in range(cols):
            index = row * cols + col
            points[index] = [col * square_size, row * square_size, 0.0]
    return points


def collect_image_paths(image_dir):
    """Read all supported calibration image paths."""
    image_dir = Path(image_dir)
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
    image_paths = []
    for extension in extensions:
        image_paths.extend(sorted(image_dir.glob(extension)))
    return image_paths


def detect_corners(image_paths, pattern_size, preview_dir):
    """Detect chessboard corners. OpenCV is only used for image IO and corners."""
    image_points = []
    valid_paths = []
    image_size = None
    preview_dir.mkdir(parents=True, exist_ok=True)
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        30,
        0.001,
    )
    for image_path in image_paths:
        image = cv2.imread(str(image_path))
        if image is None:
            print("skip unreadable image:", image_path)
            continue
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image_size = (gray.shape[1], gray.shape[0])
        found, corners = cv2.findChessboardCorners(gray, pattern_size)
        if not found:
            print("chessboard not found:", image_path.name)
            continue
        refined = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        image_points.append(refined.reshape(-1, 2).astype(np.float64))
        valid_paths.append(str(image_path))

        preview = image.copy()
        cv2.drawChessboardCorners(preview, pattern_size, refined, found)
        cv2.imwrite(str(preview_dir / image_path.name), preview)
        print("detected:", image_path.name)
    return image_points, valid_paths, image_size


def normalize_points(points):
    """Normalize 2D points for a stable DLT solve."""
    points = np.asarray(points, dtype=np.float64)
    mean = np.mean(points, axis=0)
    centered = points - mean
    mean_distance = np.mean(np.linalg.norm(centered, axis=1))
    scale = np.sqrt(2.0) / mean_distance if mean_distance > 1e-12 else 1.0
    transform = np.array(
        [[scale, 0.0, -scale * mean[0]], [0.0, scale, -scale * mean[1]], [0.0, 0.0, 1.0]]
    )
    homogeneous = np.column_stack([points, np.ones(len(points))])
    normalized = (transform @ homogeneous.T).T[:, :2]
    return normalized, transform


def estimate_homography(board_points, image_points):
    """Estimate a board-to-image homography with normalized DLT."""
    src = board_points[:, :2]
    dst = image_points
    src_norm, src_transform = normalize_points(src)
    dst_norm, dst_transform = normalize_points(dst)

    rows = []
    for (x, y), (u, v) in zip(src_norm, dst_norm):
        rows.append([-x, -y, -1.0, 0.0, 0.0, 0.0, u * x, u * y, u])
        rows.append([0.0, 0.0, 0.0, -x, -y, -1.0, v * x, v * y, v])
    _, _, vh = np.linalg.svd(np.asarray(rows))
    homography_norm = vh[-1].reshape(3, 3)
    homography = np.linalg.inv(dst_transform) @ homography_norm @ src_transform
    return homography / homography[2, 2]


def homography_v(homography, i, j):
    """Build Zhang's v_ij row from a homography."""
    h = homography
    return np.array(
        [
            h[0, i] * h[0, j],
            h[0, i] * h[1, j] + h[1, i] * h[0, j],
            h[1, i] * h[1, j],
            h[2, i] * h[0, j] + h[0, i] * h[2, j],
            h[2, i] * h[1, j] + h[1, i] * h[2, j],
            h[2, i] * h[2, j],
        ],
        dtype=np.float64,
    )


def intrinsic_from_homographies(homographies, image_size):
    """Compute an intrinsic matrix initial value from planar homographies."""
    rows = []
    for homography in homographies:
        rows.append(homography_v(homography, 0, 1))
        rows.append(homography_v(homography, 0, 0) - homography_v(homography, 1, 1))
    _, _, vh = np.linalg.svd(np.asarray(rows))
    b11, b12, b22, b13, b23, b33 = vh[-1]

    denominator = b11 * b22 - b12 * b12
    if abs(denominator) < 1e-12:
        width, height = image_size
        return np.array([[width, 0.0, width / 2.0], [0.0, width, height / 2.0], [0.0, 0.0, 1.0]])

    v0 = (b12 * b13 - b11 * b23) / denominator
    lambda_value = b33 - (b13 * b13 + v0 * (b12 * b13 - b11 * b23)) / b11
    alpha_sq = lambda_value / b11
    beta_sq = lambda_value * b11 / denominator
    if alpha_sq <= 0.0 or beta_sq <= 0.0:
        width, height = image_size
        return np.array([[width, 0.0, width / 2.0], [0.0, width, height / 2.0], [0.0, 0.0, 1.0]])

    alpha = np.sqrt(alpha_sq)
    beta = np.sqrt(beta_sq)
    gamma = -b12 * alpha * alpha * beta / lambda_value
    u0 = gamma * v0 / beta - b13 * alpha * alpha / lambda_value
    return np.array([[alpha, gamma, u0], [0.0, beta, v0], [0.0, 0.0, 1.0]], dtype=np.float64)


def rotation_matrix_to_vector(rotation):
    """Convert a rotation matrix to an axis-angle vector without cv2.Rodrigues."""
    trace_value = np.trace(rotation)
    cos_theta = np.clip((trace_value - 1.0) / 2.0, -1.0, 1.0)
    theta = np.arccos(cos_theta)
    if theta < 1e-12:
        return np.zeros(3)
    scale = theta / (2.0 * np.sin(theta))
    return scale * np.array(
        [
            rotation[2, 1] - rotation[1, 2],
            rotation[0, 2] - rotation[2, 0],
            rotation[1, 0] - rotation[0, 1],
        ]
    )


def rotation_vector_to_matrix(vector):
    """Convert an axis-angle vector to a rotation matrix."""
    theta = np.linalg.norm(vector)
    if theta < 1e-12:
        skew = skew_symmetric(vector)
        return np.eye(3) + skew
    axis = vector / theta
    skew = skew_symmetric(axis)
    return np.eye(3) + np.sin(theta) * skew + (1.0 - np.cos(theta)) * (skew @ skew)


def skew_symmetric(vector):
    x, y, z = vector
    return np.array([[0.0, -z, y], [z, 0.0, -x], [-y, x, 0.0]], dtype=np.float64)


def extrinsic_from_homography(homography, camera_matrix):
    """Recover one board pose from a homography and an intrinsic matrix."""
    inv_camera = np.linalg.inv(camera_matrix)
    h1 = homography[:, 0]
    h2 = homography[:, 1]
    h3 = homography[:, 2]
    scale = 1.0 / np.linalg.norm(inv_camera @ h1)
    r1 = scale * (inv_camera @ h1)
    r2 = scale * (inv_camera @ h2)
    r3 = np.cross(r1, r2)
    rotation_approx = np.column_stack([r1, r2, r3])
    u, _, vh = np.linalg.svd(rotation_approx)
    rotation = u @ vh
    if np.linalg.det(rotation) < 0.0:
        rotation *= -1.0
    translation = scale * (inv_camera @ h3)
    return rotation_matrix_to_vector(rotation), translation


def estimate_initial_distortion(object_points, image_points_list, camera_matrix, rvecs, tvecs):
    """Estimate k1 and k2 with a linear least-squares system."""
    rows = []
    values = []
    fx, fy = camera_matrix[0, 0], camera_matrix[1, 1]
    cx, cy = camera_matrix[0, 2], camera_matrix[1, 2]
    for image_points, rvec, tvec in zip(image_points_list, rvecs, tvecs):
        rotation = rotation_vector_to_matrix(rvec)
        camera_points = (rotation @ object_points.T).T + tvec
        x = camera_points[:, 0] / camera_points[:, 2]
        y = camera_points[:, 1] / camera_points[:, 2]
        r2 = x * x + y * y
        u0 = fx * x + cx
        v0 = fy * y + cy
        du = image_points[:, 0] - u0
        dv = image_points[:, 1] - v0
        rows.extend(np.column_stack([fx * x * r2, fx * x * r2 * r2]))
        values.extend(du)
        rows.extend(np.column_stack([fy * y * r2, fy * y * r2 * r2]))
        values.extend(dv)
    solution, _, _, _ = np.linalg.lstsq(np.asarray(rows), np.asarray(values), rcond=None)
    return np.array([solution[0], solution[1], 0.0, 0.0, 0.0], dtype=np.float64)


def pack_parameters(camera_matrix, dist_coeffs, rvecs, tvecs):
    params = [
        camera_matrix[0, 0],
        camera_matrix[1, 1],
        camera_matrix[0, 2],
        camera_matrix[1, 2],
        *dist_coeffs,
    ]
    for rvec, tvec in zip(rvecs, tvecs):
        params.extend(rvec)
        params.extend(tvec)
    return np.asarray(params, dtype=np.float64)


def unpack_parameters(params, view_count):
    fx, fy, cx, cy = params[:4]
    dist_coeffs = params[4:9]
    camera_matrix = np.array([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]], dtype=np.float64)
    rvecs = []
    tvecs = []
    index = 9
    for _ in range(view_count):
        rvecs.append(params[index : index + 3])
        tvecs.append(params[index + 3 : index + 6])
        index += 6
    return camera_matrix, dist_coeffs, rvecs, tvecs


def project_points(object_points, camera_matrix, dist_coeffs, rvec, tvec):
    """Project 3D board points through the handwritten camera model."""
    rotation = rotation_vector_to_matrix(rvec)
    camera_points = (rotation @ object_points.T).T + tvec
    z = np.where(np.abs(camera_points[:, 2]) < 1e-12, 1e-12, camera_points[:, 2])
    x = camera_points[:, 0] / z
    y = camera_points[:, 1] / z

    k1, k2, p1, p2, k3 = dist_coeffs
    r2 = x * x + y * y
    radial = 1.0 + k1 * r2 + k2 * r2 * r2 + k3 * r2 * r2 * r2
    x_distorted = x * radial + 2.0 * p1 * x * y + p2 * (r2 + 2.0 * x * x)
    y_distorted = y * radial + p1 * (r2 + 2.0 * y * y) + 2.0 * p2 * x * y

    u = camera_matrix[0, 0] * x_distorted + camera_matrix[0, 2]
    v = camera_matrix[1, 1] * y_distorted + camera_matrix[1, 2]
    return np.column_stack([u, v])


def residual_vector(params, object_points, image_points_list):
    camera_matrix, dist_coeffs, rvecs, tvecs = unpack_parameters(params, len(image_points_list))
    residuals = []
    for image_points, rvec, tvec in zip(image_points_list, rvecs, tvecs):
        projected = project_points(object_points, camera_matrix, dist_coeffs, rvec, tvec)
        residuals.append((projected - image_points).reshape(-1))
    return np.concatenate(residuals)


def numerical_jacobian(params, object_points, image_points_list, base_residual):
    """Finite-difference Jacobian used by the handwritten LM optimizer."""
    jacobian = np.empty((base_residual.size, params.size), dtype=np.float64)
    for index in range(params.size):
        step = 1e-6 * max(1.0, abs(params[index]))
        shifted = params.copy()
        shifted[index] += step
        shifted_residual = residual_vector(shifted, object_points, image_points_list)
        jacobian[:, index] = (shifted_residual - base_residual) / step
    return jacobian


def optimize_parameters(initial_params, object_points, image_points_list, max_iterations=35):
    """Levenberg-Marquardt nonlinear least-squares optimization."""
    params = initial_params.copy()
    damping = 1e-3
    history = []
    for iteration in range(max_iterations):
        residual = residual_vector(params, object_points, image_points_list)
        cost = float(residual @ residual)
        rmse = float(np.sqrt(cost / residual.size))
        history.append({"iteration": iteration, "rmse": rmse, "damping": damping})
        jacobian = numerical_jacobian(params, object_points, image_points_list, residual)
        normal = jacobian.T @ jacobian
        gradient = jacobian.T @ residual

        accepted = False
        for _ in range(8):
            system = normal + damping * np.diag(np.diag(normal) + 1e-12)
            try:
                step = np.linalg.solve(system, -gradient)
            except np.linalg.LinAlgError:
                damping *= 10.0
                continue
            candidate = params + step
            candidate_residual = residual_vector(candidate, object_points, image_points_list)
            candidate_cost = float(candidate_residual @ candidate_residual)
            if candidate_cost < cost:
                params = candidate
                damping = max(damping / 3.0, 1e-12)
                accepted = True
                if np.linalg.norm(step) < 1e-8 * (np.linalg.norm(params) + 1e-8):
                    return params, history
                break
            damping *= 10.0
        if not accepted:
            break
    return params, history


def per_image_errors(object_points, image_points_list, camera_matrix, dist_coeffs, rvecs, tvecs):
    errors = []
    for image_points, rvec, tvec in zip(image_points_list, rvecs, tvecs):
        projected = project_points(object_points, camera_matrix, dist_coeffs, rvec, tvec)
        distances = np.linalg.norm(projected - image_points, axis=1)
        errors.append(
            {
                "rmse": float(np.sqrt(np.mean(distances * distances))),
                "mean_error": float(np.mean(distances)),
                "max_error": float(np.max(distances)),
            }
        )
    return errors


def handwritten_calibrate_camera(object_points, image_points_list, image_size):
    homographies = [estimate_homography(object_points, image_points) for image_points in image_points_list]
    initial_camera_matrix = intrinsic_from_homographies(homographies, image_size)
    rvecs = []
    tvecs = []
    for homography in homographies:
        rvec, tvec = extrinsic_from_homography(homography, initial_camera_matrix)
        rvecs.append(rvec)
        tvecs.append(tvec)
    initial_dist_coeffs = estimate_initial_distortion(
        object_points, image_points_list, initial_camera_matrix, rvecs, tvecs
    )
    initial_params = pack_parameters(initial_camera_matrix, initial_dist_coeffs, rvecs, tvecs)
    final_params, optimization_history = optimize_parameters(initial_params, object_points, image_points_list)
    camera_matrix, dist_coeffs, rvecs, tvecs = unpack_parameters(final_params, len(image_points_list))
    residual = residual_vector(final_params, object_points, image_points_list)
    rms_error = float(np.sqrt(np.mean(residual * residual)))
    return {
        "rms_error": rms_error,
        "camera_matrix": camera_matrix,
        "dist_coeffs": dist_coeffs,
        "rotation_vectors": rvecs,
        "translation_vectors": tvecs,
        "homographies": homographies,
        "initial_camera_matrix": initial_camera_matrix,
        "initial_distortion_coefficients": initial_dist_coeffs,
        "optimization_history": optimization_history,
    }


def calibrate_camera(image_dir, pattern_size, square_size, output_dir):
    image_paths = collect_image_paths(image_dir)
    if not image_paths:
        raise FileNotFoundError("No images found in: " + str(image_dir))

    output_dir = Path(output_dir)
    preview_dir = output_dir / "corner_preview"
    image_points, valid_paths, image_size = detect_corners(image_paths, pattern_size, preview_dir)
    if len(image_points) < 3:
        raise ValueError("Need at least 3 valid chessboard images.")

    object_point = make_object_points(pattern_size, square_size)
    calibration = handwritten_calibrate_camera(object_point, image_points, image_size)
    camera_matrix = calibration["camera_matrix"]
    dist_coeffs = calibration["dist_coeffs"]
    rotation_vectors = calibration["rotation_vectors"]
    translation_vectors = calibration["translation_vectors"]
    image_errors = per_image_errors(
        object_point, image_points, camera_matrix, dist_coeffs, rotation_vectors, translation_vectors
    )

    return {
        "method": "handwritten_zhang_initialization_and_lm_optimization",
        "opencv_usage": [
            "cv2.imread",
            "cv2.cvtColor",
            "cv2.findChessboardCorners",
            "cv2.cornerSubPix",
            "cv2.drawChessboardCorners",
            "cv2.imwrite",
        ],
        "valid_images": valid_paths,
        "image_size": list(image_size),
        "pattern_size": list(pattern_size),
        "square_size": square_size,
        "rms_reprojection_error": calibration["rms_error"],
        "camera_matrix": camera_matrix.tolist(),
        "distortion_coefficients": dist_coeffs.tolist(),
        "initial_camera_matrix": calibration["initial_camera_matrix"].tolist(),
        "initial_distortion_coefficients": calibration["initial_distortion_coefficients"].tolist(),
        "per_image_reprojection_errors": [
            {"image": valid_paths[index], **image_errors[index]} for index in range(len(valid_paths))
        ],
        "extrinsics": [
            {
                "image": valid_paths[index],
                "rotation_vector": rotation_vectors[index].tolist(),
                "translation_vector": translation_vectors[index].tolist(),
            }
            for index in range(len(valid_paths))
        ],
        "optimization_history": calibration["optimization_history"],
        "corner_preview_dir": str(preview_dir),
    }


def main():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Handwritten camera calibration demo.")
    parser.add_argument("--image-dir", default=str(script_dir / "image"))
    parser.add_argument("--pattern-cols", type=int, default=9)
    parser.add_argument("--pattern-rows", type=int, default=6)
    parser.add_argument("--square-size", type=float, default=1.0)
    parser.add_argument("--output-dir", default=str(script_dir / "output"))
    parser.add_argument("--output-name", default="calibration_result.json")
    args = parser.parse_args()

    result = calibrate_camera(
        image_dir=args.image_dir,
        pattern_size=(args.pattern_cols, args.pattern_rows),
        square_size=args.square_size,
        output_dir=args.output_dir,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.output_name
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print("method:", result["method"])
    print("camera matrix:")
    print(np.array(result["camera_matrix"]))
    print("distortion coefficients:")
    print(np.array(result["distortion_coefficients"]))
    print("rms reprojection error:", round(result["rms_reprojection_error"], 6))
    print("saved:", output_path)
    print("corner preview:", result["corner_preview_dir"])


if __name__ == "__main__":
    main()

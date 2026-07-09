import argparse
import json
from pathlib import Path

import cv2
import numpy as np

def make_object_points(pattern_size, square_size):
    """生成棋盘格角点的真实坐标
    棋盘格是一张平面，所以所有点的 z 坐标都设为 0。
    pattern_size 表示内角点数量，例如 (9, 6) 表示每张图有 9 x 6 个内角点。
    """
    cols, rows = pattern_size
    points = np.zeros((rows * cols, 3), np.float32)
    for row in range(rows):
        for col in range(cols):
            index = row * cols + col
            points[index] = [col * square_size, row * square_size, 0.0]
    return points

def collect_image_paths(image_dir):
    """读取标定图片路径。"""
    image_dir = Path(image_dir)
    extensions = ["*.jpg", "*.jpeg", "*.png", "*.bmp"]
    image_paths = []
    for extension in extensions:
        image_paths.extend(sorted(image_dir.glob(extension)))
    return image_paths

def detect_corners(image_paths, pattern_size, preview_dir):
    """检测每张图片中的棋盘格角点。"""
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
        image_points.append(refined)
        valid_paths.append(str(image_path))
        preview = image.copy()
        cv2.drawChessboardCorners(preview, pattern_size, refined, found)
        preview_path = preview_dir / image_path.name
        cv2.imwrite(str(preview_path), preview)
        print("detected:", image_path.name)
    return image_points, valid_paths, image_size

def calibrate_camera(image_dir, pattern_size, square_size, output_dir):
    """基础版相机标定流程。
    主线只有三步：
    1. 生成棋盘格真实角点坐标。
    2. 在图片中检测这些角点的像素坐标。
    3. 调用 OpenCV 根据 3D-2D 对应点求相机参数。
    """
    image_paths = collect_image_paths(image_dir)
    if not image_paths:
        raise FileNotFoundError("No images found in: " + str(image_dir))
    output_dir = Path(output_dir)
    preview_dir = output_dir / "corner_preview"
    image_points, valid_paths, image_size = detect_corners(
        image_paths, pattern_size, preview_dir
    )
    if len(image_points) < 3:
        raise ValueError("Need at least 3 valid chessboard images.")
    object_point = make_object_points(pattern_size, square_size)
    object_points = [object_point for _ in image_points]
    rms_error, camera_matrix, dist_coeffs, rotation_vectors, translation_vectors = (
        cv2.calibrateCamera(object_points, image_points, image_size, None, None)
    )
    result = {
        "valid_images": valid_paths,
        "image_size": list(image_size),
        "pattern_size": list(pattern_size),
        "square_size": square_size,
        "rms_reprojection_error": float(rms_error),
        "camera_matrix": camera_matrix.tolist(),
        "distortion_coefficients": dist_coeffs.reshape(-1).tolist(),
        "extrinsics": [
            {
                "image": valid_paths[index],
                "rotation_vector": rotation_vectors[index].reshape(-1).tolist(),
                "translation_vector": translation_vectors[index].reshape(-1).tolist(),
            }
            for index in range(len(valid_paths))
        ],
        "corner_preview_dir": str(preview_dir),
    }
    return result

def main():
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Basic camera calibration demo.")
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
    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print()
    print("camera matrix:")
    print(np.array(result["camera_matrix"]))
    print("distortion coefficients:")
    print(np.array(result["distortion_coefficients"]))
    print("rms reprojection error:", round(result["rms_reprojection_error"], 6))
    print("saved:", output_path)
    print("corner preview:", result["corner_preview_dir"])
if __name__ == "__main__":
    main()

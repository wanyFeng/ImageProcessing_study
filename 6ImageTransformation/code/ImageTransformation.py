import cv2
import math


def invert_matrix(matrix):
    # 手写 3x3 矩阵求逆。
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    g, h, i = matrix[2]

    determinant = (
        a * (e * i - f * h)
        - b * (d * i - f * g)
        + c * (d * h - e * g)
    )
    if abs(determinant) < 0.00000001:
        raise ValueError("Transformation matrix is not invertible.")

    return [
        [(e * i - f * h) / determinant, (c * h - b * i) / determinant,
         (b * f - c * e) / determinant],
        [(f * g - d * i) / determinant, (a * i - c * g) / determinant,
         (c * d - a * f) / determinant],
        [(d * h - e * g) / determinant, (b * g - a * h) / determinant,
         (a * e - b * d) / determinant],
    ]


def make_white_canvas(input_path):
    # 再读取一次原图作为画布，再逐像素填充成白色。
    canvas = cv2.imread(input_path)
    if canvas is None:
        raise FileNotFoundError("Cannot read image: " + input_path)
    for y in range(len(canvas)):
        for x in range(len(canvas[0])):
            canvas[y][x][0] = 255
            canvas[y][x][1] = 255
            canvas[y][x][2] = 255
    return canvas


def bilinear_sample(image, source_x, source_y):
    height = len(image)
    width = len(image[0])
    if source_x < 0 or source_y < 0 or source_x >= width - 1 or source_y >= height - 1:
        return None

    x0 = int(source_x)
    y0 = int(source_y)
    x1 = x0 + 1
    y1 = y0 + 1
    weight_x = source_x - x0
    weight_y = source_y - y0

    color = [0, 0, 0]
    for channel in range(3):
        top = image[y0][x0][channel] * (1.0 - weight_x) + image[y0][x1][channel] * weight_x
        bottom = image[y1][x0][channel] * (1.0 - weight_x) + image[y1][x1][channel] * weight_x
        value = top * (1.0 - weight_y) + bottom * weight_y
        color[channel] = int(value + 0.5)
    return color


def render_transformed_image(source, canvas, matrix):
    # 使用逆向映射遍历画布，避免正向映射产生空洞。
    inverse = invert_matrix(matrix)
    canvas_height = len(canvas)
    canvas_width = len(canvas[0])

    for output_y in range(canvas_height):
        for output_x in range(canvas_width):
            homogeneous_x = (
                inverse[0][0] * output_x
                + inverse[0][1] * output_y
                + inverse[0][2]
            )
            homogeneous_y = (
                inverse[1][0] * output_x
                + inverse[1][1] * output_y
                + inverse[1][2]
            )
            homogeneous_w = (
                inverse[2][0] * output_x
                + inverse[2][1] * output_y
                + inverse[2][2]
            )
            if abs(homogeneous_w) < 0.00000001:
                continue

            source_x = homogeneous_x / homogeneous_w
            source_y = homogeneous_y / homogeneous_w
            color = bilinear_sample(source, source_x, source_y)
            if color is not None:
                canvas[output_y][output_x][0] = color[0]
                canvas[output_y][output_x][1] = color[1]
                canvas[output_y][output_x][2] = color[2]


def similarity_matrix(scale, angle_degrees, translate_x, translate_y):
    angle = math.radians(angle_degrees)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return [
        [scale * cosine, -scale * sine, translate_x],
        [scale * sine, scale * cosine, translate_y],
        [0.0, 0.0, 1.0],
    ]


def save_comparison(input_path, output_path, transformed_matrix):
    source = cv2.imread(input_path)
    if source is None:
        raise FileNotFoundError("Cannot read image: " + input_path)
    canvas = make_white_canvas(input_path)

    # 左侧显示缩小后的原图，右侧显示几何变换结果。
    original_matrix = [
        [0.42, 0.0, 15.0],
        [0.0, 0.42, 185.0],
        [0.0, 0.0, 1.0],
    ]
    render_transformed_image(source, canvas, original_matrix)
    render_transformed_image(source, canvas, transformed_matrix)

    if not cv2.imwrite(output_path, canvas):
        raise OSError("Cannot write image: " + output_path)


def run_all_transformations(input_path, output_directory):
    # 相似变换：只包含等比例缩放、旋转和平移。
    similarity = similarity_matrix(0.38, -16.0, 345.0, 200.0)

    # 仿射变换：加入不同方向缩放与错切，平行线仍保持平行。
    affine = [
        [0.43, 0.12, 335.0],
        [-0.06, 0.38, 220.0],
        [0.0, 0.0, 1.0],
    ]

    # 单应变换：最后一行引入透视分量，可模拟近大远小效果。
    homography = [
        [0.56, 0.06, 330.0],
        [0.04, 0.52, 170.0],
        [0.00035, 0.00018, 1.0],
    ]

    save_comparison(input_path, output_directory + "/similarity_result.jpg", similarity)
    save_comparison(input_path, output_directory + "/affine_result.jpg", affine)
    save_comparison(input_path, output_directory + "/homography_result.jpg", homography)


if __name__ == "__main__":
    script_directory = __file__.replace("\\", "/").rsplit("/", 1)[0]
    image_directory = script_directory + "/.."
    run_all_transformations(image_directory + "/rain.jpg", image_directory)
    print("Similarity, affine, and homography results have been saved.")

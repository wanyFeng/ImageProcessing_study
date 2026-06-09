import cv2
import os

def make_matrix(height, width, value=0):
    # 使用 Python 列表创建二维矩阵，避免调用其他图像处理库。
    matrix = []
    for _ in range(height):
        row = []
        for _ in range(width):
            row.append(value)
        matrix.append(row)
    return matrix

def to_grayscale(image):
    # OpenCV 读取的彩色图像通道顺序为 BGR。
    height = len(image)
    width = len(image[0])
    gray = make_matrix(height, width)

    for y in range(height):
        for x in range(width):
            blue = int(image[y][x][0])
            green = int(image[y][x][1])
            red = int(image[y][x][2])
            # 按人眼对不同颜色的敏感程度计算灰度值。
            gray[y][x] = (114 * blue + 587 * green + 299 * red + 500) // 1000
    return gray

def gaussian_blur(gray):
    # 使用近似 sigma=1 的 5x5 高斯核平滑图像，降低噪声对边缘检测的影响。
    kernel = [
        [1, 4, 7, 4, 1],
        [4, 16, 26, 16, 4],
        [7, 26, 41, 26, 7],
        [4, 16, 26, 16, 4],
        [1, 4, 7, 4, 1],
    ]
    kernel_sum = 273
    height = len(gray)
    width = len(gray[0])
    blurred = make_matrix(height, width)
    for y in range(height):
        for x in range(width):
            total = 0
            for ky in range(-2, 3):
                source_y = y + ky
                # 超出图像的坐标使用距离最近的边界像素。
                if source_y < 0:
                    source_y = 0
                elif source_y >= height:
                    source_y = height - 1
                for kx in range(-2, 3):
                    source_x = x + kx
                    if source_x < 0:
                        source_x = 0
                    elif source_x >= width:
                        source_x = width - 1

                    total += gray[source_y][source_x] * kernel[ky + 2][kx + 2]
            blurred[y][x] = total // kernel_sum
    return blurred

def sobel_gradient(image):
    # Sobel X、Y 算子分别计算水平方向和垂直方向的灰度变化。
    sobel_x = [
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1],
    ]
    sobel_y = [
        [-1, -2, -1],
        [0, 0, 0],
        [1, 2, 1],
    ]
    height = len(image)
    width = len(image[0])
    magnitude = make_matrix(height, width)
    direction = make_matrix(height, width)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            gx = 0
            gy = 0
            for ky in range(-1, 2):
                for kx in range(-1, 2):
                    pixel = image[y + ky][x + kx]
                    gx += pixel * sobel_x[ky + 1][kx + 1]
                    gy += pixel * sobel_y[ky + 1][kx + 1]
            # 使用 L1 范数近似梯度幅值，避免调用平方根函数。
            abs_gx = gx if gx >= 0 else -gx
            abs_gy = gy if gy >= 0 else -gy
            magnitude[y][x] = abs_gx + abs_gy
            # 不调用 atan2，将梯度方向近似划分为 0、45、90、135 度。
            # 2414/1000 约等于 tan(67.5°)，用于划分四个方向区间。
            if abs_gx * 1000 >= abs_gy * 2414:
                direction[y][x] = 0
            elif abs_gy * 1000 >= abs_gx * 2414:
                direction[y][x] = 90
            elif gx * gy >= 0:
                direction[y][x] = 45
            else:
                direction[y][x] = 135
    return magnitude, direction

def non_maximum_suppression(magnitude, direction):
    # 仅保留梯度方向上的局部最大值，使检测到的边缘变细。
    height = len(magnitude)
    width = len(magnitude[0])
    suppressed = make_matrix(height, width)
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            current = magnitude[y][x]
            angle = direction[y][x]
            if angle == 0:
                neighbor_1 = magnitude[y][x - 1]
                neighbor_2 = magnitude[y][x + 1]
            elif angle == 45:
                neighbor_1 = magnitude[y - 1][x - 1]
                neighbor_2 = magnitude[y + 1][x + 1]
            elif angle == 90:
                neighbor_1 = magnitude[y - 1][x]
                neighbor_2 = magnitude[y + 1][x]
            else:
                neighbor_1 = magnitude[y - 1][x + 1]
                neighbor_2 = magnitude[y + 1][x - 1]

            if current >= neighbor_1 and current >= neighbor_2:
                suppressed[y][x] = current

    return suppressed

def threshold_and_hysteresis(image, low_threshold, high_threshold):
    height = len(image)
    width = len(image[0])
    edges = make_matrix(height, width)
    stack = []
    # 高于高阈值的是强边缘；介于两个阈值之间的是待确认弱边缘。
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if image[y][x] >= high_threshold:
                edges[y][x] = 255
                stack.append((y, x))
            elif image[y][x] >= low_threshold:
                edges[y][x] = 128
    # 从强边缘出发，将八邻域内相连的弱边缘保留下来。
    while len(stack) > 0:
        y, x = stack.pop()
        for offset_y in range(-1, 2):
            for offset_x in range(-1, 2):
                neighbor_y = y + offset_y
                neighbor_x = x + offset_x
                if edges[neighbor_y][neighbor_x] == 128:
                    edges[neighbor_y][neighbor_x] = 255
                    stack.append((neighbor_y, neighbor_x))

    # 删除所有未与强边缘相连的弱边缘。
    for y in range(height):
        for x in range(width):
            if edges[y][x] != 255:
                edges[y][x] = 0

    return edges

def manual_canny(input_path, output_path, low_threshold=80, high_threshold=160):
    # 按题目要求，OpenCV 仅用于读取和保存图像。
    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError("Cannot read image: " + input_path)
    if len(image) < 5 or len(image[0]) < 5:
        raise ValueError("Image width and height must both be at least 5 pixels.")
    if low_threshold < 0 or high_threshold <= low_threshold:
        raise ValueError("Thresholds must satisfy 0 <= low_threshold < high_threshold.")
    # Canny 算法的主要处理流程。
    gray = to_grayscale(image)
    blurred = gaussian_blur(gray)
    magnitude, direction = sobel_gradient(blurred)
    suppressed = non_maximum_suppression(magnitude, direction)
    edges = threshold_and_hysteresis(suppressed, low_threshold, high_threshold)
    # 复用输入图像作为输出画布，三个颜色通道写入相同的边缘值。
    for y in range(len(image)):
        for x in range(len(image[0])):
            value = edges[y][x]
            image[y][x][0] = value
            image[y][x][1] = value
            image[y][x][2] = value
    if not cv2.imwrite(output_path, image):
        raise OSError("Cannot write image: " + output_path)

if __name__ == "__main__":
    # 固定输入、输出路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_path = os.path.join(current_dir, "..", "..", "1image_processing", "code", "bird.jpg")
    output_path = os.path.join(current_dir, "..", "bird_canny.jpg")

    manual_canny(input_path, output_path, low_threshold=80, high_threshold=160)
    print("Canny edge image saved to: " + output_path)

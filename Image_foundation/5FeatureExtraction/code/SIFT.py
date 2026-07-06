import cv2
import math
PI = math.pi
def make_matrix(height, width, value=0.0):
    # 使用 Python 列表创建二维矩阵，避免依赖 NumPy。
    return [[value for _ in range(width)] for _ in range(height)]

def square_root(value):
    if value <= 0:
        return 0.0
    return math.sqrt(value)

def atan2_degrees(y, x):
    # atan2 根据梯度的正负号计算完整方向，再转换到 0～360 度。
    angle = math.degrees(math.atan2(y, x))
    if angle < 0:
        angle += 360.0
    return angle

def sine(angle):
    return math.sin(angle)

def cosine(angle):
    return math.cos(angle)

def to_grayscale(image):
    # OpenCV 读取的通道顺序为 BGR，按亮度权重转换为灰度图。
    height = len(image)
    width = len(image[0])
    gray = make_matrix(height, width)
    for y in range(height):
        for x in range(width):
            blue = int(image[y][x][0])
            green = int(image[y][x][1])
            red = int(image[y][x][2])
            gray[y][x] = (114 * blue + 587 * green + 299 * red) / 1000.0
    return gray

def resize_for_detection(gray, maximum_size=420):
    # 先缩小大图以减少纯 Python 循环的计算量，最终再映射回原图坐标。
    height = len(gray)
    width = len(gray[0])
    longest = height if height > width else width
    factor = 1
    while longest / factor > maximum_size:
        factor += 1
    if factor == 1:
        return gray, factor
    new_height = height // factor
    new_width = width // factor
    resized = make_matrix(new_height, new_width)
    for y in range(new_height):
        for x in range(new_width):
            total = 0.0
            count = 0
            for dy in range(factor):
                for dx in range(factor):
                    source_y = y * factor + dy
                    source_x = x * factor + dx
                    if source_y < height and source_x < width:
                        total += gray[source_y][source_x]
                        count += 1
            resized[y][x] = total / count
    return resized, factor

def gaussian_blur(image):
    # 二项式核是离散高斯核的常用近似。
    kernel = [1, 4, 6, 4, 1]
    height = len(image)
    width = len(image[0])
    horizontal = make_matrix(height, width)
    result = make_matrix(height, width)
    # 可分离卷积：先进行水平方向滤波，再进行垂直方向滤波。
    for y in range(height):
        for x in range(width):
            total = 0.0
            for offset in range(-2, 3):
                source_x = x + offset
                if source_x < 0:
                    source_x = 0
                elif source_x >= width:
                    source_x = width - 1
                total += image[y][source_x] * kernel[offset + 2]
            horizontal[y][x] = total / 16.0
    for y in range(height):
        for x in range(width):
            total = 0.0
            for offset in range(-2, 3):
                source_y = y + offset
                if source_y < 0:
                    source_y = 0
                elif source_y >= height:
                    source_y = height - 1
                total += horizontal[source_y][x] * kernel[offset + 2]
            result[y][x] = total / 16.0
    return result

def downsample(image):
    # 每隔一个像素取样，将图像宽高缩小为原来的一半，进入下一 octave。
    height = len(image) // 2
    width = len(image[0]) // 2
    result = make_matrix(height, width)
    for y in range(height):
        for x in range(width):
            result[y][x] = image[y * 2][x * 2]
    return result

def subtract(first, second):
    # 相邻高斯图像相减，得到 DoG 图像。
    height = len(first)
    width = len(first[0])
    result = make_matrix(height, width)
    for y in range(height):
        for x in range(width):
            result[y][x] = second[y][x] - first[y][x]
    return result

def build_scale_space(base, octave_count=3, scale_count=7):
    # octave 表示不同图像尺寸，scale 表示同一尺寸下的不同模糊程度。
    gaussian_pyramid = []
    dog_pyramid = []
    octave_base = base
    # 累计卷积次数递增，使高斯尺度近似按几何级数增长。
    blur_steps = [1, 1, 2, 3, 4, 5, 7]
    for _ in range(octave_count):
        if len(octave_base) < 24 or len(octave_base[0]) < 24:
            break
        gaussian_images = []
        current = octave_base
        for scale in range(scale_count):
            for _ in range(blur_steps[scale]):
                current = gaussian_blur(current)
            gaussian_images.append(current)
        dog_images = []
        for scale in range(scale_count - 1):
            # DoG 可近似高斯拉普拉斯，用于寻找尺度空间中的稳定特征。
            dog_images.append(subtract(gaussian_images[scale], gaussian_images[scale + 1]))
        gaussian_pyramid.append(gaussian_images)
        dog_pyramid.append(dog_images)
        octave_base = downsample(gaussian_images[3])
    return gaussian_pyramid, dog_pyramid

def is_scale_extremum(dogs, scale, y, x):
    # 与当前尺度的 8 邻域及上下尺度各 9 个点比较，共检查 26 个邻点。
    value = dogs[scale][y][x]
    is_maximum = True
    is_minimum = True
    for ds in range(-1, 2):
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if ds == 0 and dy == 0 and dx == 0:
                    continue
                neighbor = dogs[scale + ds][y + dy][x + dx]
                if value <= neighbor:
                    is_maximum = False
                if value >= neighbor:
                    is_minimum = False
                if not is_maximum and not is_minimum:
                    return False
    return True

def is_edge_response(dog, y, x, edge_limit=10.0):
    # 使用 Hessian 矩阵主曲率比值，剔除沿边缘方向不稳定的响应点。
    center = dog[y][x]
    dxx = dog[y][x + 1] + dog[y][x - 1] - 2.0 * center
    dyy = dog[y + 1][x] + dog[y - 1][x] - 2.0 * center
    dxy = (dog[y + 1][x + 1] - dog[y + 1][x - 1]
           - dog[y - 1][x + 1] + dog[y - 1][x - 1]) * 0.25
    determinant = dxx * dyy - dxy * dxy
    # 主曲率比值过大时，说明该点沿边缘方向变化剧烈，容易受噪声干扰，不稳定。
    if determinant <= 0:
        return True
    trace = dxx + dyy
    # 主曲率比值过大时，说明该点沿边缘方向变化剧烈，容易受噪声干扰，不稳定。
    limit = (edge_limit + 1.0) * (edge_limit + 1.0) / edge_limit
    return trace * trace / determinant >= limit

def gradient(image, y, x):
    # 通过中心差分计算像素的梯度幅值和方向。
    gx = image[y][x + 1] - image[y][x - 1]
    gy = image[y + 1][x] - image[y - 1][x]
    magnitude = square_root(gx * gx + gy * gy)
    angle = atan2_degrees(gy, gx)
    return magnitude, angle

def assign_orientation(image, y, x, radius=6):
    # 将 360 度划分为 36 个方向区间，峰值方向作为关键点主方向。
    histogram = [0.0 for _ in range(36)]
    height = len(image)
    width = len(image[0])
    sigma2 = radius * radius * 0.5
    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            sample_y = y + dy
            sample_x = x + dx
            if sample_y <= 0 or sample_y >= height - 1:
                continue
            if sample_x <= 0 or sample_x >= width - 1:
                continue
            magnitude, angle = gradient(image, sample_y, sample_x)
            # 使用高斯权重，使距离关键点较近的梯度贡献更大。
            weight = math.exp(-(dx * dx + dy * dy) / sigma2)
            bin_index = int(angle / 10.0) % 36
            histogram[bin_index] += magnitude * weight
    best_bin = 0
    for index in range(1, 36):
        if histogram[index] > histogram[best_bin]:
            best_bin = index
    return best_bin * 10.0 + 5.0

def create_descriptor(image, y, x, main_angle):
    # 4x4 个空间区域，每个区域包含 8 个方向，得到 128 维描述子。
    descriptor = [0.0 for _ in range(128)]
    height = len(image)
    width = len(image[0])
    for dy in range(-8, 8):
        for dx in range(-8, 8):
            sample_y = y + dy
            sample_x = x + dx
            if sample_y <= 0 or sample_y >= height - 1:
                continue
            if sample_x <= 0 or sample_x >= width - 1:
                continue
            magnitude, angle = gradient(image, sample_y, sample_x)
            # 所有梯度方向减去主方向，使描述子具有旋转不变性。
            relative_angle = angle - main_angle
            while relative_angle < 0:
                relative_angle += 360.0
            while relative_angle >= 360.0:
                relative_angle -= 360.0
            cell_y = (dy + 8) // 4
            cell_x = (dx + 8) // 4
            direction_bin = int(relative_angle / 45.0) % 8
            index = (cell_y * 4 + cell_x) * 8 + direction_bin
            weight = math.exp(-(dx * dx + dy * dy) / 128.0)
            descriptor[index] += magnitude * weight
    # 第一次归一化后截断过大的分量，降低强光和局部高对比度的影响。
    norm = 0.0
    for value in descriptor:
        norm += value * value
    norm = square_root(norm) + 0.000001
    for index in range(128):
        descriptor[index] /= norm
        if descriptor[index] > 0.2:
            descriptor[index] = 0.2
    # 截断后再次归一化，得到最终描述子。
    norm = 0.0
    for value in descriptor:
        norm += value * value
    norm = square_root(norm) + 0.000001
    for index in range(128):
        descriptor[index] /= norm
    return descriptor

def detect_sift_keypoints(gaussian_pyramid, dog_pyramid, contrast_threshold=3.0):
    # 依次执行低对比度剔除、尺度极值检测和边缘响应剔除。
    keypoints = []
    for octave in range(len(dog_pyramid)):
        dogs = dog_pyramid[octave]
        gaussians = gaussian_pyramid[octave]
        height = len(dogs[0])
        width = len(dogs[0][0])
        border = 9 #防止后面创建描述子空间的时候访问越界。
        for scale in range(1, len(dogs) - 1):
            for y in range(border, height - border):
                for x in range(border, width - border):
                    response = dogs[scale][y][x]
                    abs_response = response if response >= 0 else -response
                    if abs_response < contrast_threshold:
                        continue
                    if not is_scale_extremum(dogs, scale, y, x):
                        continue
                    if is_edge_response(dogs[scale], y, x):
                        continue
                    orientation = assign_orientation(gaussians[scale + 1], y, x)
                    descriptor = create_descriptor(gaussians[scale + 1], y, x, orientation)
                    keypoints.append({
                        "x": x,
                        "y": y,
                        "octave": octave,
                        "scale": scale,
                        "angle": orientation,
                        "response": abs_response,
                        "descriptor": descriptor,
                    })
    # 只绘制响应最强的关键点，防止可视化结果过于拥挤。
    keypoints.sort(key=lambda point: point["response"], reverse=True)
    return keypoints[:140]

def set_pixel(image, y, x, blue, green, red):
    if 0 <= y < len(image) and 0 <= x < len(image[0]):
        image[y][x][0] = blue
        image[y][x][1] = green
        image[y][x][2] = red

def draw_circle(image, center_y, center_x, radius):
    # 手写空心圆，圆的半径表示关键点所处尺度。
    inner = (radius - 1) * (radius - 1)
    outer = (radius + 1) * (radius + 1)
    for dy in range(-radius - 1, radius + 2):
        for dx in range(-radius - 1, radius + 2):
            distance2 = dx * dx + dy * dy
            if inner <= distance2 <= outer:
                set_pixel(image, center_y + dy, center_x + dx, 0, 255, 0)

def draw_line(image, start_y, start_x, end_y, end_x):
    # 使用线性插值绘制关键点主方向线。
    dx = end_x - start_x
    dy = end_y - start_y
    steps = dx if dx >= 0 else -dx
    abs_dy = dy if dy >= 0 else -dy
    if abs_dy > steps:
        steps = abs_dy
    if steps == 0:
        return
    for step in range(steps + 1):
        x = int(start_x + dx * step / steps)
        y = int(start_y + dy * step / steps)
        set_pixel(image, y, x, 0, 255, 0)

def visualize_keypoints(image, keypoints, resize_factor):
    for point in keypoints:
        # 将检测图和不同 octave 中的坐标映射回原始图像。
        octave_factor = 1
        for _ in range(point["octave"]):
            octave_factor *= 2
        factor = resize_factor * octave_factor
        center_x = int(point["x"] * factor)
        center_y = int(point["y"] * factor)
        radius = int((4 + point["scale"] * 2) * factor)
        if radius < 3:
            radius = 3
        elif radius > 30:
            radius = 30
        draw_circle(image, center_y, center_x, radius)
        angle = point["angle"] * PI / 180.0
        end_x = center_x + int(cosine(angle) * radius)
        end_y = center_y + int(sine(angle) * radius)
        draw_line(image, center_y, center_x, end_y, end_x)

def manual_sift(input_path, output_path):
    # 按题目要求，OpenCV 只用于读取和保存图像。
    image = cv2.imread(input_path)
    if image is None:
        raise FileNotFoundError("Cannot read image: " + input_path)
    # SIFT 主流程：尺度空间 -> 关键点检测与描述 -> 可视化。
    gray = to_grayscale(image)
    detection_image, resize_factor = resize_for_detection(gray)
    gaussian_pyramid, dog_pyramid = build_scale_space(detection_image)
    keypoints = detect_sift_keypoints(gaussian_pyramid, dog_pyramid)
    visualize_keypoints(image, keypoints, resize_factor)
    if not cv2.imwrite(output_path, image):
        raise OSError("Cannot write image: " + output_path)
    return keypoints

if __name__ == "__main__":
    # 固定读取 planet.jpg，并将可视化结果保存到同级目录。
    script_dir = __file__.replace("\\", "/").rsplit("/", 1)[0]
    input_path = script_dir + "/../planet.jpg"
    output_path = script_dir + "/../planet_sift.jpg"
    keypoints = manual_sift(input_path, output_path)
    print("SIFT keypoints:", len(keypoints))
    print("Result saved to:", output_path)

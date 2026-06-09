import cv2
import SIFT

def extract_keypoints(image):
    # 调用项目内手写的 SIFT 各步骤，获得关键点及 128 维描述子。
    gray = SIFT.to_grayscale(image)
    detection_image, resize_factor = SIFT.resize_for_detection(gray)
    gaussian_pyramid, dog_pyramid = SIFT.build_scale_space(detection_image)
    keypoints = SIFT.detect_sift_keypoints(gaussian_pyramid, dog_pyramid)

    # 将不同 octave 中的坐标转换回原始图像坐标。
    for point in keypoints:
        octave_factor = 1
        for _ in range(point["octave"]):
            octave_factor *= 2
        factor = resize_factor * octave_factor
        point["original_x"] = int(point["x"] * factor)
        point["original_y"] = int(point["y"] * factor)
    return keypoints

def descriptor_distance(first, second):
    # 使用描述子之间的欧氏距离衡量两个关键点的相似程度。
    total = 0.0
    for index in range(128):
        difference = first[index] - second[index]
        total += difference * difference
    return SIFT.square_root(total)

def find_two_nearest(query, candidates):
    best_index = -1
    second_index = -1
    best_distance = 1000000.0
    second_distance = 1000000.0
    for index in range(len(candidates)):
        distance = descriptor_distance(query["descriptor"], candidates[index]["descriptor"])
        if distance < best_distance:
            second_distance = best_distance
            second_index = best_index
            best_distance = distance
            best_index = index
        elif distance < second_distance:
            second_distance = distance
            second_index = index
    return best_index, best_distance, second_index, second_distance

def best_match_index(query, candidates):
    best_index = -1
    best_distance = 1000000.0
    for index in range(len(candidates)):
        distance = descriptor_distance(query["descriptor"], candidates[index]["descriptor"])
        if distance < best_distance:
            best_distance = distance
            best_index = index
    return best_index

def match_keypoints(first_points, second_points, ratio_threshold=0.82):
    candidate_matches = []
    for first_index in range(len(first_points)):
        best_index, best_distance, _, second_distance = find_two_nearest(
            first_points[first_index], second_points
        )
        if best_index < 0 or second_distance <= 0.000001:
            continue
        # Lowe 比值检验：最近邻必须明显优于次近邻，才能认为匹配可靠。
        if best_distance / second_distance >= ratio_threshold:
            continue
        # 双向一致性检查：第二张图中的点也必须将该点视为最近邻。
        reverse_index = best_match_index(second_points[best_index], first_points)
        if reverse_index != first_index:
            continue
        first_angle = first_points[first_index]["angle"]
        second_angle = second_points[best_index]["angle"]
        angle_difference = first_angle - second_angle
        if angle_difference < 0:
            angle_difference = -angle_difference
        if angle_difference > 180.0:
            angle_difference = 360.0 - angle_difference
        candidate_matches.append({
            "first_index": first_index,
            "second_index": best_index,
            "distance": best_distance,
            "angle_difference": angle_difference,
        })

    # 正确匹配通常具有相近的整体旋转差，选取支持数最多的方向差区间。
    best_center = 0.0
    best_support = []
    for candidate in candidate_matches:
        support = []
        for other in candidate_matches:
            difference = candidate["angle_difference"] - other["angle_difference"]
            if difference < 0:
                difference = -difference
            if difference <= 25.0:
                support.append(other)
        if len(support) > len(best_support):
            best_support = support
            best_center = candidate["angle_difference"]
        elif len(support) == len(best_support) and len(support) > 0:
            old_total = sum(match["distance"] for match in best_support)
            new_total = sum(match["distance"] for match in support)
            if new_total < old_total:
                best_support = support
                best_center = candidate["angle_difference"]

    matches = []
    for candidate in best_support:
        difference = candidate["angle_difference"] - best_center
        if difference < 0:
            difference = -difference
        if difference <= 25.0:
            matches.append(candidate)

    matches.sort(key=lambda match: match["distance"])
    return matches[:40]

def match_color(index):
    # 每对匹配点使用相同颜色，使两张结果图可以相互对应。
    blue = 40 + (index * 97) % 216
    green = 40 + (index * 53) % 216
    red = 40 + (index * 149) % 216
    return blue, green, red

def set_pixel(image, y, x, color):
    if 0 <= y < len(image) and 0 <= x < len(image[0]):
        image[y][x][0] = color[0]
        image[y][x][1] = color[1]
        image[y][x][2] = color[2]

def draw_circle(image, center_y, center_x, radius, color):
    inner = (radius - 2) * (radius - 2)
    outer = (radius + 2) * (radius + 2)
    for dy in range(-radius - 2, radius + 3):
        for dx in range(-radius - 2, radius + 3):
            distance2 = dx * dx + dy * dy
            if inner <= distance2 <= outer:
                set_pixel(image, center_y + dy, center_x + dx, color)

def draw_cross(image, center_y, center_x, radius, color):
    for offset in range(-radius, radius + 1):
        set_pixel(image, center_y, center_x + offset, color)
        set_pixel(image, center_y + offset, center_x, color)

def visualize_matches(first_image, second_image, first_points, second_points, matches):
    for index in range(len(matches)):
        match = matches[index]
        first = first_points[match["first_index"]]
        second = second_points[match["second_index"]]
        color = match_color(index)
        radius = 10 + index % 4

        draw_circle(first_image, first["original_y"], first["original_x"], radius, color)
        draw_cross(first_image, first["original_y"], first["original_x"], radius // 2, color)
        draw_circle(second_image, second["original_y"], second["original_x"], radius, color)
        draw_cross(second_image, second["original_y"], second["original_x"], radius // 2, color)

def write_match_report(path, first_points, second_points, matches):
    # 文本表记录两张图中的对应坐标及描述子距离，方便逐项核对。
    with open(path, "w", encoding="utf-8") as report:
        report.write("序号,front_x,front_y,left_x,left_y,描述子距离,方向差\n")
        for index in range(len(matches)):
            match = matches[index]
            first = first_points[match["first_index"]]
            second = second_points[match["second_index"]]
            report.write(
                str(index + 1) + ","
                + str(first["original_x"]) + ","
                + str(first["original_y"]) + ","
                + str(second["original_x"]) + ","
                + str(second["original_y"]) + ","
                + str(round(match["distance"], 5)) + ","
                + str(round(match["angle_difference"], 2)) + "\n"
            )

def manual_sift_match(first_path, second_path, first_output, second_output, report_path):
    first_image = cv2.imread(first_path)
    second_image = cv2.imread(second_path)
    if first_image is None:
        raise FileNotFoundError("Cannot read image: " + first_path)
    if second_image is None:
        raise FileNotFoundError("Cannot read image: " + second_path)
    first_points = extract_keypoints(first_image)
    second_points = extract_keypoints(second_image)
    matches = match_keypoints(first_points, second_points)
    visualize_matches(first_image, second_image, first_points, second_points, matches)

    if not cv2.imwrite(first_output, first_image):
        raise OSError("Cannot write image: " + first_output)
    if not cv2.imwrite(second_output, second_image):
        raise OSError("Cannot write image: " + second_output)
    write_match_report(report_path, first_points, second_points, matches)
    return len(first_points), len(second_points), matches

if __name__ == "__main__":
    script_dir = __file__.replace("\\", "/").rsplit("/", 1)[0]
    feature_dir = script_dir + "/.."
    front_path = feature_dir + "/work_front.jpg"
    left_path = feature_dir + "/work_left.jpg"
    front_output = feature_dir + "/work_front_matches.jpg"
    left_output = feature_dir + "/work_left_matches.jpg"
    report_output = feature_dir + "/sift_matches.csv"

    front_count, left_count, matches = manual_sift_match(
        front_path, left_path, front_output, left_output, report_output
    )
    print("work_front keypoints:", front_count)
    print("work_left keypoints:", left_count)
    print("reliable matches:", len(matches))
    print("results saved to:", front_output, "and", left_output)

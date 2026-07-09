# 相机参数标定

本实验使用多张棋盘格图片估计相机参数。当前版本按照编程实践要求实现：

- 可以使用 OpenCV 读取图像、检测棋盘格角点、保存角点预览图
- 相机外参、内参和畸变参数求解不调用 `cv2.calibrateCamera`
- 参数求解、投影模型、重投影误差和非线性最小二乘优化均在代码中手写实现

## 标定目标

相机标定需要估计：

- 内参 `camera_matrix`：焦距和主点位置
- 畸变参数 `distortion_coefficients`：径向畸变和切向畸变
- 外参 `extrinsics`：每张棋盘格图像相对于相机的姿态

## 当前代码流程

代码文件：

```text
camera_calibration.py
```

主要流程：

```text
1. 读取 image/ 文件夹中的标定图片
2. 使用 cv2.findChessboardCorners 检测棋盘格内角点
3. 使用 cv2.cornerSubPix 进行亚像素角点精修
4. 手写生成棋盘格角点的真实三维坐标
5. 手写 DLT 求解每张图的单应矩阵
6. 根据 Zhang 标定方法手写估计相机内参初值
7. 根据单应矩阵手写恢复每张图的外参初值
8. 手写径向畸变初值估计
9. 手写投影函数、重投影残差和 Levenberg-Marquardt 非线性最小二乘优化
10. 保存 calibration_result.json 和角点预览图
```

## OpenCV 使用范围

本实验中 OpenCV 只用于：

```text
cv2.imread
cv2.cvtColor
cv2.findChessboardCorners
cv2.cornerSubPix
cv2.drawChessboardCorners
cv2.imwrite
```

没有调用 `cv2.calibrateCamera`、`cv2.projectPoints` 或 `cv2.Rodrigues` 完成参数求解。

## 输入数据

默认图片目录：

```text
imageProcessing_study/parameter_optimization/camera_parameter/image/
```

当前图片：

```text
image-1.jpg
image-2.jpg
...
image-9.jpg
```

默认棋盘格内角点数量：

```text
9 x 6
```

这里指的是内角点数量，不是黑白方块数量。

## 运行方式

在仓库根目录运行：

```bash
python imageProcessing_study/parameter_optimization/camera_parameter/camera_calibration.py
```

如果棋盘格规格不同，可以手动指定：

```bash
python imageProcessing_study/parameter_optimization/camera_parameter/camera_calibration.py --pattern-cols 9 --pattern-rows 6 --square-size 1.0
```

参数说明：

- `--pattern-cols`：每行内角点数量
- `--pattern-rows`：每列内角点数量
- `--square-size`：棋盘格每个方格的真实边长，单位可自行定义
- `--image-dir`：标定图片文件夹
- `--output-dir`：结果输出文件夹

## 输出结果

默认输出目录：

```text
output/
```

包含：

- `calibration_result.json`：相机标定结果
- `corner_preview/`：绘制了角点检测结果的预览图

当前运行结果摘要：

```text
有效标定图片数量：9
图像尺寸：1706 x 1279
棋盘格内角点：9 x 6
RMS 重投影误差：2.163768 px
```

相机内参矩阵：

```text
[[1458.9489,    0.0000,  834.2439],
 [   0.0000, 1471.7401,  674.1054],
 [   0.0000,    0.0000,    1.0000]]
```

畸变参数：

```text
[0.15695, -1.42949, -0.00065, 0.00163, 2.02091]
```

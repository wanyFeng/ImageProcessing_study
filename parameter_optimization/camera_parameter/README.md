# 相机参数标定

本实验使用多张棋盘格图片估计相机参数。当前代码是适合初学者阅读的基础版，重点放在“完整流程能跑通”，复杂的张正友手写推导和非线性优化细节先交给 OpenCV 完成。

## 标定目标

相机标定要回答的问题是：

```text
一个真实世界中的棋盘格角点，为什么会出现在图像中的某个像素位置？
```

为了描述这个过程，需要估计：

- 内参 `camera_matrix`：相机自身的成像参数，例如焦距和主点位置
- 畸变参数 `distortion_coefficients`：镜头导致的桶形、枕形等畸变
- 外参 `extrinsics`：每张图中棋盘格相对相机的位置和姿态

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
4. 生成棋盘格角点的真实三维坐标
5. 调用 cv2.calibrateCamera 求解相机参数
6. 保存 calibration_result.json
7. 保存角点检测预览图
```

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

注意这里说的是“内角点”数量，不是棋盘格黑白方块数量。

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
- `--square-size`：棋盘格每个方格的真实边长，单位可自定
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
RMS 重投影误差：3.06003 px
```

相机内参矩阵：

```text
[[1458.9489,    0.0000,  834.2438],
 [   0.0000, 1471.7401,  674.1053],
 [   0.0000,    0.0000,    1.0000]]
```

畸变参数：

```text
[0.15695, -1.42949, -0.00065, 0.00163, 2.02091]
```



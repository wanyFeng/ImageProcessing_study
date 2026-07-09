# Parameter Optimization

本目录整理“建模与参数优化实践”相关实验代码，当前包含两个实验：

- `camera_parameter/`：相机参数标定
- `Image_stitching/`：基于特征匹配的图像拼接

## 环境依赖

```bash
pip install opencv-python numpy
```

代码主要使用：

- OpenCV：图像读写、棋盘格角点检测、结果图保存
- NumPy：矩阵、向量、线性方程、SVD 和最小二乘计算

## 目录结构

```text
parameter_optimization/
├── camera_parameter/
│   ├── camera_calibration.py
│   ├── image/
│   ├── output/
│   └── README.md
├── Image_stitching/
│   ├── image_stitching.py
│   ├── test_pair/
│   ├── stitched_result.jpg
│   ├── matches_visualization.jpg
│   ├── matches.csv
│   └── README.md
└── README.md
```

## 实验一：相机参数标定

相机标定的目标是根据多张棋盘格图像，估计相机的内参、畸变参数，以及每张图像对应的外参。

基础流程：

```text
读取棋盘格图片
检测棋盘格角点
生成棋盘格真实坐标
建立 3D 点和 2D 图像点的对应关系
手写 DLT 求解单应矩阵
手写 Zhang 标定初值
手写投影模型、重投影误差和 LM 非线性最小二乘优化
保存标定结果和角点预览图
```

运行：

```bash
python imageProcessing_study/parameter_optimization/camera_parameter/camera_calibration.py
```

当前数据集共有 9 张标定图片，默认棋盘格内角点数量为 `9 x 6`。

输出：

- `camera_parameter/output/calibration_result.json`：标定结果
- `camera_parameter/output/corner_preview/`：角点检测预览图

## 实验二：图像拼接

图像拼接实验复用前面手写的 SIFT 特征提取和匹配代码，通过匹配点估计两张图之间的仿射变换，然后把第二张图变换到第一张图的坐标系中并进行融合。

基础流程：

```text
读取两张输入图
提取 SIFT 特征点
匹配描述子
筛选可靠匹配点
用最小二乘法估计仿射矩阵
反向映射第二张图
融合重叠区域
保存拼接结果
```

运行：

```bash
python imageProcessing_study/parameter_optimization/Image_stitching/image_stitching.py
```

默认输入：

- `Image_stitching/test_pair/001.png`
- `Image_stitching/test_pair/002.png`

默认输出：

- `Image_stitching/stitched_result.jpg`
- `Image_stitching/matches_visualization.jpg`
- `Image_stitching/matches.csv`

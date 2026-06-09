# ImageProcessing Study

一个以 Python 和 OpenCV 为工具的数字图像处理学习项目。仓库按照学习顺序整理了理论笔记、公式推导、手写算法和处理结果，适合用于复习基础概念与理解常见图像处理算法的实现过程。

项目中的多数练习以“自己实现核心算法、使用 OpenCV 完成图像读写”为目标。目前内容涵盖图像与 ISP 基础、颜色空间转换、直方图处理、图像滤波和 Canny 边缘检测。

## 内容导航

| 章节 | 主要内容 | 笔记与代码 |
| --- | --- | --- |
| 1. 数字图像基础 | 像素矩阵、ISP 流程、RAW/RGB/YUV 域、Gamma 校正 | [学习笔记](1image_processing/1数字图像获取.md) · [Gamma 校正](1image_processing/code/display.py) |
| 2. 颜色空间 | RGB、HSV、Lab、YCbCr，颜色空间正反变换，颜色传递 | [学习笔记](2ColorSpace/2颜色空间转换.md) · [RGB-HSV](2ColorSpace/code/RGB--HSV.py) · [RGB-Lab](2ColorSpace/code/RGB--Lab.py) · [颜色传递](2ColorSpace/colortransfer/colortransfer.py) |
| 3. 图像直方图 | 直方图绘制、直方图均衡化、直方图匹配 | [学习笔记](3histogram/histogram.md) · [代码目录](3histogram/code) |
| 4. 图像滤波 | 方框、均值、高斯、中值和双边滤波 | [学习笔记](4ImageFiltering/filtering.md) · [代码目录](4ImageFiltering/code) |
| 5. 特征提取 | Canny 原理与手写实现；SIFT 学习内容待补充 | [学习笔记](5FeatureExtraction/FeatureExtraction.md) · [手写 Canny](5FeatureExtraction/Canny.py) |

## 已实现算法

- 手写 Gamma 校正查找表与逐像素映射
- RGB 与 HSV 双向转换
- RGB、XYZ 与 Lab 双向转换
- 基于 Ruderman `lαβ` 空间的 Reinhard 颜色传递
- 灰度直方图绘制、均衡化与匹配
- 高斯滤波与双边滤波
- 完整 Canny 边缘检测流程：
  - 灰度化
  - 高斯滤波
  - Sobel 梯度计算
  - 非极大值抑制
  - 双阈值检测与滞后连接

## 效果展示

| 颜色传递 | 直方图均衡化 | Canny 边缘检测 |
| --- | --- | --- |
| ![颜色传递](2ColorSpace/colortransfer/output.jpg) | ![直方图均衡化](3histogram/code/Equalized_Image.jpg) | ![Canny 边缘检测](5FeatureExtraction/bird_canny.jpg) |

## 环境要求

- Python 3
- OpenCV
- NumPy

安装依赖：

```bash
python -m pip install opencv-python numpy
```

## 运行示例

克隆仓库：

```bash
git clone https://github.com/wanyFeng/ImageProcessing_study.git
cd ImageProcessing_study
```

运行手写 Canny 边缘检测：

```bash
python 5FeatureExtraction/Canny.py
```

程序读取 `1image_processing/code/bird.jpg`，并将结果保存为 `5FeatureExtraction/bird_canny.jpg`。

其他练习可以进入对应代码目录后运行，例如：

```bash
cd 3histogram/code
python task1.py
python task2.py
python task3.py
```

> 部分早期练习脚本使用了本机绝对路径。运行这些脚本前，请将输入和输出路径修改为自己电脑上的实际路径。

## 项目结构

```text
ImageProcessing_study/
├── 1image_processing/       # 数字图像与 ISP 基础、Gamma 校正
├── 2ColorSpace/             # 颜色空间转换与颜色传递
├── 3histogram/              # 直方图相关算法
├── 4ImageFiltering/         # 高斯滤波与双边滤波
└── 5FeatureExtraction/      # Canny 边缘检测与特征提取
```

## 学习目标

这个仓库侧重于通过代码理解算法，而不只是调用 OpenCV 的现成处理函数。后续将继续补充特征点检测、图像分割等内容，并逐步统一各示例的路径配置与运行方式。

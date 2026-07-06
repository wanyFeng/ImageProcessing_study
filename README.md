# ImageProcessing_study

这个仓库用于整理图像处理与参数优化相关课程实践代码、笔记和实验结果。

## 目录结构

```text
ImageProcessing_study/
├── Image_foundation/          # 图像处理基础
└── parameter_optimization/    # 建模与参数优化实践
```

## Image_foundation

`Image_foundation` 保存图像处理基础部分的学习内容，主要包括：

- `1image_processing`：数字图像获取、像素矩阵、ISP 基础流程。
- `2ColorSpace`：RGB、HSV、Lab 等颜色空间转换与颜色迁移。
- `3histogram`：直方图统计、均衡化和直方图匹配。
- `4ImageFiltering`：高斯滤波、双边滤波等图像滤波方法。
- `5FeatureExtraction`：Canny 边缘检测、SIFT 特征点提取与匹配。
- `6ImageTransformation`：相似变换、仿射变换、单应变换和插值。

## parameter_optimization

`parameter_optimization` 保存建模与参数优化实践内容，当前包括：

- `Image_stitching`：基于 SIFT 匹配点和最小二乘仿射变换的图像拼接实验。
- `camera_parameter`：相机参数相关学习内容。
- `建模与参数优化实践.pdf`：课程实践资料。

## 运行说明

各实验目录下通常包含对应的 `.py` 代码、`.md` 笔记和输出结果图。运行 Python 代码前请确保已经安装：

```bash
pip install opencv-python numpy
```

部分代码复用了同一仓库前面章节的手写函数，例如 `Image_stitching` 会调用 `Image_foundation/5FeatureExtraction/code` 中的手写 SIFT 特征提取和匹配代码。

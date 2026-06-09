# ImageProcessing Study

一个以 Python 和 OpenCV 为工具的数字图像处理学习项目。仓库按照学习顺序整理了理论笔记、公式推导、手写算法和处理结果，适合用于复习基础概念与理解常见图像处理算法的实现过程。

项目中的多数练习以“自己实现核心算法、使用 OpenCV 完成图像读写”为目标。目前内容涵盖图像与 ISP 基础、颜色空间转换、直方图处理、图像滤波、特征提取与匹配，以及图像几何变换。

## 内容导航

| 章节 | 主要内容 | 笔记与代码 |
| --- | --- | --- |
| 1. 数字图像基础 | 像素矩阵、ISP 流程、RAW/RGB/YUV 域、Gamma 校正 | [学习笔记](1image_processing/1数字图像获取.md) · [Gamma 校正](1image_processing/code/display.py) |
| 2. 颜色空间 | RGB、HSV、Lab、YCbCr，颜色空间正反变换，颜色传递 | [学习笔记](2ColorSpace/2颜色空间转换.md) · [RGB-HSV](2ColorSpace/code/RGB--HSV.py) · [RGB-Lab](2ColorSpace/code/RGB--Lab.py) · [颜色传递](2ColorSpace/colortransfer/colortransfer.py) |
| 3. 图像直方图 | 直方图绘制、直方图均衡化、直方图匹配 | [学习笔记](3histogram/histogram.md) · [代码目录](3histogram/code) |
| 4. 图像滤波 | 方框、均值、高斯、中值和双边滤波 | [学习笔记](4ImageFiltering/filtering.md) · [代码目录](4ImageFiltering/code) |
| 5. 特征提取 | Canny、SIFT 特征提取与特征匹配 | [学习笔记](5FeatureExtraction/FeatureExtraction.md) · [手写 Canny](5FeatureExtraction/code/Canny.py) · [手写 SIFT](5FeatureExtraction/code/SIFT.py) · [SIFT 匹配](5FeatureExtraction/code/SIFTMatch.py) |
| 6. 图像几何变换 | 相似变换、仿射变换、单应变换、逆向映射与双线性插值 | [变换代码](6ImageTransformation/code/ImageTransformation.py) |

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
- SIFT 特征提取与匹配：
  - 高斯与 DoG 尺度空间
  - 26 邻域极值检测
  - 主方向分配与 128 维描述子
  - 最近邻比值筛选与双向一致性检查
- 图像几何变换：
  - 相似变换
  - 仿射变换
  - 单应变换
  - 手写矩阵求逆、逆向映射与双线性插值

## 效果展示

| 颜色传递 | 直方图均衡化 | Canny 边缘检测 |
| --- | --- | --- |
| ![颜色传递](2ColorSpace/colortransfer/output.jpg) | ![直方图均衡化](3histogram/code/Equalized_Image.jpg) | ![Canny 边缘检测](5FeatureExtraction/bird_canny.jpg) |

| SIFT 特征点 | SIFT 特征匹配 |
| --- | --- |
| ![SIFT 特征点](5FeatureExtraction/planet_sift.jpg) | ![SIFT 特征匹配](5FeatureExtraction/work_front_matches.jpg) |

| 相似变换 | 仿射变换 | 单应变换 |
| --- | --- | --- |
| ![相似变换](6ImageTransformation/similarity_result.jpg) | ![仿射变换](6ImageTransformation/affine_result.jpg) | ![单应变换](6ImageTransformation/homography_result.jpg) |

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
python 5FeatureExtraction/code/Canny.py
```

程序读取 `1image_processing/code/bird.jpg`，并将结果保存为 `5FeatureExtraction/bird_canny.jpg`。

运行手写 SIFT 特征提取与匹配：

```bash
python 5FeatureExtraction/code/SIFT.py
python 5FeatureExtraction/code/SIFTMatch.py
```

运行图像几何变换：

```bash
python 6ImageTransformation/code/ImageTransformation.py
```

程序使用 `rain.jpg` 生成相似、仿射和单应变换结果，并在白色画布上展示原图与变换图的位置关系。

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
├── 5FeatureExtraction/      # Canny、SIFT 特征提取与匹配
└── 6ImageTransformation/    # 相似、仿射与单应变换
```

## 学习目标

这个仓库侧重于通过代码理解算法，而不只是调用 OpenCV 的现成处理函数。后续将继续补充图像分割等内容，并逐步统一各示例的路径配置与运行方式。

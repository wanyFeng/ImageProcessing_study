# ImageProcessing_foundation Study

一个使用 Python、NumPy 和 OpenCV 学习数字图像处理的实践仓库。

项目按照从图像基础到特征提取、几何变换的顺序组织，将理论笔记、公式推导、核心算法实现和处理结果放在一起。代码以理解算法原理为目标：OpenCV 主要负责图像读写，许多关键处理步骤由 NumPy 和 Python 手动实现。

## 项目特点

- 理论与代码对应：每章包含学习笔记、示例代码和结果图像
- 注重核心实现：手写颜色空间转换、直方图处理、滤波、Canny、SIFT 和几何变换
- 展示完整流程：从输入图像、算法处理到结果保存
- 适合逐章学习：内容按照基础概念到综合算法的顺序排列

## 内容导航

| 章节 | 主要内容 | 笔记 | 代码 |
| --- | --- | --- | --- |
| 1. 数字图像基础 | 像素矩阵、ISP 流程、RAW/RGB/YUV 域、Gamma 校正 | [数字图像获取](1image_processing/1数字图像获取.md) | [Gamma 校正](1image_processing/code/display.py) |
| 2. 颜色空间 | RGB、HSV、Lab、YCbCr、颜色传递 | [颜色空间转换](2ColorSpace/2颜色空间转换.md) · [颜色传递](2ColorSpace/colortransfer/colortransfer.md) | [RGB-HSV](2ColorSpace/code/RGB--HSV.py) · [RGB-Lab](2ColorSpace/code/RGB--Lab.py) · [颜色传递](2ColorSpace/colortransfer/colortransfer.py) |
| 3. 图像直方图 | 直方图绘制、均衡化、匹配 | [图像直方图](3histogram/histogram.md) | [代码目录](3histogram/code) |
| 4. 图像滤波 | 方框、均值、高斯、中值、双边滤波 | [图像滤波](4ImageFiltering/filtering.md) | [代码目录](4ImageFiltering/code) |
| 5. 特征提取 | Canny、SIFT 特征提取与匹配 | [特征提取](5FeatureExtraction/FeatureExtraction.md) | [Canny](5FeatureExtraction/code/Canny.py) · [SIFT](5FeatureExtraction/code/SIFT.py) · [SIFT 匹配](5FeatureExtraction/code/SIFTMatch.py) |
| 6. 图像几何变换 | 相似、仿射、单应变换，逆向映射，双线性插值 | [图像几何变换](6ImageTransformation/6ImageTransformation.md) | [变换代码](6ImageTransformation/code/ImageTransformation.py) |



## 已实现内容

| 模块 | 实现内容 |
| --- | --- |
| 图像基础 | Gamma 校正查找表、逐像素映射 |
| 颜色空间 | RGB 与 HSV 双向转换、RGB/XYZ/Lab 双向转换 |
| 颜色传递 | 基于 Ruderman `lαβ` 空间的 Reinhard 颜色传递 |
| 直方图 | 灰度直方图绘制、直方图均衡化、直方图匹配 |
| 图像滤波 | 高斯滤波、双边滤波 |
| Canny | 灰度化、高斯滤波、Sobel 梯度、非极大值抑制、双阈值与滞后连接 |
| SIFT | 高斯与 DoG 尺度空间、26 邻域极值检测、主方向分配、128 维描述子、特征匹配 |
| 几何变换 | 相似、仿射、单应变换，逆向映射，双线性插值，自适应输出画布 |

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

## 环境准备

建议使用 Python 3.10 或更高版本，并在虚拟环境中安装依赖：

```bash
git clone https://github.com/wanyFeng/ImageProcessing_study.git
cd ImageProcessing_study

python -m venv .venv
```

Windows PowerShell：

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy opencv-python
```

Linux 或 macOS：

```bash
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy opencv-python
```

## 运行示例

以下命令均从仓库根目录执行：

| 示例 | 运行命令 | 路径说明 | 主要输出目录 |
| --- | --- | --- | --- |
| Gamma 校正 | `python 1image_processing/code/display.py` | 运行前修改脚本中的绝对路径 | `1image_processing/` |
| 颜色传递 | `python 2ColorSpace/colortransfer/colortransfer.py` | 运行前修改脚本中的绝对路径 | `2ColorSpace/colortransfer/` |
| 手写 Canny | `python 5FeatureExtraction/code/Canny.py` | 可直接运行 | `5FeatureExtraction/` |
| 手写 SIFT | `python 5FeatureExtraction/code/SIFT.py` | 可直接运行 | `5FeatureExtraction/` |
| SIFT 特征匹配 | `python 5FeatureExtraction/code/SIFTMatch.py` | 可直接运行 | `5FeatureExtraction/` |
| 图像几何变换 | `python 6ImageTransformation/code/ImageTransformation.py` | 可直接运行 | `6ImageTransformation/` |

直方图示例需要进入代码目录运行，因为脚本使用当前目录读取输入图像：

```bash
cd 3histogram/code
python task1.py
python task2.py
python task3.py
```

图像几何变换示例会自动扩展输出画布，通过逆向映射定位原图坐标，并使用双线性插值计算像素值。源码同时标注了自定义函数以及 `math.floor()`、`math.ceil()`、`math.radians()`、`math.sin()`、`math.cos()` 等库函数的用途。

> 颜色空间转换、颜色传递和部分滤波等早期练习脚本仍使用本机绝对路径。运行前请检查脚本中的输入与输出路径，并根据自己的环境进行修改。

## 项目结构

```text
ImageProcessing_study/
├── 1image_processing/       # 数字图像与 ISP 基础、Gamma 校正
├── 2ColorSpace/             # 颜色空间转换与颜色传递
├── 3histogram/              # 直方图绘制、均衡化与匹配
├── 4ImageFiltering/         # 高斯滤波与双边滤波
├── 5FeatureExtraction/      # Canny、SIFT 特征提取与匹配
├── 6ImageTransformation/    # 相似、仿射与单应变换
├── 图像处理基础.pdf          # 汇总学习笔记
└── README.md
```

每个章节通常包含以下内容：

```text
章节目录/
├── code/                    # 算法实现
├── *.md                     # 理论笔记与公式推导
└── *.jpg / *.png            # 输入图像和处理结果
```

## 推荐学习顺序

1. 从数字图像基础和颜色空间开始，理解像素、通道及图像表示方式。
2. 学习直方图和滤波，掌握像素级统计与邻域运算。
3. 学习 Canny 和 SIFT，理解边缘、关键点及局部特征。
4. 学习几何变换，理解齐次坐标、逆向映射与插值。

## 学习目标

这个仓库侧重于通过代码理解算法，而不只是调用 OpenCV 的现成处理函数。后续将继续补充图像分割等内容，并逐步统一各示例的路径配置、参数设置与运行方式。

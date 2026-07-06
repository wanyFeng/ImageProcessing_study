# Parameter Optimization

本文件夹用于整理“建模与参数优化实践”相关的课程资料、实验代码、笔记和运行结果。

## 目录结构

```text
parameter_optimization/
├── camera_parameter/          # 相机参数学习与实验
├── Image_stitching/           # 图像拼接实验
└── 建模与参数优化实践.pdf       # 课程实践资料
```

## camera_parameter

`camera_parameter` 用于学习相机成像模型和相机参数相关内容，例如内参、外参、坐标系转换、标定模型等。

## Image_stitching

`Image_stitching` 用于完成图像拼接实验。当前实现内容包括：

- 复用前面手写的 SIFT 特征点提取与匹配代码。
- 根据匹配点构造仿射变换方程。
- 使用最小二乘法求解仿射变换参数。
- 通过反向映射和双线性插值完成图像变换。
- 对重叠区域进行融合，并保存拼接结果。

进入该目录后可以查看对应 README、代码、测试图片和输出结果。

## 运行环境

主要 Python 依赖：

```bash
pip install opencv-python numpy
```

运行具体实验时，请进入对应子目录查看说明文档，或在仓库根目录执行相应脚本。

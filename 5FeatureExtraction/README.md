# 特征提取

本目录用于学习和实验 Canny 边缘检测、SIFT 特征点检测及 SIFT 特征匹配。

## 目录内容

- `FeatureExtraction.md`：Canny 和 SIFT 理论笔记。
- `code/`：三种算法的手写实现。
- `planet.jpg`：SIFT 特征点检测输入。
- `work_front.jpg`、`work_left.jpg`：SIFT 匹配输入。
- `bird_canny.jpg`、`planet_sift.jpg`、`work_*_matches.jpg`：结果图片。
- `sift_matches.csv`：匹配点坐标和距离报告。

## 使用方法

先阅读理论笔记，再按照 `code/README.md` 运行脚本。脚本会自动从相对位置读取输入并把结果保存到本目录。

运行代码前需要安装：

```powershell
python -m pip install numpy opencv-python
```


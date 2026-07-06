# 图像几何变换

本目录用于学习相似变换、仿射变换和单应性变换，并通过逆向映射与双线性插值生成结果。

## 目录内容

- `6ImageTransformation.md`：几何变换理论和矩阵推导。
- `code/`：几何变换实现。
- `rain.jpg`：输入图片。
- `similarity_result.jpg`、`affine_result.jpg`、`homography_result.jpg`：原图与变换结果的对比图。

## 使用方法

先阅读理论笔记，再按照 `code/README.md` 运行实验。代码会自动扩展输出画布，避免变换后的图像被裁剪。

运行代码前需要安装：

```powershell
python -m pip install numpy opencv-python
```


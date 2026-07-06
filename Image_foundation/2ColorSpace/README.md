# 颜色空间

本目录用于学习 RGB、HSV、Lab、YCbCr 等颜色空间，以及不同颜色空间之间的转换和颜色传递。

## 目录内容

- `2颜色空间转换.md`：颜色空间理论笔记。
- `2颜色空间转换.html`：笔记的 HTML 版本。
- `code/`：手写 RGB-HSV 和 RGB-Lab 双向转换。
- `colortransfer/`：Reinhard 颜色传递实验。
- `image*.png`：笔记中的示意图。

## 使用方法

1. 阅读 `2颜色空间转换.md` 理解各颜色空间的含义。
2. 按照 `code/README.md` 运行颜色空间转换实验。
3. 按照 `colortransfer/README.md` 运行颜色传递实验。

运行代码前需要安装：

```powershell
python -m pip install numpy opencv-python
```


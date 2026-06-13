# Reinhard 颜色传递

本目录在 Ruderman `lαβ` 颜色空间中匹配图像各通道的均值和标准差，将目标图像的色彩风格传递给源图像。

## 文件说明

- `colortransfer.md`：算法原理和结果说明。
- `colortransfer.py`：颜色传递实现与运行入口。
- `usagi.jpg`：源图像，保留其内容结构。
- `xiaoba.jpg`：目标图像，提供色彩风格。
- `output.jpg`：颜色传递结果，重新运行后会被覆盖。

## 运行方法

脚本已经使用本仓库的固定绝对路径。在仓库位于 `D:\research\image_foundation` 时，可直接执行：

```powershell
python 2ColorSpace/colortransfer/colortransfer.py
```

如需处理其他图片，请修改脚本末尾的 `src_file`、`tgt_file` 和输出路径。若仓库移动到其他位置，也需要同步修改这些路径。


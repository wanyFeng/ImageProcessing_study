# 图像几何变换
不改变像素值，改变像素所在的位置。即像素的亮度和色彩不发生变化。
### 一.相似变换
- 缩放
  - 各向同性缩放 
  
```math
\begin{cases}
x' = s \cdot x \\
y' = s \cdot y
\end{cases}
```

对应的齐次矩阵：

```math
M=
\begin{bmatrix}
s & 0 & 0\\
0 & s & 0\\
0 & 0 & 1
\end{bmatrix}
```

- 各向异性缩放

允许不同方向的缩放系数，常用于特殊变形处理，对应齐次矩阵：

```math
M =
\begin{bmatrix}
s_x & 0 & 0 \\
0 & s_y & 0 \\
0 & 0 & 1
\end{bmatrix}
```

- 缩小算法
  - 等间隔采样缩小法：从原图像中等间隔的选取像素点构建缩小后的图像
  - 基于均值的图像缩小方法
- 放大
  - 算法
    - 像素复制法
    - 插值：实现图像的平滑放大
      - 最近领域插值：找到原图像中最近四个整数像素点，将最近的作为像素值，没考虑周围像素的灰度值
      - 双线性插值：依旧考虑原图上四个像素点，先在x方向上做插值，再在y方向上做插值  
- 平移
- 旋转
  - 绕原点逆时针旋转 $`\theta`$ 的变换矩阵
  
```math
M=
\begin{bmatrix}
\cos\theta & -\sin\theta & 0\\
\sin\theta & \cos\theta & 0\\
0 & 0 & 1
\end{bmatrix}
```

- 绕任意点旋转
  
```math
\begin{bmatrix}
x'\\
y'\\
1
\end{bmatrix}
=
\begin{bmatrix}
\cos\theta & -\sin\theta & (1-\cos\theta)c_x+\sin\theta c_y\\
\sin\theta & \cos\theta & -\sin\theta c_x+(1-\cos\theta)c_y\\
0 & 0 & 1
\end{bmatrix}
\begin{bmatrix}
x\\
y\\
1
\end{bmatrix}
```
  
- 旋转形成空穴
  - 插值填充法：临近插值法、均值插值法
### 二.仿射变换
- 仿射矩阵
  
```math
M=
\begin{bmatrix}
a & b & t_x \\
c & d & t_y
\end{bmatrix}
```

| 参数 | 作用 | 数学意义 |
|------|------|----------|
| a, d | 控制缩放 | 大于1放大，小于1缩小 |
| b, c | 控制旋转与剪切 | 产生倾斜效果 |
| $`t_x,t_y`$ | 控制平移 | 水平或垂直移动图像 |
### 三.单应变换（透视变换）
- 模拟真实世界中人眼或照相机的成像效果，达到近大远小

```math
\begin{aligned}
X &= \frac{f \cdot x}{z} \\
Y &= \frac{f \cdot y}{z}
\end{aligned}
```

- $`f`$ 是焦距（观察者到投影平面的距离）
- $`(x,y,z)`$ 是三维空间中物体的坐标
- $`(X,Y)`$ 是投影到二维平面的坐标


### 四.图像错切
- 保持各点的某一坐标值不变，而另一坐标值进行线性变换的过程

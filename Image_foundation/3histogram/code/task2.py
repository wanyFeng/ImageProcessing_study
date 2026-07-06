import cv2
import numpy as np
def histogram_equalization(gray_img):
    height,width=gray_img.shape
    total_pixels=height*width
    hist=[0]*256
    # 计算灰度直方图
    for i in range(height):
        for j in range(width):
            hist[gray_img[i,j]]+=1
    # 计算累计分布函数
    cdf=[0]*256
    cumulative_sum=0
    for i in range(256):
        cumulative_sum+=hist[i]
        cdf[i]=cumulative_sum/total_pixels
    #建立灰度映射表
    references=[0]*256
    for i in range(256):
        references[i]=round(cdf[i]*255)
    #生成均衡化后的图像
    equalized_img=np.zeros_like(gray_img)
    for i in range(height):
        for j in range(width):
            equalized_img[i,j]=references[gray_img[i,j]]
    return equalized_img

if __name__=="__main__":
    #读取图像
    gray_img=cv2.imread('gray_red.jpg', cv2.IMREAD_UNCHANGED)
    #进行直方图均衡化
    equalized_img=histogram_equalization(gray_img)
    #显示结果
    cv2.imwrite('Equalized_Image.jpg',equalized_img)

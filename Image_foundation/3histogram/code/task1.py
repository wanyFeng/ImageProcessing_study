import cv2
import numpy as np
def calculate_histogram(gray_img):
    #手动计算灰度直方图
    hist=[0]*256
    height,width=gray_img.shape
    for i in range(height):
        for j in range(width):
            pixel_val=gray_img[i,j]
            hist[pixel_val]+=1
    return hist

def draw_histogram(hist,canvas_width=512,canvas_height=400):
    #手动绘制直方图
    canvas=np.zeros((canvas_height,canvas_width),dtype=np.uint8)
    bin_width=canvas_width//256
    max_val=max(hist)
    for i in range(256):
        bin_height=int((hist[i]/max_val)*(canvas_height-20))  #缩放到画布高度
        x_start=i*bin_width
        x_end=x_start+bin_width
        canvas[canvas_height-bin_height-10:canvas_height-10,x_start:x_end]=255  #绘制白色柱状图
    return canvas

if __name__=="__main__":
    #读取图像
    gray_img=cv2.imread('gray_red.jpg', cv2.IMREAD_UNCHANGED)
    #计算直方图
    hist=calculate_histogram(gray_img)
    #绘制直方图
    hist_img=draw_histogram(hist)
    #显示结果
    cv2.imwrite('Histogram.jpg',hist_img)
    cv2.destroyAllWindows()
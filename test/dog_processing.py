import cv2 as cv
import numpy as np
from icecream import ic
from matplotlib import pyplot as plt

def get_dog(image):
    ksize = 35
    F = 1.1
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    k1_1d = cv.getGaussianKernel(35, 12)
    k1 = np.dot(k1_1d, k1_1d.T)
    
    k2_1d = cv.getGaussianKernel(35, 12*F)
    k2 = np.dot(k2_1d, k2_1d.T)
    
    k = k2 - k1
    
    dog = cv.filter2D(src=gray, ddepth=-1, kernel=k)
    
    dog[dog < 1] = 0
    dog[dog > 1] = 255
    
    # high_sigma = cv.filter2D(src=gray, ddepth=-1, kernel=k2)
    
    # print(k1[0:9, 0:9])
    
    # low_sigma = cv.GaussianBlur(gray, (ksize, ksize), 12)
    # high_sigma = cv.GaussianBlur(gray, (ksize, ksize), 12*F)
    # dog = high_sigma - low_sigma
    
    # Calculate the DoG by subtracting
    return dog

image = cv.imread('/Applications/Matlab_Toolboxes/test/MMI/sessions/OP852/bids/anat/headscan/model_mesh.jpg')
dog = get_dog(image)


# do canny edge detection on dog
# edges = cv.Canny(dog, 10, 5)



rows = dog.shape[0]
circles = cv.HoughCircles(dog, cv.HOUGH_GRADIENT, 1, 100,
                            param1=5, param2=11,
                            minRadius=10, maxRadius=28)

ic(circles)

# src = cv.cvtColor(dog, cv.COLOR_GRAY2BGR)
# src = image
# if circles is not None:
#     circles = np.uint16(np.around(circles))
#     for i in circles[0, :]:
#         center = (i[0], i[1])
#         # circle center
#         cv.circle(src, center, 1, (0, 100, 100), 3)
#         # circle outline
#         radius = i[2]
#         cv.circle(src, center, radius, (255, 0, 255), 3)
    
    
# cv.imshow("detected circles", src)
# cv.waitKey(0)

ic(image.shape)

# display the image in black and white
plt.imshow(image, cmap='gray')
plt.show()
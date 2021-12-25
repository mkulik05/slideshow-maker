import cv2
import os
import sys

def rescale(img, scale_percent):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    return resized


transform_to = input("Crop to: ").split(":")
kk = int(transform_to[0]) / int(transform_to[1])

step = 30

max_height = 1080
imgs = input("Path to your photos folder: ")
where_to_safe = input("Where to save results: ")
print("Loading ...")

photos = os.listdir(imgs)
for path in photos:
    name = path
    img = cv2.imread(imgs + path)

    a, b, c, d = (round((img.shape[0] - img.shape[1] / kk) /2), img.shape[0] -
                  round((img.shape[0] - img.shape[1] / kk) / 2), 0, img.shape[1])
    if img.shape[0] > max_height:
        percents = round(100 / (img.shape[0]/max_height) / 1.5)
    else:
        percents = 100
    while True:
        img2 = cv2.rectangle(img.copy(), (c, a), (d, b), (255, 255, 0), 3)
        cv2.imshow("result", rescale(img2, percents))
        k = cv2.waitKey()
        if k == ord("e"):
            cv2.imwrite("{}/{}".format(where_to_safe, name),
                        img[int(a):int(b), int(c):int(d)])
            print("Saving {}".format(name))
            break
        elif k == ord("q"):
            cv2.imwrite("{}/{}".format(where_to_safe, name),
                        img)
            print("Saving original {}".format(name))
            break
        elif k == ord("s"):
            if b + step < img.shape[0] - 1:
                a += step
                b += step
        elif k == ord("w"):
            if a - step > 0:
                a -= step
                b -= step
        elif k == ord("d"):
            step += 2
        elif k == ord("a"):
            if step - 2 > 0:
                step -= 2
        elif k == 27:
            print("Finish up")
            sys.exit()
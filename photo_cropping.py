import cv2
import numpy as np
import os
import sys

transform_to = input("Crop to: (ex. 16:9) ").split(":")
ratio = int(transform_to[0]) / int(transform_to[1])

step = 30

max_height = 1080
imgs = input("Path to your photos folder: ") + "/"
where_to_safe = input("Where to save results: ")
print("Loading ...")

FPS = 30
seconds = 5
framesForImg = FPS * seconds


video = cv2.VideoWriter('main.mkv',cv2.VideoWriter_fourcc(*'DIVX'), FPS, (1280, 720))

def getPoint(frame, sPoint, fPoint):
  global framesForImg
  return sPoint + (fPoint - sPoint) * frame // framesForImg

def rescale(img, scale_percent):
  width = int(img.shape[1] * scale_percent / 100)
  height = int(img.shape[0] * scale_percent / 100)
  dim = (width, height)
  resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
  return resized

def animate(img, coords, mode="preview", writer=None):
  global framesForImg, FPS
  for i in range(framesForImg):
    x1 = getPoint(i, coords[0][0][0], coords[1][0][0])
    y1 = getPoint(i, coords[0][0][1], coords[1][0][1])
    x2 = getPoint(i, coords[0][1][0], coords[1][1][0])
    y2 = getPoint(i, coords[0][1][1], coords[1][1][1])
    if mode == "preview":
      cv2.imshow("Preview", cv2.resize(img.copy()[y1:y2, x1:x2], (1280, 720)))
      k = cv2.waitKey(int(1000/FPS)) 
      if k == 27:
        cv2.destroyWindow("Preview")
        return ord("n")
    else:
      writer.write(cv2.resize(img.copy()[y1:y2, x1:x2], (1280, 720)))
  if mode == "preview":  
    k = cv2.waitKey()
    cv2.destroyWindow("Preview")
    return k
  else:
    return None

def addBlackBkg(sourceImg, size):
  res = np.zeros(size[::-1], dtype=np.uint8)
  res = cv2.merge([res, res, res])
  yS, xS = sourceImg.shape[:2]
  dX, dY = (size[0] - xS) // 2, (size[1] - yS) // 2
  print(yS, xS, dY, dX, size)
  if size[0] % 2 != 2:
    shift = 1
  else:
    shift = 0
  print(size[1], (size[0] - shift - dX),  dX, res.shape,  res[dX:(size[0] - shift - dX), 0:size[1]].shape )
  cv2.waitKey()
  res[0:size[1], dX:(size[0] - shift - dX)] = sourceImg
  return res

photos = os.listdir(imgs)
rectCoords = [0,0,0,0]
continue_without_asking = False
# horizontedImg = True
for path in photos:
  coords = []
  print("photo ", path)
  name = path
  img = cv2.imread(imgs + path)
  if not continue_without_asking:
    # Img is vertical
    if img.shape[0] > img.shape[1]:
      img = addBlackBkg(img, (int(img.shape[0] * ratio), img.shape[0]))

    yB, yT, xB, xT = (round((img.shape[0] - img.shape[1] / ratio) / 2), img.shape[0] -
                      round((img.shape[0] - img.shape[1] / ratio) / 2), 0, img.shape[1])
  

    if img.shape[0] > max_height:
      percents = round(100 / (img.shape[0] / max_height) / 1.5)
    else:
      percents = 100
    while len(coords) < 2:
      imgDraft = cv2.rectangle(img.copy(), (xB, yB), (xT, yT), (255, 255, 0), 3)

      cv2.imshow("result", rescale(imgDraft, percents))
      k = cv2.waitKey()
      if k == ord("e"):
        coords.append([(xB, yB), (xT, yT)])
        
      elif k == ord("s"):
        if yT + step <= img.shape[0] - 1:
          yB += step
          yT += step
      elif k == ord("w"):
        if yB - step >= 0:
          yB -= step
          yT -= step
      elif k == ord(">"):
        step += 2
      elif k == ord("<"):
        if step - 2 >= 0:
            step -= 2
      elif k == ord("c"):
        continue_without_asking = True
        rectCoords = [yB, yT, xB, xT]
        cv2.imwrite("{}/{}".format(where_to_safe, name),
                    img[int(yB):int(yT), int(xB):int(xT)])
        cv2.destroyAllWindows()
        break
      elif k == ord("a"):
        if xB - step >= 0:
            xB -= step
            xT -= step
      elif k == ord("d"):
        if xT + step <= img.shape[1] - 1:
            xB += step
            xT += step
      elif k == ord("z"):
        if xT - step >= 0:
            xT -= step
            yB, yT, xB = (round((img.shape[0] - xT / ratio) /2), img.shape[0] -
                  round((img.shape[0] - xT / ratio) / 2), 0)
      elif k == ord("x"):
        if xT + step <= img.shape[1] - 1:
            xT += step
            yB, yT, xB = (round((img.shape[0] - xT / ratio) /2), img.shape[0] -
                round((img.shape[0] - xT / ratio) / 2), 0)
          
      elif k == 27:
        print("Finished up")
        sys.exit()
      if len(coords) == 2:
        k = animate(img, coords, "preview")
        if k != ord("y"):
          coords = []
        else:
          animate(img, coords, "render", video)
  else:
    yB,yT,xB,xT = rectCoords
    cv2.imwrite("{}/{}".format(where_to_safe, name),
                                img[int(yB):int(yT), int(xB):int(xT)])

video.release()

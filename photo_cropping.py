import cv2
import numpy as np
import os
import sys
import json

inp = input("Do you want to import backup file? (y/n)")
if inp == "y":
  with open("data.json") as f:
    data = json.load(f)
else:
  data = {}
quality = (1920, 1080)
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
  global framesForImg, FPS, quality
  for i in range(framesForImg):
    x1 = getPoint(i, coords[0][0][0], coords[1][0][0])
    y1 = getPoint(i, coords[0][0][1], coords[1][0][1])
    x2 = getPoint(i, coords[0][1][0], coords[1][1][0])
    y2 = getPoint(i, coords[0][1][1], coords[1][1][1])
    if mode == "preview":
      cv2.imshow("Preview", cv2.resize(img.copy()[y1:y2, x1:x2], quality))
      k = cv2.waitKey(int(1000/FPS)) 
      if k == 27:
        cv2.destroyWindow("Preview")
        return ord("n")
      elif k == ord("y"):
        cv2.destroyWindow("Preview")
        return k
    else:
      writer.write(cv2.resize(img.copy()[y1:y2, x1:x2], quality))
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

def getfiles(dirpath):
    a = [s for s in os.listdir(dirpath)
         if os.path.isfile(os.path.join(dirpath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)))
    return a

photos = getfiles(imgs)
print(photos)
rectCoords = [0,0,0,0]
continue_without_asking = False


# horizontedImg = Tru

for path in photos:
  if path not in data.keys():
    coords = []
    print("photo ", path)
    name = path
    img = cv2.imread(imgs + path)
  
    # Img is vertical
    if img.shape[0] > img.shape[1]:
      img = addBlackBkg(img, (int(img.shape[0] * ratio), img.shape[0]))

    # yB, yT, xB, xT = (round((img.shape[0] - img.shape[1] / ratio) / 2), img.shape[0] -
    #                   round((img.shape[0] - img.shape[1] / ratio) / 2), 0, img.shape[1])
    xB, yB = (0, 0)
    if round(img.shape[1] / ratio) > img.shape[0]:
      w, h =  (
          round(img.shape[0] * ratio),
          img.shape[0] 
        )
    else:
      w, h =  (
          img.shape[1], 
          round(img.shape[1] / ratio), 
        )
  

    if img.shape[0] > max_height:
      percents = round(100 / (img.shape[0] / max_height) / 1.5)
    else:
      percents = 100
    while len(coords) < 2:
      imgDraft = cv2.rectangle(img.copy(), (xB, yB), (xB + w, yB + h), (255, 255, 0), 3)

      cv2.imshow("Result", rescale(imgDraft, percents))
      k = cv2.waitKey()
      if k == ord("e"):
        print("> Keyframe saved")
        coords.append([(xB, yB), (xB + w, yB + h)])
        
      elif k == ord("s"):
        if yB + h + step <= img.shape[0] - 1:
          yB += step
      elif k == ord("w"):
        if yB - step >= 0:
          yB -= step
        else:
          yB = 0
      elif k == ord(">"):
        step += 2
      elif k == ord("<"):
        if step - 2 >= 0:
          step -= 2
      elif k == ord("a"):
        if xB - step >= 0:
          xB -= step
        else:
          xB = 0
      elif k == ord("d"):
        if xB + w + step <= img.shape[1] - 1:
          xB += step
      elif k == ord("z"):
        if w - step > 0 and h - step > 0:
          w -= round(step * ratio)
          h -= step

            
      elif k == ord("x"):
        if xB + w + step < img.shape[1] and yB + h + step < img.shape[0]:
          w += round(step * ratio)
          h += step
          
      elif k == 27:
        d = json.dumps(data)
        with open('data.json', 'w') as f:
          f.write(d)
        print("> Data is backed up\n   Goodbye")
        sys.exit()
      if len(coords) == 2:
        k = animate(img, coords, "preview")
        if k != ord("y"):
          coords = []
        else:
          data[path] = coords
  
d = json.dumps(data)
with open('data.json', 'w') as f:
  f.write(d)
print("> Data is backed up")
print("> Started video creation")
print(data)
video = cv2.VideoWriter('main.mkv',cv2.VideoWriter_fourcc(*'DIVX'), FPS, quality)
for i in range(len(photos)):
  photo = photos[i]
  coords = data[photo]
  img = cv2.imread(imgs + photo)
  if img.shape[0] > img.shape[1]:
    img = addBlackBkg(img, (int(img.shape[0] * ratio), img.shape[0])) 
  animate(img, coords, "render", video)
  print("\rProcessed: {}/".format(i + 1, len(photos)), end="") 
print("> Done")
video.release()

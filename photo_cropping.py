import cv2
import numpy as np
import os
import sys
import json
from screeninfo import get_monitors


FPS = 30
seconds = 5
framesForImg = FPS * seconds
backupFile = "data.json"
outputFile = "main2.mkv"
step = 30
fadeDur = 0.3
sortByDate = False

displayQuality = (1280, 720)
for m in get_monitors():
  if m.is_primary:
    displayQuality = (m.width, m.height)


def rescale(img, scale_percent):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    return resized

inp = input("Do you want to import backup file? (y/n): ").strip()
if inp == "y":
  if os.path.exists(backupFile):
    with open(backupFile) as f:
      data = json.load(f)
    print("Loaded backup file: ", backupFile)
  else:
    print("Error while loading backup file: Path does not exist")
    data = {'size': [], 'keyframes': {}}
else:
  data = {'size': [], 'keyframes': {}}

if len(data['size']) != 2:
  while True:
    transform2res = input("Crop to resolution: (ex. 1920x1080) ").strip()
    if 'x' in transform2res:
      transform2res = transform2res.split('x')
      if len(transform2res) == 2:
        try:
          transform2res = [int(x) for x in transform2res]
          break
        except:
          print("Incorrect image size. Dimensions should be splitted by 'x' (f.e. 1920x1080)")
      else:
        print("Incorrect image size. Dimensions should be splitted by 'x' (f.e. 1920x1080)")
    else:
      print("Incorrect image size. Dimensions should be splitted by 'x' (f.e. 1920x1080)")
  data['size'] = transform2res
else:
  transform2res = data['size']

quality = transform2res
ratio = int(transform2res[0]) / int(transform2res[1])

while True:
  imgs = input("Path to your photos folder: ").strip() + "/"
  if os.path.exists(imgs):
    break
  else:
    print("Path you entered does not exist")

print("Loading ...")

def getPoint(frame, sPoint, fPoint):
  global framesForImg
  return sPoint + (fPoint - sPoint) * frame // framesForImg
# Animate image with 2 keyframes
def animate(img, coords, mode="preview", writer=None):
  global framesForImg, FPS, quality
  for i in range(framesForImg):
    x1 = getPoint(i, coords[0][0][0], coords[1][0][0])
    y1 = getPoint(i, coords[0][0][1], coords[1][0][1])
    x2 = getPoint(i, coords[0][1][0], coords[1][1][0])
    y2 = getPoint(i, coords[0][1][1], coords[1][1][1])
    if mode == "preview":
      cv2.imshow("Preview", cv2.resize(img.copy()[y1:y2, x1:x2], (round(displayQuality[0] / 1.5), round(displayQuality[1] / 1.5))))
      k = cv2.waitKey(int(1000/FPS)) 
      if k == 27:
        cv2.destroyWindow("Preview")
        return ord("n")
      elif k == ord("y"):
        cv2.destroyWindow("Preview")
        return k
    else:
      frame = cv2.resize(img.copy()[y1:y2, x1:x2], quality)
      fadeInStop = FPS * fadeDur
      fadeOutStart = framesForImg - FPS * fadeDur
      if i < fadeInStop:
        frame = changeBrightness(frame, round(i / (FPS * fadeDur) * 100))
      if i > fadeOutStart:
        frame = changeBrightness(frame, round((framesForImg - i) / fadeInStop * 100))
      writer.write(frame)
  if mode == "preview":  
    k = cv2.waitKey()
    cv2.destroyWindow("Preview")
    return k
  else:
    return None

# Add black backgroung to image
def addBlackBkg(sourceImg, size):
  res = np.zeros(size[::-1], dtype=np.uint8)
  res = cv2.merge([res, res, res])
  yS, xS = sourceImg.shape[:2]
  dX, dY = (size[0] - xS) // 2, (size[1] - yS) // 2
  if (res.shape[1] - sourceImg.shape[1]) % 2 != 0:
    shiftX = 1
  else:
    shiftX = 0
  if (res.shape[0] - sourceImg.shape[0]) % 2 != 0:
    shiftY = 1
  else:
    shiftY = 0
  res[dY:((size[1] - shiftY - dY)), dX:(size[0] - shiftX - dX)] = sourceImg
  return res

def changeBrightness(img, br):
  return np.round(img * (br / 100)).astype(np.uint8)

# Get list of files in folder, sordet by modification date
def getfiles(dirpath):
    a = [s for s in os.listdir(dirpath)
         if os.path.isfile(os.path.join(dirpath, s))]
    a.sort(key=lambda s: os.path.getmtime(os.path.join(dirpath, s)))
    return a

if sortByDate:
  allFiles = getfiles(imgs)
else:
  allFiles = os.listdir(imgs)
  allFiles.sort()
photos = []
imgTypes = ['jpg', 'png', 'jpeg']
for file in allFiles:
  if file.split('.')[1] in imgTypes:
    photos.append(file)

if len(photos) > 0:
  print("Found this photos: \n", photos)
else:
  print("Selected directory does not contain any images of types: ", ', '.join(imgTypes))

rectCoords = [0,0,0,0]
for path in photos:

  if path not in data['keyframes'].keys():
    coords = []
    print("Current photo: ", path)
    name = path
    img = cv2.imread(imgs + path)
  
    # Img is vertical, addind black lines
    if img.shape[0] > img.shape[1]:
      img = addBlackBkg(img, (int(img.shape[0] * ratio), img.shape[0]))

    xB, yB = (0, 0)
    # Calculating rect size, depends on source photo ratio
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

    while len(coords) < 2:
      imgDraft = cv2.rectangle(img.copy(), (xB, yB), (xB + w, yB + h), (255, 255, 0), 3)

      if img.shape[0] > displayQuality[1]:
          percents = round(100 / (img.shape[0]/displayQuality[1]) / 1.5)
      else:
          percents = 100
      cv2.imshow("Result", rescale(imgDraft, percents))
      k = cv2.waitKey()

      # Save keyframe
      if k == ord("e"):
        print("> Keyframe saved")
        coords.append([(xB, yB), (xB + w, yB + h)])
        
      # Shift to bottom
      elif k == ord("s"):
        if yB + h + step <= img.shape[0] - 1:
          yB += step
      
      # Shift to top
      elif k == ord("w"):
        if yB - step >= 0:
          yB -= step
        else:
          yB = 0

      elif k == ord("r"):
        xB, yB = 0, 0

      # Shift to the left
      elif k == ord("a"):
        if xB - step >= 0:
          xB -= step
        else:
          xB = 0
      
      # Shift to the right
      elif k == ord("d"):
        if xB + w + step <= img.shape[1] - 1:
          xB += step

      # Vertical centering
      elif k == ord("f"):
        Ysize, Xsize = img.shape[:2]
        yB = Ysize // 2 - h // 2

      # Horizontal centering
      elif k == ord("c"):
        Ysize, Xsize = img.shape[:2]
        xB = Xsize // 2 - w // 2

      # Inc step
      elif k == ord("m"):
        step += 5

      # Dec step
      elif k == ord("n"):
        if step - 5 >= 0:
          step -= 5

      # Decreaze size of selection
      elif k == ord("z"):
        if w - step > 0 and h - step > 0:
          w -= round(step * ratio)
          h -= step

      # Increase size of selection
      elif k == ord("x"):
        if not(xB + w + step < img.shape[1] and yB + h + step < img.shape[0]):
          if len(coords) >= 1:
            print("Rescaling is not allowed after first keyframe created")
          else:
            if not (xB + w + step < img.shape[1]):
              img = addBlackBkg(img, (xB + w + step, img.shape[0]))
            if not (yB + h + step < img.shape[0]):
              img = addBlackBkg(img, (img.shape[1], yB + h + step))
            w += round(step * ratio)
            h += step
        else:
          w += round(step * ratio)
          h += step
          
      # Stop program
      elif k == 27:
        d = json.dumps(data)
        with open(backupFile, 'w') as f:
          f.write(d)
        print("> Data is backed up\n   Goodbye")
        sys.exit()

      # Check are there enough keyframes for animation or not
      if len(coords) >= 2:
        k = animate(img, coords, "preview")
        if k != ord("y"):
          print("Deleted keyframes")
          coords = []
        else:
          print("All keyframes were saved")
          data["keyframes"][path] = {
            "coords": coords,
            "imgSize": img.shape[:2]
          }

if len(photos) > 0: 
  d = json.dumps(data)
  with open(backupFile, 'w') as f:
    f.write(d)
  print("> Data is backed up")
  print("> Started video creation")
  video = cv2.VideoWriter(outputFile,cv2.VideoWriter_fourcc(*'DIVX'), FPS, quality)

# Starting render
for i in range(len(photos)):
  # print(i)
  photo = photos[i]
  coords = data["keyframes"][photo]["coords"]
  correctImgSize = data["keyframes"][photo]["imgSize"][::-1]
  img = cv2.imread(imgs + photo)
  if img.shape[0] > img.shape[1]:
    img = addBlackBkg(img, (int(img.shape[0] * ratio), img.shape[0]))
  if img.shape[:2] != correctImgSize:
    img = addBlackBkg(img, correctImgSize)

  animate(img, coords, "render", video)
  print("\rProcessed: {}/{}".format(i + 1, len(photos)), end="") 
if len(photos) > 0: 
  print("\n> Done\nResult is saved to: ", outputFile)

video.release()

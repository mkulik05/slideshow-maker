import cv2
import numpy as np
import os
import sys
import json


def getPoint(frame, sPoint, fPoint, framesForImg):
  return sPoint + (fPoint - sPoint) * frame // framesForImg

def normalize_coords(coords):
	l, b, r, t = coords
	new_coords = [l, b, r, t]
	if l > r:
		new_coords[0] = r
		new_coords[2] = l
	if b > t:
		new_coords[1] = t
		new_coords[3] = b
	return new_coords

# TODO fix bug
def addBlackBkg(sourceImg, size):
	res = np.zeros((size[1], size[0], 3), dtype=np.uint8)
	yS, xS = sourceImg.shape[:2]
	dX = (size[0] - xS) // 2
	dY = (size[1] - yS) // 2
	shiftX = 1 if (size[0] - xS) % 2 != 0 else 0
	shiftY = 1 if (size[1] - yS) % 2 != 0 else 0
	res[dY : size[1] - dY - shiftY, dX : size[0] - dX - shiftX] = sourceImg
	return res

def rescale(img, scale_percent):
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
    return resized

def scale_rect_based_on_center(rect, scale_factor, center):
    cx, cy = center
    l, b, r, t = rect

    new_l = cx + (l - cx) * scale_factor
    new_r = cx + (r - cx) * scale_factor
    new_b = cy + (b - cy) * scale_factor
    new_t = cy + (t - cy) * scale_factor

    return np.array([new_l, new_b, new_r, new_t])

def animate_preview(frames_info, img_path):
	try:
		cv2.destroyWindow("Preview")
	except:
		print(1)

	fps = 30
	displayQuality = [960, 540] 
	secondsForFrame = 5
	
	img = cv2.imread(img_path)
	
	frame1 = frames_info["frames"][0]
	frame2 = frames_info["frames"][1]
	rect1 = np.array(normalize_coords(frame1["rect_specs"]))
	rect2 = np.array(normalize_coords(frame2["rect_specs"]))

	print(frame1, frame2)
	print(rect1, rect2)
	print(frame1["pixmap_size"])
	print(img.shape)
	print(fps * secondsForFrame)

	if frame1["scale"] >= frame2["scale"]:
		scale_factor = frame1["scale"] / frame2["scale"]
		center = ((rect2[0] + rect2[2]) / 2, (rect2[1] + rect2[3]) / 2)
		rect2 = scale_rect_based_on_center(rect2, scale_factor, center)
		frame2["scale"] = frame1["scale"]
	else:
		scale_factor = frame2["scale"] / frame1["scale"]
		center = ((rect1[0] + rect1[2]) / 2, (rect1[1] + rect1[3]) / 2)
		rect1 = scale_rect_based_on_center(rect1, scale_factor, center)
		frame1["scale"] = frame2["scale"]
	
	img = rescale(img, frame1["scale"] * 100)

	print(frame1, frame2)
	print(rect1, rect2)
	print(frame1["pixmap_size"])
	print(img.shape)
	print(fps * secondsForFrame)
	img = addBlackBkg(img, [frame1["pixmap_size"][0], frame1["pixmap_size"][1]])

	# if frame1["pixmap_size"][0] >= frame2["pixmap_size"][0]:
	# 	delta = frame1["pixmap_size"][0] - frame2["pixmap_size"][0]
	# 	rect2 += int(delta / 2)
	# 	frame2["pixmap_size"][0] = frame1["pixmap_size"][0]
	# else:
	# 	delta = frame2["pixmap_size"][0] - frame1["pixmap_size"][0]
	# 	rect1 += int(delta / 2)
	# 	frame1["pixmap_size"][0] = frame2["pixmap_size"][0]

	# l, b, r, t = coords
	for i in range(fps * secondsForFrame):
		x1 = int(getPoint(i, rect1[0], rect2[0], fps * secondsForFrame))
		y1 = int(getPoint(i, rect1[1], rect2[1], fps * secondsForFrame))
		x2 = int(getPoint(i, rect1[2], rect2[2], fps * secondsForFrame))
		y2 = int(getPoint(i, rect1[3], rect2[3], fps * secondsForFrame))
		
		x1, y1, x2, y2 = normalize_coords([x1, y1, x2, y2])
		print(x1, x2, y1, y2)		
		print(rect1[0], rect2[0])
		print(rect1[1], rect2[1])
		print(rect1[2], rect2[2])
		print(rect1[3], rect2[3])
		cv2.imshow(
			"Preview",
			cv2.resize(
				img.copy()[y1:y2, x1:x2],
				(round(displayQuality[0] / 1.5), round(displayQuality[1] / 1.5)),
			),
		)
		k = cv2.waitKey(int(1000 / fps))
		if k == 27:
			try:
				cv2.destroyWindow("Preview")
			except:
				print(1)
			return k

	k = cv2.waitKey()
	try:
		cv2.destroyWindow("Preview")
	except:
		print(1)
	return k

def changeBrightness(img, br):
    return np.round(img * (br / 100)).astype(np.uint8)
# Photos cropper

This is an python tool, created to crop images to a certain ratio of the image sides. F.e. you can crop 4:3 image to 16:9 image.

# Getting started

To start:

- Clone this repository
```bash
git clone https://github.com/mkulik05/photos_cropper.git
```
- Navigate to project directory:
```bash
cd photos_cropper
```
- If it is necessary install opencv library
```bash
pip install opencv_contrib_python
```
- Run program
```bash
python photo_cropping.py
```

# Usage

After starting you will be asked for image ratio you should get(input should be like 16:9 or 4:3), path to your photos pholder and path, where results should be saved

Then after a while opencv window will appear. Result image is surrounded with a rectangular. 
You can shift this rectangle up/down using __w__ and __s__ key. Shift step can be increased/decreased with __a__ and __d__ key.
Pressing __e__ will save picture in rectangular.
Pressing __q__ will save picture without changes.
Pressing __Esc__ will stop program.

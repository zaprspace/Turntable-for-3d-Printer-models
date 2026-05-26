This python script creates a video of a 3d model rotating in front of a black background. 

It is intended for 3d model storefronts: etsy, makerworld, cults3d, thingiverse, thangs, turbosquid, etc.

It works on Blender 4.5.4 and newer, older versions of Blender handle importing stl files differently. It was designed to run headlessly and produce a batch of videos quickly. 
You choose an input folder, output folder, color value, and camera height. The script runs on each stl file in the folder. It imports the file, centers it at the world origin
(0,0,0), scales the model's largest dimension to 1 Blender unit, applies a simple material, creates a camera and lights, renders a image of the model, the camera rotates two
degrees and renders another photo and repeats until there are 180 images. The script then compiles these 180 images into an mp4 video. The video is 30fps which gives you a 
fully loopable 6 second video at 1080x1080 resolution. Then everything is cleared from Blender for the next file in the batch. 

The script takes input arguments: 
input_folder - The folder of stl files to be imported. The script will make a video for each file in the input_folder
output_folder - Where the mp4 videos will be saved once rendered
r - the red color value
g - the green color value
b - the blue color value
camera_height_pct - This is the camera angle. The argument itself is the height of the camera based on the Height of the model expressed as a percentage. The camera will always 
point at the center of mass of the model. If a model is 10cm tall and you input 40 as the camera_height_pct, the camera will be placed at 4cm above the ground and point at the 
model's center of mass (let's say it's a cube, the camera will point at a point 5cm above the ground) 40 percent gives a nice low angle.

The script can be run with the included Tkinter GUI or from a CLI with the following example: 
    blender -b -P turntable_render.py "C:/models" "C:/renders" 0.8 0.2 0.2 0.6

How do I set it up? 
  It's only two files: 
      turntable_gui.py
      turntable_render.py
  Wherever you put turntable_gui, create a folder called "scripts" and put turntable_render in it.
Open a command prompt in the folder above and type "python turntable_gui.py"
The GUI will open, then you choose an imput folder (The folder containing your models. This will make a video for EVERY model in this folder. You may want to make a folder just
  for the models you want a video of), Choose an output folder to save the videos to (this can be the same as the input folder), then choose the color you want to apply to the
  models (It will render the model in one solid color), and choose the camera height (expressed as a percentage of the model height)

from wand.image import Image  # imagemagik library is called wand in python
import os 

def image_transform(img_path, post_transform_path, mode):
    """
    Function to apply image transformations using imagemagik library
    3 transformations: blur, shade, spread

    input:  img_path: string specifying path to image on AWS machine
            mode: int specifying which transformation to apply
                  0 = blur, 1 = shade, 2 = spread, 3 = 50 x 50 thumbnail

    output: wand Image object with transformation applied
    """
    img = Image(filename=img_path)  # create a wand image object
    if mode == 0: out = img.blur(radius=0, sigma=8)
    elif mode == 1: out = img.shade(gray=True, azimuth=286.0, elevation=45.0)
    elif mode == 2: out = img.spread(radius=8.0)
    elif mode == 3: out = img.thumbnail(50, 50)
    else: 
        print("incorrect input")
        return -1

    # in case image transformation does not work, throw exeception
    try:
        img.save(filename=post_transform_path)
        return out
    except:
        print("image transform failed!")
        return -1
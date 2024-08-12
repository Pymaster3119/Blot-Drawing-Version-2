from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import convolve
import math
import tqdm
from multiprocessing import Pool
import time

def process(minx):
    useCircles = True
    image = Image.open('image2.png').convert("L")
    image_array = np.array(image)
    maxx = minx + 16
    if maxx < image_array.shape[0]:
        array_slice = np.zeros((256, image_array.shape[1] * 16))
    else:
        array_slice = np.zeros(((image_array.shape[0] - minx) * 16, image_array.shape[1] * 16))

    for x in range(minx, maxx + 1): 
        try:
            for y in range(image_array.shape[1] + 1):
                # Get intensity
                intensity = image_array[x][y] / 16.0
                if useCircles:
                    radius = int(intensity)
                    # Draw circle with appropriate radius
                    for i in range(16):
                        for j in range(16):
                           if (i - 8) ** 2 + (j - 8) ** 2 <= radius ** 2:
                                new_x = (x - minx) * 16 + i
                                new_y = 16 * y + j
                                #if 0 <= new_x < array_slice.shape[0] and 0 <= new_y < array_slice.shape[1]:
                                array_slice[new_x][new_y] = 1
                elif x == 1:
                    #Find the maximum value
                    maximum = 0
                    if x != 0 and maximum < round(image_array[x-1][y]/256):
                        maximum = round(image_array[x-1][y]/256)
                    if x != image_array.shape[0]-1 and maximum < round(image_array[x+1][y]/256):
                        maximum = round(image_array[x+1][y]/256)
                    if y != 0 and maximum < round(image_array[x][y-1]/256):
                        maximum = round(image_array[x][y-1]/256)
                    if y != image_array.shape[1]-1 and maximum < round(image_array[x][y+1]/256):
                        maximum = round(image_array[x][y+1]/256)
                    print("Here")
                    # Check above
                    print(image_array)
                    print(array_slice.shape)
                    print(round(image_array[x-1][y]/256))
                    if x != 0 and maximum == round(image_array[x-1][y]/256):
                        for i in range(15, 15 - int(intensity), -1):
                            for j in range(-16, 16):
                                print("HERE")
                                array_slice[(x - minx) * 16 + i][16 * y + j] = 1
                                print("HERE 2")
                    '''
                    # Check below
                    if x != image_array.shape[0]-1 and maximum == round(image_array[x+1][y]/256):
                        for i in range(-16, -16 + int(intensity)):
                            for j in range(-16, 16):
                                array_slice[(x - minx) * 16 + i][16 * y + j] = 1
                                

                    # Check left
                    if y != 0 and maximum == round(image_array[x][y-1]/256):
                        for j in range(16, 16 - int(intensity), -1):
                            for i in range(-16, 16):
                                array_slice[(x - minx) * 16 + i][16 * y + j] = 1

                    # Check right
                    if y != image_array.shape[1]-1 and maximum == round(image_array[x][y+1]/256):
                        for j in range(-16, -16 + int(intensity)):
                            for i in range(-16, 16):
                                array_slice[(x - minx) * 16 + i][16 * y + j] = 1
                    print(array_slice)
                    '''
        except Exception as e:
            print(e)
            pass
    
    return minx, array_slice

def write_codelines(x):
    big_array = np.load("UpscaledArray.npy")
    towrite = ""
    for y in range(big_array.shape[1]):
        if big_array[x][y] == 0:
            #Find line if applicable - along y axis
            maxy = 0
            for i in range(big_array.shape[1]):
                try:
                    if big_array[x][y + i] == 0:
                        maxy = y + i
                        big_array[x][maxy] = 1
                    else:
                        break
                except:
                    break
            towrite += f"finalLines.push([[{y}, {x}], [{maxy}, {x}]]);\n"
            
    return towrite

global image_array, big_array


if __name__ == "__main__":
    
    #Load image
    image = Image.open('image2.png').convert("L")
    image_array = np.array(image) 
    plt.imshow(image_array, cmap='gray')
    plt.axis('off')
    plt.show()

    #Converting it to a bigger Numpy array
    big_array = np.zeros((0, image_array.shape[1] * 16))
    with Pool() as p:
        results = p.map(process, range(0, image_array.shape[0], 16))
    for minx, array_slice in results:
        big_array = np.append(big_array, array_slice, axis=0)

    #Rotate/flip the big array
    rotated_array = np.zeros(big_array.shape)
    for i in range(rotated_array.shape[0]):
        for j in range(rotated_array.shape[1]):
            rotated_array[i, rotated_array.shape[1]-1-j] = big_array[rotated_array.shape[0]-1-i, j]
    rotated_array = np.flip(rotated_array, axis=1)
    #Save and display the big array
    np.save("UpscaledArray", rotated_array)
    plt.imshow(rotated_array, cmap='gray')
    plt.axis('off')
    plt.show()

    #Blot code generation
    with open("Blotcode.js", "w") as txt:
        txt.write("//Produced by Aditya Anand's Blotinator, not human-written\n")
        txt.write(f"setDocDimensions({big_array.shape[0]}, {big_array.shape[1]});\n")
        txt.write("const finalLines = [];\n")
        with Pool() as p:
            results = p.map(write_codelines, range(big_array.shape[0]))
        for i in results:
            txt.write(i)
        txt.write("drawLines(finalLines);")
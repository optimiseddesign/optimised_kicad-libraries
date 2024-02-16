## INFO
# Simple script to export PNG images of the KiCAD PCB file from the X most recent commits in a particular branch of a local Git repo
# Both KiCAD v7.0+ and Inkscape must be installed, the Git repo locally cloned, and the config values filled out below
#
# First outputs all the X .kicad_pcb files
# Next outputs all the X .svg files using the KiCAD CLI
# Next sets all the layers of the SVG to a % opacity for visual clarity
# Next converts the X .svg to .png using inkscape
# Finally, crops the PNGs to a specified area
# Then the .PNG are available to use as you wish - e.g. Flowframes to merge (and AI interpolate) to a Gif https://github.com/n00mkrad/flowframes
#
# My initial investigations info for reference;
#'git show HASH:file/path/name.ext > some_new_name.ext' example to pipe output from a single Git hash to a file
#'git show branchname~10:file/path/name.ext' example using the branch and relative commit number
#'git -C /home/repo' to specify repo location
# These combined, gives;
#"C:\Program Files\SmartGit\git\bin\git.exe" -C "C:\freelance\git\pt115a_vrgo-fyt-electronics-main" show miniaturisation~10:./design/pt115a_vrgo-fyt-electronics-main.kicad_pcb > C:\Users\KevinBibby\Desktop\test.kicad_pcb
#
#Then use KiCAD CLI (v7 only) example to export to SVG (could also do as gerbers/PDF but SVG seems best);
#"C:\Program Files\KiCad\7.0\bin\kicad-cli" pcb export svg --output C:\Users\KevinBibby\Desktop\test3.svg -l F.Cu,B.Cu --page-size-mode 2 --exclude-drawing-sheet C:\freelance\git\pt115a_vrgo-fyt-electronics-main\design\pt115a_vrgo-fyt-electronics-main.kicad_pcb
#
## TO-DO
# Crop based on pixels rather than margins
# Document FlowFrames settings better (RIFE CUDA??, approx 3x FPS, input FPS for length desired, no de-duplication, loop round, MP4 with CRF=15 ish)
# Add config of additional duplication for final frame



import subprocess
import time
from PIL import Image # Install with 'pip3 install Pillow' before

## CONFIG VALUES - set these before using script.
## For paths, use double backslashes '\\'
## All folders must *exist already*
CONFIG_GIT_EXE_PATH = "C:\\Program Files\\SmartGit\\git\\bin\\git.exe"
CONFIG_GIT_REPO_PATH = "C:\\freelance\\git\\pt136a_giraffecctv_edge_controller_generic"
CONFIG_GIT_PCB_PATH = "./design/pt136a_giraffecctv_edge_controller_generic.kicad_pcb"
CONFIG_GIT_BRANCH = "master"
CONFIG_GIT_NUM_COMMITS = 143 #this many commits counting backwards relative to the HEAD, for changes in PCB file only
CONFIG_OUTPUT_PCB_PATH = "C:\\Users\\KevinBibby\\Desktop\\output\\"
CONFIG_OUTPUT_PCB_PREFIX = "output"
CONFIG_OUTPUT_IMAGE_PATH = "C:\\Users\\KevinBibby\\Desktop\\output\\"
CONFIG_OUTPUT_IMAGE_PREFIX = "output"
CONFIG_OUTPUT_IMAGE_DPI = 600
CONFIG_OUTPUT_IMAGE_OPACITY = 60 # setting 0 to 99 opacity % of all the layers for visual clarity adjustment
CONFIG_OUTPUT_IMAGE_CROP_LEFT = 300 #margin from left
CONFIG_OUTPUT_IMAGE_CROP_RIGHT = 2100 #margin from right
CONFIG_OUTPUT_IMAGE_CROP_TOP = 750 #margin from top
CONFIG_OUTPUT_IMAGE_CROP_BOTTOM = 950 #margin from bottom
CONFIG_OUTPUT_IMAGE_DUPLICATE = 2 # 1 default, 9 max (set higher for duplicates of each one, ensure image interpolation has de-duplication OFF)
CONFIG_INKSCAPE_PATH = "C:\\Program Files\\Inkscape\\bin\inkscape.com"
CONFIG_KICAD_CLI_PATH = "C:\\Program Files\\KiCad\\7.0\\bin\\kicad-cli"
CONFIG_KICAD_LAYERS = "F.Paste,F.Cu,F.Courtyard,In2.Cu,B.Cu,Edge.Cuts"


# First outputs all the X .kicad_pcb files
for commit_num in range(1,CONFIG_GIT_NUM_COMMITS+1):
    print("Exporting KiCAD PCB file from branch '" + CONFIG_GIT_BRANCH + "', commit #" + str(commit_num) + " (" + str(CONFIG_GIT_NUM_COMMITS - commit_num) + " behind HEAD)\n")

    cmd = [CONFIG_GIT_EXE_PATH,
            '-C',
            CONFIG_GIT_REPO_PATH,
            "show",
            CONFIG_GIT_BRANCH + "~" + str(CONFIG_GIT_NUM_COMMITS - commit_num) + ":" + CONFIG_GIT_PCB_PATH,
            ">",
            CONFIG_OUTPUT_PCB_PATH + CONFIG_OUTPUT_PCB_PREFIX + str(commit_num) + ".kicad_pcb"]    # Save in reverse numbering

    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    print(process.stdout)


# Next outputs all the X .svg files using the KiCAD CLI
for commit_num in range(1,CONFIG_GIT_NUM_COMMITS+1):
    print("Exporting SVG from output file #" + str(commit_num) + "\n")
##C:\Program Files\KiCad\7.0\bin\kicad-cli pcb export svg --output C:\Users\KevinBibby\Desktop\test3.svg -l F.Cu,B.Cu --page-size-mode 2 --exclude-drawing-sheet C:\freelance\git\pt115a_vrgo-fyt-electronics-main\design\pt115a_vrgo-fyt-electronics-main.kicad_pcb
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'svg',
            '--output',
            CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + str(commit_num) + ".svg",
            '-l',
            CONFIG_KICAD_LAYERS,
            '--page-size-mode',
            '0',    # (0 = page with frame and title block, 1 = current page size, 2 = board area only) [default: 0]
            CONFIG_OUTPUT_PCB_PATH + CONFIG_OUTPUT_PCB_PREFIX + str(commit_num) + ".kicad_pcb"]
            

    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    print(process.stdout)


# Next, modifies the SVG opacity for all layers for better visual clarity
for commit_num in range(1,CONFIG_GIT_NUM_COMMITS+1):
    print("\nSetting SVG to " + str(CONFIG_OUTPUT_IMAGE_OPACITY) + "% opacity for output file #" + str(commit_num) + "\n")

    # read svg file -> write png file
    process = subprocess.run([CONFIG_INKSCAPE_PATH,
                            '--actions=select-all;object-set-property:opacity,0.70;export-overwrite;export-do;',
                            CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + str(commit_num) + ".svg"])
       
    print(process.stdout)

    time.sleep(0.1) # Delay between each as sometimes hung mid loop


# Next converts the X .svg to .png using inkscape. Pads the output filenames with leading zeros
for commit_num in range(1,CONFIG_GIT_NUM_COMMITS+1):
    print("Converting SVG to PNG for output file #" + str(commit_num) + "\n")

    # read svg file -> write png file
    process = subprocess.run([CONFIG_INKSCAPE_PATH,
                            '--export-type=png',
                            f'--export-filename={CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + str("%04d" % (commit_num,)) + ".png"}',
                            f'--export-dpi={CONFIG_OUTPUT_IMAGE_DPI}',
                            CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + str(commit_num) + ".svg"])
    print(process.stdout)

    time.sleep(0.1) # Delay between each as sometimes hung mid loop


# Next crops the PNGs to a specified area
for commit_num in range(1,CONFIG_GIT_NUM_COMMITS+1):
    # Open image file and get size
    im = Image.open(CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + str("%04d" % (commit_num,)) + ".png")
    img_width, img_height = im.size
    
    # Setting the points for cropped image (assumes zero in top left)
    left = CONFIG_OUTPUT_IMAGE_CROP_LEFT
    top = CONFIG_OUTPUT_IMAGE_CROP_TOP
    right = img_width - CONFIG_OUTPUT_IMAGE_CROP_RIGHT
    bottom = img_height - CONFIG_OUTPUT_IMAGE_CROP_BOTTOM
    crop_string = "(l=" + str(left) + ", t=" + str(top) + ", r=" + str(right) + ", b=" + str(bottom) + ")"
    size_string = "(" + str(img_width) + "x" + str(img_height) + "px)"

    print("Cropping PNG for output file #" + str(commit_num) + ", at " + crop_string + ", for " + size_string + "\n")
     
    # Cropped image of above dimension
    im_crop = im.crop((left, top, right, bottom))
    im_crop.save(CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + "-crop-" + str("%04d" % (commit_num,)) + ".png")


    # Finally, outputs duplicates of each frame (if configured) to ensure a subsequent interpolation still pauses on each frame
    for duplicate_num in range(CONFIG_OUTPUT_IMAGE_DUPLICATE):
        print("Duplication #" + str(duplicate_num) + " for output file #" + str(commit_num) + "\n")
        im_crop.save(CONFIG_OUTPUT_IMAGE_PATH + CONFIG_OUTPUT_IMAGE_PREFIX + "-crop-final" + str("%04d" % (commit_num,)) + str(duplicate_num) + ".png")

    # Then - use these generated frames in another program to interpolate and turn into animated Gif or MP4 or similar

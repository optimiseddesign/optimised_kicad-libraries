###########################################
#
## INFO
#
# Python script to automatically export design pack from KiCAD Project, using Optimised naming etc conventions.
# Uses KiCAD v7 CLI (Command Line Interface). Written for KiCAD v7.0.6 on Win10 using Python v3.10.0.
# REQUIRES 'pypdf' python package installed, Tested using v3.15.0 - install using 'pip3 install pypdf' on command line
#
# Copyright Optimised Product Design Ltd 2023
#
#
## TO-DO
#
# - (?)Add versioning and other readme content for script.
# - Layout PDF CLI exports with missing copper on drill holes! Doesn't happen when done from GUI. Missing CLI drill marks option?
# - Add automatic BOM export once CLI feature availability in KiCAD v8 in 2024
# - Add automatic 3D viewer image save once feature available, see (unknown time) https://gitlab.com/kicad/code/kicad/-/issues/13948
#
###########################################


import subprocess
import os
from pypdf import PdfMerger, PdfReader, PdfWriter


###########################################
#
#   CONFIG VALUES - set these before using script.
#   For paths, use double backslashes '\\'
#   All folders must *exist already*
#
###########################################

# Overall configs
CONFIG_KICAD_CLI_PATH = "C:\\Program Files\\KiCad\\7.0\\bin\\kicad-cli"
CONFIG_KICAD_FOLDER = "C:\\freelance\\git\\"
CONFIG_KICAD_NAME = "pt115a_vrgo-fyt-electronics-main"  # Main configuration to set if design follows Optimiseds' conventions
CONFIG_KICAD_PROJECT = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pro"
CONFIG_KICAD_SCH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_sch"
CONFIG_KICAD_PCB = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pcb"
CONFIG_KICAD_LAYERS_FRONT = "F.Fab,Edge.Cuts,User.Drawings,F.Cu,F.Mask,F.Paste,F.Silkscreen,"
CONFIG_KICAD_LAYERS_BACK = "B.Fab,B.Cu,B.Mask,B.Paste,B.Silkscreen,User.Comments"
CONFIG_KICAD_LAYERS_2L = CONFIG_KICAD_LAYERS_FRONT + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_4L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_6L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu,In3.Cu,In4.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_8L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_OUTPUT = CONFIG_KICAD_LAYERS_2L     # **Note**: Adjust based on the number of PCB layers

# for sch_export_pdf
CONFIG_SCH_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\" + CONFIG_KICAD_NAME + "_schematic.pdf"

# for pcb_export_pdf
CONFIG_PCB_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\" + CONFIG_KICAD_NAME + "_layout.pdf"
CONFIG_PCB_EXPORT_PDF_FILEPATH_TEMP = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\" + CONFIG_KICAD_NAME + "_TEMP.pdf"
CONFIG_PCB_EXPORT_PDF_LAYERS = CONFIG_KICAD_LAYERS_OUTPUT

# for pcb_export_step
CONFIG_PCB_EXPORT_STEP_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\mechanical\\" + CONFIG_KICAD_NAME + ".step"

# for pcb_export_pos
CONFIG_PCB_EXPORT_POS_FILEPATH_FRONT = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\" + CONFIG_KICAD_NAME + "-top-pos.csv"
CONFIG_PCB_EXPORT_POS_FILEPATH_BACK = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\" + CONFIG_KICAD_NAME + "-bottom-pos.csv"

# for pcb_export_drill
CONFIG_PCB_EXPORT_DRILL_FOLDERPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\"  # Note: is a FOLDER not a FILE path for drill

# for pcb_export_gerbers
CONFIG_PCB_EXPORT_GERBERS_FOLDERPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\"  # Note: is a FOLDER not a FILE path for gerbers
CONFIG_PCB_EXPORT_GERBERS_LAYERS = CONFIG_KICAD_LAYERS_OUTPUT
CONFIG_PCB_EXPORT_GERBERS_LAYERS_COMMON = ""    # Think best to have no common layers, though could be Edge.Cuts?



###########################################
#
#   Export KICAD Schematic PDF
#   Uses: kicad-cli sch export pdf [-h] [--output VAR] [--theme VAR] [--black-and-white] [--exclude-drawing-sheet] [--no-background-color] [--plot-one] input
#
###########################################

def sch_export_pdf():
    print("\n## Exporting Schematic PDF...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'sch',
            'export',
            'pdf',
            '--output',
            CONFIG_SCH_EXPORT_PDF_FILEPATH,
            '--no-background-color',
            CONFIG_KICAD_SCH]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)

    # Don't read and re-write PDF here - actually *increases* PDF size for Schematic unlike Layout PDF so not worth it.
    # Also want to keep the schematic links (v useful feature in KiCAD v7) so can't use that saving.
        


###########################################
#
#   Export KICAD PCB Layout PDF
#   Uses: kicad-cli pcb export pdf [-h] [--output VAR] [--layers VAR] [--mirror] [--exclude-refdes] [--exclude-value] [--include-border-title] [--negative] [--black-and-white] [--theme VAR] input
#
###########################################

def pcb_export_pdf():
    print("\n## Exporting Layout PDF of all layers...")

    # Create PDF Object to merge all the individual Layer PDFs into
    merger = PdfMerger()

    # Loop over layers in CONFIG_PCB_EXPORT_PDF_LAYERS_2L to export individually
    layers = CONFIG_PCB_EXPORT_PDF_LAYERS
    for layer in layers.split(","):

        # Export single-layer temporary PDF using KiCAD CLI
        print("Exporting Layout PDF (temp single layer: " + layer + ")...")
        pcb_export_pdf_single(layer)

        # Append this temporary PDF page to our created PDF object
        merger.append(open(CONFIG_PCB_EXPORT_PDF_FILEPATH_TEMP, 'rb'))
    
    # Save merged PDF of all the individual layer pages
    print("Saving merged Layout PDF of all layers, to;\n" + CONFIG_PCB_EXPORT_PDF_FILEPATH + " ...\n")
    with open(CONFIG_PCB_EXPORT_PDF_FILEPATH, "wb") as fout:
        merger.write(fout)

    # Delete temporary PDF file
    os.remove(CONFIG_PCB_EXPORT_PDF_FILEPATH_TEMP)

    # Read and re-write PDF to reduce file size by approx 10%...
    print("Reading & re-writing PDF to reduce file size...")
    reader = PdfReader(CONFIG_PCB_EXPORT_PDF_FILEPATH)
    writer = PdfWriter()
    
    for page in reader.pages:
        writer.add_page(page)

    writer.remove_links()   # Reduces PDF size by further 76% on test project (7.6MB to 1.8MB)!
    writer.add_metadata(reader.metadata)

    with open(CONFIG_PCB_EXPORT_PDF_FILEPATH, "wb") as fp:
        writer.write(fp)


def pcb_export_pdf_single(layer):
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'pdf',
            '--output',
            CONFIG_PCB_EXPORT_PDF_FILEPATH_TEMP,
            '--layers',
            layer + ",Edge.Cuts",
            '--include-border-title',
            '--black-and-white',
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout .STEP 3D Model
#   Uses: kicad-cli pcb export step [-h] [--drill-origin] [--grid-origin] [--no-virtual] [--subst-models] [--force] [--board-only] [--min-distance VAR] [--user-origin VAR] [--output VAR] input
#
###########################################

def pcb_export_step():
    print("\n## Exporting Layout .STEP 3D Model...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'step',
            '--output',
            CONFIG_PCB_EXPORT_STEP_FILEPATH,
            '--subst-models',
            '--force',
            '--drill-origin',
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout .pos footprint position file
#   Param: "front" "back" or "both"
#   Uses: kicad-cli pcb export pos [-h] [--output VAR] [--side VAR] [--format VAR] [--units VAR] [--bottom-negate-x] [--use-drill-file-origin] [--smd-only] [--exclude-fp-th] [--gerber-board-edge] input
#
###########################################

def pcb_export_pos(side):
    print("\n## Exporting Layout .pos footprint position file (side: " + side + ") ...")

    # set the output filename based on whether "front" or "back" for the 'side' argument
    if side == "front":
        CONFIG_PCB_EXPORT_POS_FILEPATH = CONFIG_PCB_EXPORT_POS_FILEPATH_FRONT
    if side == "back":
        CONFIG_PCB_EXPORT_POS_FILEPATH = CONFIG_PCB_EXPORT_POS_FILEPATH_BACK
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'pos',
            '--output',
            CONFIG_PCB_EXPORT_POS_FILEPATH,
            '--use-drill-file-origin',
            '--format',
            'csv',
            '--units',
            'mm',
            '--side',           
            side,
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout drill and map files
#   Uses: kicad-cli pcb export drill [-h] [--output VAR] [--format VAR] [--drill-origin VAR] [--excellon-zeros-format VAR] [--excellon-units VAR] [--excellon-mirror-y] [--excellon-min-header] [--excellon-separate-th] [--generate-map] [--map-format VAR] [--gerber-precision VAR] input
#
###########################################

def pcb_export_drill():
    print("\n## Exporting Layout drill .drl and .map files ...")
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'drill',
            '--output',
            CONFIG_PCB_EXPORT_DRILL_FOLDERPATH, # FOLDER not FILE path
            '--map-format',
            'gerberx2',
            '--excellon-separate-th',
            '--generate-map',
            '--drill-origin',
            'plot',
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout Gerber files
#   Uses: kicad-cli pcb export gerbers [-h] [--output VAR] [--layers VAR] [--exclude-refdes] [--exclude-value] [--include-border-title] [--no-x2] [--no-netlist] [--subtract-soldermask] [--disable-aperture-macros] [--use-drill-file-origin] [--precision VAR] [--no-protel-ext] [--common-layers VAR] [--board-plot-params] input
#
###########################################

def pcb_export_gerbers():
    print("\n## Exporting Layout Gerber files ...")
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'gerbers',
            '--output',
            CONFIG_PCB_EXPORT_GERBERS_FOLDERPATH, # FOLDER not FILE path
            '--layers',
            CONFIG_PCB_EXPORT_GERBERS_LAYERS,
            '--include-border-title',
            '--exclude-value',
            '--use-drill-file-origin',
            '--no-protel-ext',
            '--precision',
            '6',
            '--common-layers',
            CONFIG_PCB_EXPORT_GERBERS_LAYERS_COMMON,
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   MAIN
#   Calls all the other functions in turn to export the design pack
#
###########################################

print("\n####################################################################")
print("Exporting design pack from;\n" + CONFIG_KICAD_PROJECT)
print("####################################################################\n")

sch_export_pdf()
#sch_export_bom() - future addition
pcb_export_pdf()
pcb_export_step()
#pcb_export_images() - future addition
pcb_export_pos("front")
pcb_export_pos("back")
pcb_export_drill()
pcb_export_gerbers()

print("\nEnd of design pack export!")
print("\n####################################################################\n")




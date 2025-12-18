###########################################
#
## INFO
#
# Python script to automatically export design pack from KiCAD Project, using Optimised naming etc conventions.
# Uses KiCAD v9 CLI (Command Line Interface). Written for KiCAD v9.0.5 (updated, was for v8.0.8 and initially for v7.0.6) on Win10 using Python v3.10.0 .
# REQUIRES 'pypdf' python package installed, Tested using v3.15.0 - install using 'pip3 install pypdf' on command line
# 
# Once all the requirements are installed and the CONFIG values are filled out, simply run this script with python in your preferred way.
#
# Copyright Optimised Product Design Ltd 2023-2025
#
#
## TO-DO
#
# - use new flag '--mode-multipage' for separate-page PDF export of multiple layers
# - Use DRC/ERC from CLI(?)
# - Set soldermask expansion/min web values(?)
# - Use custom colour scheme(?)
# - fixes before IPC-2581 can be used
#            a) 'revision' field is always 1.0 (check if fixed in v9 or later?)
#            b) import error into ZofZPCB (but may just be that program?)
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
CONFIG_KICAD_VERSION_BOM = "1A"
CONFIG_KICAD_CLI_PATH = "C:\\Program Files\\KiCad\\9.0\\bin\\kicad-cli"
CONFIG_KICAD_FOLDER = "C:\\freelance\\git\\"
CONFIG_KICAD_NAME = "pt140a_vsmsc_8sim_4g_usb_dongle"  # Main configuration to set, if design follows Optimiseds' conventions
CONFIG_KICAD_PROJECT = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pro"
CONFIG_KICAD_SCH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_sch"
CONFIG_KICAD_PCB = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pcb"
CONFIG_KICAD_LAYERS_FRONT = "F.Fab,Edge.Cuts,User.Drawings,F.Cu,F.Mask,F.Paste,F.Silkscreen,"
CONFIG_KICAD_LAYERS_BACK = "B.Fab,B.Cu,B.Mask,B.Paste,B.Silkscreen,User.Comments"
CONFIG_KICAD_LAYERS_FLEX = "User.1,User.2" # i.e. "Flex.pcb.rigid,Flex.pcb.not.rigid"
CONFIG_KICAD_LAYERS_2L = CONFIG_KICAD_LAYERS_FRONT + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_4L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_4LR_2LF = CONFIG_KICAD_LAYERS_4L + "," + CONFIG_KICAD_LAYERS_FLEX
CONFIG_KICAD_LAYERS_6L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu,In3.Cu,In4.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_8L = CONFIG_KICAD_LAYERS_FRONT + "In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu," + CONFIG_KICAD_LAYERS_BACK
CONFIG_KICAD_LAYERS_OUTPUT = CONFIG_KICAD_LAYERS_6L     # **Note**: Adjust based on the number/type of PCB layers

# for sch_export_pdf
CONFIG_SCH_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\" + CONFIG_KICAD_NAME + "_schematic.pdf"

# for sch_export_bom
CONFIG_PCB_EXPORT_BOM_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_bom_" + CONFIG_KICAD_VERSION_BOM + ".csv"
CONFIG_PCB_EXPORT_BOM_FIELDS = "${ITEM_NUMBER},Reference,${QUANTITY},${DNP},Value,Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Vendor1,SKU1,Vendor2,SKU2"
CONFIG_PCB_EXPORT_BOM_LABELS = "Item,References,Qty,FitPart,Value,Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Vendor1,SKU1,Vendor2,SKU2"
CONFIG_PCB_EXPORT_BOM_GROUP = "Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Value,${DNP},Footprint"

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

# for pcb_export_render
CONFIG_PCB_EXPORT_RENDER_FILETYPE = ".png" # .png, .jpg, or .jpeg
CONFIG_PCB_EXPORT_RENDER_FILEPATH_TOP = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\images\\" + CONFIG_KICAD_NAME + "_top" + CONFIG_PCB_EXPORT_RENDER_FILETYPE
CONFIG_PCB_EXPORT_RENDER_FILEPATH_BOTTOM = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\images\\" + CONFIG_KICAD_NAME + "_bottom" + CONFIG_PCB_EXPORT_RENDER_FILETYPE
CONFIG_PCB_EXPORT_RENDER_WIDTH = "3200"
CONFIG_PCB_EXPORT_RENDER_HEIGHT = "1800"
CONFIG_PCB_EXPORT_RENDER_ZOOM = "1"   # Zoom factor as INTEGER

# for pcb_export_odb
CONFIG_PCB_EXPORT_ODB_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_odb.zip"
CONFIG_PCB_EXPORT_ODB_COMPRESSION = "zip" # none, zip (default), or tgz
CONFIG_PCB_EXPORT_ODB_UNITS = "mm" # mm (default) or in
CONFIG_PCB_EXPORT_ODB_PRECISION = "6"

# for pcb_export_ipc2581
CONFIG_PCB_EXPORT_IPC2581_VERSION = "B"
CONFIG_PCB_EXPORT_IPC2581_FILEPATH = CONFIG_KICAD_FOLDER + CONFIG_KICAD_NAME + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_ipc2581.xml"
CONFIG_PCB_EXPORT_IPC2581_BOM_ID = "Reference"
CONFIG_PCB_EXPORT_IPC2581_BOM_MFG = "Manufacturer1"
CONFIG_PCB_EXPORT_IPC2581_BOM_MFG_PN = "MPN1"
CONFIG_PCB_EXPORT_IPC2581_BOM_DIST = "Vendor1"
CONFIG_PCB_EXPORT_IPC2581_BOM_DIST_PN = "SKU1"



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
    # Also want to keep the schematic links (v useful feature in KiCAD v7+) so can't use that saving.



###########################################
#
#   Export KICAD Bill Of Materials (BOM)
#   Uses: kicad-cli sch export bom [--help] [--output OUTPUT_FILE] [--preset PRESET] [--format-preset FMT_PRESET] [--fields FIELDS] [--labels LABELS] [--group-by GROUP_BY] [--sort-field SORT_BY] [--sort-asc] [--filter FILTER] [--exclude-dnp] [--field-delimiter FIELD_DELIM] [--string-delimiter STR_DELIM] [--ref-delimiter REF_DELIM] [--ref-range-delimiter REF_RANGE_DELIM] [--keep-tabs] [--keep-line-breaks] INPUT_FILE
#
###########################################

def sch_export_bom():
    print("\n## Exporting Schematic BoM...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'sch',
            'export',
            'bom',
            '--output',
            CONFIG_PCB_EXPORT_BOM_FILEPATH,
            '--string-delimiter',
            '"',
            '--ref-delimiter',
            ' ',
            '--ref-range-delimiter',
            '',
            '--fields',
            CONFIG_PCB_EXPORT_BOM_FIELDS,
            '--labels',
            CONFIG_PCB_EXPORT_BOM_LABELS,
            '--group-by',
            CONFIG_PCB_EXPORT_BOM_GROUP,
            '--sort-asc',
            CONFIG_KICAD_SCH]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)   



###########################################
#
#   Export KICAD PCB Layout PDF
#   Uses: kicad-cli pcb export pdf [-h] [--output VAR] [--layers VAR] [--mirror] [--exclude-refdes] [--exclude-value] [--include-border-title] [--negative] [--black-and-white] [--theme VAR] input
#
###########################################

def pcb_export_pdf():
    print("\n## Exporting Layout PDF of all layers...")

    # Create PDF Object to merge all the individual Layer PDFs into
    merger = PdfWriter()
    #pypdf.errors.DeprecationError: PdfMerger is deprecated and was removed in pypdf 5.0.0. Use PdfWriter instead.

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
            '--drill-shape-opt',    # Fix for missing copper in drill holes, requires KiCAD v7.0.8
            '0',                    # Fix for missing copper in drill holes, requires KiCAD v7.0.8
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
            '--exclude-value',
            '--use-drill-file-origin',
            '--no-protel-ext',
            '--subtract-soldermask',
            '--disable-aperture-macros',
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
#   Export KICAD PCB Layout Render Image
#   Param: "top" or "bottom"
#   Uses: kicad-cli pcb render [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE] [--width WIDTH] [--height HEIGHT] [--side SIDE] [--background BG] [--quality QUALITY] [--preset PRESET] [--floor] [--perspective] [--zoom ZOOM] [--pan VECTOR] [--pivot PIVOT] [--rotate ANGLES] [--light-top COLOR] [--light-bottom COLOR] [--light-side COLOR] [--light-camera COLOR] [--light-side-elevation ANGLE] INPUT_FILE
#
###########################################

def pcb_export_render(side):
    print("\n## Exporting Layout Render image (side: " + side + ") ...")

    # set the output filename based on whether "top" or "bottom" for the 'side' argument
    if side == "top":
        CONFIG_PCB_EXPORT_RENDER_FILEPATH = CONFIG_PCB_EXPORT_RENDER_FILEPATH_TOP
    if side == "bottom":
        CONFIG_PCB_EXPORT_RENDER_FILEPATH = CONFIG_PCB_EXPORT_RENDER_FILEPATH_BOTTOM
        
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'render',
            '--output',
            CONFIG_PCB_EXPORT_RENDER_FILEPATH,
            '--side',
            side,
            '--quality',
            'high',
            '--background',
            'transparent',
            '--preset',
            'follow_plot_settings',
            '--width',
            CONFIG_PCB_EXPORT_RENDER_WIDTH,
            '--height',
            CONFIG_PCB_EXPORT_RENDER_HEIGHT,
            '--zoom',
            CONFIG_PCB_EXPORT_RENDER_ZOOM,
            '--floor',
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)

    
    
###########################################
#
#   Export KICAD PCB Layout ODB++ archive
#   Uses: kicad-cli pcb export odb [--help] [--output OUTPUT_FILE] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE] [--precision PRECISION] [--compression VAR] [--units VAR] INPUT_FILE
#
###########################################

def pcb_export_odb():
    print("\n## Exporting Layout ODB++ archive ...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'odb',
            '--output',
            CONFIG_PCB_EXPORT_ODB_FILEPATH,
            '--compression',
            CONFIG_PCB_EXPORT_ODB_COMPRESSION,
            '--units',
            CONFIG_PCB_EXPORT_ODB_UNITS,
            '--precision',
            CONFIG_PCB_EXPORT_ODB_PRECISION,
            CONFIG_KICAD_PCB]
    process = subprocess.run(args=cmd,
                            stdout=subprocess.PIPE,
                            shell=True,
                            universal_newlines=True)
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout IPC-2581 file
#   Uses: kicad-cli pcb export ipc2581 [--help] [--output OUTPUT_FILE] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE] [--precision PRECISION] [--compress] [--version VAR] [--units VAR] [--bom-col-int-id FIELD_NAME] [--bom-col-mfg-pn FIELD_NAME] [--bom-col-mfg FIELD_NAME] [--bom-col-dist-pn FIELD_NAME] [--bom-col-dist FIELD_NAME] INPUT_FILE
#
###########################################

def pcb_export_ipc2581():
    print("\n## Exporting Layout IPC-2581[" + CONFIG_PCB_EXPORT_IPC2581_VERSION + "] file ...")
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'ipc2581',
            '--output',
            CONFIG_PCB_EXPORT_IPC2581_FILEPATH,
            '--compress',
            '--version',
            CONFIG_PCB_EXPORT_IPC2581_VERSION,
            '--units',
            'mm',
            '--bom-col-int-id',
            CONFIG_PCB_EXPORT_IPC2581_BOM_ID,
            '--bom-col-mfg',
            CONFIG_PCB_EXPORT_IPC2581_BOM_MFG,
            '--bom-col-mfg-pn',
            CONFIG_PCB_EXPORT_IPC2581_BOM_MFG_PN,
            '--bom-col-dist',
            CONFIG_PCB_EXPORT_IPC2581_BOM_DIST,
            '--bom-col-dist-pn',
            CONFIG_PCB_EXPORT_IPC2581_BOM_DIST_PN,
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
sch_export_bom()
pcb_export_pdf()
pcb_export_step()
pcb_export_render("top")
pcb_export_render("bottom")
pcb_export_pos("front")
pcb_export_pos("back")
pcb_export_drill()
pcb_export_gerbers()
pcb_export_odb()
#pcb_export_ipc2581() - DRAFT for future addition once issues are resolved (see top)

print("\nEnd of design pack export!")
print("\n####################################################################\n")




###########################################
#
## INFO
#
# Python script to automatically export design pack from KiCAD Project, using Optimised naming etc conventions.
# Uses KiCAD v10 CLI (Command Line Interface). Written for KiCAD v10.0.6 (updated, was for v9.0.5, v8.0.8 and initially for v7.0.6) on Win11 (previously Win10).
# Requires KiCAD v10.0.3 or later (3D PDF, statistics report, variants and wire hop-over options are v10+, multipage layout PDF is v10.0.3+).
# Tested using python v3.15.0, no extra python packages needed (pypdf no longer used since multipage layout PDF is now native in KiCAD)
# 
# Once all the requirements are installed and the CONFIG values are filled out, simply run this script with python in your preferred way.
#
# Copyright Optimised Product Design Ltd 2023-2026
#
#
## TO-DO
#
# - Possibly add Layout PDF property popups (remove --no-property-popups) once issues with top/bottom parts improved
# - Set soldermask expansion/min web values(?)
# - Use custom colour scheme(?)
# - fixes before IPC-2581 can be used
#            a) F.Courtyard imports into ZofZPCB as a Silkscreen layer - raise support ticket with ZofZPCB
#               (KiCAD v10.0.6 exports it as layerFunction="COURTYARD" side="TOP", valid in IPC-2581B1 & C schemas)
#            b) assess IPC-2581 output more rigorously before enabling (schema, layers, vs. Gerbers/drill/BOM/pos)
#            c) decide CONFIG_PCB_EXPORT_IPC2581_BOM_ID (Reference means all unique and no grouping, omit means Description differences don't cause unique)
#            d) also just missing lots of BOM info... Description field, dielectric voltage tolerance etc, MPN2 and SKU fields etc
#            e) decide B or C revision
#
###########################################


import subprocess
import os


###########################################
#
#   CONFIG VALUES - set these before using script.
#   For paths, use double backslashes '\\'
#   All folders must *exist already*
#
###########################################

# Overall configs
CONFIG_KICAD_VERSION_BOM = "4A"
CONFIG_KICAD_CLI_PATH = "C:\\Program Files\\KiCad\\10.0\\bin\\kicad-cli"
CONFIG_KICAD_FOLDER = "C:\\freelance\\git\\pt140a_vsmsc_8sim_4g_cellular_gateway"   # Main configuration to set, if design follows Optimiseds' conventions
CONFIG_KICAD_NAME = "pt140a_vsmsc_8sim_4g_cellular_gateway"                         # Main configuration to set, if design follows Optimiseds' conventions
CONFIG_KICAD_PROJECT = CONFIG_KICAD_FOLDER + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pro"
CONFIG_KICAD_SCH = CONFIG_KICAD_FOLDER + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_sch"
CONFIG_KICAD_PCB = CONFIG_KICAD_FOLDER + "\\design\\" + CONFIG_KICAD_NAME + ".kicad_pcb"
CONFIG_KICAD_VARIANTS = ["N4-7600E","N4-7600A","N8-7600E","N8-7600A"] # e.g. ["N4-7600E","N4-7600A","N8-7600E","N8-7600A"] to match the names in KiCAD, or [None] for none/default. Applies to schematic PDF & BOM only
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
#CONFIG_SCH_EXPORT_PDF_FILEPATH defined within function to cope with variants

# for sch_export_bom
# CONFIG_PCB_EXPORT_BOM_FILEPATH defined within function to cope with variants
CONFIG_PCB_EXPORT_BOM_FIELDS = "${ITEM_NUMBER},Reference,${QUANTITY},${DNP},Value,Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Vendor1,SKU1,Vendor2,SKU2"
CONFIG_PCB_EXPORT_BOM_LABELS = "Item,References,Qty,FitPart,Value,Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Vendor1,SKU1,Vendor2,SKU2"
CONFIG_PCB_EXPORT_BOM_GROUP = "Description,Manufacturer1,MPN1,Manufacturer2,MPN2,Value,${DNP},Footprint"

# for pcb_export_pdf
CONFIG_PCB_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_layout.pdf"
CONFIG_PCB_EXPORT_PDF_LAYERS = CONFIG_KICAD_LAYERS_OUTPUT

# for pcb_export_step
CONFIG_PCB_EXPORT_STEP_FILEPATH = CONFIG_KICAD_FOLDER + "\\mechanical\\" + CONFIG_KICAD_NAME + ".step"

# for pcb_export_3dpdf
CONFIG_PCB_EXPORT_3DPDF_FILEPATH = CONFIG_KICAD_FOLDER + "\\mechanical\\" + CONFIG_KICAD_NAME + "_3d.pdf"   # Same folder as STEP file

# for pcb_export_pos
CONFIG_PCB_EXPORT_POS_FILEPATH_FRONT = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "-top-pos.csv"
CONFIG_PCB_EXPORT_POS_FILEPATH_BACK = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "-bottom-pos.csv"

# for pcb_export_drill
CONFIG_PCB_EXPORT_DRILL_FOLDERPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\"  # Note: is a FOLDER not a FILE path for drill

# for pcb_export_gerbers
CONFIG_PCB_EXPORT_GERBERS_FOLDERPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\"  # Note: is a FOLDER not a FILE path for gerbers
CONFIG_PCB_EXPORT_GERBERS_LAYERS = CONFIG_KICAD_LAYERS_OUTPUT
CONFIG_PCB_EXPORT_GERBERS_LAYERS_COMMON = ""    # Think best to have no common layers, though could be Edge.Cuts?

# for pcb_export_render
CONFIG_PCB_EXPORT_RENDER_FILETYPE = ".png" # .png, .jpg, or .jpeg
CONFIG_PCB_EXPORT_RENDER_FILEPATH_TOP = CONFIG_KICAD_FOLDER + "\\images\\" + CONFIG_KICAD_NAME + "_top" + CONFIG_PCB_EXPORT_RENDER_FILETYPE
CONFIG_PCB_EXPORT_RENDER_FILEPATH_BOTTOM = CONFIG_KICAD_FOLDER + "\\images\\" + CONFIG_KICAD_NAME + "_bottom" + CONFIG_PCB_EXPORT_RENDER_FILETYPE
CONFIG_PCB_EXPORT_RENDER_WIDTH = "3200"
CONFIG_PCB_EXPORT_RENDER_HEIGHT = "1800"
CONFIG_PCB_EXPORT_RENDER_ZOOM = "1.2"   # Camera zoom factor. Decimal (docs say integer but v10.0.6 code takes a decimal)

# for pcb_export_odb
CONFIG_PCB_EXPORT_ODB_FILEPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_odb.zip"
CONFIG_PCB_EXPORT_ODB_COMPRESSION = "zip" # none, zip (default), or tgz
CONFIG_PCB_EXPORT_ODB_UNITS = "mm" # mm (default) or in
CONFIG_PCB_EXPORT_ODB_PRECISION = "6"

# for pcb_export_ipc2581
CONFIG_PCB_EXPORT_IPC2581_VERSION = "B"
CONFIG_PCB_EXPORT_IPC2581_FILEPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_ipc2581.zip"   # zip as exported with --compress (contains the .xml)
CONFIG_PCB_EXPORT_IPC2581_BOM_ID = "Reference"   # One BOM line per RefDes: no grouping, but never merges different parts
# OR - don't set Internal ID field at all, so KiCAD generates one per library_footprint_value (GUI "Generate unique") but then misses Description uniqueness
CONFIG_PCB_EXPORT_IPC2581_BOM_MFG = "Manufacturer1"
CONFIG_PCB_EXPORT_IPC2581_BOM_MFG_PN = "MPN1"
CONFIG_PCB_EXPORT_IPC2581_BOM_REV = CONFIG_KICAD_VERSION_BOM    # BOM revision field, same as BOM file version
# No distributor P/N exported: KiCAD only takes one fixed distributor for all parts so not useful

# for sch_erc
CONFIG_SCH_ERC_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_report-erc.txt"

# for pcb_drc
CONFIG_PCB_DRC_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_report-drc.txt"

# for pcb_export_stats
CONFIG_PCB_EXPORT_STATS_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_report-statistics.txt"


###########################################
#
#   Export KICAD Schematic PDF
#   Uses: kicad-cli sch export pdf [--help] [--output OUTPUT_FILE] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE]…​ [--variant VAR] [--theme THEME_NAME] [--black-and-white] [--exclude-drawing-sheet] [--default-font VAR] [--draw-hop-over] [--exclude-pdf-property-popups] [--exclude-pdf-hierarchical-links] [--exclude-pdf-metadata] [--no-background-color] [--pages PAGE_LIST] INPUT_FILE
#
###########################################

def sch_export_pdf():
    for CONFIG_KICAD_VARIANT in CONFIG_KICAD_VARIANTS:
        if CONFIG_KICAD_VARIANT:
            CONFIG_SCH_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_schematic_" + CONFIG_KICAD_VARIANT + ".pdf"
        else:
            CONFIG_SCH_EXPORT_PDF_FILEPATH = CONFIG_KICAD_FOLDER + "\\" + CONFIG_KICAD_NAME + "_schematic.pdf"

        if CONFIG_KICAD_VARIANT:
            print("\n## Exporting Schematic PDF (Variant " + CONFIG_KICAD_VARIANT + ")...")
        else:
            print("\n## Exporting Schematic PDF...")
                
        cmd = [CONFIG_KICAD_CLI_PATH,
            'sch',
            'export',
            'pdf',
            '--output',
            CONFIG_SCH_EXPORT_PDF_FILEPATH,
            '--no-background-color',
            '--draw-hop-over',
            CONFIG_KICAD_SCH]

        # Only add --variant if one is specified
        if CONFIG_KICAD_VARIANT:
            cmd.extend(['--variant', CONFIG_KICAD_VARIANT])
               
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
#   Uses: kicad-cli sch export bom [--help] [--output OUTPUT_FILE] [--variant VAR] [--preset PRESET] [--format-preset FMT_PRESET] [--fields FIELDS] [--labels LABELS] [--group-by GROUP_BY] [--sort-field SORT_BY] [--sort-asc VAR] [--filter FILTER] [--exclude-dnp] [--include-excluded-from-bom] [--field-delimiter FIELD_DELIM] [--string-delimiter STR_DELIM] [--ref-delimiter REF_DELIM] [--ref-range-delimiter REF_RANGE_DELIM] [--keep-tabs] [--keep-line-breaks] INPUT_FILE
#
###########################################

def sch_export_bom():
    for CONFIG_KICAD_VARIANT in CONFIG_KICAD_VARIANTS:
        if CONFIG_KICAD_VARIANT:
            CONFIG_PCB_EXPORT_BOM_FILEPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_bom_" + CONFIG_KICAD_VERSION_BOM + "_" + CONFIG_KICAD_VARIANT + ".csv"
        else:
            CONFIG_PCB_EXPORT_BOM_FILEPATH = CONFIG_KICAD_FOLDER + "\\manufacturing\\" + CONFIG_KICAD_NAME + "_bom_" + CONFIG_KICAD_VERSION_BOM + ".csv"

        if CONFIG_KICAD_VARIANT:
            print("\n## Exporting Schematic BoM (Variant " + CONFIG_KICAD_VARIANT + ")...")
        else:
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
                CONFIG_KICAD_SCH,
                '--sort-asc']

        # Only add --variant if one is specified
        if CONFIG_KICAD_VARIANT:
            cmd.extend(['--variant', CONFIG_KICAD_VARIANT])
               
        process = subprocess.run(args=cmd, 
                                stdout=subprocess.PIPE,
                                shell=True, 
                                universal_newlines=True)
        
        print("Result: " + process.stdout)   



###########################################
#
#   Export KICAD PCB Layout PDF
#   Uses: kicad-cli pcb export pdf [--help] [--output OUTPUT_DIR] [--layers LAYER_LIST] [--common-layers COMMON_LAYER_LIST] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE]…​ [--mirror] [--exclude-refdes] [--exclude-value] [--include-border-title] [--subtract-soldermask] [--sketch-pads-on-fab-layers] [--hide-DNP-footprints-on-fab-layers] [--sketch-DNP-footprints-on-fab-layers] [--crossout-DNP-footprints-on-fab-layers] [--negative] [--black-and-white] [--theme THEME_NAME] [--drill-shape-opt VAR] [--mode-single] [--mode-separate] [--mode-multipage] [--scale SCALE] [--bg-color COLOR] [--check-zones] [--variant VAR] INPUT_FILE
#
###########################################

def pcb_export_pdf():
    print("\n## Exporting Layout PDF of all layers, to;\n" + CONFIG_PCB_EXPORT_PDF_FILEPATH + " ...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'pdf',
            '--output',
            CONFIG_PCB_EXPORT_PDF_FILEPATH,
            '--mode-multipage',     # One page per layer, in CONFIG_PCB_EXPORT_PDF_LAYERS order
            '--layers',
            CONFIG_PCB_EXPORT_PDF_LAYERS,
            '--common-layers',      # Edge.Cuts on every page
            'Edge.Cuts',
            '--include-border-title',
            '--black-and-white',
            '--drill-shape-opt',    # Fix for missing copper in drill holes, requires KiCAD v7.0.8
            '0',                    # Fix for missing copper in drill holes, requires KiCAD v7.0.8
            '--no-property-popups', # No footprint popups/bookmarks, smaller file (could remove in future once fixed? bit broken, links don't distinguish front/back components)
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)



###########################################
#
#   Export KICAD PCB Layout .STEP 3D Model
#   Uses: kicad-cli pcb export step [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE]…​ [--force] [--no-unspecified] [--no-dnp] [--variant VAR] [--grid-origin] [--drill-origin] [--subst-models] [--board-only] [--cut-vias-in-body] [--no-board-body] [--no-components] [--component-filter VAR] [--include-tracks] [--include-pads] [--include-zones] [--include-inner-copper] [--include-silkscreen] [--include-soldermask] [--fuse-shapes] [--fill-all-vias] [--no-extra-pad-thickness] [--min-distance MIN_DIST] [--net-filter VAR] [--no-optimize-step] [--user-origin VAR] INPUT_FILE
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
#   Export KICAD PCB Layout 3D PDF (PDF with embedded U3D 3D Model - view in Adobe Acrobat/Reader)
#   Note: requires KiCAD v10+ CLI. Uses same options as pcb_export_step() so 3D PDF matches the .STEP model.
#   Uses: kicad-cli pcb export 3dpdf [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE] [--force] [--no-unspecified] [--no-dnp] [--variant VAR] [--grid-origin] [--drill-origin] [--subst-models] [--board-only] [--cut-vias-in-body] [--no-board-body] [--no-components] [--component-filter VAR] [--include-tracks] [--include-pads] [--include-zones] [--include-inner-copper] [--include-silkscreen] [--include-soldermask] [--fuse-shapes] [--fill-all-vias] [--no-extra-pad-thickness] [--min-distance MIN_DIST] [--net-filter VAR] [--user-origin VAR] INPUT_FILE
#
###########################################

def pcb_export_3dpdf():
    print("\n## Exporting Layout 3D PDF...")
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            '3dpdf',
            '--output',
            CONFIG_PCB_EXPORT_3DPDF_FILEPATH,
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
#   Uses: kicad-cli pcb export pos [--help] [--output OUTPUT_FILE] [--side VAR] [--format FORMAT] [--units UNITS] [--bottom-negate-x] [--use-drill-file-origin] [--smd-only] [--exclude-fp-th] [--exclude-dnp] [--gerber-board-edge] [--variant VAR] INPUT_FILE
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
#   Uses: kicad-cli pcb export drill [--help] [--output OUTPUT_DIR] [--format FORMAT] [--drill-origin DRILL_ORIGIN] [--excellon-zeros-format ZEROS_FORMAT] [--excellon-oval-format OVAL_FORMAT] [--excellon-units UNITS] [--excellon-mirror-y] [--excellon-min-header] [--excellon-separate-th] [--generate-map] [--generate-report] [--report-path REPORT_FILE] [--generate-tenting] [--map-format MAP_FORMAT] [--gerber-precision VAR] INPUT_FILE
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
#   Uses: kicad-cli pcb export gerbers [--help] [--output OUTPUT_DIR] [--layers LAYER_LIST] [--common-layers COMMON_LAYER_LIST] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE]…​ [--exclude-refdes] [--exclude-value] [--include-border-title] [--sketch-pads-on-fab-layers] [--hide-DNP-footprints-on-fab-layers] [--sketch-DNP-footprints-on-fab-layers] [--crossout-DNP-footprints-on-fab-layers] [--no-x2] [--no-netlist] [--subtract-soldermask] [--disable-aperture-macros] [--use-drill-file-origin] [--precision PRECISION] [--no-protel-ext] [--check-zones] [--variant VAR] [--board-plot-params] INPUT_FILE
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
#   Uses: kicad-cli pcb render [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE]…​ [--variant VAR] [--width WIDTH] [--height HEIGHT] [--side SIDE] [--background BG] [--quality QUALITY] [--preset PRESET] [--use-board-stackup-colors VAR] [--floor] [--perspective] [--zoom ZOOM] [--pan VECTOR] [--pivot PIVOT] [--rotate ANGLES] [--light-top COLOR] [--light-bottom COLOR] [--light-side COLOR] [--light-camera COLOR] [--light-side-elevation ANGLE] INPUT_FILE
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
            '--use-board-stackup-colors',   # Needed in v10: off unless given (v9 always used stackup colours)
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
#   Uses: kicad-cli pcb export odb [--help] [--output OUTPUT_FILE] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE]…​ [--precision PRECISION] [--compression VAR] [--units VAR] [--variant VAR] INPUT_FILE
#
###########################################

def pcb_export_odb():
    print("\n## Exporting Layout ODB++ archive ...")

    # Remove previous ODB file if it exists (for some reason KiCAD CLI can't overwrite!)
    try:
        os.remove(CONFIG_PCB_EXPORT_ODB_FILEPATH)
    except FileNotFoundError:
        pass

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
#   Uses: kicad-cli pcb export ipc2581 [--help] [--output OUTPUT_FILE] [--drawing-sheet SHEET_PATH] [--define-var KEY=VALUE]…​ [--precision PRECISION] [--compress] [--version VAR] [--units VAR] [--bom-col-int-id FIELD_NAME] [--bom-col-mfg-pn FIELD_NAME] [--bom-col-mfg FIELD_NAME] [--bom-col-dist-pn FIELD_NAME] [--bom-col-dist FIELD_NAME] [--bom-rev REVISION] [--variant VAR] INPUT_FILE
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
            '--bom-rev',
            CONFIG_PCB_EXPORT_IPC2581_BOM_REV,
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)


###########################################
#
#   Export KICAD SCH Electrical Rules Check (ERC)
#   Uses: kicad-cli sch erc [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE]​ [--format VAR] [--units VAR] [--severity-all] [--severity-error] [--severity-warning] [--severity-exclusions] [--exit-code-violations] INPUT_FILE
#
###########################################

def sch_erc():
    print("\n## Schematic Electrical Rules Check (ERC) ...")
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'sch',
            'erc',
            '--output',
            CONFIG_SCH_ERC_FILEPATH,
            '--severity-error',     # errors + warnings only, i.e. excluded violations not reported
            '--severity-warning',
            '--exit-code-violations',
            CONFIG_KICAD_SCH]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)
    if process.returncode != 0:
        print("KiCad reported violations.")
        print("Error: " + process.stderr)
    else:
        print("KiCad reported No violations.")


###########################################
#
#   Export KICAD PCB Design Rules Check (DRC)
#   Uses: kicad-cli pcb drc [--help] [--output OUTPUT_FILE] [--define-var KEY=VALUE]​ [--format FORMAT] [--all-track-errors] [--schematic-parity] [--units UNITS] [--severity-all] [--severity-error] [--severity-warning] [--severity-exclusions] [--exit-code-violations] [--refill-zones] [--save-board] INPUT_FILE
#
###########################################

def pcb_drc():
    print("\n## PCB Design Rules Check (DRC) ...")
        
    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'drc',
            '--output',
            CONFIG_PCB_DRC_FILEPATH,
            '--severity-error',     # errors + warnings only, i.e. excluded violations not reported
            '--severity-warning',
            '--exit-code-violations',
            CONFIG_KICAD_PCB]
            
    process = subprocess.run(args=cmd, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True, 
                            universal_newlines=True)
    
    print("Result: " + process.stdout)

    if process.returncode != 0:
        print("KiCad reported violations.")
        print("Error: " + process.stderr)
    else:
        print("KiCad reported No violations.")



###########################################
#
#   Export KICAD PCB Statistics summary report (board size/area, copper areas, min track/drill, pad/via/component counts, drill table)
#   Note: requires KiCAD v10+ CLI
#   Uses: kicad-cli pcb export stats [--help] [--output OUTPUT_FILE] [--format FORMAT] [--units UNITS] [--exclude-footprints-without-pads] [--subtract-holes-from-board] [--subtract-holes-from-copper] INPUT_FILE
#
###########################################

def pcb_export_stats():
    print("\n## Exporting PCB Statistics summary report ...")

    cmd = [CONFIG_KICAD_CLI_PATH,
            'pcb',
            'export',
            'stats',
            '--output',
            CONFIG_PCB_EXPORT_STATS_FILEPATH,
            '--exclude-footprints-without-pads',    # Don't count logo/graphic-only footprints as components
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

sch_erc()
pcb_drc()
pcb_export_stats()
sch_export_pdf()
sch_export_bom()
pcb_export_pdf()
pcb_export_step()
pcb_export_3dpdf()
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




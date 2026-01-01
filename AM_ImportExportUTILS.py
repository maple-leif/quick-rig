import maya.cmds as cmds
import json
from dataclasses import dataclass

def export_temp_objects():
    """Utilities for Exporting Curves and Locators as json data"""
    
    """
    get temp objects
    seperate Locators and Curves
    Create LocatorData list of dictionaries
    Create Curvedata list of dictionaris
    Combine lists into dictionary
    open/make file
    dump data
    """
 

        
    curve_names = [cmds.listRelatives(i, p=1, type='transform')[0] for i in cmds.ls(type='nurbsCurve', o=1, r=1, ni=1) if "Temp_" in i]
    locator_names = [cmds.listRelatives(i, p=1, type='transform')[0] for i in cmds.ls(type='locator', o=1, r=1, ni=1) if "Temp_" in i ]
    curve_shapes = [cmds.listRelatives(name, shapes=True, path=True)[0] for name in curve_names]#multiple shapes can be assighned im guessing but we just need the one 
    #We now have a bunuch of names because having the objects would be to much i guess
    
    def get_knots(shape):
        info_node = cmds.createNode('curveInfo')
        cmds.connectAttr(f'{shape}.worldSpace[0]', f'{info_node}.inputCurve')
        knots = cmds.getAttr(f'{info_node}.knots[*]')
        cmds.disconnectAttr(f'{shape}.worldSpace[0]', f'{info_node}.inputCurve')
        cmds.delete(info_node)
        return knots
    
    get_color = lambda shape:{
        "override":cmds.getAttr(f'{shape}.overrideEnabled'),
        "index_color":cmds.getAttr(f'{shape}.overrideColor'),
        "rgb_color":cmds.getAttr(f'{shape}.overrideColorRGB'),
        "should_rgb":cmds.getAttr(f'{shape}.overrideRGBColors')
        }
        
    curves = [
                    {"name":name,
                    "cvs":cmds.getAttr(f"{curve}.cv[*]"),
                    "degree":cmds.getAttr(f"{curve}.degree"),
                    "form":cmds.getAttr(f"{curve}.form"),
                    "knots":get_knots(curve),
                    "color":get_color(curve),                     
                    "transform":cmds.xform(name, query=True, wd=True, piv=True)}#cmds.getAttr(name+'.worldMatrix')}#cmds.xform(name, query=True, m=True, rp=True, ws=True)}
                    
            
        for curve,name in zip(curve_shapes,curve_names)
    ]
    
    locators = [{"name":loc, "transform":cmds.xform(loc, query=True, wd=True, piv=True), "color":get_color(loc)} for loc in locator_names]
    
    data = {"curves":curves,"locators":locators}
    import os
    start = os.path.dirname(__file__)
    file = start + "/template.json"
    with open(file, "w") as fh:
        json.dump(data, fh, indent=4)
   
def import_temp_objects():
    """Utilities for Importing Curves and Locators from json data"""
    import os
    start = os.path.dirname(__file__)
    file = start + "/template.json"
    with open(file, "r") as fh:
        data = json.load(fh)
    return data

    
    

    


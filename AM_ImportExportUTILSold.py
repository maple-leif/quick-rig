import maya.cmds as cmds
import json
from dataclasses import dataclass

class ExportUtils():
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

    class DataEncoder(json.JSONEncoder):
        """ Sets formating for dataclasses for exporting to json  """
        def default(self, obj):
            if isinstance(obj, CurveData):
                return {
                    "name":obj.name,
                    "cvs": obj.cvs,
                    "degree": obj.degree,
                    "form": obj.form,
                    "knots": obj.knots,
                    "color": obj.color,
                    "transform": obj.transform,
                    
                }
            elif isinstance(obj, LocatorData):
                return {
                    "name":obj.name,
                    "transform": obj.transform,
                    "color": obj.color,
                }
            return json.JSONEncoder.default(self, obj)
        
    def export_temp_objects(self):
        ""
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
                CurveData(name=name,
                        cvs=cmds.getAttr(f"{curve}.cv[*]"),
                        degree=cmds.getAttr(f"{curve}.degree"),
                        form=cmds.getAttr(f"{curve}.form"),
                        knots=get_knots(curve),
                        color=get_color(curve),                     
                        transform=cmds.xform(name, query=True, m=True)
                )
            for curve,name in zip(curve_shapes,curve_names)
        ]
        
        locators = [LocatorData(name=loc, transform=cmds.xform(loc, query=True, m=True), color=get_color(loc)) for loc in locator_names]
        
        data = {"curves":curves,"locators":locators}
        import os
        start = os.path.dirname(__file__)
        file = start + "/template.json"
        with open(file, "w") as fh:
            json.dump(data, fh, indent=4, cls=self.DataEncoder)

    

    
    
class ImportUtils():
    """Utilities for Importing Curves and Locators from json data"""
    with open('template.json', 'r') as file:
        data = json.load(file)
    print(data)
    
    
@dataclass
class CurveData():
    name: str
    cvs : None
    degree : None
    form : None
    knots: None
    color : None 
    transform : None 
        
@dataclass
class LocatorData():
    name: str
    transform : None
    color: None
    


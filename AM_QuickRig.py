from PySide6.QtCore import *
from PySide6.QtWidgets import *
from maya import OpenMayaUI as omui 
from shiboken6 import wrapInstance
import maya.cmds as cmds
from QuickRig import AM_ImportExportUTILS as IO



class Template_WindowUI(QWidget):
    
    def __init__(self):
        self.br = buildrig()
        super(Template_WindowUI, self).__init__()
        mw_ptr = omui.MQtUtil.mainWindow() 
        mayaMainWindow = wrapInstance(int(mw_ptr), QMainWindow)
        self.setParent(mayaMainWindow)
        self.draw()

    def _close(self):
        "Close window"
        self.close
    
    def draw(self):
        """Set up Window"""
        self.setWindowTitle("QuickRig")
        self.resize(200,125)
        
        """Layout"""
        box = QVBoxLayout(self)

        """Dynamic Button and label builder"""    
        def buttondoer(i,br,win):
            
            funcs = {1:br.step_one, 2:br.step_two, 3:br.step_three, 4:br.step_four}
            lbls = {1:QLabel("Line up the template Controls with your mesh then press step 1!", objectName = 'Lbl', wordWrap=True),
                    2:QLabel("Line up the locators with desired Bone positions then press step 2!", objectName = 'Lbl', wordWrap=True),
                    3:QLabel("Line up the Pivots rig with your mesh then press step 3!", objectName = 'Lbl', wordWrap=True),
                    4:QLabel("Press step 4 To generate rig then start skinnning!", objectName = 'Lbl', wordWrap=True)
                    }
            lbls[i].font().setPointSize(72)
            box.addWidget(lbls[i])
            button = QPushButton(f"Step {i}", self)
            button.clicked.connect(funcs[i])
            button.clicked.connect(button.hide)
            button.clicked.connect(lbls[i].hide)  
            button.clicked.connect(lambda: buttondoer(i+1,br,win)) if i < 4 else button.clicked.connect(win.close)
            box.addWidget(button)
    
        
        buttondoer(1, self.br,self)
        
    
        
        """Draw"""
        self.setWindowFlags(Qt.Window) 
        self.show()# Run 
        self = None # widget is parented, so it will not be destroyed.
        #^^^This is done for mem managment im guessing??
        
        
        


class buildrig():
    """This class contains the methods for each step of the process"""
    data = None
    """
        This is very extra I know but I don't want to hard code more than i have to
        and these can be used for the rest of the steps as well
        Think of it as future proffing incase any of these values change
    """
    
    #put in json?
    prefixes = {"TMP": "Temp_", "DEF":"DEF_","CTRL":"CTRL_", "MCH":"MCH_", "TGT":"TGT_"}
    sufixes = {"Center":"_C", "Left":"_L","Right":"_R"}
    controls = ['Root','SubRoot','Hips','Pole','Foot','Pivot','HeelPivot','ToeRaise']
    bone_loc = ['BN_Hip','BN_Thy','BN_Knee','BN_Ankle', 'BN_Ball','BN_Toe']
    pivots = ['FootCtrl_Pivot','Piv_Ankle',  'Piv_Foot_In', 'Piv_Foot_Out', 'Piv_Toe']
    
    def toggle_visabiltiy(self, layers, on_off):
        for obj in layers:
            cmds.setAttr(obj+"Shape.visibility", on_off)
            
    def set_limits(self, limits):
        for lims in limits:
            #I'm sorry I just dont want to add twice the lines to the json file
            etx=lims["tx"][0] or lims["tx"][1]
            ety=lims["ty"][0] or lims["ty"][1]
            etz=lims["tz"][0] or lims["tz"][1]
            erx=lims["rx"][0] or lims["rx"][1]
            ery=lims["ry"][0] or lims["ry"][1]
            erz=lims["rz"][0] or lims["rz"][1]
            cmds.transformLimits(lims["name"], etx=[etx,etx],ety=[ety,ety],etz=[etz,etz],
                                 erx=[erx,erx],ery=[ery,ery],erz=[erz,erz],
                                 tx = lims["tx"] ,ty= lims["ty"] ,tz= lims["tz"] ,
                                 rx= lims["rx"] ,ry= lims["ry"] ,rz= lims["rz"] )
            
    def lock(self, obj, atrb, lock):
        for a in atrb:
            cmds.setAttr(obj+"."+a,l=lock,cb=False,k=False)
    
    def colorize(self,obj,color):
        colors = self.data["color"]
        cmds.setAttr(f"{obj}Shape.overrideEnabled", True)
        cmds.setAttr(f"{obj}Shape.overrideRGBColors", True)
        cmds.setAttr(f"{obj}Shape.overrideColorR", colors[color][0])# I hate this 
        cmds.setAttr(f"{obj}Shape.overrideColorG", colors[color][1])
        cmds.setAttr(f"{obj}Shape.overrideColorB", colors[color][2])
    
    def step_one(self):
        cmds.undoInfo(openChunk=True, chunkName='Step 1')
        """Import, make all objects, hide all but the bone locators"""
        self.data = IO.import_temp_objects()
        def build_obj( obj,type):
            ""
            make_curve_or_locator = {"CRV":lambda o: cmds.curve(p= o["cvs"],k=o["knots"],d = o["degree"], ws=True), "LOC": lambda o: cmds.spaceLocator(p=o["transform"][:3])}
            
            
            t= make_curve_or_locator[type](obj)
            cmds.rename(t, f"{obj['name']}")
            cmds.xform(obj["name"], wd=True, piv=obj["transform"][:3]) if type=="CRV" else cmds.xform(obj["name"], centerPivots=True)
            self.lock(obj["name"], ["r"], True) if type=="LOC" else None          
            self.colorize(obj["name"],"white")
            return obj["name"]
        
        curves_names = [build_obj(curve,"CRV") for curve in self.data["curves"]]
        locators_names = [build_obj(loc,"LOC") for loc in self.data["locators"]]
        
        #I could proably do this in two loops but i would need a way to get the prefixs corect, Proably just build them out before hand but eh
        for name in self.controls[1:3]+[self.controls[4]]:#subroot,foot,hips
            cmds.parent(self.prefixes["TMP"]+self.prefixes["CTRL"]+name,self.prefixes["TMP"]+self.prefixes["CTRL"]+ self.controls[0])
             
        cmds.parent(self.prefixes["TMP"]+self.bone_loc[0],self.prefixes["TMP"]+self.prefixes["CTRL"]+ self.controls[0])# hipbn
        
        for name in self.controls[5:]+[self.controls[3]]:#heel,toe,pivot to foot
            cmds.parent(self.prefixes["TMP"]+self.prefixes["CTRL"]+name,self.prefixes["TMP"]+self.prefixes["CTRL"]+ self.controls[4]) 
            
        for name in self.pivots+self.bone_loc[1:]:#foot pivots and bns (not hips) to foot
            cmds.parent(self.prefixes["TMP"]+name,self.prefixes["TMP"]+self.prefixes["CTRL"]+ self.controls[4])
        
        #Layers for toggling visability between steps and keeping up with names and order
        self.layer_ctrls = [self.prefixes["TMP"]+self.prefixes["CTRL"]+name for name in self.controls]#CTRLS
        self.layer_bones = [self.prefixes["TMP"]+name for name in self.bone_loc]#Bones
        self.layer_pivots = [self.prefixes["TMP"]+name for name in self.pivots]#Pivots
        
        #TODO set viewport to xray for locators maybe curves  
        self.toggle_visabiltiy(self.layer_bones+self.layer_pivots, False)  
        cmds.undoInfo(closeChunk=True)
    def step_two(self):
        """Hide bone locators, show pivot locators """
        #TODO set viewport to xray for locators maybe curves
        cmds.undoInfo(openChunk=True, chunkName='Step 2')
        self.toggle_visabiltiy(self.layer_bones, True)
        self.toggle_visabiltiy(self.layer_ctrls, False)
        cmds.undoInfo(closeChunk=True)
    def step_three(self):
        """Hide previous show controls"""
        cmds.undoInfo(openChunk=True, chunkName='Step 3')
        #TODO set viewport to xray for locators maybe curves
        self.toggle_visabiltiy(self.layer_pivots, True)
        self.toggle_visabiltiy(self.layer_bones, False)
        cmds.undoInfo(closeChunk=True)
    
    def step_four(self):
        cmds.undoInfo(openChunk=True, chunkName='Step 4')
        #self.toggle_visabiltiy(self.layer_pivots, False)
        """Build the damn rig"""
        for name in self.layer_pivots+self.layer_bones:
            self.lock(name, ["r"], False)#Unlock
        
        """Bones"""
        bones = {"DEF"+bn[2:]:cmds.xform(self.prefixes["TMP"]+bn, query=True, ws=True, piv=True) for bn in self.bone_loc}
        self.layer_bones = list(bones.keys())
        [cmds.delete(self.prefixes["TMP"]+bn) for bn in self.bone_loc]
        #this or parent hips to world after wards
        cmds.select(d=True)
        hbone,hplace = list(bones.items())[0]
        cmds.joint(n=hbone+self.sufixes["Center"], p=hplace[:3])# hips
        parent= hbone+self.sufixes["Center"]#rparent =
        for bone,place in list(bones.items())[1:]:
            cmds.select(parent)
            cmds.joint(n=bone+self.sufixes["Left"], p=place[:3])
            parent = bone+self.sufixes["Left"]
        
        """Orient"""
        cmds.joint(hbone+self.sufixes["Center"],e=True, oj='xyz', sao='yup',children=True)
        #Fix knees May be fucked either way ngl
        cmds.joint(self.layer_bones[2]+self.sufixes["Left"],e=True, oj='xyz', sao='ydown')
        #cmds.joint(self.layer_bones[2]+self.sufixes["Right"],e=True, oj='xyz', sao='ydown')
        
        
        """Controls"""
        
        """Start with changing temp to CTRL_*_L//"""
        layer_ctrls_temp = [cmds.rename(name, name[5:]) for name in self.layer_ctrls[:3]]
        layer_ctrls_temp += [cmds.rename(name, name[5:]+self.sufixes["Left"]) for name in self.layer_ctrls[3:]]
        self.layer_ctrls = layer_ctrls_temp
        self.layer_ctrls[2]=cmds.rename(self.layer_ctrls[2], self.layer_ctrls[2]+self.sufixes["Center"])#hips
        self.layer_pivots = [cmds.rename(name, self.prefixes["MCH"]+self.prefixes["TGT"]+name[5:]+self.sufixes["Left"]) for name in self.layer_pivots]
        cmds.xform(self.layer_ctrls[4], ws=True, piv=cmds.xform(self.layer_pivots[0], query=True, ws=True, piv=True)[:3])
        for name in self.layer_pivots:
            cmds.parent(name, w=True)
        for name in self.layer_ctrls[3:6]:
            self.colorize(name,"green")
            cmds.makeIdentity(name,a=True)
        for name in self.layer_ctrls[6:]:
            self.colorize(name,"lime")
            cmds.makeIdentity(name,a=True)
        self.colorize("CTRL_Root","purple")
        self.colorize("CTRL_SubRoot","yellow")
        self.colorize("CTRL_Hips_C","blue")
        
        """Add missing locators"""
        self.layer_pivots += [cmds.spaceLocator(name=self.prefixes["MCH"]+bone[4:]+self.sufixes["Left"],p=cmds.xform(bone+self.sufixes["Left"], query=True, ws=True, piv=True)[:3],a=True)[0] for bone in self.layer_bones[-3:]][::-1]
        self.layer_pivots += [cmds.duplicate(self.layer_pivots[-2], n="MCH_ToeRaise_L")[0],cmds.duplicate(self.layer_pivots[-2], n="MCH_TGT_FootPivot_L")[0]]
        self.layer_pivots[0] = cmds.rename(self.layer_pivots[0],'MCH_TGT_FootParent_L')
        [cmds.xform(l, centerPivots=True) for l in self.layer_pivots[-5:]]#Fix Locator pivots because maya
        
        """Hierarchy"""
        
        cmds.parent(self.layer_pivots[0],self.layer_ctrls[1], a=True)
        cmds.parent(self.layer_pivots[-2],self.layer_pivots[-4], a=True)
        cmds.parent(self.layer_pivots[-1],self.layer_pivots[0], a=True)
        for x,y in zip(self.layer_pivots, self.layer_pivots[1:-2:]):
            cmds.parent(y,x,a=True)    
        cmds.parent(self.layer_ctrls[2],self.layer_ctrls[4],self.layer_ctrls[1], a=True)
        for x,y in zip(self.layer_ctrls[4:], self.layer_ctrls[5:]):#Tops
            cmds.parent(y,x,a=True)
        cmds.parent(self.layer_ctrls[3],self.layer_ctrls[4],a=True)#Pole
        cmds.parent("DEF_Hip_C","CTRL_SubRoot", a=True)#hips
        
        """Add missing controls"""
        self.layer_ctrls += [cmds.circle(n="CTRL_ToePivot_L",c=cmds.xform("MCH_TGT_Piv_Toe_L",q=True, piv=True, ws=True)[:3],nry=1,nrz=0)[0]]
        self.colorize(self.layer_ctrls[-1],"lime")
        cmds.parent("CTRL_ToePivot_L",self.layer_ctrls[4], r=True)
        cmds.xform("CTRL_ToePivot_L", centerPivots=True)
        cmds.parent(self.layer_ctrls[-3], "CTRL_ToePivot_L", a=True)
        
        
        """IKS"""
        layer_ikl=[cmds.ikHandle(sj=start+self.sufixes["Left"],ee=end+self.sufixes["Left"], n="MCH_Ik_"+end[4:]+self.sufixes["Left"])[0] for start, end in zip(self.layer_bones[1:2]+self.layer_bones[3:],self.layer_bones[3:])]
        for ik in layer_ikl:
            cmds.parent(ik, ik[:3]+ik[6:], a=True)
        cmds.parent("MCH_Ik_Toe_L","MCH_ToeRaise_L", a=True)
        #layer_ikr=[cmds.ikHandle(sj=start+self.sufixes["Right"],ee=end+self.sufixes["Right"], n="MCH_Ik_"+end[3:]+self.sufixes["Right"]) for start, end in zip(self.layer_bones[1:2]+self.layer_bones[3:],self.layer_bones[3:])]
        
        """Unlock"""
        for l in self.layer_pivots:
            self.lock(l, ["r"], False)
            
        """Limtis"""
        self.set_limits(self.data["limits"])
        
        """Constraints"""
        constraint_funcs = {"parent":cmds.parentConstraint,"orient":cmds.orientConstraint,"pole":cmds.poleVectorConstraint}
        for c in self.data["constraints"]:
            if c["constraint"] == "orient":
                constraint_funcs[c["constraint"]](c["target"],c["name"],sk=c["sk"])
            elif c["constraint"] == "pole":
                constraint_funcs[c["constraint"]](c["target"],c["name"])
            else:
                constraint_funcs[c["constraint"]](c["target"],c["name"],mo=True)
        """Expresions"""
        
        for expresion in self.data["expresions"]:
            for e,st in expresion["expresions"]:
                cmds.expression(expresion["name"],s=e, n=expresion["name"]+st)
         
        """Lock"""
        for locks in self.data["lock"]:
            self.lock(locks["name"],locks["locks"], True)
        self.lock(self.layer_bones[0]+"_C",["t","r","s"], True)#Hips
        
        """Mirror Foot"""
        cmds.duplicate(["MCH_TGT_FootParent_L","CTRL_Foot_L","DEF_Thy_L"],un=True,rc=True)
        cmds.group(["MCH_TGT_FootParent_L1","CTRL_Foot_L1","DEF_Thy_L1"], n="right")
        cmds.xform("right", ws=True, piv=[0,0,0])
        right_side = cmds.listRelatives("right", c=True, ad=True,typ="transform")
        cmds.delete(["DEF_Hip_C1","CTRL_Hips_C1"])

        left_side = [name+"_L" for name in self.layer_bones[1:]] + self.layer_pivots + self.layer_ctrls[3:] 
        right_side = [cmds.rename(name+"1",name[:-2]+"_R") for name in left_side]
        #Unironically this is the best way I know to update these expresions which has to be done for somereason else they do not calculate corectly wtf?
        cmds.scale(-1,1,1,"right")
        #Fuck Maya Fuck Maya Fuck Maya Fuck Maya Fuck Maya Fuck Maya Fuck Maya 
        #cmds.parent("MCH_TGT_FootParent_R","DEF_Thy_R","CTRL_SubRoot",a=True)
        cmds.rename("right","right_controls")#Either this or unparent everything on the right including the shape data of foot make id and then reparent a=1 MAYBE
        cmds.parent("DEF_Thy_R","DEF_Hip_C",a=True)
        cmds.expression(self.data["expresions"][1]["name"]+"rx1",e = True)
        cmds.expression(self.data["expresions"][1]["name"]+"rz1",e = True)
        #cmds.scale(1,1,1,"MCH_TGT_FootParent_R")
        #cmds.scale(1,1,1,"CTRL_Foot_R")
        cmds.scale(1,1,1,"DEF_Thy_R")
        #cmds.xform("CTRL_Foot_R",ro=[0,180,0],ws=True,a=True)
        #cmds.rotate(0,0,0,"CTRL_Foot_R")
        
        for name in self.layer_ctrls[3:6]:
            self.colorize(name[:-2]+"_R","red")
        for name in self.layer_ctrls[6:]:
            self.colorize(name[:-2]+"_R","blush")
        
        
        """Set up layers"""
        layers = []
        self.toggle_visabiltiy(right_side[5:], True)
        self.toggle_visabiltiy(self.layer_pivots, True)
        self.toggle_visabiltiy(self.layer_ctrls, True)
        [cmds.rename(name+"1", name[:-1]+"R") for name in layer_ikl]
        cmds.select(self.layer_ctrls+[name[:-1]+"R" for name in self.layer_ctrls[3:]])
        layers.append(cmds.createDisplayLayer(nr=True,n="CTRLS"))
        cmds.select(self.layer_pivots+[name[:-1]+"R" for name in self.layer_pivots+layer_ikl]+layer_ikl)
        layers.append(cmds.createDisplayLayer(nr=True,n="MCH"))
        cmds.select([self.layer_bones[0]+"_C"]+[name+"_L" for name in self.layer_bones[1:]]+[name+"_R" for name in self.layer_bones[1:]]) 
        layers.append(cmds.createDisplayLayer(nr=True,n="DEF"))
        cmds.select(self.layer_ctrls[:2])
        layers.append(cmds.createDisplayLayer(nr=True,n="ROOTS"))
        cmds.setAttr(layers[0]+".visibility", False)
        cmds.setAttr(layers[1]+".visibility", False)
        
        
        cmds.undoInfo(closeChunk=True)
        
        

def main():
    win = Template_WindowUI()

# CustomProceduralRigTool
Custom Procedural Rig Tool for Game(Unreal)		    
This is a procedural modular rigging tool for game, especially for Unreal Engine.		    
Before using the script, you need to make true that your maya setup is OK for UE4.		    
Because this is a modular rigging tool, you can use it to rig any type of creatures. For example, you can use it to rig a monster with 4
arms, 2 spines and multi legs.		

# How to install:
1. Download the project file and unzip it somewhere in the computer, make ture to remember the directory of the unzip file location;		    
2. Open Maya 2017+ and open script Editor;		    
3. New a Python tab, and enter following scrip;		    

Dir = 'X:\WHERE\YOU\PUT\THE\FILE'		    
import sys		

if Dir not in sys.path:		
				sys.path.append(r'X:\WHERE\YOU\PUT\THE\FILE')      
  
import CustomProceduralRigTool    
from CustomProceduralRigTool import Main_UI as Main_UI    
reload(Main_UI)    
    
UI = Main_UI.RiggingMainUI(dock=1)    

# How to use:
I will record a video for using this script. To be continued...    

# Bugs:
If you find any type of bugs, please e-mail me at: razer_mamba@qq.com.    
    
If you like this script, please STAR this repository. Thank you very much.    

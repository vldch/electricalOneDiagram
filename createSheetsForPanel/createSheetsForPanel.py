import clr
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
clr.AddReference("RevitAPI")
import Autodesk
from Autodesk.Revit.DB import *
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
from System.Collections.Generic import *
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
from operator import itemgetter
ids = uidoc.Selection.GetElementIds()
idd = [str(i) for i in ids]
#-----------------------------------------------------
if isinstance(idd, list) == True:
	views = [doc.GetElement(ElementId(int(i))) for i in idd]
else:
	views = doc.GetElement(ElementId(int(idd)))
#------------------------
titletype = IN[0]
titletype2 = IN[4]
pX = IN[1]/304.8
pY = IN[2]/304.8
xyz=XYZ(pX,pY,0)
#----------------------------------------------------
list=[]
for view in views:
	name = view.Name
	list.append([view,name])
list2 = sorted(list,key=itemgetter(1))
views2=[]
for v in list2:
	views2.append(v[0])
list_sheet=[]
i=0
p=0
TransactionManager.Instance.EnsureInTransaction(doc)
for view in views2:
	name1 = view.Name
	check = name1[-2:]
	name2 = name1[:-2]
	if check=="_1":
		sheet = ViewSheet.Create(doc,ElementId(titletype.Id))
		xyz1 = xyz
		name2 = name2+" (начало)"
		p=p+1
	else:
		sheet = ViewSheet.Create(doc,ElementId(titletype2.Id))
		xyz1 = XYZ(pX+40/304.8,pY,0)
		name2 = name2+" (продолжение)"
		p=0		
	sheet.Name = name2
	try:
		Viewport.Create(doc, sheet.Id, view.Id, xyz1)
	except:
		a = Autodesk.Revit.DB.Electrical.PanelScheduleSheetInstance.Create(doc, view.Id, sheet)
		a1 = a.Location.Move(xyz)	
	if p>1:
		name4 = name3[:-9]
		sheet2.Name = name4
		p=1	
	sheet2=sheet
	name3=name2			
	i=i+1
if p==1:
	name4 = name3[:-9]
	sheet2.Name = name4
TransactionManager.Instance.TransactionTaskDone()	
OUT = "OK"

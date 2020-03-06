import clr
import math
clr.AddReference('ProtoGeometry')
from Autodesk.DesignScript.Geometry import *
clr.AddReference('RevitAPI')
from Autodesk.Revit.DB import *
import Autodesk
clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.GeometryConversion)
clr.AddReference("RevitServices")
import RevitServices
from RevitServices.Persistence import DocumentManager
from RevitServices.Transactions import TransactionManager
clr.AddReference("RevitNodes")
import Revit
clr.ImportExtensions(Revit.Elements)
doc = DocumentManager.Instance.CurrentDBDocument
uiapp = DocumentManager.Instance.CurrentUIApplication
app = uiapp.Application
from System.Collections.Generic import *
uidoc = DocumentManager.Instance.CurrentUIApplication.ActiveUIDocument
a_view = doc.ActiveView
circuits = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_ElectricalCircuit).WhereElementIsNotElementType().ToElements()
schemes = FilteredElementCollector(doc,a_view.Id).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType().ToElements()
sch_type = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsElementType().ToElements()
views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
spaces = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_MEPSpaces).WhereElementIsNotElementType().ToElements()	
phase = doc.GetElement(Autodesk.Revit.DB.ElementId(int(float(spaces[0].get_Parameter(BuiltInParameter.ROOM_PHASE_ID).AsValueString()))))
from operator import itemgetter
vf = ViewFamily.Drafting
#-----------------------------------------------------
#-----------------ВРЕМЕННЫЕ ФУНКЦИИ-----------------------


##################################################################################################################################################
#--------------------------УДАЛЕНИЕ ЭЛЕМЕНТОВ-----------------------------------------------------------------------------------------------------------
##################################################################################################################################################
def delete_generic_anotations(doc,view):
	els_1 = FilteredElementCollector(doc,view.Id).OfCategory(BuiltInCategory.OST_GenericAnnotation).WhereElementIsNotElementType().ToElements()
	TransactionManager.Instance.EnsureInTransaction(doc)
	for el in els_1:
		try:
			id = el.Id
			doc.Delete(id)
		except:
			0		
	TransactionManager.Instance.TransactionTaskDone()
	return "ok"
#-----------Удаление элементов-----------------
def delete_els(els):
	for el in els:
		id=el.Id
		doc.Delete(id)	
##################################################################################################################################################
#--------------------------СОЗДАНИЕ ЭЛЕМЕНТОВ-----------------------------------------------------------------------------------------------------
##################################################################################################################################################

#--------------СОЗДАНИЕ НОВОГО ЧЕРТЕЖНОГО ВИДА ПО ПАНЕЛИ ДЛЯ РАЗМЕЩЕНИЯ СХЕМЫ ЩИТА-----------	

def create_view(doc,view_name):
	t_view = get_draftingview_type()
	list_views = get_draftingviews(doc)
	name_drafting_views = list_views[0]
	list_drafting_views = list_views[1]
	dview=None
	check=0
	#ПРОВЕРКА ИМЕЕТСЯ ЛИ УЖЕ ВИД С ИМЕНЕМ view_name
	i=0
	for name in name_drafting_views:
		if name==view_name:
			dview = list_drafting_views[i]
			check = 1
		i=i+1
	#СОЗДАНИЕ НОВОГО ВИДА ЕСЛИ ЕГО НЕТ		
	if check==0:		
		TransactionManager.Instance.EnsureInTransaction(doc)		
		dview = ViewDrafting.Create(doc,t_view)
		dview.Name = view_name
		TransactionManager.Instance.TransactionTaskDone()
		
	return dview
	
#--------------СОЗДАНИЕ ШАПКИ СХЕМЫ ЩИТА-----------	

def create_head(doc,dview,head_types,keys_h,panel,panel_name,coss,abc,circuit_head,circuit_2):
	head_type_name = get_type_panel(panel,head_types,keys_h)
	type = filter_type_by_name(sch_type,head_type_name)
	TransactionManager.Instance.EnsureInTransaction(doc)
	point = XYZ(0,0,0)
	el_2D = create_el(point,type,dview)
	copy_pars_to_head(panel,el_2D,panel_name,coss,abc,circuit_head,circuit_2)
	TransactionManager.Instance.TransactionTaskDone()
	
#--------------СОЗДАНИЕ НИЖНЕЙ ЧАСТИ СХЕМЫ ЩИТА-----------	

def create_circuits_down(doc,dview,circuits,x,y,type_down):
	TransactionManager.Instance.EnsureInTransaction(doc)
	new_els=[]
	coss = []
	for circuit in circuits:
		point = XYZ(x,y,0)
		type_2D = filter_type_by_name(sch_type,type_down)
		el_2D = create_el(point,type_2D,dview)
		add_id(circuit,el_2D,p_2D_id)
		list = copy_pars_to_down(circuit,el_2D)
		_cos = list[0]
		cat = list[1]
		coss.append(_cos)
		change_UGO(el_2D,cat)
		x = x + 20/304.8
		y = y + 0
		new_els.append([circuit,el_2D])
	TransactionManager.Instance.TransactionTaskDone()
	return new_els,coss
	
#--------------СОЗДАНИЕ ВЕРХНЕЙ ЧАСТИ СХЕМЫ ЩИТА-----------

def create_circuits_up(doc,dview,circuits,x,y,types_up,keys,Номер_контактора):
	TransactionManager.Instance.EnsureInTransaction(doc)
	new_els=[]
	i=0
	for circuit in circuits:
		point = XYZ(x,y,0)
		key = circuit.LookupParameter("KAV.Назначение аппарата защиты").AsString()
		type_2D = types_up[0]
		if key == "выключатель":
			a = circuit.LookupParameter("Аналог контакторов групповых линий").AsValueString()
			if a is not None and a!="(none)" and a!="(нет)" and len(a)>0:
				Номер_контактора = Номер_контактора + 1
				type_2D = types_up[1]
			else:
				type_2D = types_up[0]			
		elif key == "силовой контакт пускателя":
			Номер_контактора = Номер_контактора + 1
			type_2D = types_up[1]
		elif key == "узо":
			type_2D = types_up[2]
		elif key == "рубильник":	
			type_2D = types_up[3]	
		#type_2D = get_type_2D(circuit,types_up,keys)
		type_2D = filter_type_by_name(sch_type,type_2D)
		el_2D = create_el(point,type_2D,dview)
		add_id(circuit,el_2D,p_2D_id)
		list_2 = copy_pars_to_up(circuit,el_2D,Номер_контактора,key,name_uniq,list_uniq)
		x = x + 20/304.8
		y = y + 0
		new_els.append([circuit,el_2D])
		Номер_автомата = list_2[2]
		i=i+1
	TransactionManager.Instance.TransactionTaskDone()
	return new_els,x,y,Номер_контактора,Номер_автомата,i

#-----------------Создание 2D элемента на виде--------------------

def create_el(point,familytype,view):
	el = doc.Create.NewFamilyInstance(point,familytype,view)
	return el

#----------------Создание резервной группы--------------------------------

def create_reserv(name_uniq,list_uniq,x,y,type_down,Номер_контактора,Номер_автомата,i_1,b,n_1,panel_name,prefix,suffix,dview,perc_reserv):
	Номер = int(float(Номер_автомата))
	new_uniq=[]
	new_list=[]
	sum_list=[]
	i=0	
	k=0
	for n in name_uniq:
		if n not in new_uniq:
			new_uniq.append(n)
			new_list.append([list_uniq[i],-k])
			k=k+1
		i=i+1
	new_list = sorted(new_list, key=itemgetter(1))
	for name_2 in new_uniq:
		sum=0
		for name_3 in name_uniq:
			if name_3 == name_2:
				sum = sum+1
		sum_list.append(sum)	
	list4=[]
	list5=[]
	j=0
	for new_l in new_list:
		el = new_l[0]
		kolvo = sum_list[j]
		n2 = math.ceil(kolvo*perc_reserv/100)
		i2=0
		while i2<n2:
			list4.append(el)
			i2=i2+1
		j=j+1	
	for list_pars in list4:
		if i_1>b:
			n_1=n_1+1
			view_name = prefix+panel_name+suffix+"_"+str(n_1)
			dview = create_view(doc,view_name)
			i_1=0
			x=0
		Номер = Номер+1
		list_2 = create_reserv_down(doc,dview,x,0,type_down,Номер)
		el_2D = list_2[0]
		list_3 = create_reserv_up(doc,dview,x,116/304.8,types_up,list_pars,Номер_контактора,Номер)
		el_2D = list_3[0]
		Номер_контактора = list_3[1]
		x=x+20/304.8
		i_1=i_1+1
	return sum_list			
#--------------СОЗДАНИЕ НИЖНЕЙ ЧАСТИ СХЕМЫ ЩИТА-----------		
		
def create_reserv_down(doc,dview,x,y,type_down,Номер):
	Номер_автомата = str(Номер)
	TransactionManager.Instance.EnsureInTransaction(doc)
	point = XYZ(x,y,0)
	type_2D = filter_type_by_name(sch_type,type_down)
	el_2D = create_el(point,type_2D,dview)
	list = copy_pars_to_down_reserv(el_2D,Номер_автомата)
	x = x + 20/304.8
	y = y + 0
	TransactionManager.Instance.TransactionTaskDone()
	return el_2D,0
	
#--------------СОЗДАНИЕ ВЕРХНЕЙ ЧАСТИ СХЕМЫ ЩИТА-----------

def create_reserv_up(doc,dview,x,y,types_up,list,Номер_контактора,Номер):
	Номер_автомата = str(Номер)
	TransactionManager.Instance.EnsureInTransaction(doc)
	point = XYZ(x,y,0)
	key = list[7]
	a = list[8]
	type_2D = types_up[0]
	if key == "выключатель":
		if a is not None and a!="(none)" and a!="(нет)" and len(a)>0:
			Номер_контактора = Номер_контактора + 1
			type_2D = types_up[1]
		else:
			type_2D = types_up[0]			
	elif key == "силовой контакт пускателя":
		Номер_контактора = Номер_контактора + 1
		type_2D = types_up[1]
	elif key == "узо":
		type_2D = types_up[2]
	elif key == "рубильник":	
		type_2D = types_up[3]	
	type_2D = filter_type_by_name(sch_type,type_2D)
	el_2D = create_el(point,type_2D,dview)
	copy_pars_to_up_reserv(el_2D,Номер_контактора,list,Номер_автомата)
	x = x + 20/304.8
	y = y + 0
	TransactionManager.Instance.TransactionTaskDone()
	return el_2D,Номер_контактора		
			
##################################################################################################################################################
#--------------------------ФИЛЬТРАЦИЯ-----------------------------------------------------------------------------------------------------
##################################################################################################################################################	

#-----Проверка созданных 2D элементов схем
def check_create(els,sch,par):
	id_els = [i.Id for i in els]
	id_sch=[]
	for i in sch:
		id = get_param(i,par)
		if id is not None:
			id_sch.append(id)	
	list_new = []
	list_update = []
	i=0
	for id_el in id_els:
		if (id_el not in id_sch) and (str(id_el) not in id_sch):
			list_new.append(els[i])
		else:
			j=0
			for id in id_sch:
				if id==id_el or id==str(id_el):
					sch1 = sch[j]
				j=j+1	
			list_update.append([els[i],sch1])
		i=i+1
	return list_new,list_update	
			
def filter_els(els,par,val):
	list=[]
	for el in els:
		val2 = get_param(el,par)
		if val == val2:
			list.append(el)
	return list

def filter_els_head(els,val):
	list=[]
	for el in els:
		val2 = el.LookupParameter("Load Name").AsString()
		if val2 in val:
			a = el
	return a	
def filter_type_by_name(types,name):
	list=None
	for type in types:
		name2 = type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		if name == name2:
			list = type
	return list		

##################################################################################################################################################
#--------------------------КОПИРОВАНИЕ ПАРАМЕТРОВ-----------------------------------------------------------------------------------------------------
##################################################################################################################################################	

def copy_pars_to_head(panel,head,panel_name,coss,abc,circuit_head,circuit_2):
	TransactionManager.Instance.EnsureInTransaction(doc)	
	head.LookupParameter("Имя щита").Set(panel_name)
	iA = abc[0]
	iB = abc[1]
	iC = abc[2]
	pA = abc[3]
	pB = abc[4]
	pC = abc[5]
	TrueLoad_list = []
	ApparentLoad_list = []
	list_max = [pA, pB, pC]
	Pmax = find_max(list_max)
	head.LookupParameter("I фаза A").Set(str(round(iA, 2)).replace(".",","))
	head.LookupParameter("I фаза B").Set(str(round(iB, 2)).replace(".",","))
	head.LookupParameter("I фаза C").Set(str(round(iC, 2)).replace(".",","))
	head.LookupParameter("P фаза A").Set(str(round(pA, 2)).replace(".",","))
	head.LookupParameter("P фаза B").Set(str(round(pB, 2)).replace(".",","))
	head.LookupParameter("P фаза C").Set(str(round(pC, 2)).replace(".",","))
	list = calc_up(iA,iB,iC)
	kA = list[0]
	head.LookupParameter("Превышение по A").Set(kA.replace(".",","))
	kB = list[1]
	head.LookupParameter("Превышение по B").Set(kB.replace(".",","))
	kC = list[2]
	head.LookupParameter("Превышение по C").Set(kC.replace(".",","))
	kol = panel.LookupParameter("KAV.Количество полюсов аппарата защиты").AsInteger()
	set_phase(head,kol)
	try:
		I_vvod_apparat = _try(panel.LookupParameter("KAV.Mar.Ток уставки расцепителя").AsString())
		Type_vvod_apparat = _try(panel.LookupParameter("KAV.Mar.Тип аппарата защиты").AsString())
		head.LookupParameter("Тип вводного автомата").Set(Type_vvod_apparat)
		head.LookupParameter("Ток вводного автомата").Set(I_vvod_apparat)
		Length_cabel_inner = int(round(float(circuit_head.LookupParameter("2.6_Длина кабеля вручную").AsValueString().replace(",",".")),0))
		WireType_cabel_inner = _try(circuit_head.LookupParameter("KW.Марка изоляции").AsString())
		Sechenie_cabel_inner = _try(circuit_head.LookupParameter("KW.Число, сечение, кол-во жил, напряжение").AsString())
		Panel_cabel_inner = panel.LookupParameter("Supply From").AsString()
		head.LookupParameter("Коробка отбора мощности").Set(Panel_cabel_inner)
		head.LookupParameter("Наименование шинопровода").Set(Name_Busbar)
		Insert_parametr = WireType_cabel_inner + " " + Sechenie_cabel_inner + " " + str(Length_cabel_inner)+"м"
		head.LookupParameter("Ввод-провод").Set(Insert_parametr)
		head.LookupParameter("Ввод-источник").Set(Panel_cabel_inner)
	except:
		0
	for circuits in circuit_2:
		TrueLoad_list.append(round(float(circuits.get_Parameter(BuiltInParameter.RBS_ELEC_TRUE_LOAD).AsValueString().replace(",",".")),2))
		ApparentLoad_list.append(round(float(circuits.get_Parameter(BuiltInParameter.RBS_ELEC_APPARENT_LOAD).AsValueString().replace(",",".")),2))
	SummTrueLoad = summ_power(TrueLoad_list)
	SummApparentLoad = summ_power(ApparentLoad_list)
	CosF = round(SummTrueLoad / SummApparentLoad, 2) 
	head.LookupParameter("CosF").Set(str(CosF).replace(".",","))
	Ks = str(round(panel.get_Parameter(BuiltInParameter.RBS_ELEC_PANEL_TOTAL_DEMAND_FACTOR_PARAM).AsDouble(), 2)).replace(".",",")
	head.LookupParameter("K спроса").Set(Ks)
	Pu = round(pA, 2) + round(pB, 2) + round(pC, 2)
	head.LookupParameter("P установленное").Set(str(round(Pu, 2)).replace(".",","))
	Pr = Pu * float(Ks.replace(",","."))
	Pr_str = str(round(Pr,2))
	head.LookupParameter("P расчетное").Set(Pr_str.replace(".",","))
	#Ir = str(round((Pmax*3) / (0.38 * float(CosF) * 1.732050807568877), 2)).replace(".",",")
	Ir = str(round(Pr / (0.38 * float(CosF) * 1.732050807568877), 2)).replace(".",",")
	head.LookupParameter("I расчетный").Set(Ir)	
	TransactionManager.Instance.TransactionTaskDone()


def copy_pars_to_down(circuit,el_2D):
	TransactionManager.Instance.EnsureInTransaction(doc)
	CosF = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_POWER_FACTOR).AsValueString()
	el_2D.LookupParameter("CosF").Set(str(round(float(CosF.replace(",",".")), 2)).replace(".",","))
	Pu = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_TRUE_LOAD).AsValueString()
	el_2D.LookupParameter("Pu").Set(str(round(float(Pu.replace(",",".")), 2)).replace(".",","))
	#Pp = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_TRUE_LOAD).AsValueString()
	#el_2D.LookupParameter("Pp").Set(str(round(float(Pp.replace(",",".")), 2)).replace(".",","))
	Ip = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_APPARENT_CURRENT_PARAM).AsValueString()
	if Ip == "0,0":
		Ip = "0,1"
	el_2D.LookupParameter("Ip").Set(Ip)	
	U = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_VOLTAGE).AsDouble()
	cN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_NUMBER).AsString()
	pN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_PANEL_PARAM).AsString()
	phase = circuit.LookupParameter(par_Phase).AsString()
	el_2D.LookupParameter("Фаза").Set(phase)
	S = circuit.LookupParameter("KW.Сечение").AsDouble()
	L1 = float(circuit.LookupParameter("2.6_Длина кабеля вручную").AsValueString())
	L2 = float(circuit.LookupParameter("2.6_Длина кабеля для спецификации").AsValueString())
	if L1 == 0 or None:
		L = L2
	else:
		L = L1
	dU = str(calc_dU(Ip,U,L,CosF,S)).replace(".",",")
	el_2D.LookupParameter("dU").Set(dU)
	try:	
		Способ_прокладки = circuit.LookupParameter("KK.Обозначение").AsString()
		el_2D.LookupParameter("Способ прокладки").Set(Способ_прокладки)
	except:	
		el_2D.LookupParameter("Способ прокладки").Set("")
	try:	
		Марка_провода = circuit.LookupParameter("KW.Марка изоляции").AsString()		
		el_2D.LookupParameter("Марка провода").Set(Марка_провода)
	except:
		0	
	try:
		Сечение = circuit.LookupParameter("KW.Число, сечение, кол-во жил, напряжение").AsString()
		el_2D.LookupParameter("Сечение").Set(Сечение)
	except:
		0
	try:		
		Длина = circuit.LookupParameter("2.6_Длина кабеля для спецификации").AsValueString()
		el_2D.LookupParameter("L").Set(Длина)
	except:
		0
	try:	
		Number = cN.replace(pN,"").replace("-Гр.","")
		el_2D.LookupParameter("№").Set(Number)
	except:
		0
	list = generate_name(circuit)	
	LN = list[0]
	category = list[1]
	el_2D.LookupParameter("Наименование потребителей").Set(LN)
	TransactionManager.Instance.TransactionTaskDone()
	CosF=float(CosF.replace(",","."))

	return CosF,category

def copy_pars_to_up(circuit,el_2D,Номер_контактора,key,name_uniq,list_uniq):
	TransactionManager.Instance.EnsureInTransaction(doc)	
	kol = _try(circuit.LookupParameter("KAV.Количество полюсов аппарата защиты").AsInteger())
	set_phase(el_2D,kol)
	try:
		Ток_автомата = _try(circuit.LookupParameter("KAV.Mar.Ток уставки расцепителя").AsString())
		el_2D.LookupParameter("Номинальный ток автомата").Set(Ток_автомата)
	except:
		message.append("Нет параметра <Номинальный ток автомата> в 2D семействе схемы щита верхней")
	try:	
		Ток_контактора = _try(circuit.LookupParameter("KAV.Mar.Ток уставки расцепителя").AsString())
		el_2D.LookupParameter("Номинальный ток контактора").Set(Ток_контактора)
	except:
		0
	try:	
		Ток_утечки_УЗО = _try(circuit.LookupParameter("KAV.Mar.Ток дифференциальной утечки").AsString())
		el_2D.LookupParameter("Ток утечки УЗО").Set(Ток_утечки_УЗО)
	except:
		0
	try:	
		Voltage = circuit.LookupParameter("Voltage").AsValueString()
		el_2D.LookupParameter("Управляющее напряжение").Set(Voltage)
	except:
		0
		
	cN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_NUMBER).AsString()
	pN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_PANEL_PARAM).AsString()	
	Номер_автомата = cN.replace(pN,"").replace("-Гр.","")
	el_2D.LookupParameter("Номер автомата").Set(Номер_автомата)

	el_2D.LookupParameter("Номер контактора").Set(str(Номер_контактора))
	
	try:	
		Тип_автомата = _try(circuit.LookupParameter("KAV.Mar.Тип аппарата защиты").AsString())
		el_2D.LookupParameter("Тип автомата").Set(Тип_автомата)
	except:
		0
	try:	
		Тип_контактора = _try(circuit.LookupParameter("KAV.SP.Тип, марка, обозначение документа").AsString())
		el_2D.LookupParameter("Тип контактора").Set(Тип_контактора)
	except:
		0
	key = _try(circuit.LookupParameter("KAV.Назначение аппарата защиты").AsString())
	a = _try(circuit.LookupParameter("Аналог контакторов групповых линий").AsValueString())	
	name_uniq.append(Ток_автомата+Тип_автомата+key+a)
	list_uniq.append([kol,Ток_автомата,Ток_контактора,Ток_утечки_УЗО,Voltage,Тип_автомата,Тип_контактора,key,a])
	return name_uniq,list_uniq,Номер_автомата
	TransactionManager.Instance.TransactionTaskDone()
#-----Копирование значения из параметра одного элемента в параметр другого------------	
def copy_par(el1,par1,el2,par2):
	val1 = get_param(el1,par1)
	el2.LookupParameter(par2).Set(val1)
	return el2
#------------------Копирование значений параметров между элементами---
def copy_pars(els,pars1,pars2):
	for el in els:
		el1 = el[0]
		el2 = el[1]
		i=0
		for par1 in pars1:
			try:
				copy_par(el1,par1,el2,pars2[i])
			except:
				0			
			i=i+1
			
def add_id(el,sch_el,par):
	id = str(el.Id)
	sch_el.LookupParameter(par).Set(id)	

def set_phase(el,kol):
	if kol==2:
		el.LookupParameter("2 фаза").Set(1)
		el.LookupParameter("3 фаза").Set(0)
	elif kol>2:
		el.LookupParameter("2 фаза").Set(1)
		el.LookupParameter("3 фаза").Set(1)
	else:
		el.LookupParameter("2 фаза").Set(0)
		el.LookupParameter("3 фаза").Set(0)
		
def change_UGO(el_2D,key):
	list = get_name_and_types(el_2D)
	names = list[0]
	types = list[1]
	type = None
	if key == "Осветительные приборы" or key == "Lighting Fixtures":
		i=0
		for name in names:
			if name == osv_2d:
				type = types[i]
			i=i+1
	if key == "Силовые электроприборы" or key == "Electrical Fixtures":
		i=0
		for name in names:
			if name == roz_2d:
				type = types[i]
			i=i+1			
	TransactionManager.Instance.EnsureInTransaction(doc)
	try:
		el_2D.LookupParameter("УГО").Set(type)
	except:
		0	
	TransactionManager.Instance.TransactionTaskDone()		


def copy_pars_to_down_reserv(el_2D,Номер_автомата):
	TransactionManager.Instance.EnsureInTransaction(doc)
	try:	
		el_2D.LookupParameter("№").Set(Номер_автомата)
	except:
		0
	TransactionManager.Instance.TransactionTaskDone()
			
def copy_pars_to_up_reserv(el_2D,Номер_контактора,list,Номер_автомата):
	TransactionManager.Instance.EnsureInTransaction(doc)
	kol = list[0]
	Ток_автомата = _try(list[1])
	Ток_контактора = _try(list[2])
	Ток_утечки_УЗО = _try(list[3])
	Управляющее_напряжение = _try(list[4])
	Номер_контактора = _try(Номер_контактора)
	Тип_автомата = _try(list[5])
	Тип_контактора = _try(list[6])
	key = _try(list[7])
	set_phase(el_2D,kol)
	#--Внесение параметров в 2д элемент--------------------
	el_2D.LookupParameter("Номинальный ток автомата").Set(Ток_автомата)	
	el_2D.LookupParameter("Номинальный ток контактора").Set(Ток_контактора)
	el_2D.LookupParameter("Ток утечки УЗО").Set(Ток_утечки_УЗО)
	el_2D.LookupParameter("Управляющее напряжение").Set(Управляющее_напряжение)
	el_2D.LookupParameter("Номер автомата").Set(Номер_автомата)
	el_2D.LookupParameter("Номер контактора").Set(str(Номер_контактора))		
	el_2D.LookupParameter("Тип автомата").Set(Тип_автомата)
	el_2D.LookupParameter("Тип контактора").Set(Тип_контактора)
	TransactionManager.Instance.TransactionTaskDone()	
	
##################################################################################################################################################
#--------------------------ВЗЯТИЕ ПАРАМЕТРОВ----------------------------------------------------------------------------------------------------
##################################################################################################################################################


def get_draftingview_type():
	vf1 = FilteredElementCollector(doc).OfClass(ViewFamilyType).ToElements()
	view = None
	for v in vf1:
		nm = v.FamilyName
		if nm=="Чертежный вид" or nm=="Drafting View":
			view = v.Id
	return view
	
def get_draftingviews(doc):
	views = FilteredElementCollector(doc).OfCategory(BuiltInCategory.OST_Views).WhereElementIsNotElementType().ToElements()
	list_drafting_views = []
	name_drafting_views = []
	for view in views:
		if not view.IsTemplate:
			type=view.ViewType.ToString()
			if type=="DraftingView":
				name = view.ViewName
				name_drafting_views.append(name)
				list_drafting_views.append(view)
	return 	name_drafting_views,list_drafting_views
	
def get_type_2D(el,types_up,keys):
	key = get_param(el,"KAV.Назначение аппарата защиты")
	i=0
	for key2 in keys:
		if key2 == key:
			type = types_up[i]
		i=i+1
	return type
	
def get_type_panel(el,types,keys):
	key = get_param(el,"KAV.Назначение аппарата защиты")
	type=types[0]
	i=0
	try:
		for key2 in keys:
			if key2 == key:
				type = types[i]
			i=i+1
	except:
		0	
	return type	

def get_panel():
	if isinstance(idd, list) == True:
		els = [doc.GetElement(ElementId(int(i))) for i in idd]
	else:
		els = doc.GetElement(ElementId(int(idd)))
	panel=None	
	for el in els:
		try:
			cat = el.Category.Name
			if cat=="Electrical Equipment" or cat =="Электрооборудование":
				panel = el
		except:
			0
	return panel

#--------Взятие значения параметра вне зависимости от формата----	
def get_param(el,LookupValue):
	p = el.LookupParameter(LookupValue)
	try:
		ty = p.StorageType.ToString()
		if ty == 'ValueString':
			p = p.AsValueString()
		elif ty == 'String':
			p = p.AsString()
		elif ty == 'Double':
			p = str(round(p.AsDouble(), 2))
		elif ty == 'Integer':
			p = p.AsInteger()
		elif ty == 'ElementId':
			p = p.AsElementId()
		return p
	except:
		return None

def get_name_and_types(el):
	sub = el.LookupParameter("УГО").AsElementId()
	type = doc.GetElement(sub)
	family = type.Family
	o_types = family.GetFamilySymbolIds()
	new_names=[]
	new_types=[]
	for o_type in o_types:
		type = doc.GetElement(o_type)
		o_name = type.get_Parameter(BuiltInParameter.ALL_MODEL_TYPE_NAME).AsString()
		new_names.append(o_name)
		new_types.append(o_type)
	return new_names,new_types
	
##################################################################################################################################################
#--------------------------РАСЧЕТЫ----------------------------------------------------------------------------------------------------
##################################################################################################################################################
	
def calc_up(iA,iB,iC):
	min=0.00
	if iA<iB:
		if iA<iC:
			min=iA
		else:
			min=iC
	elif iB<iC:
		min=iB
	else:
		min=iC
	kA = str((100-round(min/iA*100, 2)))
	kB = str((100-round(min/iB*100, 2)))
	kC = str((100-round(min/iC*100, 2)))
	return kA,kB,kC

def check_phase(pA,pB,pC):
	phase = "none"
	if pA>0 and pB==0 and pC==0:
		phase = "A"
	elif pB>0 and pC==0:
		phase = "B"
	elif pC>0:
		phase = "C"
	elif pA>0 and pB>0 and pC>0:
		phase = "ABC"
	return phase		

def calc_dU(Ip,U,L,CosF,S):
	if U<2400:
		b=2.00
	else:
		b=1.00
	Ip=float(Ip.replace(",","."))	
	CosF=float(CosF.replace(",","."))
	sinF = pow((1-pow(CosF,2)), 0.5)
	dU = 0
	
	try:
		dU = round(((Ip*(b*L*(((0.0225*CosF)/S)+(0.00008* sinF))/220)))*100, 2)
	except:
		0	
	return dU

def sort(circuits):
	list=[]
	for circuit in circuits:
		cN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_NUMBER).AsString()
		pN = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_CIRCUIT_PANEL_PARAM).AsString()	
		n = float(cN.replace(pN,"").replace("-Гр.",""))
		list.append([circuit,n])
	list2 = sorted(list, key = itemgetter(1))
	list3=[]
	for e in list2:
		list3.append(e[0])
	return list3

def generate_name(circuit):
	els = circuit.Elements
	spaces = []
	text=""
	i=0
	for el in els:
		if i==0:
			try:
				classification = el.LookupParameter("Классификация нагрузок").AsValueString()
				text = classification + ". Пом."
				category = el.Category.Name
			except:
				classification = el.Symbol.LookupParameter("Классификация нагрузок").AsValueString()
				text = classification + ". Пом."
				category = el.Category.Name				
		sp = el.Space[phase]
		try:		
			num = sp.get_Parameter(BuiltInParameter.ROOM_NUMBER).AsString()
		except:
			num=""		
		spaces.append(num)	
		i=i+1
	uniq = []
	uniq3 = []
	for num in spaces:
		if num not in uniq:
			uniq.append(num)
	uniq2 = sorted(uniq)
	i=0
	for u in uniq2:
		if i==0:
			text = text + u
		else:
			text = text + ", " + u
		i=i+1
	return text,category	
	
def grouping_circuits(circuits_2,a,b):
	i=0
	k=0
	list_gc=[]
	list2=[]
	for circuit in circuits_2:
		if k==0:
			if i<a:
				list2.append(circuit)
			else:
				k=1
				list_gc.append(list2)
				list2=[]
				list2.append(circuit)
				i=0
		else:
			if i<b:
				list2.append(circuit)
			else:
				list_gc.append(list2)
				list2=[]
				list2.append(circuit)
				i=0
		i=i+1
	list_gc.append(list2)	
	return list_gc

def search_min(a,b,c):
	min=0
	i=0
	if a<=b:
		if a<=c:
			min=a
			i=0
		else:
			min=c
			i=2
	elif b<c:
		min=b
		i=1
	else:
		min=c
		i=2
	return i,min	
def balance_phase(els):
	TransactionManager.Instance.EnsureInTransaction(doc)
	list=[]
	phase_a = []
	phase_b = []
	phase_c = []
	for el in els:
		circuit = el
		p = circuit.get_Parameter(BuiltInParameter.RBS_ELEC_APPARENT_CURRENT_PARAM).AsValueString()
		v = float(p.replace(",","."))
		k = -v
		list.append([el,v,k])		
	list2 = sorted(list, key=itemgetter(2))
	Ia=0.00
	Ib=0.00
	Ic=0.00
	for s in list2:
		n = search_min(Ia,Ib,Ic)[0]
		el = s[0]
		ip = s[1]
		if n==0:
			Ia=Ia+ip
			phase_a.append(el)
			el.LookupParameter(par_Phase).Set("A")
		elif n==1:
			Ib=Ib+ip
			phase_b.append(el)
			el.LookupParameter(par_Phase).Set("B")
		else:
			Ic=Ic+ip
			phase_c.append(el)
			el.LookupParameter(par_Phase).Set("C")
	Pa = summ_power(ext_phase(phase_a))
	Pb = summ_power(ext_phase(phase_b))
	Pc = summ_power(ext_phase(phase_c))
	TransactionManager.Instance.TransactionTaskDone()			
	return Ia,Ib,Ic,Pa,Pb,Pc
	
def summ_power(power_a):
	sum_power = 0
	for i in power_a:
		sum_power = sum_power + i
	return sum_power
	
def _try(value):
	if value is None:
		value = ""
	return value	

def ext_phase(phase_a):
	power = []
	for a in phase_a:
		power.append(float(a.LookupParameter("True Load").AsValueString().replace(",",".")))
	return power

def find_max(lst):
    elements = set(lst)
    for elem in elements:
        lesser_elements_count = 0
        for curr_elem in elements:
            if elem > curr_elem:
                lesser_elements_count += 1
        if lesser_elements_count == len(elements) - 1:
            return elem

#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#----------ВХОДНЫЕ ДАННЫЕ----------------
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
p_2D_id = IN[1]
p_filter = IN[2]
prefix = IN[3]
suffix = IN[4]
head_type_1 = IN[5]
head_type_2 = IN[6]
head_type_3 = IN[18]
circuit_down = IN[7]
circuit_up_1 = IN[8]
circuit_up_2 = IN[9]
circuit_up_3 = IN[10]
circuit_up_4 = IN[11]
osv_2d = IN[12]
roz_2d = IN[13]
par_Length = IN[14]
par_Phase = IN[15]
perc_reserv = IN[16]
panel = UnwrapElement(IN[17])
#Panel_Items= IN[18]
Name_Busbar= IN[19]
a = 6
b = 16
message = []
message.append("ok")
#///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#----------ОСНОВНОЙ КОД----------------
#/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
panel_name = panel.get_Parameter(BuiltInParameter.RBS_ELEC_PANEL_NAME).AsString()
circuits_1 = filter_els(circuits,p_filter,panel_name)
circuit_head = filter_els_head(circuits,panel_name)
circuits_2 = sort(circuits_1)
abc = balance_phase(circuits_2)
name_uniq = []
list_uniq = []
groups = grouping_circuits(circuits_2,a,b)
n=0
Номер_контактора=0
for circuits_n in groups:
	n=n+1
	view_name = prefix+panel_name+suffix+"_"+str(n)
	dview = create_view(doc,view_name)
	delete_generic_anotations(doc,dview)
	x=10/304.8
	y=0
	c = create_circuits_down(doc,dview,circuits_n,x,y,circuit_down)
	coss = c[1]
	x=10/304.8
	y=116/304.8
	types_up=[circuit_up_1,circuit_up_2,circuit_up_3,circuit_up_4]
	keys_up = ["выключатель","силовой контакт пускателя","узо","рубильник"]
	c = create_circuits_up(doc,dview,circuits_n,x,y,types_up,keys_up,Номер_контактора)
	x=c[1]
	y=c[2]
	Номер_контактора = c[3]
	n_avtomat = c[4]
	i=c[5]
	if n<2:
		head_types=[head_type_1,head_type_2,head_type_3]
		keys_h = ["выключатель","рубильник","шинопровод"]
		v = create_head(doc,dview,head_types,keys_h,panel,panel_name,coss,abc,circuit_head,circuits_2)	
sum_list = create_reserv(name_uniq,list_uniq,x,y,circuit_down,Номер_контактора,n_avtomat,i,b,n,panel_name,prefix,suffix,dview,perc_reserv)

OUT = 0
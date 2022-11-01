
from asyncio.windows_events import NULL
from modulefinder import Module
import pickle
from tokenize import String
from bs4 import BeautifulSoup
import urllib.request
import threading
import os
import urllib.parse
import re
import unicodedata
import datetime
import json
import glob

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def getIdsFromString(text):
    #ids appear to be always 7 letters long with 2 letters then a letter or number then 4 numbers
    x = re.findall("\W?(\w{2}\w\d{4})\W?",text)
    return x

class injestThread(threading.Thread):
    def __init__(self, threadID, name, path, outX):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.path = path
        self.outX = outX
    def run(self):
        modules.append(HTMLToModule(self.path))

class module:
    def __init__(self, id, title="", part=0, semester=0, url="", department="", year="", graduate="", preRequisite=[],coRequisite=[], exclusive=[]) -> None:
        self.id = id
        self.department = department
        self.graduate = graduate
        self.title = title
        self.academicYear = year
        self.part = part
        self.semester = semester
        self.url = url
        self.preRequisite = preRequisite
        self.coRequisite = coRequisite
        self.exclusive = exclusive
        self.creditValue = int(id[-2:])

    def __str__(self) -> str:
        return f"(Part: {self.part} Semester: {self.semester}) {self.id}: {self.title}"

    def __repr__(self) -> str:
        return f'(P:{self.part},S:{self.semester}) {self.id}: {self.title}'


def validAttr(dict, keyname):
    if dict.has_attr(keyname) and dict[keyname] != None and dict[keyname] != "" and dict[keyname] != "unknown":
        return True
    else:
        return False

def HTMLToModule(HTMLPath) -> module:
    # Read and process HTMLFile and companion file if present
    html_file = open(HTMLPath, "r", encoding="UTF-8")
    html_data = html_file.read()
    html_file.close()

    got_json_flag = False
    data_json = {}

    data_file_path = os.path.join(os.path.dirname(HTMLPath), f"{os.path.splitext(os.path.basename(HTMLPath))[0]}_data.json")
    if os.path.exists(data_file_path):
        data_file = open(data_file_path, "r")
        data_data = data_file.read()
        data_file.close()
        data_json = json.loads(data_data)
        got_json_flag = True

    
    id = os.path.splitext(os.path.basename(HTMLPath))[0]
    title = ""
    

    part = ""
    semester = ""
    academicYear = ""
    url = ""
    graduate = ""
    department = ""
    preRequisite = []
    coRequisite = []
    exclusive = []

    if validAttr(data_json, "semester"):
        part = data_json["part"]

    if validAttr(data_json, "startyear"):
        semester = data_json["semester"]

    if validAttr(data_json, "oURL"):
        url = data_json["oURL"]

    if validAttr(data_json, "graduateString"):
        graduate = data_json["graduateString"]

    if validAttr(data_json, "department"):
        department = data_json["department"]


    soup = BeautifulSoup(html_data, 'html.parser')

    module_container = soup.find_all(class_="content")[0].next
    infoTable = module_container.find_all(class_="module-x-column-left", recursive=True)
    for item in infoTable:
        dvalue = item.find_next_sibling(class_="module-x-column-right")
        leftpair = remove_control_characters(item.text).replace("\xa0","").strip()
        rightpair = remove_control_characters(dvalue.text).replace("\xa0","").strip()

        #dataPair = (leftpair, rightpair)
        
        foundIds = getIdsFromString(rightpair)
        #print(dataPair)

        if leftpair == "Module Identifier" or leftpair == "Cod y Modiwl":
            pass
        elif leftpair == "Module Title" or leftpair == "Teitl y Modiwl":
            title = rightpair
        elif leftpair == "Academic Year" or leftpair == "Blwyddyn Academaidd":
            academicYear = rightpair #could do some str to int stuff but i cba
        elif leftpair == "Co-ordinator" or leftpair == "Cyd-gysylltydd y Modiwl":
            pass
        elif leftpair == "Semester": #same in welsh
            pass
        elif leftpair == "Reading List" or leftpair == "Rhestr Ddarllen":
            pass
        elif leftpair == "Other Staff" or leftpair == "Rhestr Ddarllen":
            pass
        elif leftpair == "Pre-Requisite":
            # Could do some logic to determin if these are "and" or "or" Pre-Requisites but im not sure how I would implement a search for that 
            
            preRequisite.extend(foundIds)
        elif leftpair == "Co-Requisite":
            # Could do some logic to determin if these are "and" or "or" Pre-Requisites but im not sure how I would implement a search for that 
            coRequisite.extend(foundIds)
        elif leftpair == "Exclusive (Any Acad Year)":
            # Could do some logic to determin if these are "and" or "or" eclusive  but im not sure how I would implement a search for that 
            exclusive.extend(foundIds)
    
    outMod = module(id, part=part, semester=semester, url=url, department=department, title=title, year=academicYear, preRequisite=preRequisite, coRequisite=coRequisite, exclusive=exclusive, graduate=graduate)
    return outMod

def moduleToJSON(mod:module, type="full",numDept=-1):
    json_dict={}
    if type == "full":
        json_dict = {
            "id":mod.id,
            "title":mod.title,
            "dept":mod.department,
            "grad":mod.graduate,
            "year":mod.academicYear,
            "part":mod.part,
            "semester":mod.semester,
            "url":mod.url,
            "preRequisite":mod.preRequisite,
            "coRequisite":mod.coRequisite,
            "exclusive":mod.exclusive,
            "creditValue":mod.creditValue

        }
    if type == "slim": #essential data only
        json_dict = {
            "id":mod.id,
            "title":mod.title,
            "dept":mod.department,
            "grad":mod.graduate,
            "year":mod.academicYear,
            "part":mod.part,
            "semester":mod.semester,
            "url":mod.url,
            "creditValue":mod.creditValue
        }
    if type == "superslim": #essential data only
        json_dict = {
            "id":mod.id,
            "title":mod.title,
            "dept":mod.department,
            "semester":mod.semester,
            "url":mod.url
        }
    if type == "optislim":
        json_dict = {
            "id":mod.id,
            "title":mod.title,
            "dept": numDept,
            "semester":mod.semester,
            "url":"/".join(mod.url.split("/")[-4:])
        }

    return json_dict

#base url is https://www.aber.ac.uk/en/modules/
modules = []

def ingestHTMLFiles(dir):
    patt = os.path.join(dir, "**/modules/*.html")
    startTime = datetime.datetime.now()
    for file in glob.iglob(patt, recursive=True):
        print("Working on: " + file)
        modules.append(HTMLToModule(file))
        ##thread = injestThread(1, "BEANS", file, 1)
        ##thread.start()
    while (threading.activeCount() > 1):
        continue
    print(f"--- {len(modules)} modules processed in {datetime.datetime.now() - startTime}")


def exportModulesToJSON(modules:module,outFile, type="full"):
    bigString = ""
    bigArr = {
        "depts": [],
        "modules":[]
    }
    

    for mod in modules:
        if type=="optislim":
            if mod.department not in bigArr["depts"]:
                bigArr["depts"].append(mod.department)
            
            bigArr["modules"].append(moduleToJSON(mod, type=type, numDept=bigArr["depts"].index(mod.department)))
    f = open(outFile, "w")
    f.write(json.dumps(bigArr))
    f.close()

def saveModulesToFile(path):
    pickle_modules = pickle.dumps(modules)
    f = open(path, "wb")
    f.write(pickle_modules)
    f.close()


def openModulesFile(path):
    global modules
    f = open(path, "rb")
    modules = pickle.loads(f.read())

def cliMenu():
    return "\n\t1 - Ingest new modules\n\t2 - Load dumps\n\t3 - Save dumps\n\t4 - List modules \n\t5 - Export snippit to json\n\t6 - Export ALL to json"

if __name__ == "__main__":
    while (1==1):
        print(cliMenu())
        inp = input("?:")
        if inp == "1":
            path = input("Root folder:").replace('\\',"/")
            ingestHTMLFiles(path)
            
        elif inp == "2":
            path = input("dumps path:").replace('\\',"/")
            openModulesFile(path)
            print(f"{len(modules)} items loaded")
            

            
        elif inp == "3":
            path = input("dumps path:").replace('\\',"/")
            saveModulesToFile(path)
            
        elif inp == "4":
            for mod in modules:
                print(mod.__str__())
            print(f"{len(modules)} items")

        elif inp == "5":
            snippit = int(input("snippit size:"))
            type = input("What type?:")
            if type == "":
                type="full"
            
            path = input("snippit json out path:").replace('\\',"/")
            exportModulesToJSON(modules[:snippit], path,type=type)

        elif inp == "6":
            type = input("What type?:")
            if type == "": 
                type="full"
            path = input(" ALL json out path:").replace('\\',"/")
            exportModulesToJSON(modules, path, type=type)

from asyncio.windows_events import NULL
import pickle
from bs4 import BeautifulSoup
import urllib.request
import threading
import os
import urllib.parse
import re
import unicodedata
def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

class module:
    def __init__(self, id, part=0, semester=0, url="", department="") -> None:
        self.id = id
        self.department = department
        self.graduate = ""
        self.title = ""
        self.academicYear = ""
        self.part = part
        self.semester = semester
        self.url = url
        self.preRequisite = []
        self.coRequisite = []
        self.exclusive = []

    def __str__(self) -> str:
        return f"(Part: {self.part} Semester: {self.semester}) {self.id}: {self.title}"

    def __repr__(self) -> str:
        return f'(P:{self.part},S:{self.semester}) {self.id}: {self.title}'

class downloadThread(threading.Thread):
    def __init__(self, threadID, name, url, outputPath):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.url = url
        self.outputPath = outputPath
    def run(self):
        urllib.request.urlretrieve(self.url, self.outputPath)
      
#globals
modules = []



def downloadHTML(url, finalBasePath, name, newthread=False, ignoreExistingFile=False):
    downloadfile(url, finalBasePath + name + '.html',newthread=newthread ,ignoreExistingFile=ignoreExistingFile)

def getModule(id) -> module:
        for mod in modules:
            if mod.id == id:
                return mod

def getIdsFromString(text):
    #ids appear to be always 7 letters long with 2 letters then a letter or number then 4 numbers
    x = re.findall("\W?(\w{2}\w\d{4})\W?",text)
    return x

def commonMember(a, b):
    a_set = set(a)
    b_set = set(b)
 
    if (a_set & b_set):
        commonM = a_set & b_set
        return list(commonM)
    else:
        return []

def downloadfile(url,outputPath, newthread=False, ignoreExistingFile=False):
    file_exists = os.path.exists(outputPath)
    if ignoreExistingFile == False and file_exists:
        print(f"'{outputPath}' already exists.")
        return
    if ignoreExistingFile and file_exists:
        print(f"'{outputPath}' already exists. Overriding it")
    else:
        print(f"Download to'{outputPath}'")
    if newthread:
        dwthread = downloadThread(1, f"DL", url, outputPath)
        dwthread.start()
    else:
        urllib.request.urlretrieve(url, outputPath)
        


def indexAberDepartment(deptURL,forseRedownload=False):
    print("Indexing from Aber Website, this may take a few mins on first run\nDownloading modules index file")
    
    if os.path.exists("indexfiles/modules") == False:
        os.makedirs("indexfiles/modules")

    # Index Aber Modules
    #Module url https://www.aber.ac.uk/en/modules/deptcurrent/Computer+Science/
    #deptURL = "https://www.aber.ac.uk/en/modules/deptcurrent/Computer+Science/"
    indexbasePath = "indexfiles"

    newFileName = deptURL.split("/")
    newFileName = newFileName[len(newFileName)-3] + "-" + newFileName[len(newFileName)-2]

    downloadHTML(deptURL, indexbasePath ,'/' + newFileName, ignoreExistingFile=forseRedownload)

    modules_doc_read = open(indexbasePath +'/' + newFileName +'.html', "r")
    modules_doc = modules_doc_read.read()
    modules_doc_read.close()


    soup = BeautifulSoup(modules_doc, 'html.parser')

    deptName = re.findall("- (.*) ",soup.find_all(attrs={"name":"postgraduate-modules"})[0].next.text)[0]


    #print(soup.prettify())
    for link in soup.find_all("a"):
        href = link.get("href")
        #print(href)
        if (href != None) and (len(getIdsFromString(href)) == 1): #Doesnt take into account SEM modules
            graduateString = link.parent.parent.parent.previous_element.previous_element.previous_element
            partSemString = link.parent.parent.parent.previous_element

            if graduateString[:1].upper() == "U":
                graduateString = "undergraduate"
            elif graduateString[:1].upper() == "P":
                graduateString = "postgraduate"
            else:
                print("Something is wrong")

            

            part = re.match("Part (\d)", partSemString)

            if part != None:
                part = int(partSemString[part.regs[len(part.regs)-1][0]:part.regs[len(part.regs)-1][1]])

            semester = re.match(".*Semester (\d)", partSemString)

            if semester != None:
                semester = int(partSemString[semester.regs[len(semester.regs)-1][0]:semester.regs[len(semester.regs)-1][1]])

            
            if partSemString == "Distance Learning":
                semester = "Distance Learning"


            
            id = link.text
            #part = int(x[1])
            #semester = int(x[2])
            fullUrl = urllib.parse.urljoin(deptURL, href)

            mod = module(id,part, semester, url=fullUrl, department=deptName)
            modules.append(mod)
            #links_array.append(href)
            print("Found: " + id)

    #print(links_array)
    print("Staring Module Downloads")
    for mod in modules:
        fullURL = mod.url
        #print(fullURL)
        downloadHTML(fullURL, indexbasePath +'/modules/', mod.id, newthread=True, ignoreExistingFile=forseRedownload)
        #urllib.request.urlretrieve(mod, indexbasePath +'modulePage/' + mod[3:7] + '.html')
    
    while (threading.activeCount() > 1):
        continue
    
    print("Finished Module Downloads\n Now starting index process")
    #Process module file
    # Notes:
    #   The Part is not decernable from the file itself will have to pre save that

    for mod in modules:
        #Loop through modules and do data processing on their html file

        #if (mod.id[0:2] == "CC"): #Ignore welsh for now
        #    continue

        filePath = indexbasePath +'/modules/' + mod.id.upper() + ".html"
        f = open(filePath, "r", encoding="UTF-8")
        raw_file = f.read()
        f.close()
        modsoup = BeautifulSoup(raw_file, 'html.parser')
        
        # Now do html processing
        module_container = modsoup.find_all(class_="content")[0].next
        egg = module_container.find_all(class_="module-x-column-left", recursive=True)
        for item in egg:
            dvalue = item.find_next_sibling(class_="module-x-column-right")
            leftpair = remove_control_characters(item.text).replace("\xa0","").strip()
            rightpair = remove_control_characters(dvalue.text).replace("\xa0","").strip()
            #dataPair = (leftpair, rightpair)
            
            foundIds = getIdsFromString(rightpair)
            #print(dataPair)

            if leftpair == "Module Identifier" or leftpair == "Cod y Modiwl":
                pass
            elif leftpair == "Module Title" or leftpair == "Teitl y Modiwl":
                mod.title = rightpair
            elif leftpair == "Academic Year" or leftpair == "Blwyddyn Academaidd":
                mod.academicYear = rightpair #could do some str to int stuff but i cba
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
                
                mod.preRequisite.extend(foundIds)
            elif leftpair == "Co-Requisite":
                # Could do some logic to determin if these are "and" or "or" Pre-Requisites but im not sure how I would implement a search for that 
                mod.coRequisite.extend(foundIds)
            elif leftpair == "Exclusive (Any Acad Year)":
                # Could do some logic to determin if these are "and" or "or" eclusive  but im not sure how I would implement a search for that 
                mod.exclusive.extend(foundIds)
    saveModulesToFile();
        

def search(coReq="", preReq="", part=[], semester=[]):
    noReq_list = []
    preReq_list = []
    coReq_list = []

    if coReq.__class__  != "list" or hasattr(coReq, "__iter__") == False:
        coReq = [coReq]

    if preReq.__class__  != "list" or hasattr(preReq, "__iter__") == False:
        preReq = [preReq]

    if hasattr(part, "__iter__") == False:
        part = [part]

    if hasattr(semester, "__iter__") == False:
        semester = [semester]


    for mod in modules:
        if mod.title == "":
            continue
        if (part != []) and (mod.part not in part):
            continue
        if (semester != []) and (mod.semester not in semester):
            continue

        if (mod.preRequisite == []) and (mod.coRequisite == []):
            #No requirments
            noReq_list.append(mod)
        elif len(commonMember(preReq, mod.preRequisite)) > 0:
            #You may have the requirements for this module
            preReq_list.append(mod)
        elif len(commonMember(coReq, mod.coRequisite)) > 0:
            #You may have the requirements for this module
            coReq_list.append(mod)

    print("\nNo Requirements:")
    for i in noReq_list:
        print(i)

    print("Maybe have Pre-Requisites:")
    for i in preReq_list:
        print(i)
    
    print("Maybe have Co-Requisites:")
    for i in coReq_list:
        print(i)

def saveModulesToFile():
    pickle_modules = pickle.dumps(modules)
    f = open("dumps", "wb")
    f.write(pickle_modules)
    f.close()


def openModulesFile():
    global modules
    f = open("dumps", "rb")
    modules = pickle.loads(f.read())

def commandLineMenu():
    print("Please select what you would like to do:")
    print("\t1 - Index a Aber department")
    print("\t2 - Search")
    print("\t3 - List")
    print("\tq - Quit")


def yntoBool(text):
    if text.upper() == "Y":
        return True
    elif text.upper() == "N":
        return False

while (1==1):

    commandLineMenu()
    res = input()
    if res == "1":
        aberDepartUrl = input("Module Index URL")
        forseReDownload = yntoBool(input("Forse Re-Download (y/n)"))
        indexAberDepartment(aberDepartUrl,forseRedownload=forseReDownload)

    elif res == "2":
        pass
    elif res == "3":
        arrayNames = []
        arrayTings = []
        for i in modules:
            #print(i)
            if i.department not in arrayNames:
                arrayNames.append(i.department)
                arrayTings.append([])
            
            foundindex = arrayNames.index(i.department)
            arrayTings[foundindex].append(i)

        counter = 0
        for lists in arrayTings:
            print(f"{arrayNames[counter]}:")
            for mod in lists:
                print("\t" + mod.__str__())
            counter+=1

        print(f"You have indexed {len(modules)} modules")
    elif res == "q":
        exit()
    

#openModulesFile()
#search(part=2, semester=1, preReq="CS21120")
print("Done")
from asyncio.windows_events import NULL
import pickle
from bs4 import BeautifulSoup
import urllib.request
import threading
import os
import urllib.parse
import re
import unicodedata
import datetime
import json

from aberToJson import module
def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")


class downloadThread(threading.Thread):
    def __init__(self, threadID, name, url, outputPath):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.url = url
        self.outputPath = outputPath
    def run(self):
        urllib.request.urlretrieve(self.url, self.outputPath)



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
        while (threading.activeCount() > 100) :
            pass
        dwthread.start()
    else:
        urllib.request.urlretrieve(url, outputPath)

def downloadHTML(url, finalBasePath, name, newthread=False, ignoreExistingFile=False, createCompanionJSON=True, companionJSONdata={}):
    downloadfile(url, os.path.join(finalBasePath, name + '.html'),newthread=newthread ,ignoreExistingFile=ignoreExistingFile)
    if createCompanionJSON:
        # Create a compaion file with data
        defaultData = {
            "oURL" : url,
            "dateCreated" : "now"#datetime.datetime.now()
        }
        data = {**defaultData ,**companionJSONdata}
        f = open(os.path.join(finalBasePath, name + '_data.json'),"w")
        f.write(json.dumps(data))
        f.close()
    return os.path.join(finalBasePath, name + '.html')


def getIdsFromString(text):
    #ids appear to be always 7 letters long with 2 letters then a letter or number then 4 numbers
    x = re.findall("\W?(\w{2}\w\d{4})\W?",text)
    return x


def downloadRootDown(rootURL, years=["current", "future"], forseReDownload=False): #NFINISHED
    if os.path.exists(indexbasePath) == False:
        os.makedirs(indexbasePath)
    #downloadHTML(rootURL, indexbasePath, "root", ignoreExistingFile=forseRedownload) only needed for random years


def downloadYearDown(indexURL="https://www.aber.ac.uk/en/modules",year="current",forseReDownload=False,modjsonDATA={}):
    if os.path.exists(indexbasePath) == False:
        os.makedirs(indexbasePath)
    # Aberystwyth modules website automatically redirects to the correct deptcurrent or deptfuture so no logic needed
    now = datetime.datetime.now()
    
    if year == "current": # Needs some better logic probably
        year = now.year
    if year == "future":
        year = now.year+1

    indexURL += f"/{year}/"
    #Suspected term end date 25/08/2022 Research needed
    #endTermNowYear = datetime.datetime(now.year, 8,25)
    #if year == "current":
    #    if now > endTermNowYear:
    #        # year is current year/next year *probably
    #        year = f"{now.year}-{now.year+1}"
    #    else:
    #        #year is last year/this year
    #        year = f"{now.year-1}-{now.year}"

    #    indexURL += "/deptcurrent/"
    #elif year == "future":
    #    if now > endTermNowYear:
    #        # year is current year+1/next year+1 *probably
    #        year = f"{now.year+1}-{now.year+2}"
    #    else:
    #        #year is current year/next year
    #        year = f"{now.year}-{now.year+1}"
    #    indexURL += "/deptfuture/"
    myJSONData = {}
    myJSONData["startyear"] = year

    yearFolderDir = os.path.join(indexbasePath, str(year))

    if os.path.exists(yearFolderDir) == False:
        os.makedirs(yearFolderDir)
    filePATH = downloadHTML(indexURL,yearFolderDir, "deptlist", ignoreExistingFile=forseReDownload)

    # interpret file

    doc_read = open(filePATH, "r")
    doc = doc_read.read()
    doc_read.close()

    soup = BeautifulSoup(doc, 'html.parser')

    #Need to decide if this is an module index file or a department index file
    indexFileType = "module"

    if indexFileType == "module":
        #In here I need to inerpret the index file into all modules and pass it to download those modules
        #I also need to pass as much information as possible to be written
        #print(soup.prettify())
        moduleDirPath = os.path.join(yearFolderDir, "modules")
        if os.path.exists(moduleDirPath) == False:
            os.makedirs(moduleDirPath)
        number = 1
        moduleCodeX25 = soup.find_all(attrs={"class": "module-code-x-25"})
        for modulecodeparent in moduleCodeX25:
            
            id = modulecodeparent.text
            myJSONData["id"] = id
            JSONData = {**modjsonDATA, **myJSONData}
            print(f"{number}/{len(moduleCodeX25)}:",end="")
            downloadHTML(indexURL + f"{id}/", moduleDirPath, id, newthread=True, ignoreExistingFile=forseReDownload, companionJSONdata=JSONData)
            number+=1

        
    elif indexFileType == "department":

        deptURLs = [] 

        for link in soup.find_all("a"):
            href = link.get("href")
            
            if (href != None) and (len(re.findall("^[^\/]+\/$",href))):
                # store urls
                deptURLs.append(f"{indexURL}/{href}")
                
                print(href)
        
        deptsPath = os.path.join(yearFolderDir, "depts")

        if os.path.exists( deptsPath) == False:
            os.makedirs(deptsPath)

        for depturl in deptURLs:
            downloadDeptDown(depturl,deptsPath, modjsonDATA=modjsonDATA)
        # call department download for all departments
    
def downloadDeptDown(URL, baseDir, forseReDownload=False, modjsonDATA={}):
    # Index Aber Modules
    #Module url https://www.aber.ac.uk/en/modules/deptcurrent/Computer+Science/
    #deptURL = "https://www.aber.ac.uk/en/modules/deptcurrent/Computer+Science/"
    
    newFileName = URL.split("/")
    deptName = newFileName[len(newFileName)-2].replace("+", " ").replace("%26", "&")

    print(f"\nDownloading department {deptName} --->")

    baseDeptPath = os.path.join(baseDir, deptName)

    if os.path.exists(baseDeptPath) == False:
        os.makedirs(baseDeptPath)

    downloadHTML(URL, baseDeptPath ,deptName, ignoreExistingFile=forseReDownload)

    modules_doc_read = open(baseDeptPath +'/' + deptName +'.html', "r")
    modules_doc = modules_doc_read.read()
    modules_doc_read.close()


    soup = BeautifulSoup(modules_doc, 'html.parser')

    #deptName = re.findall("- (.*) ",soup.find_all(attrs={"name":"postgraduate-modules"})[0].next.text)[0]
    moduleDirPath = os.path.join(baseDeptPath, "modules")
    if os.path.exists(moduleDirPath) == False:
        os.makedirs(moduleDirPath)

    postGradAObj = soup.findAll("a", {"name":"postgraduate-modules"})
    postGradPos = -1
    if len(postGradAObj) > 0:
        postGradPos = postGradAObj[0].sourcepos
   
    #print(soup.prettify())
    for link in soup.find_all("a"):
        href = link.get("href")
        #print(href)
        if (href != None) and (len(getIdsFromString(href)) == 1):
            graduateString = "unknown"
            partSemString = link.parent.parent.parent.previous_element

            #if graduateString[:1].upper() == "U":
            #    graduateString = "undergraduate"
            #elif graduateString[:1].upper() == "P":
            #    graduateString = "postgraduate"
            #else:
            #    print("Something is wrong")

            if (link.sourcepos < postGradPos) or (postGradPos == -1):
                #We are Undergrad
                graduateString = "undergraduate"
            else:
                #We are Postgrad
                graduateString = "postgraduate"

            

            part = re.match("Part (\d)", partSemString)

            if part != None:
                part = int(partSemString[part.regs[len(part.regs)-1][0]:part.regs[len(part.regs)-1][1]])

            semester = re.match(".*Semester (\d)", partSemString)

            if semester != None:
                semester = int(partSemString[semester.regs[len(semester.regs)-1][0]:semester.regs[len(semester.regs)-1][1]])

            
            if partSemString == "Distance Learning":
                semester = "Distance Learning"


            
            id = link.text
            fullURL = urllib.parse.urljoin(URL, href)

            print("Found: " + id)

            myJSONData = {
                "id" : id,
                "department": deptName,
                "part" : part,
                "semester" : semester,
                "graduateString" : graduateString
            }
            JSONData = {**modjsonDATA, **myJSONData}
            downloadHTML(fullURL, moduleDirPath, id, newthread=True, ignoreExistingFile=forseReDownload, companionJSONdata=JSONData)

    

    #print(links_array)
    
    #while (threading.activeCount() > 1):
    #    continue
    # all done

#indexbasePath = os.path.join(os.getcwd(), "indexfiles")
indexbasePath = os.path.join("C:\\Users\\thoma\\Documents\\Real Documents\\Aberystwyth Module Downloads TEST", "indexfiles")
#C:\Users\thoma\Documents\Real Documents\Aberystwyth Module Downloads TEST

downloadYearDown(year=2021)

def cmdMenu():

    while (1==1):
        print("0 - Run Year Down")
        inputtxt = input("?:")
        if inputtxt == "0":
            outputDir = input("OutputDir:")
            global indexbasePath
            indexbasePath = os.path.join(outputDir, "indexfiles")
            downloadYearDown(year=2021)
            print("-------All Done-------")



cmdMenu()
    





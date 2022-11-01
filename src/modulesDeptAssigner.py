import json

f = open("./optislimAll.json", "r") #ingest file
beans = json.loads(f.read())
f.close()

deptlist = beans["depts"]
deptmatches = []

for num in range(len(deptlist)):
    deptmatches.append([])
    

for mod in beans["modules"]:
    currentLetters = deptmatches[mod["dept"]]
    newLetters = mod["id"][:2]
    try:
        index = currentLetters.index(newLetters)
    except ValueError:
        deptmatches[mod["dept"]].append(newLetters)

        
dict = {
    "depts":deptlist,
    "letters": {}
}
num = 0
for dept in deptmatches:
    for item in dept:

        dict["letters"][item] = num
    num+=1


f = open("deptlookup.json", "w")
f.write(json.dumps(dict))
f.close()
print("beans")

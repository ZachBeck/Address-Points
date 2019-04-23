import arcpy
import re
from xxhash import xxh64

def removeNone(word):
    if word == None:
        word = ''
    return word

def deleteDuplicatePts(inPts, inFlds):
    digestDict = {}
    duplicateLst = []
    dupAddressPrintLst = []
    digTrim = re.compile(r'(\d+\.\d{2})(\d+)')
    with arcpy.da.SearchCursor(inPts, inFlds) as sCursor:
        for row in sCursor:
            if row[1] != None:
                coordTrim = digTrim.sub(r'\1', row[1])
                row0 = removeNone(row[0])
                hash = xxh64(str(row0 + coordTrim))
                digest = hash.hexdigest()
                if digest not in digestDict:
                    digestDict.setdefault(digest)
                else:
                    duplicateLst.append(row[2])
                    dupAddressPrintLst.append(row0)
            if row[1] == None:
                duplicateLst.append(row[2])
                dupAddressPrintLst.append(row0)

        print (dupAddressPrintLst)

    if len(duplicateLst) >= 1:
        sql = '"OBJECTID" IN ({})'.format(', '.join(str(d) for d in duplicateLst))
        duplicatePts_FL = arcpy.MakeFeatureLayer_management(inPts, 'duplicatePts_FL', sql)
        print ('Deleted {} records'.format(len(duplicateLst)))
        arcpy.DeleteFeatures_management(duplicatePts_FL)
    else:
        print ('No Duplicates to Delete')
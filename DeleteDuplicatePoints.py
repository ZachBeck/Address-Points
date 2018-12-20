import arcpy
from xxhash import xxh64

def deleteDuplicatePts(inPts, inFlds):
    with arcpy.da.SearchCursor(inPts, inFlds) as sCursor:
        digestDict = {}
        duplicateLst = []
        dupAddressPrintLst = []
        for row in sCursor:
            if row[1] != None:
                hash = xxh64(str(row[0] + row[1]))
                digest = hash.hexdigest()
                if digest not in digestDict:
                    digestDict.setdefault(digest)
                else:
                    duplicateLst.append(row[2])
                    dupAddressPrintLst.append(row[0])
            if row[1] == None:
                duplicateLst.append(row[2])
                dupAddressPrintLst.append(row[0])

        print dupAddressPrintLst

    if len(duplicateLst) >= 1:
        sql = '"OBJECTID" IN ({})'.format(', '.join(str(d) for d in duplicateLst))
        duplicatePts_FL = arcpy.MakeFeatureLayer_management(inPts, 'duplicatePts_FL', sql)
        print 'Deleted {} records'.format(len(duplicateLst))
        arcpy.DeleteFeatures_management(duplicatePts_FL)
    else:
        print 'No Duplicates to Delete'
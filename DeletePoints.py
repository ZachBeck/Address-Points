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
                #row0 = removeNone(row[0])
                hash = xxh64(str(row[0] + coordTrim))
                digest = hash.hexdigest()
                if digest not in digestDict:
                    digestDict.setdefault(digest)
                else:
                    duplicateLst.append(row[2])
                    dupAddressPrintLst.append(f'{row[2]} {row[0]}')
            if row[1] == None:
                duplicateLst.append(row[2])
                dupAddressPrintLst.append(row[0])

        print (dupAddressPrintLst)

    if len(duplicateLst) >= 1:
        sql = '"OBJECTID" IN ({})'.format(', '.join(str(d) for d in duplicateLst))
        duplicatePts_FL = arcpy.MakeFeatureLayer_management(inPts, 'duplicatePts_FL', sql)
        print ('Deleted {} duplicates'.format(len(duplicateLst)))
        arcpy.DeleteFeatures_management(duplicatePts_FL)
    else:
        print ('No Duplicates to Delete')

def delete_by_query(in_pts, sql):
    '''Used to delete points that can not be removed with the attributes provided
       by the county (i.e Park City points in Wasatch County)'''
    delete_pts_fl = arcpy.MakeFeatureLayer_management(in_pts, 'delete_pts_fl', sql)
    delete_count = int(arcpy.GetCount_management(delete_pts_fl).getOutput(0))
    arcpy.DeleteFeatures_management(delete_pts_fl)
    print(f'Deleted {delete_count} records with {sql}')




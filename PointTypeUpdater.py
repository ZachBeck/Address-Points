import arcpy
import os

sgid = r'C:\sde\SGID_internal\SGID_agrc.sde'

def ptTypeUpdates_SaltLake(sgid, pts, polyLyrDict, lirDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        # polys = os.path.join(sgid, polyLyrDict[lyr][0])
        # print(polys)

        # propCodes = (
        #     '102', '103', '104', '105', '106', '110', '111', '112', '113', '114', '115', '116', '117', '118',
        #     '119', '120', '142', '150', '160', '199', '504', '511', '512', '524', '535', '540', '563', '576',
        #     '613', '614', '615', '620', '699', '901', '903', '913', '997')
        # sql = """"{}" IN {}""".format('PROP_TYPE', propCodes)

        #sql = f'"PROP_CLASS" NOT IN \'{exclude_list}\''
        #polyFC = arcpy.MakeFeatureLayer_management(polys, 'polyFC', sql)
        polyFC = os.path.join(sgid, polyLyrDict[lyr][0])

        nearTBL = '{}_nearTbl'.format(lyr)

        arcpy.GenerateNearTable_analysis(pts, polyFC, nearTBL, '1 Meters', 'NO_LOCATION', 'NO_ANGLE', 'CLOSEST')

        pt2Poly_Dict = {}
        polyDict = {}

        polyLyrFLDS = ['OBJECTID', polyLyrDict[lyr][1]]

        with arcpy.da.SearchCursor(nearTBL, nearFLDS) as sCursor:
            for row in sCursor:
                pt2Poly_Dict[row[0]] = row[1]
                polyDict.setdefault(row[1])
        with arcpy.da.SearchCursor(polyFC, polyLyrFLDS) as sCursor:
            for row in sCursor:
                if row[0] in polyDict:
                    polyDict[row[0]] = row[1]

        ucursorFLDS = ['OBJECTID', lyr]
        ucursor = arcpy.da.UpdateCursor(pts, ucursorFLDS)
        for urow in ucursor:
            try:
                if pt2Poly_Dict[urow[0]] in polyDict:
                    urow[1] = returnKey(polyDict[pt2Poly_Dict[urow[0].upper()]], lirDict)
            except:
                urow[1] = 'Unknown'

            if urow[1] == '':
                urow[1] = 'Unknown'
            if urow[1] == None:
                urow[1] = 'Unknown'

            ucursor.updateRow(urow)

        arcpy.Delete_management(nearTBL)

def returnKey(word, d):
    if word == None:
        word = ''
    for key, value in d.items():
        if word == '':
            return ''
        if word == key:
            return key
        if type(value) is str:
            if word == value:
                return key
        else:
            for v in value:
                if word == v:
                    return key
    return ''


def addPolyAttributesLIR(sgid, pts, polyLyrDict, lirDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        polyFC = os.path.join(sgid, polyLyrDict[lyr][0])
        print (polyFC)

        nearTBL = '{}_nearTbl'.format(lyr)

        arcpy.GenerateNearTable_analysis(pts, polyFC, nearTBL, '1 Meters', 'NO_LOCATION', 'NO_ANGLE', 'CLOSEST')

        pt2Poly_Dict = {}
        polyDict = {}

        polyLyrFLDS = ['OBJECTID', polyLyrDict[lyr][1]]

        with arcpy.da.SearchCursor(nearTBL, nearFLDS) as sCursor:
            for row in sCursor:
                pt2Poly_Dict[row[0]] = row[1]
                polyDict.setdefault(row[1])
        with arcpy.da.SearchCursor(polyFC, polyLyrFLDS) as sCursor:
            for row in sCursor:
                if row[0] in polyDict:
                    polyDict[row[0]] = row[1]

        ucursorFLDS = ['OBJECTID', lyr]
        ucursor = arcpy.da.UpdateCursor(pts, ucursorFLDS)
        for urow in ucursor:
            try:
                if pt2Poly_Dict[urow[0]] in polyDict:
                    if returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict) == '':
                        continue
                    else:
                        urow[1] = returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict)
            except:
                print('except')
                #urow[1] = 'Unknown'

            if urow[1] == '':
                urow[1] = 'Unknown'

            ucursor.updateRow(urow)

        arcpy.Delete_management(nearTBL)


def UpdatePropertyTypeLIR(sgid, pts, polyLyrDict, lirDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        polyFC = os.path.join(sgid, polyLyrDict[lyr][0])
        print (polyFC)

        nearTBL = '{}_nearTbl'.format(lyr)

        arcpy.GenerateNearTable_analysis(pts, polyFC, nearTBL, '1 Meters', 'NO_LOCATION', 'NO_ANGLE', 'CLOSEST')

        pt2Poly_Dict = {}
        polyDict = {}

        polyLyrFLDS = ['OBJECTID', polyLyrDict[lyr][1]]

        with arcpy.da.SearchCursor(nearTBL, nearFLDS) as sCursor:
            for row in sCursor:
                pt2Poly_Dict[row[0]] = row[1]
                polyDict.setdefault(row[1])
        with arcpy.da.SearchCursor(polyFC, polyLyrFLDS) as sCursor:
            for row in sCursor:
                if row[0] in polyDict:
                    polyDict[row[0]] = row[1]

        ucursorFLDS = ['OBJECTID', lyr]
        ucursor = arcpy.da.UpdateCursor(pts, ucursorFLDS)
        for urow in ucursor:
            if pt2Poly_Dict[urow[0]] in polyDict:
                if returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict) == 'Residential':

                    print(returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict))
                    urow[1] = returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict)
            else:
                continue

            ucursor.updateRow(urow)
        


            ucursor.updateRow(urow)

        arcpy.Delete_management(nearTBL)
import arcpy
import os

sgid10 = r'C:\ZBECK\Addressing\SGID10.sde'

def ptTypeUpdates_SaltLake(sgid10, pts, polyLyrDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        polys = sgid10 + '\\' + polyLyrDict[lyr][0]
        print(polys)

        propCodes = (
            '102', '103', '104', '105', '106', '110', '111', '112', '113', '114', '115', '116', '117', '118',
            '119', '120', '142', '150', '160', '199', '504', '511', '512', '524', '535', '540', '563', '576',
            '613', '614', '615', '620', '699', '901', '903', '913', '997')

        sql = """"{}" IN {}""".format('PROP_TYPE', propCodes)

        polyFC = arcpy.MakeFeatureLayer_management(polys, 'polyFC', sql)

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
                    urow[1] = 'Residential'
                    # urow[1] = polyDict[pt2Poly_Dict[urow[0]]]
            except:
                continue

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


def addPolyAttributesLIR(sgid10, pts, polyLyrDict, lirDict):

    arcpy.env.workspace = os.path.dirname(pts)
    arcpy.env.overwriteOutput = True

    nearFLDS = ['IN_FID', 'NEAR_FID', 'NEAR_DIST']

    for lyr in polyLyrDict:

        polyFC = sgid10 + '\\' + polyLyrDict[lyr][0]
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
                   urow[1] = returnKey(polyDict[pt2Poly_Dict[urow[0]]], lirDict)
            except:
                urow[1] = ''

            ucursor.updateRow(urow)

        arcpy.Delete_management(nearTBL)
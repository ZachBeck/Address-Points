import arcpy
import os

def createErrorPts(dict, outLocation, outFile, fldName, countySrcPts):

    def removeNone(word):
        if word == None:
            word = ''
        return word

    arcpy.env.workspace = outLocation
    arcpy.env.overwriteOutput = True
    shp_fullPath = os.path.join(outLocation, outFile)
    proj = arcpy.Describe(countySrcPts).SpatialReference

    arcpy.CreateFeatureclass_management(outLocation, outFile, 'POINT', '', '', '', proj)
    print 'Created ' + shp_fullPath
    arcpy.AddField_management(shp_fullPath, fldName, 'TEXT')
    arcpy.AddField_management(shp_fullPath, 'NOTES', 'TEXT')
    arcpy.DeleteField_management(shp_fullPath, 'Id')

    flds = [fldName, 'NOTES', 'SHAPE@']
    iCursor = arcpy.da.InsertCursor(shp_fullPath, flds)

    for d in dict:
        inFld = removeNone(d)
        notes = dict[d][0]
        shp = dict[d][1]

        iCursor.insertRow((inFld, notes, shp))

    del iCursor
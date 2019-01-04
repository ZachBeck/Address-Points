import arcpy
import datetime, time

def deleteAddressPts(inCounty, inPoints):

    print 'START ' + str(datetime.datetime.now())

    fipsDict = {'Beaver': '49001', 'Box Elder': '49003', 'Cache': '49005', 'Carbon': '49007', 'Daggett': '49009', \
                'Davis': '49011', 'Duchesne': '49013', 'Emery': '49015', 'Garfield': '49017', 'Grand': '49019', \
                'Iron': '49021', 'Juab': '49023', 'Kane': '49025', 'Millard': '49027', 'Morgan': '49029', \
                'Piute': '49031', 'Rich': '49033', 'Salt Lake': '49035', 'San Juan': '49037', 'Sanpete': '49039', \
                'Sevier': '49041', 'Summit': '49043', 'Tooele': '49045', 'Uintah': '49047', 'Utah': '49049', \
                'Wasatch': '49051', 'Washington': '49053', 'Wayne': '49055', 'Weber': '49057'}

    if inPoints == appAddressPts:
        sql = """"CountyID" = """ + "'" + fipsDict[inCounty] + "' and " + """"Status" = 'COMPLETE'"""
    else:
        sql = """"CountyID" = """ + "'" + fipsDict[inCounty] + "'"
        #sql = """"CountyID" = """ + "'" + fipsDict[inCounty] + "' and " + """"AddSource" <> 'PARK CITY GIS'"""

    print sql

    addPts_FL = arcpy.MakeFeatureLayer_management(inPoints, 'addPts_FL', sql)
    print 'Made Feature Layer ' + sql
    arcpy.DeleteFeatures_management(addPts_FL)
    arcpy.Delete_management(addPts_FL)

    print 'END ' + str(datetime.datetime.now())



appAddressPts = r'Database Connections\DC_AddressAdmin@AddressPointEditing@itdb104sp.sde\AddressPointEditing.ADDRESSADMIN.AddressPoints'
sgidAddressPts = r'Database Connections\DC_Location@SGID10@sgid.agrc.utah.gov.sde\SGID10.LOCATION.AddressPoints'


deleteAddressPts('Davis', sgidAddressPts) #Update input points and SQL query



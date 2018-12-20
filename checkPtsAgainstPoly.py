import arcpy

emptyValues = [None, '']
unincorpList = []
sgid10 = r'Database Connections\dc_agrc@SGID10@sgid.agrc.utah.gov.sde'
citiesAndLocations = sgid10 + '\\SGID10.LOCATION.CitiesTownsLocations'
zips = sgid10 + '\\SGID10.BOUNDARIES.ZipCodes'
munis = sgid10 + '\\SGID10.BOUNDARIES.Municipalities'
addrSys = sgid10 + '\\SGID10.LOCATION.AddressSystems'

def checkInsidePolys(polyFC, polyFLD, pts, ptsFLDS):

    polyFL = arcpy.MakeFeatureLayer_management(polyFC)
    polyFL = arcpy.SelectLayerByLocation_management(polyFL, 'INTERSECT', pts, '', 'NEW_SELECTION')

    ptsFL = arcpy.MakeFeatureLayer_management(pts)

    sCursorPoly = arcpy.da.SearchCursor(polyFL, polyFLD)

    for poly in sorted(set(sCursorPoly)):

        uniquePoly = ''.join(poly)
        sql = """"{}" = '{}'""".format(polyFLD, uniquePoly)

        print '---------------------' + uniquePoly + '-------------------------'

        arcpy.SelectLayerByAttribute_management(polyFL, "NEW_SELECTION", sql)
        arcpy.SelectLayerByLocation_management(ptsFL, 'WITHIN', polyFL, '', 'NEW_SELECTION')

        with arcpy.da.UpdateCursor(ptsFL, ptsFLDS) as uCursor_pts:
            for urow in uCursor_pts:
                if urow[0] != uniquePoly.upper():
                    errorValue = '{}{}{}{}{}'.format('[', polyFLD, '=', uniquePoly.upper(), ']')
                    if urow[1] in emptyValues:
                        urow[1] = errorValue
                    else:
                        urow[1] = '{} {}'.format(urow[1], errorValue)

                uCursor_pts.updateRow(urow)

    arcpy.SelectLayerByAttribute_management(ptsFL, 'CLEAR_SELECTION')
    arcpy.SelectLayerByAttribute_management(polyFL, 'CLEAR_SELECTION')


def checkOutsidePolys(polyFC, polyFLD, pts, ptsFLDS, coName):

    sql = """"COUNTY" = '{}' and "TYPE" = 'Place'""".format(coName)
    with arcpy.da.SearchCursor(citiesAndLocations, ['NAME', 'COUNTY', 'TYPE'], sql) as sCurosr:
        for row in sCurosr:
            unincorpList.append(row[0].upper())


    polyFL = arcpy.MakeFeatureLayer_management(polyFC)
    polyFL = arcpy.SelectLayerByLocation_management(polyFL, 'INTERSECT', pts, '', 'NEW_SELECTION')

    ptsFL = arcpy.MakeFeatureLayer_management(pts)
    arcpy.SelectLayerByLocation_management(ptsFL, 'WITHIN', polyFL, '', 'NEW_SELECTION', 'INVERT')
    count = int(arcpy.GetCount_management(ptsFL).getOutput(0))
    print count

    with arcpy.da.UpdateCursor(ptsFL, ptsFLDS) as uCursor_Pts:
        for urow in uCursor_Pts:
            errorValue = '{} {}{}'.format('[Outside ' + ptsFLDS[0], urow[0], ']')
            if urow[0] not in emptyValues:
                if urow[0] not in unincorpList:
                    if urow[1] not in emptyValues:
                        print errorValue
                        urow[1] = '{} {}'.format(urow[1], errorValue)
                    else:
                        urow[1] = errorValue
                else:
                    continue
            else:
                continue

            uCursor_Pts.updateRow(urow)

# checkInsidePolys(munis, 'NAME', addPts, ['City', 'FLAG'])
# checkInsidePolys(zips, 'ZIP5', addPts, ['ZipCode', 'FLAG'])
# checkInsidePolys(addSys, 'GRID_NAME', addPts, ['AddSystem', 'FLAG'])
#
# checkOutsidePolys(munis, 'NAME', addPts, ['City', 'FLAG'])
# checkOutsidePolys(addSys, 'GRID_NAME', addPts, ['AddSystem', 'FLAG'])



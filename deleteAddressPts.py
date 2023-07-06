import arcpy
import datetime, time

def delete_address_pts(delete_county, in_points):

    print ('START ' + str(datetime.datetime.now()))

    fips_dict = {'Beaver': '49001', 'Box Elder': '49003', 'Cache': '49005', 'Carbon': '49007', 'Daggett': '49009',
                'Davis': '49011', 'Duchesne': '49013', 'Emery': '49015', 'Garfield': '49017', 'Grand': '49019',
                'Iron': '49021', 'Juab': '49023', 'Kane': '49025', 'Millard': '49027', 'Morgan': '49029',
                'Piute': '49031', 'Rich': '49033', 'Salt Lake': '49035', 'San Juan': '49037', 'Sanpete': '49039',
                'Sevier': '49041', 'Summit': '49043', 'Tooele': '49045', 'Uintah': '49047', 'Utah': '49049',
                'Wasatch': '49051', 'Washington': '49053', 'Wayne': '49055', 'Weber': '49057'}

    sql = f'"CountyID" = \'{fips_dict[delete_county]}\''

    pts_fl = arcpy.MakeFeatureLayer_management(in_points, 'pts_fl', sql)
    print (f'-----Made Feature Layer of {delete_county.upper()} COUNTY address points')

    pt_count = arcpy.management.GetCount(pts_fl)

    arcpy.DeleteFeatures_management(pts_fl)
    arcpy.Delete_management(pts_fl)

    print(f'-----Deleted {pt_count} address points')

    print ('END ' + str(datetime.datetime.now()))



sgid_internal_pts = r'C:\sde\SGID_internal\SGID_Location.sde\SGID.LOCATION.AddressPoints'

delete_address_pts('Davis', sgid_internal_pts) #Update input points and SQL query



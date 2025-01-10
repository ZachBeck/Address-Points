import arcpy
import sys
import datetime, time
from pathlib import Path

def update_sde(county_name):

    print(f'Start SDE Update {str(datetime.datetime.now())}')

    fips_dict = {'Beaver':'49001', 'Box Elder':'49003', 'Cache':'49005', 'Carbon':'49007', 'Daggett':'49009',
                 'Davis':'49011', 'Duchesne':'49013', 'Emery':'49015', 'Garfield':'49017', 'Grand':'49019',
                 'Iron':'49021', 'Juab':'49023', 'Kane':'49025', 'Millard':'49027', 'Morgan':'49029',
                 'Piute':'49031', 'Rich':'49033', 'Salt Lake':'49035', 'San Juan':'49037', 'Sanpete':'49039',
                 'Sevier':'49041', 'Summit':'49043', 'Tooele':'49045', 'Uintah':'49047', 'Utah':'49049',
                 'Wasatch':'49051', 'Washington':'49053', 'Wayne':'49055', 'Weber':'49057'}
    

    path_name = ''.join(county_name.title().split())
    update_pts = f'..\{path_name}\{path_name}.gdb\AddressPoints_{path_name}'
    

    if arcpy.Exists(update_pts):

        sgid_pts = str(Path(__file__).resolve().parents[3].joinpath('sde', 'SGID_internal', 'SGID_Location.sde', 'SGID.LOCATION.AddressPoints'))
        
        #sql = f'"CountyID" = \'{fips_dict[county_name.title()]}\' AND NOT "AddSource" = \'DABC\''
        sql = f'"CountyID" = \'{fips_dict[county_name.title()]}\' AND "AddSource" NOT IN (\'DABC\', \'HAFB\', \'UGRC\')'
     
        sgid_pts_fl = arcpy.MakeFeatureLayer_management(sgid_pts, 'sgid_pts_fl', sql)

        print(f'-----Made Feature Layer of {county_name.upper()} COUNTY address points')

        count_update_pts = arcpy.GetCount_management(update_pts)[0]
        count_sgid_pts_fl = arcpy.GetCount_management(sgid_pts_fl)[0]
        pt_increase = int(count_update_pts) - int(count_sgid_pts_fl)

        if int(count_sgid_pts_fl) > int(count_update_pts):
            print(f'!!!!!{county_name.upper()} COUNTY update has fewer points ({count_update_pts}) than what is in SDE ({count_sgid_pts_fl})')
            raise Exception('Update has fewer points than SDE')


        arcpy.DeleteFeatures_management(sgid_pts_fl)
        arcpy.Delete_management(sgid_pts_fl)
        print(f'-----Deleted {count_sgid_pts_fl} address points from SDE')


        try:
            arcpy.Append_management(update_pts, sgid_pts, 'NO_TEST')
            print(f'-----Appending {county_name.upper()} COUNTY into {sgid_pts}')
            print(f'     {count_update_pts} points added, {pt_increase} new points from last update')
        except:
            print(f'!!!!!APPEND failed, you broke something')
        
    else:
        print(f'!!!!!{county_name.title()} County address points not found - {update_pts}')
    
    #-----verify update-------
    updated_sgid_pts_fl = arcpy.MakeFeatureLayer_management(sgid_pts, 'updated_sgid_pts_fl', sql)
    count_updated_sgid_pts_fl = arcpy.GetCount_management(updated_sgid_pts_fl)[0]

    if count_updated_sgid_pts_fl != count_update_pts:
        point_difference = int(count_updated_sgid_pts_fl) - int(count_update_pts)
        print(f'!!!!!SGID.LOCATION.AddressPoint has a {point_difference} point difference than the update source')

    print(f'End SDE Update {str(datetime.datetime.now())}')



update_sde('Duchesne') #Update input points and SQL query



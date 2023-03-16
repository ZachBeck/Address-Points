import arcpy
import datetime
from UpdatePointAttributes import addPolyAttributes
from UpdatePointAttributes import updateAddPtID


print(f'Start {str(datetime.datetime.now())}')

inputDict = {'AddSystem':['SGID.LOCATION.AddressSystemQuadrants', 'GRID_NAME', '']}

sgid = r'C:\sde\SGID_internal\SGID_agrc.sde'
address_pts = r'C:\ZBECK\Addressing\zTesting\AddressPoints.gdb\SGID_LOCATION_AddressPoints'

print(f'----Start updating grid attributes {str(datetime.datetime.now())}')
addPolyAttributes(sgid, address_pts, inputDict)
print(f'----Done updating grid attributes {str(datetime.datetime.now())}')

print(f'----Start updating AddPtID {str(datetime.datetime.now())}')
updateAddPtID(address_pts)
print(f'----Done updating AddPtID {str(datetime.datetime.now())}')

print(f'End {str(datetime.datetime.now())}')
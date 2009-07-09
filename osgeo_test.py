#test osgeo

import sys,os

sys.path.append('./bin')

os.environ['PATH']=r'.\bin\gdalwin32-1.6\bin' + os.environ['PATH']

from osgeo import gdal,ogr,osr
import osgeo

print os.environ['GDAL_DATA']
print os.environ['PATH']

wgs=osr.SpatialReference()
wgs.ImportFromEPSG(4326)
olm=osr.SpatialReference()
olm.ImportFromEPSG(2992)
ct=osr.CoordinateTransformation(wgs,olm)
p=ct.TransformPoint(45,-117)

print p.GetX(),p.GetY()
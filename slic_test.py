<<<<<<< HEAD
from skimage.segmentation import slic
import rasterio
import numpy as np
from skimage.filters import threshold_otsu
from shapely.geometry import Polygon, MultiPolygon
import cv2
from osgeo import ogr, osr
from shapely.affinity import affine_transform

img = rasterio.open('clipped.tif')
image1 = np.double(rasterio.open('clipped.tif').read(1)) 
image = image1 > threshold_otsu(image1)

slic = slic(image, n_segments=5000,compactness=0.1)

        
contour, s = cv2.findContours(slic, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
liste= []
for i in contour:
        if len(i) >= 3:
            liste.append(Polygon(np.squeeze(i)))
mp = affine_transform(MultiPolygon(liste), [img.transform[0],
                                                           img.transform[1],
                                                           img.transform[3],
                                                           img.transform[4],
                                                           img.transform[2],
                                                           img.transform[5]])           
def create(n, name):
    driver      = ogr.GetDriverByName('ESRI Shapefile')
    driver_ds   = driver.CreateDataSource(f'sonuclar/{name}.shp')
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(int(str(img.crs).split(':')[1]))
    layer       = driver_ds.CreateLayer('Shapefile', spatial_ref)
    
    
    
    
    
    defn           = layer.GetLayerDefn()
    feature_create = ogr.Feature(defn)
    
    
    
    
           
    geo = ogr.CreateGeometryFromWkb(n.wkb)
    feature_create.SetGeometry(geo)
    
    layer.CreateFeature(feature_create)
    
    driver_ds = layer = feature_create = geo = None
    
=======
from skimage.segmentation import slic
import rasterio
import numpy as np
from skimage.filters import threshold_otsu
from shapely.geometry import Polygon, MultiPolygon
import cv2
from osgeo import ogr, osr
from shapely.affinity import affine_transform

img = rasterio.open('clipped.tif')
image1 = np.double(rasterio.open('clipped.tif').read(1)) 
image = image1 > threshold_otsu(image1)

slic = slic(image, n_segments=5000,compactness=0.1)

        
contour, s = cv2.findContours(slic, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
liste= []
for i in contour:
        if len(i) >= 3:
            liste.append(Polygon(np.squeeze(i)))
mp = affine_transform(MultiPolygon(liste), [img.transform[0],
                                                           img.transform[1],
                                                           img.transform[3],
                                                           img.transform[4],
                                                           img.transform[2],
                                                           img.transform[5]])           
def create(n, name):
    driver      = ogr.GetDriverByName('ESRI Shapefile')
    driver_ds   = driver.CreateDataSource(f'sonuclar/{name}.shp')
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(int(str(img.crs).split(':')[1]))
    layer       = driver_ds.CreateLayer('Shapefile', spatial_ref)
    
    
    
    
    
    defn           = layer.GetLayerDefn()
    feature_create = ogr.Feature(defn)
    
    
    
    
           
    geo = ogr.CreateGeometryFromWkb(n.wkb)
    feature_create.SetGeometry(geo)
    
    layer.CreateFeature(feature_create)
    
    driver_ds = layer = feature_create = geo = None
    
>>>>>>> f9113b84092bc6155c5c83b4b793ec4532558973
create(mp, 'deneme')
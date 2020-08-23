import rasterio
from rasterio.enums import Resampling
from rasterio.mask import mask
from rasterio.plot import show
from rasterio.features import shapes
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon, box
from osgeo import ogr, osr
import os
import geopandas
import json

class NDWI:
    """
    This class working properly for Sentinel 2A satellite image. The resample function created for a sentinel2A bands.
    """

    def __init__(self, path_NIR, path_SWIR, output_name):
        """
        Parameters
        ----------
        path_NIR : String
            NIR Band path for NDWI. 
            NDWI = (NIR - SWIR) / (NIR + SWIR)
            
            if you want to use mNDWI just put green band path as a NIR band input
            mNDWI = (Green - SWIR) / (Green + SWIR)
            
        path_SWIR : String
            SWIR Band path for NDWI
            
        output_name: String
            Output name as a tif format //Example: output.tif, ndwi.tif

        Returns
        -------
        None.

        """
        self.path_NIR    = path_NIR
        self.path_SWIR   = path_SWIR
        self.output_name = output_name
        self.runApp()
                
    def read_images(self):
        """
        Function read NIR and SWIR bands
        
        Returns
        -------
        NIR and SWIR bands

        """
        band_NIR  = rasterio.open(self.path_NIR)
        band_SWIR = rasterio.open(self.path_SWIR)
        
        return (band_NIR, band_SWIR)
        
    def resample(self):
        """
        Function calculate the resample_factor and resample(bilinear) the SWIR band
        
        Returns
        -------
        Array of uint16 

        """
        resample_factor = int(self.read_images()[0].width / self.read_images()[1].width)
        resampled_SWIR = self.read_images()[1].read(out_shape=(self.read_images()[1].count,
                                                    int(self.read_images()[1].height * resample_factor),
                                                    int(self.read_images()[1].width * resample_factor)
                                                    ), resampling=Resampling.bilinear)
        return resampled_SWIR
            
    def NDWI_calc(self):
        """
        Function calculate NDWI

        Returns
        -------
        Array
            Returns NDWI as a array of uint16

        """    
        np.seterr(divide='ignore', invalid='ignore') #Settings before ndwi process
        return  (self.read_images()[0].read().astype(float) - self.resample().astype(float)) / (self.read_images()[0].read() + self.resample())
            
    def save_NDWI(self):
        """
        Function create NDWI file on tif format and save current path.

        Returns
        -------
        None.

        """
        
        meta = self.read_images()[0].meta
        meta.update(driver='GTiff')
        meta.update(dtype=rasterio.float32)
        
        with rasterio.open(self.output_name, 'w', **meta) as dst:
            dst.write(self.NDWI_calc().astype(rasterio.float32))
            dst.close()
            print('NDWI has created succesfully')
    
    
    def runApp(self):
        self.save_NDWI()

class Clip_NDWI:
    
    def __init__(self, input, output_name, minx = 620000, miny = 4442000, maxx = 650000, maxy = 4455000):
        self.input = rasterio.open(input)
        self.output = output_name
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.run()

    def create_box(self):
        return geopandas.GeoDataFrame({'geometry': box(self.minx, self.miny, self.maxx, self.maxy)},
                                index=[0], crs=self.input.crs)

    def get_json(self):
        return [json.loads(self.create_box().to_json())['features'][0]['geometry']]
    
    def clip_image(self):
        clipped, clipped_transform = mask(dataset=self.input, shapes=self.get_json(), crop=True)
        clipped_meta = self.input.meta.copy()
        clipped_meta.update({"driver": "GTiff",
                 "height": clipped.shape[1],
                 "width": clipped.shape[2],
                 "transform": clipped_transform,
                 "crs": self.input.crs}
                         )
        return clipped, clipped_meta
    
    
    def save_clip(self):
        with rasterio.open(self.output, 'w', **self.clip_image()[1]) as clp:
            clp.write(self.clip_image()[0])
            clp.close()
            
    def run(self):
        self.save_clip()
    
class Calculate_Area:
    
    def __init__(self, ndwi_path):
        """
        Constructor function

        Parameters
        ----------
        ndwi_path : String
            NDVI input file path 


        """
        self.path = ndwi_path
        self.run()
            
    def read_image(self):
        return rasterio.open(self.path).read(1)
    
    def threshold(self):
        
        return self.read_image() > 0.65   
    
    def calc_area(self):
        return len(self.threshold()[self.threshold()==True])* 10*10*10**(-6)
    
    def print_screen(self):
        
        print('{:.2f} km²'.format(self.calc_area()))
        
        fig, ax = plt.subplots(1, figsize=(12, 12))
        plt.ticklabel_format(style = 'plain')
        plt.title(f'{self.path}  ({rasterio.open(self.path).crs})')
        show(self.threshold(), cmap='gray', transform=rasterio.open(self.path).transform)     
        plt.show()
        
        
        
    def run(self):
        self.calc_area()
        
class Vectorize:
    
    def __init__(self, input_raster, output_name, feat_name = 'Ulubatli Golu'):
        
        self.image     = rasterio.open(input_raster)
        self.input     = np.float32(Calculate_Area(input_raster).threshold().astype(float))
        self.area      = Calculate_Area(input_raster).calc_area()
        self.output    = output_name
        self.lake_name = feat_name
        self.array = []
        self.runApp()
        
    def find_contours(self):  
        return [shape['coordinates'] for shape, value in shapes(self.input, transform=self.image.transform)]
    
    
    def multipolygon(self): 
        for i in self.find_contours():
            if len(i) == 1:
                self.array.append(Polygon(np.squeeze(i)))
        temp = Polygon(np.squeeze(self.find_contours()[-2][0]))
        return temp.difference(MultiPolygon(self.array))
        
    def save_shp(self):
        
        if self.output in os.listdir():
            
            raise Exception(f'{self.output} file is exists!')
            
        else:
            driver      = ogr.GetDriverByName('ESRI Shapefile')
            driver_ds   = driver.CreateDataSource(self.output)
            spatial_ref = osr.SpatialReference()
            spatial_ref.ImportFromEPSG(int(str(self.image.crs).split(':')[1]))
            layer       = driver_ds.CreateLayer('Shapefile', spatial_ref)
            
            
            layer.CreateField(ogr.FieldDefn('Lake', ogr.OFTString))
            layer.CreateField(ogr.FieldDefn('Area (km²)', ogr.OFTReal))
            
            defn           = layer.GetLayerDefn()
            feature_create = ogr.Feature(defn)
            
            #Setting up Fields
            feature_create.SetField('lake', self.lake_name)
            feature_create.SetField('Area (km²)', self.area)
            
        
            geometry = ogr.CreateGeometryFromWkb(self.multipolygon().wkb)
            feature_create.SetGeometry(geometry)
            
            layer.CreateFeature(feature_create)
    
    def show_vector(self):
        vector = geopandas.read_file(self.output)
        fig, ax = plt.subplots()
        ax.ticklabel_format(style='plain')
        vector.plot(ax=ax)

    def runApp(self):
        self.save_shp()
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
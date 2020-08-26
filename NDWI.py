import rasterio
import cv2
from rasterio.enums import Resampling
from rasterio.plot import show
import numpy as np
from skimage.filters import threshold_otsu
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from osgeo import ogr, osr
import os
import geopandas
from shapely.affinity import affine_transform

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
        """
        This function open and read as a numpy array image.

        Returns
        -------
        numpy array
            Returns images' numpy array.

        """
        return rasterio.open(self.path).read(1)
    
    def threshold(self):
        """
        This function create thresholded image to seperate water and soil.

        Returns
        -------
        Numpy Array
            Returns numpy array which consist of booleans.

        """
        return self.read_image() > threshold_otsu(np.nan_to_num(self.read_image(), 0))    
    
    def calc_area(self):
        """
        This function calculate and return water area.
        
        Returns
        -------
        float
            Water Area.
        """
        return len(self.threshold()[self.threshold()==True])* 10*10*10**(-6)
    
    def print_screen(self):
        """
        This function create matplotlib image graphic and also print area of water.
        """
        print('{:.2f} km²'.format(self.calc_area()))
        
        fig, ax = plt.subplots(1, figsize=(12, 12))
        plt.ticklabel_format(style = 'plain')
        plt.title(f'{self.path}  ({rasterio.open(self.path).crs})')
        show(self.threshold(), cmap='gray', transform=rasterio.open(self.path).transform)     
        plt.show()
        
    def run(self):
        self.calc_area()
        
class Vectorize:
    
    def __init__(self, input_raster, output_name):
        """
        Parameters
        ----------
        input_raster : String
            Input raster name with extension or path and name with extension. (e.g: 'input.tif' or 'folder_name/input.tif')
        output_name : String
            Output vector path or path and name with shp format extension (e.g: 'output.shp' or 'folder_name/output.shp') 
        feat_name : String, optional
            It is optional. The default is 'Ulubatli Golu'.
        """
        self.image     = rasterio.open(input_raster)
        self.input     = np.uint8(Calculate_Area(input_raster).threshold())
        self.area      = Calculate_Area(input_raster).calc_area()
        self.output    = output_name
        self.array = []
        self.runApp()
        
    def find_contours(self):  
        """
        This function return list of vector's border coordinates

        Returns
        -------
        Tuple
            Tuple of contours coordinates and hierarchy.
        """
        return cv2.findContours(self.input, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    
    def multipolygon(self): 
        """
        This function create multipolygons with list of find_contours' vector coordinates.

        Returns
        -------
        shapely.geometry MultiPolygon
            Return Multipolygon.
        """
        for i in self.find_contours()[0]:
            if len(i) >= 3:
                self.array.append(Polygon(np.squeeze(i)))
        
        return affine_transform(MultiPolygon(self.array), [self.image.transform[0],
                                                           self.image.transform[1],
                                                           self.image.transform[3],
                                                           self.image.transform[4],
                                                           self.image.transform[2],
                                                           self.image.transform[5]])
        
    def save_shp(self):
        """
        This function create a shp file with proper coordinate and projection system data.

        Raises
        ------
        Exception
            If the same name with shp name is exist, the error will be throw to warn user.
        """
        if self.output in os.listdir():
            
            raise Exception(f'{self.output} file is exists!')
            
        else:
            #Create driver for .shp file
            driver      = ogr.GetDriverByName('ESRI Shapefile')
            driver_ds   = driver.CreateDataSource(self.output)
            
            #Create Spatial Reference
            spatial_ref = osr.SpatialReference()
            spatial_ref.ImportFromEPSG(int(str(self.image.crs).split(':')[1]))
            layer       = driver_ds.CreateLayer('Shapefile', spatial_ref)
            
            #Create Field
            layer.CreateField(ogr.FieldDefn('Area (km²)', ogr.OFTReal))
            
            #Create Feature
            defn           = layer.GetLayerDefn()
            feature_create = ogr.Feature(defn)
            
            #Setting up Fields
            feature_create.SetField('Area (km²)', self.area)
            
            #Create geometry
            geometry = ogr.CreateGeometryFromWkb(self.multipolygon().wkb)
            feature_create.SetGeometry(geometry)
            
            layer.CreateFeature(feature_create)
    
    def show_vector(self):
        """
        This function shows shp file on the graph with geopandas and matplotlib library.

        """
        vector = geopandas.read_file(self.output)
        fig, ax = plt.subplots()
        ax.ticklabel_format(style='plain')
        vector.plot(ax=ax)

    def runApp(self):
        self.save_shp()
        
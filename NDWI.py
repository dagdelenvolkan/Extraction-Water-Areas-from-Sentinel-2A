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
import zipfile
import shutil
import geopandas
from shapely.affinity import affine_transform
from sentinelsat import SentinelAPI, geojson_to_wkt, read_geojson



class Download_Sentinel:
    
    def __init__(self, username, password, geo_json, platform_name = 'Sentinel-2', processinglevel = 'Level-2A', date_s ='NOW-3DAYS', date_e='NOW', cloud = (0, 5)):
        """

        Parameters
        ----------
        username : String
            Copernicus Scihub username.
        password : String
            Copernicus Scihub password.
        geo_json : String
            geo_json path.
        platform_name : String, optional
            DESCRIPTION. The default is 'Sentinel-2'.
        processinglevel : String, optional
            DESCRIPTION. The default is 'Level-2A'.
        date_s : String, optional
            DESCRIPTION. The default is 'NOW-3DAYS'.
        date_e : String, optional
            DESCRIPTION. The default is 'NOW'.
        cloud : Tuple, optional
            DESCRIPTION. The default is (0, 5).

        """

        self.platform_name    = platform_name
        self.processinglevel  = processinglevel
        self.date_s           = date_s
        self.date_e           = date_e
        self.cloud            = cloud
        self.json             = geojson_to_wkt(read_geojson(geo_json)) 
        self.api              = SentinelAPI(username, password)
        self.run()

    
    def query(self):
        
        return self.api.query(
            self.json,
            platformname         = self.platform_name,
            processinglevel      = self.processinglevel,
            date                 = (self.date_s, self.date_e),
            cloudcoverpercentage = self.cloud,
            )
    
    def download(self):
        
        return self.api.download_all(self.query())
    
    def run(self):
        self.download()


class unzip:
    
    def __init__(self, path=os.getcwd()):
        self.path = path
        self.unzip_bands()
        
    def unzip_bands(self):
        """
        Unzip and folder band3 and band12 to prepare NDWI class

        """
        os.chdir(self.path)
        for i in os.listdir():
            if i.startswith('S2A_MSIL2A'):
                zipfile.ZipFile(i, 'r').extractall()
                os.mkdir(i[:-4])
                direct  = os.listdir(f'{i[:-4]}.SAFE/GRANULE')[0]
                bands   = os.listdir(f'{i[:-4]}.SAFE/GRANULE/{direct}/IMG_DATA/R10m')
                bands20 = os.listdir(f'{i[:-4]}.SAFE/GRANULE/{direct}/IMG_DATA/R20m')
                for band in bands:
                    if band.endswith('B03_10m.jp2'):
                        shutil.move(f'{i[:-4]}.SAFE/GRANULE/{direct}/IMG_DATA/R10m/{band}', i[:-4])
                for band20 in bands20:
                    if band20.endswith('B12_20m.jp2'):
                        shutil.move(f'{i[:-4]}.SAFE/GRANULE/{direct}/IMG_DATA/R20m/{band20}', i[:-4])
            
                shutil.rmtree(f'{i[:-4]}.SAFE')
                
    
class NDWI:
    """
    This class working properly for Sentinel 2A satellite image. The resample function created for a sentinel2A bands.
    """

    def __init__(self, path, output_name):
        """
        Parameters
        ----------
        path: String
            The path which include sentinel-2A bands.
            
        output_name: String
            Output name as a tif format //Example: output.tif, ndwi.tif

        """
        self.path        = path
        self.output_name = output_name
        self.runApp()
                
    def read_images(self):
        """
        Function read NIR and SWIR bands
        
        Returns
        -------
        NIR and SWIR bands

        """
        for band in os.listdir(self.path):
            if band.endswith('B03_10m.jp2'):
                band_NIR = rasterio.open(f'{self.path}/{band}')
            if band.endswith('B12_20m.jp2'):
                band_SWIR = rasterio.open(f'{self.path}/{band}')
        
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
        return self.read_image() > threshold_otsu(np.nan_to_num(self.read_image(), 0)) - 0.10    
    
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
        show(rasterio.open(self.path).read(1), cmap='gray', transform=rasterio.open(self.path).transform)     
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
        fig, ax = plt.subplots(1, figsize=(12, 12))
        ax.ticklabel_format(style='plain')
        vector.plot(ax=ax)

    def runApp(self):
        self.save_shp()
        
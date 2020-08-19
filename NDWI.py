import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt


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
        self.path_NIR  = path_NIR
        self.path_SWIR = path_SWIR
        self.output_name = output_name
        self.runApp()
        
        
    def read_images(self):
        """
        Function read NIR and SWIR bands
        
        Returns
        -------
        NIR and SWIR bands

        """
        band_NIR = rasterio.open(self.path_NIR)
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
        self.print_screen()
        
    
    def read_image(self):
        return rasterio.open(self.path).read(1)
    
    def calc_area(self):
        return self.read_image()[4500:6000, 2000:4800] > 0.45
    
    def print_screen(self):
        print('{:.2f} km²'.format(len(self.calc_area()[self.calc_area()==True])* 10*10*10**(-6)))
        plt.imshow(self.calc_area(), cmap='gray')
        plt.title(self.path)
        plt.show()
        
        
    def run(self):
        self.print_screen()
        
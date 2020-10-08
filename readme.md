# Extraction Water Areas from Sentinel-2A Images
A Python library for extraction water areas as shapefile extension.

<br/>

# Quick Usage

## Importing library

```Python
import NDWI
```
<br/>

## Download Sentinel-2A Data from Copernicus Scihub.

```Python
NDWI.Download_Sentinel('username',
                       'password', 
                       'geo.json path')
```
<br/>

## Unzip and prepare bands which proper to mNDWI process.

```Python
#Select only folder path, file will be selected automatically
NDWI.unzip('Sentinel 2 Data folder path') 
```
<br/>

## mNDWI process
```Python
# Select only folder path, bands will be detected automatically.
NDWI.NDWI('folder path which included proper bands', 
          'output name <.tif>')
```

<br/>

## Vectorize
```Python 
NDWI.Vectorize('NDWI processed Image path <.tif>',
               'Output vector name <.shp>')

```
<br/>

> example.ipynb file has real examples. Do not forget to check out if you have a question.

---

<br/>

## Special thanks to Dr. Kaan Kalkan for him mentorship.

## İlerleme

[x] 19.08.2020 --> NDWI Hesaplayan, thresholding yapan ve alan hesaplayan sınıflar yazıldı ve ulubatlı gölü üzerinde testler gerçekleştirildi.

[x] 20.08.2020 --> Raster to Vector için Vectorize sınıfı eklendi ve jupyter lab üzerinden testler gerçekleştirildi. Eksenlerle ilgili bir sorun da düzeltildi.

[x] 21.08.2020 --> Clip eklendi, vectorize için projeksiyon bilgisi ve bu projeksiyona ait gerçek koordinatlar vector için üretilir hale getirildi.


## To-Do

* Su alanlarının bulunmasında otomatik eşik değeri bulan bir sisteme geçilecek.
* Kıyı çizgisi çiziminde iyileştirme (eksiksiz belirleme için)
* Sentinel görüntülerinin otomatik indirilmesi (bulutluluk ve bölge seçerek)
* NDWI map üzerinden görüntü işleme ile iyileştirme
* Fiona ile web tabanlı gösterim ve değişim gösterimi (farklı zamanlı görüntüler ile su alanlarının değişiminin izlenmesi)
* Vektörlerin topoloji kontrolleri
* Test verilieride yüklensin buraya
* Robust bir kod olması açısından sadece verinin olduğu klasörü sorup içinden veriyi otomatik okusun ilgili bantları
* Watershed segmentation ile su alanlarını belirleme
* Otsu vb thresholding algoritmaları ile thresholdlama çalışılacak
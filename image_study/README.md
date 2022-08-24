There are three models that store image URLs in the database

```
>>> DocumentImage.objects.count()
32994
>>> Photograph.objects.count()
219
>>> TranscriptPage.objects.count()
44728
```

I dumped all the values into nuremberg_images.xlsx


## DocumentImage

Almost all DocumentImage urls match r'/proxy_image/HLSL_NUR_\d{8}.jpg'
e.g. 41|/proxy_image/HLSL_NUR_00001001.jpg

```
>>> DocumentImage.objects.filter(url__iregex=r'/proxy_image/HLSL_NUR_\d{8}.jpg').count()
32461
```

6 of the remaining 533 match r'/proxy_image/printing/HLSL_NUR_\d{8}.jpg').count()
e.g. /proxy_image/printing/HLSL_NUR_00198001.jpg

```
>>> DocumentImage.objects.exclude(url__iregex=r'/proxy_image/HLSL_NUR_\d{8}.jpg').count()
533
>>> DocumentImage.objects.filter(url__iregex=r'/proxy_image/printing/HLSL_NUR_\d{8}.jpg').count()
6
```

35 have no URL
```
>>> DocumentImage.objects.filter(url__isnull=True).count()
35
```

The rest match r'/static/image_cache/thumb/HLSL_NUR_\d{8}.jpg'
e.g. '/static/image_cache/thumb/HLSL_NUR_03799001.jpg'

```
>>> DocumentImage.objects.filter(url__iregex=r'/static/image_cache/thumb/HLSL_NUR_\d{8}.jpg').count()
492
```


## Photograph

All Photograph object URLs match r'http://nrs\.harvard\.edu/urn-3:HLS\.Libr:\d{6}'
e.g. http://nrs.harvard.edu/urn-3:HLS.Libr:1192266

```
>>> Photograph.objects.filter(image_url__iregex=r'http://nrs\.harvard\.edu/urn-3:HLS\.Libr:\d{6}').count()
219
```

## TranscriptPage

All TranscriptPage object URLs match r'//s3.amazonaws.com/nuremberg-transcripts/NRMB-NMT\d\d-\d\d_\d{5}_\d\.jpg'
e.g. //s3.amazonaws.com/nuremberg-transcripts/NRMB-NMT01-01_00001_0.jpg

```
>>> TranscriptPage.objects.filter(image_url__iregex=r'//s3.amazonaws.com/nuremberg-transcripts/NRMB-NMT\d\d-\d\d_\d{5}_\d\.jpg').count()
44728
```

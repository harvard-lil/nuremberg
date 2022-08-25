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

These images are served via [this view](https://github.com/harvard-lil/nuremberg/blob/post-heroku/nuremberg/core/urls.py#L26), which just takes whatever comes after `/proxy_image/` and sticks it onto `http://s3.amazonaws.com/nuremberg-documents/` and serves you that.

### Outliers

There are 533 outliers.

#### 6 at "printing" URL

>>> DocumentImage.objects.exclude(url__iregex=r'/proxy_image/HLSL_NUR_\d{8}.jpg').count()
533

6 of the remaining 533 match r'/proxy_image/printing/HLSL_NUR_\d{8}.jpg')

```
>>> DocumentImage.objects.filter(url__iregex=r'/proxy_image/printing/HLSL_NUR_\d{8}.jpg').count()
6
```

1154|/proxy_image/printing/HLSL_NUR_00198001.jpg
2374|/proxy_image/printing/HLSL_NUR_00340001.jpg
8520|/proxy_image/printing/HLSL_NUR_01844001.jpg
1155|/proxy_image/printing/HLSL_NUR_00198002.jpg
1158|/proxy_image/printing/HLSL_NUR_00198003.jpg
22274|/proxy_image/printing/HLSL_NUR_02583022.jpg

These are served via [this view](https://github.com/harvard-lil/nuremberg/blob/post-heroku/nuremberg/core/urls.py#L23), which similarly takes whatever comes after `proxy_image/printing/` and sticks it onto `http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/`... which in all cases 404s.

```

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_00198001.jpg
HTTP/1.1 404 Not Found

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_00340001.jpg
HTTP/1.1 404 Not Found

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_01844001.jpg
HTTP/1.1 404 Not Found

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_00198002.jpg
HTTP/1.1 404 Not Found

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_00198003.jpg
HTTP/1.1 404 Not Found

curl -I http://nuremberg.law.harvard.edu/imagedir/HLSL_NUR_printing/HLSL_NUR_02583022.jpg
HTTP/1.1 404 Not Found
```

That is the `IMAGE_URL_ROOT` specified in [`documents/models.py`](https://github.com/harvard-lil/nuremberg/blob/506aefb364f1bdda973bd1066a291ef53fb9ef99/nuremberg/documents/models.py#L8)... but `IMAGE_URL_ROOT` is not referenced anywhere in the current codebase, that I can see.

This [custom Django management command](https://github.com/harvard-lil/nuremberg/blob/master/nuremberg/core/management/commands/scan_image_files.py#L37), which appears to have been used current a migration of the project from an older structure to a newer one, also references http://nuremberg.law.harvard.edu/imagedir/, but `HLSL_NMT01` rather than `HLSL_NUR_printing`.

Ben reports that all six images are present in the S3 bucket in the normal way.

My best guess, lacking any context on the project, is that this was a processing error of some kind... But we should ask Paulif those images are somehow special. If not, we can just remove the special handling. But if yes.... we need to know what is special, so we can recreate whatever the special handling was supposed to do lol.


#### 35 with no URL

```
>>> DocumentImage.objects.filter(url__isnull=True).count()
35
```

I confirmed that, indeed, the app is attempting to display images for these objects. See, for instance, page one of document 836 (the `first()` of the above queryset):
http://nuremberg.law.harvard.edu/documents/836#p.1

I'm trying to see if we can find what these wanted to point to. For what it's worth, [this code](https://github.com/harvard-lil/nuremberg/blob/master/nuremberg/documents/models.py#L89) clearly is not is use: it does not work... `url` is not defined.

I think they might truly be missing.

Why?

So, continuing with document 836: there are two images associated with the object, page 1 and page 2.

```
>>> [first_page, second_page]= list(Document.objects.get(pk=836).images.all())
>>> print(first_page, first_page.url)
#836 Page 1 s 700x1000 None
>>> print(second_page, second_page.url)
#836 Page 2 s 824x1319 /proxy_image/HLSL_NUR_00836002.jpg
```

One would expect to find `HLSL_NUR_00836001.jpg`, for page 1, in the bucket, but one does not.

```
curl -I http://nuremberg.law.harvard.edu/proxy_image/HLSL_NUR_00836001.jpg
HTTP/1.1 500 Internal Server Error
```

Ben confirms `HLSL_NUR_00836001.jpg` is not present in the documents bucket.

I checked and the same is true with document 2, page 13, the `last()` of the queryset; I presume it's true of all of them.

This is something else we should check with Paul about.

#### 492 at /static/image_cache/thumb/

The rest match r'/static/image_cache/thumb/HLSL_NUR_\d{8}.jpg'
e.g. '/static/image_cache/thumb/HLSL_NUR_03799001.jpg'

```
>>> DocumentImage.objects.filter(url__iregex=r'/static/image_cache/thumb/HLSL_NUR_\d{8}.jpg').count()
492
```

These appear to all be 404s as well.

```
>>> import requests
>>>
>>> cached_document_images = DocumentImage.objects.filter(url__iregex=r'/static/image_cache/thumb/HLSL_NUR_\d{8}.jpg')
>>>
>>> response_codes = set()
>>> for image in cached_document_images:
...     response_codes.add(requests.get(f'http://nuremberg.law.harvard.edu{image.url}').status_code)
>>>
>>> response_codes
{404}
```

While there is an [`image_cache` directory in the `static` directory of the `transcripts` app](https://github.com/harvard-lil/nuremberg/tree/master/nuremberg/transcripts/static/image_cache/transcripts), there is not one in the [`static` directory of the `documents` app](https://github.com/harvard-lil/nuremberg/tree/master/nuremberg/documents/static). I did not look at every commit in the documents app's [`static` directory's history](https://github.com/harvard-lil/nuremberg/commits/master/nuremberg/documents/static), but I didn't see an image cache present there in any of the commits I spot checked. [This commit removes the transcript cache](https://github.com/harvard-lil/nuremberg/commit/3293036bbb5d9118b118d476adcf4afddfdd3fc0), and then next one puts it back; I don't see anything similar for docs.

A search doesn't turn up any matches for `image_cache` in the repo; I don't see any code there that would create either cache; running `collectstatic` collects the `image_cache` for transcripts as expected but doesn't do anything magic for documents.

I don't think this is it either, but I looked to see if [Django's file system caching](https://docs.djangoproject.com/en/4.1/topics/cache/#filesystem-caching) could possibly be implicated... There is no evidence that is or ever was the case.

I suspect these are all safely in the S3 bucket; for instance, see http://nuremberg.law.harvard.edu/proxy_image/HLSL_NUR_03799001.jpg

I will not download them all now, to avoid spending the money.


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

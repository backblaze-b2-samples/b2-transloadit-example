# Backblaze B2 + TransloadIt Video Sharing Example

'CatTube' is a simple video sharing website comprising: 

* A web app implemented with [Django](https://www.djangoproject.com) and JavaScript.
* Video uploading with [Uppy](https://uppy.io) and processing at [TransloadIt](https://transloadit.com/).
* Cloud object storage at [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html).

## User Experience

* Users upload videos from their browser via the Uppy widget on the web app's 'Upload Video' page.

* Once the video is uploaded, a JavaScript front end in the browser polls an API at the web app until the transcoded version is available.

* The Uppy widget uploads the video file to TransloadIt, which transforms it according to a preconfigured template. TransloadIt saves the following set of assets to a private bucket in Backblaze B2:

  * The original video uploaded by the user
  * An intermediate, resized version of the video
  * The final resized, watermarked video for sharing
  * A thumbnail image taken from the watermarked video

* Once processing is complete, TransloadIt POSTs a JSON notification back to the web app containing full details of the 'assembly' process.

* The web app updates the video's database record with the name of the transcoded file.

* The next call from the JavaScript front end will return with the name of the transcoded video, signalling that the transcoding operation is complete. The browser shows the transcoded video, ready for viewing.

## Prerequisites

* An internet-accessible host
* [Python 3.9.2](https://www.python.org/downloads/release/python-392/) (other Python versions _may_ work) and `pip`
* Backblaze account
* TransloadIt account

## Installation

Clone this repository onto the host, `cd` into the local repository directory, then use `pip install` to install dependencies for the components as required:

```bash
git clone 
cd web-application
pip install -r requirements.txt
cd ..
```

For the worker:

```bash
cd worker
pip install -r requirements.txt
cd ..
```

## Configuration

### Web Application

Create a `.env` file in the `web-application` directory or set environment variables with your configuration:

```bash
AWS_S3_REGION_NAME="<for example: us-west-001>"
AWS_ACCESS_KEY_ID="<your B2 application key ID>"
AWS_SECRET_ACCESS_KEY="<your B2 application key>"
AWS_PRIVATE_BUCKET_NAME="<your private B2 bucket, for uploaded videos>"
AWS_STORAGE_BUCKET_NAME="<your public B2 bucket, for static web assets>"
TRANSCODER_WEBHOOK="<the API endpoint for the transcoder worker, e.g. http://1.2.3.4:5678/videos>"
```

Edit `cattube/settings.py` and add the domain name of your application server to `ALLOWED_HOSTS`. For example, if you were running the sample at `videos.example.com` you would use

```python
ALLOWED_HOSTS = ['videos.example.com']
```

_Note that `ALLOWED_HOSTS` is a list of strings - the square brackets are required._

From the `web-application` directory, run the usual commands to initialize a Django application:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### Worker

Create a `.env` file in the worker directory or set environment variables with your configuration:

```bash
B2_ENDPOINT_URL="<for example: https://s3.us-west-001.backblazeb2.com>"
B2_APPLICATION_KEY_ID="<your B2 application key ID>"
B2_APPLICATION_KEY="<your B2 application key>"
BUCKET_NAME="<your private B2 bucket, for uploaded videos>"
```

When the worker app receives a transcoding request, it downloads the raw video from B2 to a temporary file in the local filesystem. Similarly, `ffmpeg` writes the transcoded video file to a temporary file before the worker app uploads it to B2. By default, the app will delete the temporary files after the upload is complete, but
you can override this if necessary by editing `config.json` and setting `DELETE_TMP_FILES` to `false`.

## Run the Worker App

Use `flask run` to run the app in the Flask development server.

You may change the interface and port to which the worker app binds with the `-h/--host` and `-p/--port` options. For
example, to listen on the standard HTTP port on all interfaces, you would use:

```bash
flask run -h 0.0.0.0 -p 80
```

## Run the Web App

To start the development server:

```bash
python manage.py runserver
```

You may provide the runserver command with the interface and port to which the web app should bind. For example, to
listen on the standard HTTP port on all interfaces, you would use:

```bash
python manage.py runserver 0.0.0.0:80
```

## Caveats

Note that this is an example system! To run a similar system in production, you would need to make several changes,
including:

* Using a message queue such as [Apache Kafka](https://kafka.apache.org) or [RabbitMQ](https://www.rabbitmq.com) rather
  than HTTP POST notifications.
* Running the apps from a WSGI server such as [Green Unicorn](http://gunicorn.org/)
  or [Apache Web Server](https://httpd.apache.org) with [`mod_wsgi`](https://github.com/GrahamDumpleton/mod_wsgi).

Feel free to fork this repository and submit a pull request if you make an interesting change!

_The web application was originally forked from the
excellent [simple-s3-setup](https://github.com/sibtc/simple-s3-setup) by [sibtc](https://github.com/sibtc/)_.

# Backblaze B2 + bunny.net + TransloadIt Video Sharing Example

'CatTube' is a simple video sharing website comprising: 

* A web app implemented with [Django](https://www.djangoproject.com) and JavaScript.
* Video uploading with [Uppy](https://uppy.io) and processing at [TransloadIt](https://transloadit.com/).
* Cloud object storage at [Backblaze B2](https://www.backblaze.com/b2/cloud-storage.html).
* Content distribution via [bunny.net](bunny.net).

## User Experience

* Users upload videos from their browser to TransloadIt via the Uppy widget on the web app's 'Upload Video' page.

* Once the video is uploaded, a JavaScript front end in the browser polls an API at the web app until the transcoded version is available.

* TransloadIt transforms the video file according to a preconfigured template and saves the following set of assets to a private bucket in Backblaze B2:

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
* A Backblaze account. [Sign up here](https://www.backblaze.com/b2/sign-up.html?referrer=nopref).
* A bunny.net account. [Sign up here](https://panel.bunny.net/user/register/).
* A TransloadIt account. [Sign up here](https://transloadit.com/c/signup/).

## Backblaze B2

Click **Buckets** in the navigation menu on the left, then **Create a Bucket**. Give the bucket a name (you may need more than one try, the bucket name must be globally unique!), leave the remaining settings, and click **Create a Bucket**. Make a note of the **Endpoint** shown in the bucket details; it's a domain name of the form `s3.us-west-004.backblazeb2.com`. Make a note also of the region portion of the endpoint; this is the string following `s3.` and preceding `.backblazeb2.com`. In the example above, it's `us-west-004`, but yours may be different.

You'll be creating three Application Keys–one each for bunny.net, TransloadIt and the web application. Why three keys? The three B2 clients need different levels of access. bunny.net only needs to read files to cache and deliver them; TransloadIt only needs to write raw and processed files; the web app needs read/write access, but only to files with the `static/` prefix - Django's `collectstatic` command uploads new and updated assets such as CSS files and images with this prefix. 

Click **App Keys** in the left nav menu, then **Add a New Application Key**. Name the key `read-only-key-for-bunny`, select the bucket you just created, select **Read Only** and **Allow List All Bucket Names**, and click **Create New Key**. Make careful note of the key - you will not be able to retrieve it after navigating away from the page!

Now click **Add a New Application Key** a second time and name the key `write-only-key-for-transloadit`. Select your bucket, **Write Only** and **Allow List All Bucket Names**, and click **Create New Key**. Again, make careful note of the key!

Add a third Application Key, named `read-write-key-for-video-app`, with **Read and Write** access to the bucket you just created, and **Allow List All Bucket Names**. One more time, copy that key somewhere safe!

## bunny.net

Click **Pull Zones** in the navigation menu on the left, then **Add Pull Zone**. Give your Pull Zone a globally unique name, and set the **Origin URL** to `https://<your bucket name>.<your bucket endpoint>`. For example, if your bucket was called `example-movies` and the endpoint was `s3.us-west-004.backblazeb2.com`, the Origin URL would be `https://example-movies.s3.us-west-004.backblazeb2.com`. Scroll down and click **Add Pull Zone**.

Click **Skip the Instructions**, then click **Caching** in the left nav menu. Scroll down and enable **Optimize for video delivery**. This setting configures bunny.net to cut up cached files and store them in 5MB chunks. This allows bunny.net to process byte range requests for uncached files allowing video skipping for uncached content and lower origin traffic.

Now, in the left nav menu, click **Security**, then **S3 Authentication**. Click **Enable S3 Authentication** and paste in the read-only credentials you created in Backblaze: paste the Application Key ID into **AWS Key**, the Application Key into **AWS Secret**, and the region portion of your bucket's endpoint into **AWS Region Name**. Click **Save AWS Configuration**.

Finally, click **Edge Rules** in the left nav bar, then **Add Edge Rule**. Leave the action set to **Block Request** and give the rule a suitable description, for example: "Allow requests to only the static, watermarked and thumbnail folders". Set **Condition Matching** to **Match None**, then click **Add Condition**. Leave the attribute set to **Request URL** and operation as **Match Any**, and add three trigger values:

* `https://<your pull zone hostname>/thumbnail/*`
* `https://<your pull zone hostname>/watermarked/*`
* `https://<your pull zone hostname>/static/*`

Click **Save Edge Rule**. Now, bunny.net will disallow requests to URLs outside the permitted list, such as `https://<your pull zone hostname>/resized/*`.

## TransloadIt

You can create a new App, or use an existing one, as you see fit.

Click **Credentials** in the navigation menu on the left, then, under **Third-party Credentials** click **Add new Credential**. Select **Backblaze** as the service, name the key `backblaze-write-only`, and paste in the Backblaze B2 Bucket name, Application Key ID and Application Key. Click **Save**.

Now click **Templates** in the left nav menu, then **New Template**. Click **Blank** to create an empty template. Give the template a suitable name and paste in the [assembly instructions](assembly-instructions.json). Feel free to replace the `watermark_url` and otherwise customize the template! Click **Create Template** and copy the template id displayed at the top of the page.

Finally, to secure access to your template, click **Settings** in the left nav menu and, under **API Settings**, enable **Require a correct Signature**. The web application contains code to generate a unique signature for each file upload.

## Web Application

### Installation

Clone this repository onto the host, `cd` into the local repository directory, then use `pip install` to install dependencies for the components as required:

```bash
git clone git@github.com:backblaze-b2-samples/b2-transloadit-example.git
cd b2-transloadit-example
pip install -r requirements.txt
```

### Configuration

Copy `.env.template` to `.env`, or set environment variables with your configuration:

```bash
AWS_ACCESS_KEY_ID = "<Your Backblaze Application Key ID>"
AWS_SECRET_ACCESS_KEY = "<Your Backblaze Application Key>"
AWS_STORAGE_BUCKET_NAME = "<Your Backblaze Bucket>"
AWS_S3_REGION_NAME = "<Your Backblaze endpoint region, e.g. us-west-004>"

BUNNY_PULL_ZONE_DOMAIN = "<Your bunny.net Pull Zone domain, e.g. example-movies.b-cdn.net>"

TRANSLOADIT_KEY = "<Your TransloadIt Auth Key>"
TRANSLOADIT_SECRET = "<Your TransloadIt Auth Secret>"
TRANSLOADIT_TEMPLATE_ID = "<Your TransloadIt Template ID>"

WEB_APPLICATION_HOST = "<Your web application's domain, e.g. movies.example.com>"
```

Run the usual commands to initialize a Django application:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
```

### Run the Web App

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
including running the app from a WSGI server such as [Green Unicorn](http://gunicorn.org/)
  or [Apache Web Server](https://httpd.apache.org) with [`mod_wsgi`](https://github.com/GrahamDumpleton/mod_wsgi).

Feel free to fork this repository and submit a pull request if you make an interesting change!

_The web application is based on the [Backblaze B2 Video Sharing Example](https://github.com/backblaze-b2-samples/b2-video-sharing-example), which in turn was originally forked from the 
excellent [simple-s3-setup](https://github.com/sibtc/simple-s3-setup) by [sibtc](https://github.com/sibtc/)_.

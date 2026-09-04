import hashlib
import hmac
import json
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from cattube import settings as app_settings
from cattube.storage_backends import StaticStorage

from .models import Video


class B2ConfigurationTests(SimpleTestCase):
    def test_missing_env_reports_all_required_names(self):
        environ = {name: 'value' for name in app_settings.REQUIRED_ENV_VARS}
        del environ['B2_APPLICATION_KEY_ID']
        del environ['B2_PUBLIC_URL_BASE']

        with self.assertRaises(ImproperlyConfigured) as context:
            app_settings._require_env_vars(environ)

        message = str(context.exception)
        self.assertIn('B2_APPLICATION_KEY_ID', message)
        self.assertIn('B2_PUBLIC_URL_BASE', message)

    def test_public_url_base_normalizes_bare_domain(self):
        self.assertEqual(
            app_settings._normalize_public_url_base('cdn.example.com/'),
            'https://cdn.example.com',
        )

    def test_public_url_base_rejects_http(self):
        with self.assertRaisesMessage(ImproperlyConfigured, 'https:// URL'):
            app_settings._normalize_public_url_base('http://cdn.example.com')

    def test_static_storage_preserves_public_url_path_prefix(self):
        storage = StaticStorage(
            custom_domain='f004.backblazeb2.com/file/mybucket',
            location='static',
        )

        self.assertEqual(
            storage.url('css/app.css'),
            'https://f004.backblazeb2.com/file/mybucket/static/css/app.css',
        )

    def test_static_storage_supports_pathless_public_url_domain(self):
        storage = StaticStorage(custom_domain='cdn.example.com', location='static')

        self.assertEqual(
            storage.url('css/app.css'),
            'https://cdn.example.com/static/css/app.css',
        )


class TransloaditNotificationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='password')
        self.video = Video.objects.create(
            title='Sample video',
            assembly_id='assembly-123',
            transcoded='https://cdn.example.com/watermarked/old.mp4',
            thumbnail='https://cdn.example.com/thumbnail/old.jpg',
            user=self.user,
        )

    def _notification_payload(self):
        return json.dumps(
            {
                'assembly_id': self.video.assembly_id,
                'results': {
                    'watermarked': [{'name': 'movie.mp4'}],
                    'thumbnail': [{'name': 'thumb.jpg'}],
                },
            },
            separators=(',', ':'),
        )

    def _signature(self, payload):
        return 'sha384:' + hmac.new(
            settings.TRANSLOADIT_SECRET.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha384,
        ).hexdigest()

    def _post_notification(self, data):
        return self.client.post(
            reverse('notification'),
            urlencode(data),
            content_type='application/x-www-form-urlencoded',
        )

    def test_notification_rejects_missing_signature_without_mutating_video(self):
        response = self._post_notification({'transloadit': self._notification_payload()})

        self.assertEqual(response.status_code, 403)
        self.video.refresh_from_db()
        self.assertEqual(self.video.transcoded, 'https://cdn.example.com/watermarked/old.mp4')
        self.assertEqual(self.video.thumbnail, 'https://cdn.example.com/thumbnail/old.jpg')

    def test_notification_rejects_bad_signature_without_mutating_video(self):
        response = self._post_notification(
            {
                'transloadit': self._notification_payload(),
                'signature': 'sha384:' + ('0' * 96),
            },
        )

        self.assertEqual(response.status_code, 403)
        self.video.refresh_from_db()
        self.assertEqual(self.video.transcoded, 'https://cdn.example.com/watermarked/old.mp4')
        self.assertEqual(self.video.thumbnail, 'https://cdn.example.com/thumbnail/old.jpg')

    def test_notification_accepts_valid_signature_and_updates_video(self):
        payload = self._notification_payload()

        response = self._post_notification(
            {
                'transloadit': payload,
                'signature': self._signature(payload),
            },
        )

        self.assertEqual(response.status_code, 204)
        self.video.refresh_from_db()
        self.assertEqual(
            self.video.transcoded,
            'https://cdn.example.com/watermarked/assembly-123/movie.mp4',
        )
        self.assertEqual(
            self.video.thumbnail,
            'https://cdn.example.com/thumbnail/assembly-123/thumb.jpg',
        )

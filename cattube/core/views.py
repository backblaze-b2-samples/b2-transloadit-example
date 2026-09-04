import json
import hmac
import hashlib
from datetime import datetime, timedelta
from json import JSONDecodeError
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.safestring import mark_safe
from django.views.decorators.cache import never_cache
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.decorators import parser_classes
from rest_framework.parsers import FormParser
from rest_framework.response import Response

from .models import Video
from .serializers import VideoSerializer, NotificationSerializer

videos_url_path = f'{settings.B2_PUBLIC_URL_BASE}/watermarked/'
thumbnails_url_path = f'{settings.B2_PUBLIC_URL_BASE}/thumbnail/'

# From https://codereview.stackexchange.com/a/24416/27914
def url_path_join(*parts):
    """Normalize url parts and join them with a slash."""
    schemes, netlocs, paths, queries, fragments = zip(*(urlsplit(part) for part in parts))
    scheme = first(schemes)
    netloc = first(netlocs)
    path = '/'.join(x.strip('/') for x in paths if x)
    query = first(queries)
    fragment = first(fragments)
    return urlunsplit((scheme, netloc, path, query, fragment))


def first(sequence, default=''):
    return next((x for x in sequence if x), default)


def valid_transloadit_signature(transloadit_payload, signature):
    expected = 'sha384:' + hmac.new(
        settings.TRANSLOADIT_SECRET.encode('utf-8'),
        transloadit_payload.encode('utf-8'),
        hashlib.sha384,
    ).hexdigest()
    return hmac.compare_digest(signature, expected)


class VideoListView(ListView):
    model = Video

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        videos = Video.objects.all()
        context['videos'] = videos
        return context


class VideoDetailView(DetailView):
    model = Video
    slug_field = 'id'
    slug_url_kwarg = 'video_id'


@method_decorator(login_required, name='dispatch')
class VideoCreateView(CreateView):
    model = Video
    fields = ['title', 'assembly_id', ]

    def get_success_url(self):
        return reverse_lazy('watch', kwargs={'video_id': self.object.id})

    def get_context_data(self, **kwargs):
        template_id = settings.TRANSLOADIT_TEMPLATE_ID
        notify_url = self.request.build_absolute_uri(reverse('notification'))  # .replace("http:", "https:")

        # Signature calculation from
        # https://transloadit.com/docs/topics/signature-authentication/#signature-python-sdk-demo
        expires = (timedelta(seconds=60 * 60) + datetime.utcnow()).strftime("%Y/%m/%d %H:%M:%S+00:00")
        auth_key = settings.TRANSLOADIT_KEY
        auth_secret = settings.TRANSLOADIT_SECRET
        params = {
            'auth': {
                'key': auth_key,
                'expires': expires,
            },
            'template_id': template_id,
            'notify_url': notify_url
        }

        message = json.dumps(params, separators=(',', ':'), ensure_ascii=False)
        signature = hmac.new(auth_secret.encode('utf-8'),
                             message.encode('utf-8'),
                             hashlib.sha384).hexdigest()

        context = super().get_context_data(**kwargs)
        # Need to mark message as safe so Django doesn't escape the JSON
        context['params'] = mark_safe(message)
        context['signature'] = 'sha384:' + signature
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return super().form_valid(form)


@method_decorator(login_required, name='dispatch')
class VideoDeleteView(DeleteView):
    model = Video
    slug_field = 'id'
    slug_url_kwarg = 'video_id'

    def get_success_url(self):
        return reverse('home')


@login_required
def delete_all_videos(request):
    print('Deleting all the videos!')
    Video.objects.all().delete()
    return HttpResponseRedirect(reverse('home'))


# JavaScript polls this endpoint - we don't want the browser to cache the response!
@never_cache
@api_view(['GET'])
def video_detail(request, video_id):
    print(f'Received request for detail on: {video_id}')

    doc = get_object_or_404(Video, id=video_id)
    serializer = VideoSerializer(doc)
    print(f'Returning : {serializer.data}')
    return Response(serializer.data)


@api_view(['POST'])
@parser_classes([FormParser])
def receive_notification_from_transcoder(request):
    transloadit_payload = request.data.get('transloadit')
    signature = request.data.get('signature', '')
    if transloadit_payload and not valid_transloadit_signature(transloadit_payload, signature):
        return Response(status=status.HTTP_403_FORBIDDEN)

    serializer = NotificationSerializer(data=request.data)
    if serializer.is_valid():
        print(f'Received notification: {serializer.data}')

        try:
            transloadit = json.loads(serializer.validated_data['transloadit'])
            assembly_id = transloadit['assembly_id']
            watermarked_name = transloadit['results']['watermarked'][0]['name']
            thumbnail_name = transloadit['results']['thumbnail'][0]['name']
        except (JSONDecodeError, KeyError, IndexError, TypeError):
            return Response(
                {'transloadit': ['Invalid TransloadIt notification payload.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        print(f'Getting {assembly_id}')
        doc = get_object_or_404(Video, assembly_id=assembly_id)

        doc.transcoded = url_path_join(videos_url_path, assembly_id, watermarked_name)
        doc.thumbnail = url_path_join(thumbnails_url_path, assembly_id, thumbnail_name)

        print(f'Saving {doc}')
        doc.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    print(f'Serializer errors: {serializer.errors}')
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

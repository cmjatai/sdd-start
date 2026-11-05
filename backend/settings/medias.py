from pathlib import Path

from decouple import AutoConfig
from easy_thumbnails.conf import Settings as thumbnail_settings

config = AutoConfig()

PROJECT_DIR = Path(__file__).parent.parent.parent

DEBUG = config('DEBUG', default=False, cast=bool)

MEDIA_URL = '/media/'

MEDIA_ROOT = PROJECT_DIR.parent / 'backend_media' / 'media'
MEDIA_CACHE_ROOT = PROJECT_DIR.parent / 'backend_media' / 'media_cache'


if DEBUG and '/var/project' not in str(PROJECT_DIR):
    MEDIA_ROOT = Path('/mnt/volumes') / 'backend_media' / 'media'
    MEDIA_CACHE_ROOT = Path('/mnt/volumes') / 'backend_media' / 'media_cache'

FILTERS_HELP_TEXT_FILTER = False

IMAGE_CROPPING_SIZE_WARNING = True
IMAGE_CROPPING_JQUERY_URL = None

THUMBNAIL_PROCESSORS = (
    'image_cropping.thumbnail_processors.crop_corners',
) + thumbnail_settings.THUMBNAIL_PROCESSORS

THUMBNAIL_SOURCE_GENERATORS = ('backend.utilss.pil_image',)

MAX_DOC_UPLOAD_SIZE = 1512 * 1024 * 1024  # 1512MB
MAX_IMAGE_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


FILE_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_DOC_UPLOAD_SIZE

DATA_UPLOAD_MAX_NUMBER_FILES = 1000

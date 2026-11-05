from django import forms
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, PermissionsMixin
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db.models.deletion import PROTECT, SET_NULL
from django.db.models.fields.json import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from image_cropping import ImageCropField, ImageRatioField

from backend.globalrules import PERMS_FOR_USERS
from backend.model_mixins import SearchModelMixin
from backend.utilss import get_settings_auth_user_model


def groups_remove_user(user, groups_name):
    if not isinstance(groups_name, list):
        groups_name = [
            groups_name,
        ]
    for group_name in groups_name:
        if not group_name or not user.groups.filter(name=group_name).exists():
            continue
        g = Group.objects.get_or_create(name=group_name)[0]
        user.groups.remove(g)


def groups_add_user(user, groups_name):
    if not isinstance(groups_name, list):
        groups_name = [
            groups_name,
        ]
    for group_name in groups_name:
        if not group_name or user.groups.filter(name=group_name).exists():
            continue
        g = Group.objects.get_or_create(name=group_name)[0]
        user.groups.add(g)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        """
        Creates and saves a User with the given username, email and password.
        """
        now = timezone.now()
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            is_staff=is_staff,
            is_active=True,
            is_superuser=is_superuser,
            date_joined=now,
            **extra_fields,
        )
        user.set_password(password)
        try:
            user.save(using=self._db)
        except:
            user = self.model.objects.get_by_natural_key(email)

        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        return self._create_user(email, password, True, True, **extra_fields)


def sizeof_fmt(num, suffix='B'):
    """
    Shamelessly copied from StackOverflow:
    http://stackoverflow.com/questions/1094841/reusable-library-to-get-human-readable-version-of-file-size

    :param num:
    :param suffix:
    :return:
    """
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return '%3.1f%s%s' % (num, unit, suffix)
        num /= 1024.0
    return '%.1f%s%s' % (num, 'Yi', suffix)


def avatar_validation(image):
    if image:
        # 10 MB
        max_file_size = 10 * 1024 * 1024
        if image.size > max_file_size:
            raise forms.ValidationError(
                _('The maximum file size is {0}').format(sizeof_fmt(max_file_size))
            )


class User(AbstractBaseUser, SearchModelMixin, PermissionsMixin, models.Model):
    FIELDFILE_NAME = ('avatar',)

    fields_search = [
        'first_name',
        'last_name',
        'email',
    ]

    objects = UserManager()
    USERNAME_FIELD = 'email'

    email = models.EmailField(_('email address'), unique=True)

    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as '
            'active. Unselect this instead of deleting accounts.'
        ),
    )

    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    # -------------------------------------------------

    avatar = ImageCropField(
        upload_to='avatars/',
        verbose_name=_('Avatar'),
        validators=[avatar_validation],
        null=True,
        blank=True,
    )

    avatar_cropping = ImageRatioField(
        'avatar',
        '128x128',
        verbose_name=_('Seleção (Enquadramento)'),
        help_text=_(
            'A configuração do Avatar é possível após a atualização da fotografia.'
        ),
    )

    class Meta(AbstractBaseUser.Meta):
        abstract = False
        permissions = PERMS_FOR_USERS
        ordering = ('-is_superuser', 'first_name', 'last_name')
        verbose_name = _('Usuário')
        verbose_name_plural = _('Usuários')

    def __str__(self):
        return self.get_display_name()

    @property
    def username(self):
        return self.get_username()

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        return ' '.join([self.first_name, self.last_name]).strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def get_display_name(self):
        return self.get_full_name() or self.email

    def get_absolute_url(self):
        return 'users_profile', [self.pk], {}


class AuditLogManager(models.Manager):
    use_for_related_fields = True

    def last_action_user(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False).first()
        return qs

    def first_action_user(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False).last()
        return qs

    def actions_users(self):
        # for_related_fields
        qs = self.get_queryset()
        qs = qs.filter(user__isnull=False)
        return qs


class AuditLog(models.Model):
    objects = AuditLogManager()

    OPERATION_CHOICES = (
        ('U', 'Atualizado'),
        ('C', 'Criado'),
        ('D', 'Excluído'),
        ('P', 'Pesquisa'),
    )

    user = models.ForeignKey(
        get_settings_auth_user_model(),
        verbose_name=_('Usuário'),
        on_delete=SET_NULL,
        blank=True,
        null=True,
        default=None,
    )

    email = models.CharField(
        max_length=100, verbose_name=_('email'), blank=True, db_index=True
    )

    operation = models.CharField(
        max_length=1,
        verbose_name=_('operation'),
        choices=OPERATION_CHOICES,
        db_index=True,
    )

    timestamp = models.DateTimeField(
        verbose_name=_('timestamp'), editable=False, auto_now_add=True
    )

    obj = JSONField(
        verbose_name=_('Object'),
        blank=True,
        null=True,
        default=None,
        encoder=DjangoJSONEncoder,
    )

    content_type = models.ForeignKey(
        ContentType, blank=True, null=True, default=None, on_delete=PROTECT
    )
    object_id = models.PositiveIntegerField(blank=True, null=True, default=None)
    content_object = GenericForeignKey('content_type', 'object_id')

    obj_id = models.PositiveIntegerField(verbose_name=_('object_id'), db_index=True)

    model_name = models.CharField(
        max_length=100, verbose_name=_('model'), db_index=True
    )
    app_name = models.CharField(max_length=100, verbose_name=_('app'), db_index=True)

    class Meta:
        verbose_name = _('AuditLog')
        verbose_name_plural = _('AuditLogs')
        ordering = ('-id',)

    def __str__(self):
        return '[%s] %s %s.%s %s' % (
            self.timestamp,
            self.operation,
            self.app_name,
            self.model_name,
            self.user,
        )

from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from project_package.otkauth import OTK
from project_package.hash_data import hash_data
from project_package.serialization import *


OTK_PREFIX = hash_data('votings_site')


class CustomUser(AbstractUser):

	password = models.BinaryField(_("password"), max_length=1024)

	@staticmethod
	def get_otk_request_for_id():
		request = OTK.get_request_for_id(OTK_PREFIX)
		return serialize_to_string(request).hex()

	def get_otk_request_for_update(self):
		otk = deserialize_from_string(self.password)
		request = otk.get_request_for_update()
		return serialize_to_string(request).hex()

class Profile(models.Model):
	user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
	contacts = models.CharField(max_length=1024, null=True, default='Отсутствуют')
	sign_pk = models.BinaryField(null=True, default=None)
	kem_pk = models.BinaryField(null=True, default=None)

	def has_public_keys(self):
		if self.sign_pk and self.kem_pk:
			return True
		else:
			return False

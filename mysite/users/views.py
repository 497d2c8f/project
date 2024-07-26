from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate, login
from django.views.generic import TemplateView
from .models import *
from .forms import *
from project_package.serialization import *
import os

# Create your views here.


class CreateUserView(TemplateView):

	template_name = 'users/create_user.html'

	def get(self, request, *args, **kwargs):
		otk_request_for_id = get_user_model().get_otk_request_for_id()
		return render(request, self.template_name, {'otk_request_for_id': otk_request_for_id})

	def post(self, request, *args, **kwargs):
		otk_id_data = deserialize_from_string(bytes.fromhex(request.POST['otk_id'])).get_data()
		username = otk_id_data['current_hash'].hex()
		password = bytes.fromhex(request.POST['otk_id'])
		user = get_user_model().objects.create_user(username=username, password=password)
		user.save()
		Profile.objects.create(
			user=get_user_model().objects.get(username=username)
		)
		return redirect('users:login')




class LoginUserView(TemplateView):

	template_name = 'users/login_user.html'

	def get(self, request, *args, **kwargs):
		otk_request_for_id = get_user_model().get_otk_request_for_id()
		return render(request, self.template_name, {'otk_request_for_id': otk_request_for_id})

	def post(self, request, *args, **kwargs):

		if 'otk' in request.POST:
			username = request.POST['username']
			otk = bytes.fromhex(request.POST['otk'])
			user = authenticate(username=username, password=otk)
			if user is not None:
				login(request, user)
			return redirect('index')

		username = deserialize_from_string(bytes.fromhex(request.POST['otk_id'])).get_data()['current_hash'].hex()

		try:
			user = get_user_model().objects.get(username=username)
			return render(request, self.template_name, {'username': username, 'otk_request_for_update': user.get_otk_request_for_update()})
		except:
			return redirect('index')




class ShowProfileView(LoginRequiredMixin, TemplateView):

	template_name = 'users/show_profile.html'

	def get(self, request, username, *args, **kwargs):
		user = get_user_model().objects.get(username=username)
		user_has_public_keys = user.profile.has_public_keys()
		votings = {
			'author': user.voting_set.all(),
			'participant': [participant.voting for participant in user.participant.all()]
		}
		content = {
			'username': username,
			'contacts': user.profile.contacts,
			'update_contacts_form': UpdateContactsForm(),
			'user_has_public_keys': user_has_public_keys,
			'votings': votings
		}
		return render(request, self.template_name, context=content)

	def post(self, request, *args, **kwargs):
		UpdateContactsForm(request.POST).save_contacts(request)
		try:
			public_keys = deserialize_from_string(bytes.fromhex(request.POST['public_keys']))
			profile = get_user_model().objects.get(username=request.user.username).profile
			profile.sign_pk = public_keys['sign_pk']
			profile.kem_pk = public_keys['kem_pk']
			profile.save()
		except:
			pass
		return redirect('users:show_profile', username=request.user.username)

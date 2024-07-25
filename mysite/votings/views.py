from project_package.voting import Voting as VotingObject
from project_package.files import get_file_like_object, SUFFIX_LENGTH
from project_package.ciphertext import Ciphertext
from project_package.hash_data import hash_data
from project_package.serialization import *
from project_package.message import *
from .models import *
from .forms import *
from users.models import Profile
from django.shortcuts import render, redirect
from django.http import HttpResponseNotFound, FileResponse
from django.views.generic import ListView, TemplateView
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin


class IndexView(TemplateView):

	template_name = 'votings/index.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name)


class VotingsListView(LoginRequiredMixin, ListView):

	model = Voting
	template_name = 'votings/votings_list.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['votings'] = Voting.objects.all()
		return context


class CreateVotingView(LoginRequiredMixin, TemplateView):

	template_name = 'votings/create_voting.html'

	def get(self, request, *args, **kwargs):
		return render(
			request,
			self.template_name,
			context={
				'user_profile_has_public_keys': request.user.profile.has_public_keys(),
				'upload_voting_file_form': UploadVotingFileForm()
			}
		)

	def post(self, request, *args, **kwargs):
		voting = UploadVotingFileForm(request.POST, request.FILES).save_voting(request)
		if voting:
			return redirect(
				'voting_page',
				v_id=voting.v_id
			)
		return redirect('index')


class VotingPageView(LoginRequiredMixin, TemplateView):

	template_name = 'votings/voting_page.html'

	def get(self, request, v_id, *args, **kwargs):

		voting = Voting.objects.get(v_id=v_id)
		participant = self._try_to_get_participant(request, voting)
		self._redirect_to_voting_list_if_user_is_not_allowed_to_voting(request, voting)

		return render(
			request,
			self.template_name,
			{
				'voting_data': voting.get_voting_data(),
				'profile_has_public_keys': request.user.profile.has_public_keys(),
				'selected_mediator': self._try_to_get_selected_mediator(request, voting),
				'mediators_with_msg_ma_number': self._get_mediators_with_msg_ma_number(voting),
				'upload_msg_mw_file_form': UploadMsgMWFileForm(),
				'upload_msg_em_file_form': UploadMsgEMFileForm(),
				'upload_msg_ma_file_form': UploadMsgMAFileForm(),
				'upload_msg_voting_summary_file_form': UploadMsgVotingSummaryFileForm(),
				'msg_em_exists': self._msg_em_exists(participant),
				'msg_mw_exists': self._msg_mw_exists(participant),
				'msg_ma_exists': self._msg_ma_exists(participant),
				'msg_voting_summary_exists': self._msg_voting_summary_exists(voting)
			}
		)

	def post(self, request, v_id, *args, **kwargs):

		voting = Voting.objects.get(v_id=v_id)
		participant = self._try_to_get_participant(request, voting)

		response = self._process_pressed_buttons(request, voting, participant)
		if response:
			return response
		self._process_valid_forms(request, v_id, voting, participant)

		return redirect('voting_page', v_id=v_id)

	def _process_pressed_buttons(self, request, voting, participant):

		if 'become_mediator' in request.POST:
			self._toggle_participant_is_mediator(request, voting, participant)

		if 'select_mediator' in request.POST:
			self._toggle_selected_mediator(request, voting, participant)

		if 'registration' in request.POST:
			self._toggle_registration(request, voting)

		if 'is_open' in request.POST:
			self._toggle_voting_is_open(request, voting)

		if 'download_voting_file' in request.POST:
			return self._get_voting_file_response(request, voting, participant)

		if 'download_msg_wm_1_file' in request.POST:
			return self._get_msg_wm_1_file_response(request, voting)

		if 'download_msg_wm_2_file' in request.POST:
			return self._get_msg_wm_2_file_response(request, voting, participant)

		if 'download_msg_wa_file' in request.POST:
			return self._get_msg_wa_file_response(request, voting, participant)

	@staticmethod
	def _process_valid_forms(request, v_id, voting, participant):
		UploadMsgEMFileForm(request.POST, request.FILES).save_file(v_id, participant)
		UploadMsgMWFileForm(request.POST, request.FILES).save_file(participant)
		UploadMsgMAFileForm(request.POST, request.FILES).save_file(voting, participant)
		UploadMsgVotingSummaryFileForm(request.POST, request.FILES).save_file(voting)

	@staticmethod
	def _redirect_to_voting_list_if_user_is_not_allowed_to_voting(request, voting):
		user_is_allowed_to_voting = VotingPageView._user_is_allowed_to_voting(request, voting)
		user_is_author = voting.author == request.user
		if not user_is_allowed_to_voting and not user_is_author:
			return redirect('votings_list')

	@staticmethod
	def _user_is_allowed_to_voting(request, voting):
		profile_has_public_keys = request.user.profile.has_public_keys()
		if profile_has_public_keys:
			return deserialize_from_string(voting.voting_object).get_s_a_lvp().get_data().check(request.user.profile.sign_pk)
		else:
			return False

	@staticmethod
	def _try_to_get_participant(request, voting):
		try:
			return Participant.objects.get(user=request.user, voting=voting)
		except:
			return None

	@staticmethod
	def _toggle_participant_is_mediator(request, voting, participant):
		if request.POST['become_mediator'] == 'yes':
			if participant:
				participant.is_mediator = True
				participant.save()
			else:
				Participant.objects.create(user=request.user, voting=voting, is_mediator=True)
		elif request.POST['become_mediator'] == 'no':
			electors = request.user.mediator.all()
			for elector in electors:
				if elector.is_mediator:
					elector.mediator = None
					elector.save()
				else:
					elector.delete()
			participant = Participant.objects.get(user=request.user, voting=voting)
			if participant.mediator:
				participant.is_mediator = False
				participant.save()
			else:
				participant.delete()

	@staticmethod
	def _toggle_selected_mediator(request, voting, participant):
		if request.POST['select_mediator'] == 'yes':
			mediator = get_user_model().objects.get(username=request.POST['selected_mediator_username'])
			if participant:
				participant.mediator = mediator
				participant.save()
			else:
				Participant.objects.create(user=request.user, voting=voting, mediator=mediator)
		if request.POST['select_mediator'] == 'no':
			if participant.is_mediator:
				participant.mediator = None
				participant.save()
			else:
				participant.delete()

	@staticmethod
	def _toggle_registration(request, voting):
		voting.registration = bool(request.POST['registration'])
		if voting.registration:
			voting.is_open = False
		else:
			voting.update_voting_object()
		voting.save()

	@staticmethod
	def _toggle_voting_is_open(request, voting):
		voting.is_open = bool(request.POST['is_open'])
		voting.save()

	@staticmethod
	def _get_voting_file_response(request, voting, participant):
		voting_object = deserialize_from_string(voting.voting_object)
		selected_m_sign_pk = bytes(32)
		if request.user != voting.author:
			try:
				mediator_profile = participant.mediator.profile
				m_sign_pk = mediator_profile.sign_pk
				mediator_kem_pk = mediator_profile.kem_pk
				voting_object.set_d_sel_m_pk({'m_sign_pk': m_sign_pk, 'm_kem_pk': mediator_kem_pk})
				selected_m_sign_pk = m_sign_pk
			except AttributeError: # а точнее AttributeError
				pass
		return FileResponse(get_file_like_object(voting=voting_object), as_attachment=False, filename=f'voting__{voting_object.get_v_id().hex()[:SUFFIX_LENGTH]}_{selected_m_sign_pk.hex()[:SUFFIX_LENGTH]}')

	@staticmethod
	def _get_msg_wm_1_file_response(request, voting):
		electors = request.user.mediator.filter(voting=voting)
		l_e_emek_e_eaek_b = [deserialize_from_string(elector.e_emek_e_eaek_b) for elector in electors]
		msg_wm_1 = MsgWM1(l_e_emek_e_eaek_b)
		file_like_object = get_file_like_object(msg_wm_1=msg_wm_1)
		m_sign_pk = request.user.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_wm_1__{voting.v_id[:SUFFIX_LENGTH]}_{bytes(8).hex()}_{m_sign_pk.hex()[:SUFFIX_LENGTH]}')

	@staticmethod
	def _get_msg_wm_2_file_response(request, voting, participant):
		msg_mw = deserialize_from_string(participant.msg_mw)
		l_h_e_emek_e_eaek_b = msg_mw.get_data()['s_m_l_h_e_emek_e_eaek_b'].get_data()
		electors = request.user.mediator.filter(voting=voting)
		l_rfp = []
		for elector in electors:
			e_emek_e_eaek_b = deserialize_from_string(elector.e_emek_e_eaek_b)
			h_e_emek_e_eaek_b = hash_data(e_emek_e_eaek_b)
			if h_e_emek_e_eaek_b in l_h_e_emek_e_eaek_b:
				rfp = deserialize_from_string(elector.rfp)
				l_rfp.append(rfp)
		msg_wm_2 = MsgWM2(l_rfp)
		file_like_object = get_file_like_object(msg_wm_2=msg_wm_2)
		m_sign_pk = request.user.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_wm_2__{voting.v_id[:SUFFIX_LENGTH]}_{bytes(8).hex()}_{m_sign_pk.hex()[:SUFFIX_LENGTH]}')

	@staticmethod
	def _get_msg_wa_file_response(request, voting, participant):
		mediators_with_msg_ma = voting.participant_set.filter(msg_ma__isnull=False)
		msg_wa = {}
		for mediator in mediators_with_msg_ma:
			m_sign_pk = mediator.user.profile.sign_pk
			msg_ma = deserialize_from_string(mediator.msg_ma)
			msg_wa[m_sign_pk] = msg_ma
		file_like_object = get_file_like_object(msg_wa=msg_wa)
		a_sign_pk = voting.author.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_wa__{voting.v_id[:SUFFIX_LENGTH]}_{bytes(8).hex()}_{a_sign_pk.hex()[:SUFFIX_LENGTH]f}')

	@staticmethod
	def _msg_em_exists(participant):
		try:
			return bool(participant.rfp) and bool(participant.e_emek_e_eaek_b)
		except AttributeError:
			return False

	@staticmethod
	def _msg_mw_exists(participant):
		try:
			return bool(participant.msg_mw)
		except AttributeError:
			return False

	@staticmethod
	def _msg_ma_exists(participant):
		try:
			return bool(participant.msg_ma)
		except AttributeError:
			return False

	@staticmethod
	def _msg_voting_summary_exists(voting):
		try:
			return bool(voting.msg_voting_summary)
		except AttributeError:
			return False

	@staticmethod
	def _try_to_get_selected_mediator(request, voting):
		try:
			return request.user.participant.get(voting=voting).mediator.username
		except:
			return None

	@staticmethod
	def _get_mediators_with_msg_ma_number(voting):
		mediators_with_msg_ma_number = len(voting.participant_set.filter(msg_ma__isnull=False))
		return mediators_with_msg_ma_number


class VotingMessagesView(LoginRequiredMixin, TemplateView):

	template_name = 'votings/voting_messages.html'

	def get(self, request, v_id, *args, **kwargs):

		voting = Voting.objects.get(v_id=v_id)
		mediators = voting.participant_set.filter(is_mediator=True)

		return render(request, self.template_name, {'voting': voting, 'mediators': mediators})

	def post(self, request, v_id, *args, **kwargs):

		voting = Voting.objects.get(v_id=v_id)
		mediators = voting.participant_set.filter(is_mediator=True)
		response = self._process_pressed_buttons(request, voting)
		if response:
			return response

		return render(request, self.template_name, {'voting': voting, 'mediators': mediators})

	def _process_pressed_buttons(self, request, voting):

		if 'download_msg_mw_file' in request.POST:
			username = request.POST['download_msg_mw_file']
			mediator = get_user_model().objects.get(username=username).participant.get(voting=voting)
			return self._get_msg_mw_file_response(mediator, voting)

		if 'download_msg_ma_file' in request.POST:
			username = request.POST['download_msg_ma_file']
			mediator = get_user_model().objects.get(username=username).participant.get(voting=voting)
			return self._get_msg_ma_file_response(mediator, voting)

		if 'download_msg_voting_summary_file' in request.POST:
			return self._get_msg_voting_summary_file_response(voting)

	@staticmethod
	def _get_msg_mw_file_response(mediator, voting):
		msg_mw = deserialize_from_string(mediator.msg_mw)
		file_like_object = get_file_like_object(msg_mw=msg_mw)
		m_sign_pk = mediator.user.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_mw__{voting.v_id[:SUFFIX_LENGTH]}_{m_sign_pk.hex()[:SUFFIX_LENGTH]}_{bytes(8).hex()}')

	@staticmethod
	def _get_msg_ma_file_response(mediator, voting):
		msg_ma = deserialize_from_string(mediator.msg_ma)
		file_like_object = get_file_like_object(msg_ma=msg_ma)
		m_sign_pk = mediator.user.profile.sign_pk
		a_sign_pk = voting.author.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_ma__{voting.v_id[:SUFFIX_LENGTH]}_{m_sign_pk.hex()[:SUFFIX_LENGTH]}_{a_sign_pk.hex()[:SUFFIX_LENGTH]}')

	@staticmethod
	def _get_msg_voting_summary_file_response(voting):
		msg_voting_summary = deserialize_from_string(voting.msg_voting_summary)
		file_like_object = get_file_like_object(msg_voting_summary=msg_voting_summary)
		a_sign_pk = voting.author.profile.sign_pk
		return FileResponse(file_like_object, as_attachment=False, filename=f'msg_voting_summary__{voting.v_id[:SUFFIX_LENGTH]}_{a_sign_pk.hex()[:SUFFIX_LENGTH]}_{bytes(8).hex()}')


class ProgramView(TemplateView):

	template_name = 'votings/program.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name)


class VotingManualView(LoginRequiredMixin, TemplateView):

	template_name = 'votings/voting_manual.html'

	def get(self, request, *args, **kwargs):
		return render(request, self.template_name)


def page_not_found(request, exception):
	return HttpResponseNotFound('<h1>Страница не найдена</h1>')

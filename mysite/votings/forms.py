from django import forms
from .models import *
from project_package.message import *
from project_package.serialization import *
from project_package.ciphertext import Ciphertext


__all__ = [
	'UploadVotingFileForm',
	'UploadMsgEMFileForm',
	'UploadMsgMWFileForm',
	'UploadMsgMAFileForm',
	'UploadMsgVotingSummaryFileForm'
]


class UploadVotingFileForm(forms.Form):
	file = forms.FileField(label='Загрузить файл голосования "voting__*"')

	def save_voting(self, request):
		if self.is_valid():
			uploaded_voting = self._get_voting_object()
			if self._voting_is_allowed_to_create(request, uploaded_voting):
				voting = self._create_voting_in_db(request, uploaded_voting)
				return voting

	def _get_voting_object(self):
		voting_file = self.cleaned_data['file']
		uploaded_voting = read_file_object(voting_file)['voting']
		return uploaded_voting

	@staticmethod
	def _voting_is_allowed_to_create(request, uploaded_voting):
		a_sign_pk = request.user.profile.sign_pk
		a_kem_pk = request.user.profile.kem_pk
		voting_does_not_exists = not Voting.objects.filter(v_id=uploaded_voting.get_v_id().hex()).exists()
		voting_keys_and_author_keys_match = (a_sign_pk, a_kem_pk) == (uploaded_voting.get_keys()['a_sign_pk'], uploaded_voting.get_keys()['a_kem_pk'])
		return voting_does_not_exists and voting_keys_and_author_keys_match

	@staticmethod
	def _create_voting_in_db(request, uploaded_voting):
		voting = Voting(author=request.user, v_id=uploaded_voting.get_v_id().hex(), voting_object=serialize_to_string(uploaded_voting))
		voting.save()
		voting_data = uploaded_voting.get_data()
		question, description, options = voting_data['question'], voting_data['description'], voting_data['options']
		Question.objects.create(voting=voting, text=question)
		Description.objects.create(voting=voting, text=description)
		for index, option in enumerate(options):
			Option.objects.create(option_id=index, voting=voting, text=option)
		return voting


class UploadMsgEMFileForm(forms.Form):

	msg_em_file = forms.FileField(label='Загрузить файл "msg_em__*"')

	def save_file(self, v_id, participant):
		if self.is_valid():
			msg_em_file = self.cleaned_data['msg_em_file']
			msg_em = read_file_object(msg_em_file)['msg_em']
			v_id = bytes.fromhex(v_id)
			e_sign_pk = participant.user.profile.sign_pk
			if msg_em.check(v_id, e_sign_pk):
				msg_em_data = msg_em.get_data()
				rfp = msg_em_data['rfp']
				e_emek_e_eaek_b = msg_em_data['e_emek_e_eaek_b']
				participant.rfp = serialize_to_string(rfp)
				participant.e_emek_e_eaek_b = serialize_to_string(e_emek_e_eaek_b)
				participant.save()


class UploadMsgMWFileForm(forms.Form):

	msg_mw_file = forms.FileField(label='Загрузить файл "msg_mw__*"')

	def save_file(self, participant):
		if self.is_valid():
			msg_mw_file = self.cleaned_data['msg_mw_file']
			msg_mw = read_file_object(msg_mw_file)['msg_mw']
			m_sign_pk = participant.user.profile.sign_pk
			if msg_mw.check(m_sign_pk):
				participant.msg_mw = serialize_to_string(msg_mw)
				participant.save()


class UploadMsgMAFileForm(forms.Form):

	msg_ma_file = forms.FileField(label='Загрузить файл "msg_ma__*"')

	def save_file(self, voting, participant):
		if self.is_valid():
			msg_ma_file = self.cleaned_data['msg_ma_file']
			msg_ma = read_file_object(msg_ma_file)['msg_ma']
			voting_object = deserialize_from_string(voting.voting_object)
			m_sign_pk = participant.user.profile.sign_pk
			if msg_ma.check(voting_object, m_sign_pk):
				participant.msg_ma = serialize_to_string(msg_ma)
				participant.save()


class UploadMsgVotingSummaryFileForm(forms.Form):

	msg_voting_summary_file = forms.FileField(label='Загрузить файл с результатами голосования "msg_voting_summary__*"')

	def save_file(self, voting):
		if self.is_valid():
			voting_object = deserialize_from_string(voting.voting_object)
			v_id = voting_object.get_v_id()
			d_m_pk = voting_object.get_keys()['d_m_pk']
			a_sign_pk = voting.author.profile.sign_pk
			a_kem_pk = voting.author.profile.kem_pk
			msg_voting_summary_file = self.cleaned_data['msg_voting_summary_file']
			msg_voting_summary = read_file_object(msg_voting_summary_file)['msg_voting_summary']
			if msg_voting_summary.check(v_id, d_m_pk, a_sign_pk, a_kem_pk):
				self._count_votes_and_save_result_in_db(voting, msg_voting_summary)

	@staticmethod
	def _count_votes_and_save_result_in_db(voting, msg_voting_summary):
		voting.msg_voting_summary = serialize_to_string(msg_voting_summary)
		voting.save()
		votes = msg_voting_summary.count_votes()
		options = voting.option_set.all()
		for option in options:
			try:
				option.counter = votes[option.option_id]
				option.save()
			except:
				continue

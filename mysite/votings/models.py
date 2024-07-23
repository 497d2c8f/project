from django.db import models
from django.contrib.auth import get_user_model
from project_package.voting_protocol import *
from project_package.voting_protocol import Voting as VotingClass
from project_package.serialization import *


__all__ = [
	'Voting',
	'Question',
	'Description',
	'Option',
	'Participant'
]


class Voting(models.Model):

	created = models.DateTimeField(auto_now_add=True)
	author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, null=True, default=None)
	v_id = models.CharField(max_length=32, null=True, default='')
	registration = models.BooleanField(default=False)
	voting_object = models.BinaryField(null=True, default=None)
	msg_voting_summary = models.BinaryField(null=True, default=None)

	def __str__(self):
		return f'pk={self.pk}, question={self.question.text[:32]}'

	def get_voting_data(self):
		options = [{'option_id': option.option_id, 'text': option.text, 'counter': option.counter} for option in self.option_set.all()]
		participants = [participant.user.username for participant in self.participant_set.all()]
		voted_participants_number = len(self.participant_set.filter(rfp__isnull=False, e_emek_e_eaek_b__isnull=False))
		electors = [participant.user.username for participant in self.participant_set.all() if participant.mediator]
		mediators = {participant.user.username: len(participant.user.mediator.filter(voting=self)) for participant in self.participant_set.filter(is_mediator=True)}
		result = {}
		for option in self.option_set.all():
			option_id = option.option_id
			result[option_id] = option.counter

		voting_data = {
			'author': self.author.username,
			'v_id': self.v_id,
			'registration': self.registration,
			'question': self.question.text,
			'description': self.description.text,
			'options': options,
			'participants': participants,
			'voted_participants_number': voted_participants_number,
			'mediators': mediators,
			'electors': electors,
			'result': result
		}
		return voting_data

	def update_voting_object(self):
		d_m_pk = {participant.user.profile.sign_pk: participant.user.profile.kem_pk for participant in self.participant_set.filter(is_mediator=True)}
		v = deserialize_from_string(self.voting_object)
		v.set_d_m_pk(d_m_pk)
		self.voting_object = serialize_to_string(v)
		self.save()

class Question(models.Model):

	voting = models.OneToOneField('Voting', on_delete=models.CASCADE, null=True)
	text = models.CharField(max_length=1024)

	def __str__(self):
		return self.text

class Description(models.Model):

	voting = models.OneToOneField('Voting', on_delete=models.CASCADE, null=True)
	text = models.CharField(max_length=1024)

	def __str__(self):
		return self.text

class Option(models.Model):

	voting = models.ForeignKey('Voting', on_delete=models.CASCADE, null=True)
	option_id = models.IntegerField(default=0)
	text = models.CharField(max_length=1024)
	counter = models.IntegerField(default=0)

	def __str__(self):
		return f'{self.text}, {self.counter}'




class Participant(models.Model):

	user = models.ForeignKey(get_user_model(), related_name='participant', on_delete=models.CASCADE, null=True, default=None)
	voting = models.ForeignKey(Voting, on_delete=models.CASCADE, null=True, default=None)
	mediator = models.ForeignKey(get_user_model(), related_name='mediator', on_delete=models.SET_NULL, null=True, default=None)
	is_mediator = models.BooleanField(default=False)
	rfp = models.BinaryField(null=True, default=None)
	e_emek_e_eaek_b = models.BinaryField(null=True, default=None)
	msg_mw = models.BinaryField(null=True, default=None)
	msg_ma = models.BinaryField(null=True, default=None)

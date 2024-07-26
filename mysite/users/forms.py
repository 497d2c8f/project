from django import forms


__all__ = [
	'UpdateContactsForm'
]


class UpdateContactsForm(forms.Form):

	contacts = forms.CharField(max_length=1024, widget=forms.Textarea(attrs={"cols": "20", "rows": "1"}))

	def save_contacts(self, request):
		if self.is_valid():
			profile = request.user.profile
			profile.contacts = self.cleaned_data['contacts']
			profile.save()
		return self

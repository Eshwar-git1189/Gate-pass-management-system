from django import forms
from django.utils import timezone
from .models import Gatepass

class GatepassRequestForm(forms.ModelForm):
    class Meta:
        model = Gatepass
        fields = ['purpose', 'destination', 'from_time', 'to_time']
        widgets = {
            'from_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}, 
                format='%Y-%m-%dT%H:%M'
            ),
            'to_time': forms.DateTimeInput(
                attrs={'type': 'datetime-local'},
                format='%Y-%m-%dT%H:%M'
            ),
        }

    def clean(self):
        cleaned_data = super().clean()
        from_time = cleaned_data.get('from_time')
        to_time = cleaned_data.get('to_time')

        if from_time and to_time:
            # Ensure from_time is in the future
            if from_time < timezone.now():
                self.add_error('from_time', 'From time must be in the future')

            # Ensure to_time is after from_time
            if to_time <= from_time:
                self.add_error('to_time', 'To time must be after from time')

            # Maximum duration check (e.g., 24 hours)
            max_duration = timezone.timedelta(hours=24)
            if to_time - from_time > max_duration:
                self.add_error('to_time', 'Maximum gatepass duration is 24 hours')

        return cleaned_data
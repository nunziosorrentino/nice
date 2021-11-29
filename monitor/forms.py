from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
import datetime #for checking renewal date range.

class LabelGlitchInstanceForm(forms.Form):
    new_glitch_class_code = forms.CharField(max_length=8, help_text="Enter the glitch name",required=False)
    new_notes = forms.CharField(max_length=500, help_text="Enter additional notes on the glitch",required=False)
    new_labeler_username = forms.CharField(max_length=20, help_text="Enter the labeler username",required=False)
    new_glitch_class_name = forms.CharField(max_length=20, help_text="Enter the glitch class",required=False)

    #back to the selection
    tmin_gps = forms.FloatField(label="tmin_gps")
    tmax_gps = forms.FloatField(label="tmax_gps")
    fmin = forms.FloatField(label="fmin")
    fmax = forms.FloatField(label="fmax")
    snrmin = forms.FloatField(label="snrmin")
    snrmax = forms.FloatField(label="snrmax")


    #def clean_new_glitch_class_code(self):
    #    data = self.cleaned_data['new_glitch_class_code']

    #    #validate

    #    return data

    def clean_tmin_gps(self):
        data = self.cleaned_data["tmin_gps"]

        return data

    def clean_tmax_gps(self):
        data = self.cleaned_data["tmax_gps"]

        return data

    def clean_fmin(self):
        data = self.cleaned_data["fmin"]

        return data

    def clean_fmax(self):
        data = self.cleaned_data["fmax"]

        return data

    def clean_snrmin(self):
        data = self.cleaned_data["snrmin"]

        return data

    def clean_snrmax(self):
        data = self.cleaned_data["snrmax"]

        return data

    def clean_new_notes(self):
        data = self.cleaned_data['new_notes']
        #    #validate

        return data

    def clean_new_glitch_class_name(self):
        data = self.cleaned_data["new_glitch_class_name"]
        return data

    def clean_new_labeler_username(self):
        data = self.cleaned_data["new_labeler_username"]
        return data



    #renewal_date = forms.DateField(help_text="Enter a date between now and 4 weeks (default 3).")


    """
    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        #Check date is not in past.
        if data < datetime.date.today():
            raise ValidationError(_('Invalid date - renewal in past'))

        #Check date is in range librarian allowed to change (+4 weeks).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(_('Invalid date - renewal more than 4 weeks ahead'))

        # Remember to always return the cleaned data.
        return data
    """

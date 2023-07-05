from django import forms
 
class VoiceFileForm(forms.Form):
    voicefile = forms.FileField(
        label = 'Select a file',
        help_text = 'max. 42 megabytes'
        )
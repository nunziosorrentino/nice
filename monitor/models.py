from django.db import models

# Create your models here.


import uuid # Required for unique book instances
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


def validate_freq(value):
    if value <0 :
        raise ValidationError(
            _('%(value)s is not a a valid umber (enter positive only)'),
            params={'value': value},
        )

###########################
# Channel of the glitch
###########################
class Channel(models.Model):
    """
    Model representing a glitch type (e.g. Gauss, etc).
    """
    name = models.CharField(max_length=40, help_text="Enter the channel name")
    detector = models.ForeignKey('Detector', on_delete=models.CASCADE)
    description = models.CharField(max_length=200, help_text="Enter the description of the channel")

    def __str__(self):
        """
        String for representing the Model object
        """
        return '%s' % (self.id)

###########################
# Interferometer
###########################
class Detector(models.Model):
    """
    Model representing a detector
    """

    code = models.CharField("code",max_length=2, help_text="Enter the detector code (V1,L1,H1)")
    name = models.CharField("Name", max_length=30, help_text="Enter the full name of the detector")
    latitude = models.FloatField("Latitude", help_text="Latitude of the detector")
    longitude = models.FloatField("Longitude", help_text="Longitude of the detector")
    description = models.CharField(max_length=200, help_text="Enter the description of the detector")

    def __str__(self):
        """
        String for representing the object
        """
        return self.code


class GlitchClass(models.Model):
    """
    Model representing a glitch class (e.g. Gauss, etc).
    """

    #id = models.IntegerField(primary_key=True)
    code = models.CharField(max_length=8, help_text="Enter the glitch name")
    name = models.CharField(max_length=20, help_text="Enter the glitch name")
    description = models.CharField(max_length=200, help_text="Enter the glitch description")

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.name


class GlitchInstance(models.Model):
    """
    #Model representing a specific glitch
    """

    #id = models.UUIDField(primary_key=True, default=uuid.uuid4, help_text="Unique ID for this particular glitch")

    glitch_class = models.ForeignKey('GlitchClass', on_delete=models.CASCADE, null=True, blank=True)
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE)
    glitch_pipeline = models.ForeignKey('Pipeline', on_delete=models.CASCADE)

    peak_time_gps = models.FloatField("GPS Peak Time ", help_text="Glitch frequency")
    duration = models.FloatField("Duration ", help_text="Glitch duration (s.)")
    peak_frequency = models.FloatField("Peak Frequency ", help_text="Glitch frequency")
    bandwidth = models.FloatField("Bandwidth ", help_text="Glitch bandwidth")
    snr = models.FloatField("SNR",help_text="Glitch frequency")

    notes = models.CharField(max_length=500, help_text="Enter additional notes on the glitch")
    #output_dir = models.ForeignKey('OutputDirectory', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return "%s" % self.id

class Pipeline(models.Model):
    """
    Model representing a search or classification pipeline
    """

    #pipeline_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=20, help_text="Enter the pipeline name")
    pipeline_type = models.CharField(max_length=20, help_text="Enter the pipeline type")
    out_directory = models.CharField(max_length=300, help_text="Enter the output directory")
    description = models.CharField(max_length=200, help_text="Enter the pipeline description")
    setup_command = models.CharField(max_length=30, help_text="Enter the output directory")
    list_command = models.CharField(max_length=30, help_text="Enter the output directory")
    run_command = models.CharField(max_length=30, help_text="Enter the run command")

    def __str__(self):
        """
        String for representing the Model object (in Admin site etc.)
        """
        return self.name

class OutputDirectory(models.Model):
    """
    Model representing the list of out directories
    """

    name = models.CharField(max_length=6, help_text="Enter the pipeline name")

from django.db import models
from time import strftime

class Location(models.Model):
	""" Name and location from which the image files are read (i.e. DVD name) """
	# Name of media
	name = models.CharField(max_length=100)
	# Type of media (R - readonly, H - harddisk)
	type = models.CharField(max_length=1)

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ['name']

class Tag(models.Model):
	""" A tag description """
	# Name of the tag
	name = models.CharField(max_length=200)
	# Description of the tag
	description = models.CharField(max_length=400)

	def __unicode__(self):
		return self.name

	class Meta:
		ordering = ['name']

class Media(models.Model):
	""" Info about the image or movie """
	# Original name of file
	name = models.CharField(max_length=200)
	# Original folder of file
	path = models.CharField(max_length=500)
	# Date
	date = models.DateField()
	# Date is separated in fields for easier search
	year = models.IntegerField()
	month = models.IntegerField()
	day = models.IntegerField()
	# Info (from EXIF or other sources)
	info = models.CharField(max_length=1000)

	# Location from which the file was read
	location = models.ForeignKey(Location)
	# Assigned tags
	tags = models.ManyToManyField(Tag)

	def __unicode__(self):
		return '%s (%s)' % (self.name, strftime('%Y.%m.%d', self.date))

	class Meta:
		ordering = ['date', 'name']

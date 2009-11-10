from datetime import datetime
from django.conf import settings
from qphotos.main.models import *
import Image, os
import EXIF

EXTENSIONS = ('.jpg')
WANTED_EXIF = (
	('EXIF ExposureTime',	'S:%s, '),
	('EXIF FNumber',		'F/%s, '),
	('EXIF FocalLength',	'Foc: %s<br/>'),
	('EXIF WhiteBalance',	'White: %s, '),
	('EXIF Flash',			'Flash: %s, '),
	('EXIF ExposureMode',	'ExpMod: %s<br/>'),
	('Image Orientation',	'Orient: %s'),
)

def check_extension(fname):
	""" Check if the extension of the filename is accepted for import """
	ext = os.path.splitext(fname)[-1].lower()
	return ext and ext in EXTENSIONS

def get_location(path):
	""" Get the location object from a path """
	# not implemented for now
	locs = Location.objects.filter(type='H')
	if not locs:
		loc = Location()
		loc.name = 'HardDisk'
		loc.type = 'H'
		loc.save()
		return loc
	else:
		return locs[0]

def get_thumb_info(fname):
	""" Determine the location of a thumbfile.
	Returns the thumbfile name (thumbs are kept in a folder with
	date '/data/2009/10/28/...'), EXIF info, photo date.

	First EXIF info is used to check for a date, then a parent folder
	with date in it, then the file creation date (which won't be too 
	accurate) """

	def fix_exif_val(val):
		""" Make the arithmetic to display a correct number """
		if not '/' in val:
			return val
		vals = map(float, val.split('/'))
		if vals[0] > vals[1]:
			return '%.1f' % (vals[0]/vals[1])
		else:
			return val

	dir = None
	exif_info = []

	# Check in EXIF
	with open(fname, 'rb') as f:
		tags = EXIF.process_file(f, details=False)
		for k, p in WANTED_EXIF:
			if k in tags:
				exif_info.append(p % fix_exif_val(tags[k].printable))
		if 'EXIF DateTimeOriginal' in tags:
			# Date format is 2008:06:01 14:57:43
			parts = tags['EXIF DateTimeOriginal'].values.replace(' ', ':').split(':')
			dir = os.sep.join(parts[:3])
			pdate = datetime(*map(int, parts))
	
	if not dir:
		# Check parent folder
		pass

	if not dir:
		# Check file creation date (ze lamest of them all)
		dir = '2000/01/01'
		pdate = datetime(2000, 1, 1, 0, 0, 0)

	return (os.path.join(dir, os.path.basename(fname)), ''.join(exif_info), pdate)

def create_thumbnail(fname):
	print fname
	size = settings.THUMB_SIZE
	img = Image.open(fname)
	img.thumbnail(size, Image.ANTIALIAS)
	#bkg = Image.new('RGBA', size, (0, 0, 0, 0))
	#bkg.paste(img, ((size[0]-img.size[0])/2, (size[1]-img.size[1])/2))
	bkg = img

	# *** Save the thumb
	thumbfile, thumbinfo, pdate = get_thumb_info(fname)
	thumbfile = os.path.join(settings.DATA_DIR, thumbfile)

	# Create the dir if not already there
	dir = os.path.dirname(thumbfile)
	if not os.path.isdir(dir):
		os.makedirs(dir)

	bkg.save(thumbfile)

	# *** Save in DB only if not already there
	if not Media.objects.filter(path=fname):
		m = Media()
		m.name = os.path.basename(fname)
		m.path = fname
		m.date = pdate
		m.year = pdate.year
		m.month = pdate.month
		m.day = pdate.day
		m.thumb_url = os.path.join('data', '%04d' % m.year, '%02d' % m.month, '%02d' % m.day, m.name)
		m.info = thumbinfo
		m.location = get_location(fname)
		m.save()
	else:
		thumbinfo = 'Already in DB'

	# Return some info
	return '<b>%s - %s</b><br/>%s' % (fname, thumbfile, thumbinfo)

def import_location(path):
	""" This is actually an iterator that returns info about the imported files """
	yield 'Adding '+path
	# Go recursively and find all image files
	for root, dirs, files in os.walk(path):
		for f in files:
			# Skip files with unwanted extension
			if not check_extension(f):
				continue

			# Import the file
			file = os.path.join(root, f)
			yield create_thumbnail(file)

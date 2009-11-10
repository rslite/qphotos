from django.conf import settings
from django.db.models import Count
from qphotos.main.models import Media, Location, Tag
import Image, os

def tag_media(sel, tags):
	"""
	Tag the provided media with the provided tags
	"""
	# Get tags as objects
	htags = {}
	for stag in tags:
		print 'Tag:', stag
		otag = Tag.objects.filter(name=stag)
		if not otag:
			otag = Tag(name=stag)
			otag.save()
		else:
			otag = otag[0]
		htags[stag] = otag

	# Check the tags for each object
	qs = Media.objects.filter(pk__in=sel)
	for media in qs:
		print 'Media:', media.name
		dirty = False
		for tag in htags.values():
			if not tag in media.tags.all():
				media.tags.add(tag)
				dirty = True
		if dirty:
			print '...saved'
			media.save()

def rotate_thumbs(queryset, direction):
	"""
	Rotate the thumbs in the provided direction
	"""
	for media in queryset:
		path = os.path.join(settings.DATA_DIR, '%04d' % media.year,
				'%02d' % media.month, '%02d' % media.day, media.name)
		print 'Rotate', path
		im = Image.open(path)
		im = im.transpose(Image.ROTATE_90 if direction == 'rccw' else Image.ROTATE_270)
		im.save(path)

def get_session_param(req, name, default=None):
	"""
	Get a value from GET and if not found from session.
	If not found in session returns the default value
	"""
	sname = 'q_' + name
	try:
		val = req.GET[name]
		req.session[sname] = val
	except:
		if sname in req.session:
			val = req.session[sname]
		else:
			val = default
	return val

def del_session_param(req, name, default=None):
	"""
	Delete a parameter from session
	Returns the default value passed to assign default on delete.
	"""
	sname = 'q_' + name
	if sname in req.session:
		del req.session[sname]
	return default

def get_timeline(queryset):
	"""
	Return a list of date parts (year, month, day) with their counts form the
	photos selected in the queryset.
	The list item is a tuple with the date part (pos 0) and the count (pos 1).

	Also on the second position returns a timeline that can be used
	to go to the previous level
	"""
	# Try by year
	res = queryset.values('year').annotate(Count('year')).order_by()
	back = ['All',]
	if len(res) > 1:
		res = [(k['year'], k['year__count']) for k in res]
		return res, back

	# then by month
	year = res[0]['year']
	res = queryset.values('month').annotate(Count('month')).order_by()
	back.append('%04d' % (year))
	if not res: return None
	if len(res) > 1:
		res = [('%04d.%02d' % (year, k['month']), k['month__count']) for k in res]
		return res, back

	# then by day
	month = res[0]['month']
	res = queryset.values('day').annotate(Count('day')).order_by()
	back.append('%04d.%02d' % (year, month))
	res = [('%04d.%02d.%02d' % (year, month, k['day']), k['day__count']) for k in res]
	return res, back


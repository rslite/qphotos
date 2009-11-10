from qphotos.main.models import Media, Location, Tag

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

def get_session_param(req, name, default=None):
	"""
	Get a value from GET and if not found from session.
	If not found in session returns the default value
	"""
	try:
		val = req.GET[name]
		req.session[name] = val
	except:
		if name in req.session:
			val = req.session[name]
		else:
			val = default
	return val

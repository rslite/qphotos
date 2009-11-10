from django.core.paginator import Paginator
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import Context, loader
from qphotos.main.models import Media, Location, Tag
from qphotos.main.qimport import import_location
from qphotos.main.utils import *
import Image, os

def index(req):
	return render_to_response('main/index.htm')

def qimport(req):
	""" Import of new media """

	def import_iter():
		""" Used to return output as it is generated """
		# First return the template
		t = loader.get_template('main/qimport.htm')
		c = Context()
		yield t.render(c)
		# Now process the files
		if req.method == 'POST':
			location = req.POST['location']
			if location:
				for finfo in import_location(location):
					yield finfo+"<br/>"

	return HttpResponse(import_iter())

def browse(req):
	"""
	Browse the photos (with filtering if needed)
	"""
	# Get a tag for filtering
	ftag = get_session_param(req, 'tag')
	# Get the page number
	pagenr = get_session_param(req, 'p', 1)
	# Get the timeline
	ftl = get_session_param(req, 'tl')

	print 'ftag:', ftag
	print 'pagenr:', pagenr
	print 'ftl:', ftl

	# If the 'all' parameter is sent then filtering is removed
	if 'all' in req.GET :
		print 'RESET'
		ftag = del_session_param(req, 'tag')
		pagenr = del_session_param(req, 'p', 1)
		ftl = del_session_param(req, 'tl')

	# Set the queryset
	if ftag:
		qs = Media.objects.filter(tags__name=ftag)
	else:
		qs = Media.objects.all()

	# Add the timeline filtering
	if ftl and ftl.lower() != 'all':
		parts = map(int, ftl.split('.'))
		if len(parts) > 0: qs = qs.filter(year=parts[0])
		if len(parts) > 1: qs = qs.filter(month=parts[1])
		if len(parts) > 2: qs = qs.filter(day=parts[2])

	# Get the total number of images from DB
	total_count = qs.aggregate(Count('name'))['name__count']

	# Paginate here and get the correct objects
	# TODO Get these from settings
	COLS = 4
	ROWS = 3
	# TODO Implement ftaging here
	paginator = Paginator(qs, COLS*ROWS)
	try:
		page = paginator.page(pagenr)
	except:
		page = paginator.page(1)
		pagenr = 1
	data = [page.object_list[i*COLS:i*COLS+COLS] for i in xrange(ROWS)]

	# Get tags
	alltags = Tag.objects.all()

	# Get the timeline for the current selection
	timeline, back_timeline = get_timeline(qs)

	# Get the last tags
	last_tags = req.session.get('last_tags', [])

	# The form will be redirected to command
	form_action = "/command"

	return render_to_response('main/browse.htm', locals())

def command(req):
	"""
	Execute commands passed from the server
	"""

	def getids(list):
		"""
		The ids are in the form ',dv_NNN,dv_NNN'
		This function returns a list of integer ids from that.
		"""
		list = list.lstrip(',').split(',')
		list = map(lambda x: int(x[3:]), list)
		return list

	cmd = req.POST['cmd']
	sel = getids(req.POST['sel'])
	if cmd == 'del':
		qs = Media.objects.filter(pk__in = sel)
		qs.delete()
	elif cmd == 'tag':
		tags = req.POST['tags']
		if tags:
			# Save the last entered tag
			try:
				last_tags = req.session['last_tags']
			except:
				last_tags = req.session['last_tags'] = []
			# Remove if already in list (to keep the MRU at end)
			if tags in last_tags:
				last_tags.remove(tags)
			# Add the tag and save back in session
			last_tags.append(tags)
			req.session['last_tags'] = last_tags
			# Apply the tag
			tag_media(sel, tags.split(' '))
	elif cmd == 'rcw' or cmd == 'rccw':
		qs = Media.objects.filter(pk__in = sel)
		rotate_thumbs(qs, cmd)
	else:
		return HttpRequestNotFound()

	# Redirect to the browsing page (for now)
	return HttpResponseRedirect('/browse')

def slide(req):
	try:
		photo = Media.objects.filter(id=req.GET['id']).get()
	except:
		return HttpRequestNotFound()

	return render_to_response('main/slide.htm', locals())

def getfile(req):
	"""
	Serve an image as an origingal or resized
	id - the id of the Media object
	s (optional) - the size of the object (S, M, L).
		If missing the original size is returned
	"""

	try:
		fobj = Media.objects.filter(id=req.GET['id']).get()
	except:
		return HttpRequestNotFound()

	# Check if 's'ize parameter was passed
	psize = req.GET['s']
	if not psize:
		wrapper = FileWrapper(file(fobj.path, 'rb'))
		response = HttpResponse(wrapper, content_type='image/jpeg')
	else:
		# Parameter should be S, M, L (for now just hardcode it)
		size = (800, 600)
		im = Image.open(fobj.path)
		im.thumbnail(size, Image.ANTIALIAS)
		# Check the orientation
		if fobj.rotation == 1:
			im = im.transpose(Image.ROTATE_90)
		elif fobj.rotation == 3:
			im = im.transpose(Image.ROTATE_270)
		response = HttpResponse(content_type='image/jpeg')
		im.save(response, 'JPEG')
	response['Content-Length'] = os.path.getsize(fobj.path)
	return response

def deleteall(req):
	"""
	Delete all media objects from the database and all thumbnails
	"""

	Media.objects.all().delete()
	import shutil
	shutil.rmtree(settings.DATA_DIR)
	return HttpResponseRedirect('/')

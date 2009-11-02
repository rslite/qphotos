from django.core.paginator import Paginator
from django.core.servers.basehttp import FileWrapper
from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import Context, loader
from qphotos.main.models import Media, Location, Tag
from qphotos.main.qimport import import_location
from qphotos.main.utils import tag_media
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
	# Get the page number
	try:
		pagenr = int(req.GET['p'])
	except:
		pagenr = 1
	# Get the total number of images from DB
	total_count = Media.objects.aggregate(Count('name'))['name__count']
	# Paginate here and get the correct objects
	# TODO Get these from settings
	COLS = 4
	ROWS = 3
	# TODO Implement filtering here
	paginator = Paginator(Media.objects.all(), COLS*ROWS)
	try:
		page = paginator.page(pagenr)
	except (EmptyPage, InvalidPage):
		page = paginator.page(1)
		pagenr = 1
	data = [page.object_list[i*COLS:i*COLS+COLS] for i in xrange(ROWS)]

	# Get tags
	alltags = Tag.objects.all()

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
			tag_media(sel, tags.split(' '))
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

import argparse
import os
import os.path
import shutil
import hashlib
import exifread
from dateutil.parser import parse
from datetime import datetime


FILE_TYPES_TO_PROCESS = ('.jpg', '.jpeg', '.mov', '.avi', '.mp4', '.cr2', '.3gp', '.wmv', '.mpg', '.m4v', '.png')
FILES_TO_DELETE = ('.picasa.ini', 'picasa.ini', '.ds_store', '._.ds_store', 'thumbs.db', 'zbthumbnail.info')
DATETIME_EXIF_TAG = 'Image DateTime'
DATETIME_EXIF_TAG_FORMAT = '%Y:%m:%d %H:%M:%S'
FILE_DUP_MAX_RETRIES = 50

def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def get_files(path):
	for i in sorted(os.listdir(path)):
		p = os.path.join(path, i)
		if os.path.isdir(p):
			for f in get_files(p):
				yield f
		else:
			yield p

def remove_empty_dirs(path):
	for i in sorted(os.listdir(path)):
		p = os.path.join(path, i)
		if os.path.isdir(p):
			remove_empty_dirs(p)
			if not os.listdir(p):
				print("removing empty dir {0}".format(p))
				os.rmdir(p)

def get_file_date(path):
	f = open(path, 'rb')
	tags = exifread.process_file(f, details=False)
	if DATETIME_EXIF_TAG in tags:
		dt_str = str(tags[DATETIME_EXIF_TAG])
		try:
			return datetime.strptime(dt_str, DATETIME_EXIF_TAG_FORMAT)
		except ValueError as e:
			return None
		#return parse(dt_str)
	else:
		ts = os.stat(path).st_mtime
		return datetime.fromtimestamp(ts)
	return None


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Organize photo library')
	parser.add_argument('src', help='source folder')
	parser.add_argument('dest', help='destination folder')
	parser.add_argument('-c', '--copy-only', 
						action='store_true',
						help='copy files instead of moving')

	args = parser.parse_args()

	src = os.path.normpath(args.src)
	dest = os.path.normpath(args.dest)

	if not os.path.exists(src):
		print("source path {0} does not exists".format(src))
		exit(0)

	if not os.path.exists(dest):
		print("destination path {0} does not exists".format(dest))
		exit(0)

	if os.stat(src) == os.stat(dest):
		print("cannot use same path {0} as source and destination".format(src))
		exit(0)	

	for f in get_files(src):
		# print(f)
		# if f == r"d:\temp\src\craciun miami 2005\28 dec 2\PIC_0001.JPG":
		# 	import pdb;pdb.set_trace()
		_, ext = os.path.splitext(f)
		ext = ext.lower()
		if ext not in FILE_TYPES_TO_PROCESS:
			if os.path.basename(f).lower() in FILES_TO_DELETE:
				if not args.copy_only:
					print("deleting {0}".format(f))
					os.remove(f)
				continue
			else:
				if args.copy_only:
					print("skipping {0}, not a file type to copy".format(f))
				else:
					print("skipping {0}, not a file type to move".format(f))
				continue
		d = get_file_date(f)
		if not d:
			print("skipping {0}, no date found".format(f))
			continue
		# dest_folder = os.path.join(dest, 
		# 							"-".join((str(d.year), 
		# 										"{0:02}".format(d.month), 
		# 										"{0:02}".format(d.day)
		# 									))
		# 							)
		dest_folder = os.path.join(dest, 
									str(d.year), 
									"{0:02}".format(d.month), 
									"{0:02}".format(d.day)									
									)
		if not os.path.exists(dest_folder):
			os.makedirs(dest_folder)
		dest_path = os.path.join(dest_folder, os.path.split(f)[1])
		if os.path.exists(dest_path):
			if os.stat(f).st_size == os.stat(dest_path).st_size and \
				md5(f) == md5(dest_path):
				print("skipping {0}, already exists as {1} with same size and hash".format(f, dest_path))
				if not args.copy_only:
					os.remove(f)
				continue
			else:
				counter = 1
				new_path = dest_path
				while os.path.exists(new_path) and counter < FILE_DUP_MAX_RETRIES:
					new_path = ("-" + str(counter)).join(os.path.splitext(dest_path))
					counter += 1
				if counter < FILE_DUP_MAX_RETRIES:
					dest_path = new_path
				else:
					print("error: cannot copy {0}, already exists as {1}".format(f, new_path))

		if args.copy_only:
			print("copying {0} to {1}".format(f, dest_path))
			shutil.copy2(f, dest_path)
		else:
			print("moving {0} to {1}".format(f, dest_path))
			os.rename(f, dest_path)

	if not args.copy_only:
		remove_empty_dirs(src)







import os
from django.shortcuts import render
from django.http import JsonResponse
from django.conf import settings
import subprocess
import threading
from .models import FileModel


# get media file's length
def get_length(input_video):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of',
                             'default=noprint_wrappers=1:nokey=1', input_video], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    return float(result.stdout)


# get total seconds from time string
def get_secs(strtime):
    arr = strtime.split(':')
    if len(arr) == 3:
        return int(int(arr[0]) * 3600 + int(arr[1]) * 60 + float(arr[2]))
    else:
        return 0


# save uploaded file
def handle_uploaded_file(f, file_name):
    with open(file_name, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)


def background_process(cmds, fileitem):
    process = subprocess.Popen(cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    for line in process.stdout:
        if 'time=' in line:
            arr = line.split(' ')
            for item in arr:
                if 'time=' in item:
                    strTime = item.split('=')[1]
                    fileitem.status = int(get_secs(strTime) * 100 / fileitem.length + 0.5)
                    fileitem.save()
                    break
    fileitem.status = 100
    fileitem.save()

# main processing
def index(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        avformat = request.POST.get('avformat')
        startfile = request.POST.get('startfile')
        convertfrom = request.POST.get('convertfrom')
        endfile = request.POST.get('endfile')
        convertto = request.POST.get('convertto')

        fileitem = FileModel.objects.get(id=file_id)

        filename = os.path.splitext(os.path.basename(fileitem.name))[0]
        output_file = os.path.join(settings.MEDIA_ROOT, os.path.join('converted', filename + '.' + avformat))

        # save converted file path
        fileitem.converted_name = output_file
        fileitem.save()

        cmds = []
        if startfile != 'on' or endfile != 'on':
            if startfile == 'on':
                convertfrom = '00:00:00'
            starttime = get_secs(convertfrom)
            endtime = fileitem.length
            if endfile != 'on':
                endtime = get_secs(convertto)
            duration = str(endtime - starttime)
            cmds = ["ffmpeg", "-ss", convertfrom, "-t", duration, "-i", fileitem.name, "-y", output_file]
            if avformat == '3gp':
                cmds = ["ffmpeg", "-ss", convertfrom, "-t", duration, "-i", fileitem.name, '-r', '20', '-s', '352x288',
                        '-vb', '400k', '-acodec', 'aac', '-strict', 'experimental', '-ac', '1', '-ar', '8000', '-ab',
                        '24k', "-y", output_file]
        else:
            cmds = ["ffmpeg", "-i", fileitem.name, "-y", output_file]
            if avformat == '3gp':
                cmds = ["ffmpeg", "-i", fileitem.name, '-r', '20', '-s', '352x288', '-vb', '400k', '-acodec',
                        'aac', '-strict', 'experimental', '-ac', '1', '-ar', '8000', '-ab', '24k', "-y", output_file]

        processThread = threading.Thread(target=background_process, args=[cmds, fileitem])
        processThread.start()

        return JsonResponse({'success': True})
    return render(request, 'index.html')


# get uploaded file
def upload_file(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        file_name = str(file.name)
        save_dir = os.path.join(settings.MEDIA_ROOT, file_name)
        handle_uploaded_file(file, save_dir)
        file_len = get_length(save_dir)
        seconds = int(file_len % 60)
        mins = int(file_len / 60 % 60)
        hrs = int(file_len / 3600)
        str_file_len = '%02d:%02d:%02d' % (hrs, mins, seconds)

        filemodel = FileModel(name=save_dir, length=file_len, status=0)
        filemodel.save()

        return JsonResponse({'success': True, 'file_id': filemodel.id, 'length': str_file_len})
    return None


# get converting status
def get_status(request):
    if request.method == 'POST':
        file_id = request.POST.get('file_id')
        fileitem = FileModel.objects.get(id=file_id)

        out_path = ''
        if fileitem.converted_name is not None:
            out_path = os.path.join('/uploaded/converted', os.path.basename(fileitem.converted_name))
        return JsonResponse({'status': fileitem.status, 'path': out_path})
    return None


def terms(request):
    return render(request, 'terms.html')


def policy(request):
    return render(request, 'policy.html')


def features(request):
    return render(request, 'features.html')

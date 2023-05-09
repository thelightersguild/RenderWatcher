import json
import os
import subprocess
import threading

from katana_render_submitter import util

PACKAGE_DIR = '/tlg/shows/{}/tmp'.format(util.get_shot_context())


def get_rendered_frames(render_path):
    """"
    Gets the number of rendered frames, due to 3delight cloud touching the files with 0kb, we need to parse actually rendered files, assume
    greater than 0kb is running

    Args:
        render_path (str) - render_path directory

    Returns:
         valid_renders (int) - length of number of frames rendered

    """
    valid_renders = list()
    files = os.listdir(render_path)
    for file_ in files:
        full_path = f'{render_path}/{file_}'
        file_size = os.path.getsize(full_path)
        if file_size > 100:
            valid_renders.append(True)
    return len(valid_renders)


def get_render_jobs():
    jobs = {}
    # get jobs
    for job in os.listdir(PACKAGE_DIR):
        if job.endswith('.json'):
            full_path = f'{PACKAGE_DIR}/{job}'
            jobs[job] = os.path.getmtime(full_path)
    # sort into list by time
    if jobs:
        sorted_jobs = sorted(jobs.items(), key=lambda x: x[1], reverse=True)
        return sorted_jobs
    else:
        return None


def get_job_data(job_id):
    json_file = '{}/{}'.format(PACKAGE_DIR, job_id)
    f = open(json_file)
    job_data = json.load(f)
    f.close()
    return job_data


def launch_render(main_widget, tree_widget, data):
    #TODO dont need the extra arguments which arent being used
    threaded_dict = {}
    if tree_widget.topLevelItemCount() == 0:
        print ('need to load job first')
        return False
    for k, v in data.items():
        for pass_info in v:
            rndr_cmd = pass_info.get('batch_cmd')
            #frames = pass_info.get('frame_range')
            pass_name = pass_info.get('pass_name')
            # run the threads
            t = threading.Thread(target=render_thread_job, args=(main_widget, rndr_cmd, pass_name), daemon=False)
            t.start()


def render_thread_job(main_widget, rndr_cmd, pass_name):
    subprocess.run(rndr_cmd)

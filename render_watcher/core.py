import json
import os
import subprocess
import threading

from katana_render_submitter import util


PACKAGE_DIR = '/tlg/shows/{}/tmp'.format(util.get_shot_context())


#TODO, want to inspect the job, create a dictionary of this, max the threads at 4?
#e.g {job:{thread1:pass1, thread2:pass2, thread3:pass3, thread4:pass4}}

def get_render_jobs():
    jobs = [j for j in os.listdir(PACKAGE_DIR) if j.endswith('.json')]
    if jobs:
        return jobs
    else:
        return None


def get_job_data(job_id):
    json_file = '{}/{}'.format(PACKAGE_DIR, job_id)
    f = open(json_file)
    job_data = json.load(f)
    f.close()
    return job_data


def launch_render(main_widget, tree_widget, data):
    threaded_dict = {}
    if tree_widget.topLevelItemCount() == 0:
        print ('need to load job first')
        return False
    for k, v in data.items():
        for pass_info in v:
            rndr_cmd = pass_info.get('batch_cmd')
            # here we need to break this down into frame chunks
            frames = pass_info.get('frame_range')
            frame_range_split = frames.split('-')
            pass_name = pass_info.get('pass_name')
            frame_start = int(frame_range_split[0])
            frame_end = int(frame_range_split[1])
            # run the threads
            t = threading.Thread(target=render_thread_job, args=(main_widget, rndr_cmd, frame_start, frame_end, pass_name), daemon=False)
            t.start()
            #NON THREADED RENDER
            #render_thread_job(main_widget, rndr_cmd, frame_start, frame_end, pass_name)


def render_thread_job(main_widget, rndr_cmd, frame_start, frame_end, pass_name):
    subprocess.run(rndr_cmd)
    #TODO this will run slower and is more efficient, but does update the progress bars.
    # for frame in range(frame_start, frame_end):
    #     rndr_cmd[5] = '--t={}'.format(frame)
    #     subprocess.run(rndr_cmd)
    #     main_widget.update_progress(frame, pass_name)

import json
import os
import subprocess
import threading
import psutil
import time

from katana_render_submitter import util

PACKAGE_DIR = '/tlg/shows/{}/tmp'.format(util.get_shot_context())


def check_render_process_running():
    """
    checks how many renderboot processes are running

    Returns:
        num_processors (int): number of renderboot processes running
    """
    num_processors = int()
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'renderboot':
            num_processors += 1
    return num_processors


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
    if os.path.exists(render_path):
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

def split_range(frame_range, num_frames):
    """split a frame range by 2. returns tuple"""
    start, end = frame_range.split('-')
    split_frames = int(num_frames) / 2
    range1 = f'{start}-{str(int(int(start) + split_frames))}'
    range2 = f'{int(int(start) + split_frames) + 1}-{end}'
    return (range1, range2)


def process_render(render_passes, passes_data):
    """processes the render job and launches the render"""
    #render_passes = render_passes
    # if there is a - in the frame range, assume full frame renders..
    fr_range_check = passes_data[0].get('frame_range')
    if '-' in fr_range_check:
        split_job = True
    else:
        split_job = False
        thread_limit = 4
    if split_job:
        # run passes synchronous, this is to stop 3delight cloud's nsi export filling up mem/space
        while True:
            if render_passes:
                if not check_render_process_running():
                    pass_name = render_passes.pop(0)
                    # we want to get the pass data for the active rendering pass
                    for pass_data in passes_data:
                        if pass_data.get('pass_name') == pass_name:
                            cmd = pass_data.get('batch_cmd')
                            num_frames = pass_data.get('num_frames')
                            frame_range = pass_data.get('frame_range')
                            frames_split = split_range(frame_range, num_frames)
                            for range in frames_split:
                                cmd[5] = f'--t={range}'
                                batch_cmd = cmd
                                t = threading.Thread(target=render_thread_job, args=(batch_cmd,), daemon=False)
                                t.start()
                time.sleep(60)
            else:
                break
    else:
        # run passes concurrently, still need to limit this to work on 8 cores/threaded machine.
        while True:
            if render_passes:
                if check_render_process_running() < thread_limit:
                    render_pass = render_passes.pop(0)
                    pass_data = [d for d in passes_data if d.get('pass_name') == render_pass][0]
                    batch_cmd = pass_data.get('batch_cmd')
                    t = threading.Thread(target=render_thread_job, args=(batch_cmd,), daemon=False)
                    t.start()
                    # when initally starting the render, we need to wait a little bit to catch the process running
                    time.sleep(10)
                else:
                    # limit has been reached, lets pause the loop for one minute
                    time.sleep(60)
            else:
                break


def launch_render(data):
    """add doc string"""
    # need a split/full frame range condition, still want to render fml and 10s threaded (up to a certain amount)
    # split the job, we can only render 1 pass at a time, but we want to split the frame range
    render_passes = list()
    passes_data = list()
    for values in data.values():
        for pass_data in values:
            passes_data.append(pass_data)
            render_passes.append(pass_data.get('pass_name'))
    process_rnd_thread = threading.Thread(target=process_render, args=(render_passes, passes_data), daemon=False)
    process_rnd_thread.start()


def render_thread_job(rndr_cmd):
    subprocess.run(rndr_cmd)

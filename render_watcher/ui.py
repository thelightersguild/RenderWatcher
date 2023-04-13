from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QObject, QThread, pyqtSignal
import sys
import time
import datetime

from render_watcher import core

RENDER_WATCHER = object()


# TODO/NICE TO HAVES
'''
do style sheets, probably look like katana
add title for window
centre text in columns, RESIZE APPROPRIATE
'''

class Worker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    def run(self):
        rendering = True
        render_status = dict()
        tree_widget = RENDER_WATCHER.render_tree_widget
        status_data = tree_widget.status_data
        #TODO can prob do this in one line
        #everything is initially not rendering
        for pass_name in status_data.keys():
            render_status[pass_name] = True
        file_ = '/tlg/shows/axis/235/0010/tmp/log.log'
        f = open(file_, 'w')
        f.write(f'render starting: {datetime.datetime.now()}\n')
        #i = 0
        it = list(status_data.values())[0].get('widget_item')
        prog_widget = tree_widget.itemWidget(it, 5)
        f.write(f'maximum value of progress bar is {prog_widget.maximum()}\n')
        # update the status column
        job_item = tree_widget.topLevelItem(0)
        for i in range(job_item.childCount()):
            child_item = job_item.child(i)
            child_item.setText(2, 'RUNNING')
        while rendering:
            f.write(f'I am going to sleep now for 60 secs: {datetime.datetime.now()}\n')
            # we only want to check each render passes progress every 60 secs
            time.sleep(30)
            #f.write(f'waking up: {datetime.datetime.now()}\n')
            # final condition here
            for pass_name, data in status_data.items():
                f.write(f'processing pass {pass_name}: {datetime.datetime.now()}\n')
                #print ('processing pass')
                #i += 1
                #print (f'value of counter is {i}')
                #f.write(f'value of counter is {i}: {datetime.datetime.now()}\n')
                # if i == 15:
                #     f.write(f'value of counter is now 15: {datetime.datetime.now()}\n')
                #     rendering = False
                # only run check on pass if it is still rendering
                #print (f'render status is {render_status.get(pass_name)}\n')
                if render_status.get(pass_name) is True:
                    output_path = data.get('output_path')
                    widget_item = data.get('widget_item')
                    progress_widget = tree_widget.itemWidget(widget_item, 5)
                    num_frames = data.get('num_frames')
                    #TODO this is overkill and should be set initally first
                    widget_item.setText(2, 'RUNNING')
                    #subprocess.run(['touch', f'{output_path}/{random.randint(0, 5555)}.txt'])

                    current_frames = core.get_rendered_frames(output_path)
                    #print(f'current frames on disk are {current_frames} out of {num_frames}\n')
                    f.write(f'current frames on disk are {current_frames} of {num_frames}: {datetime.datetime.now()}\n')
                    #update progress bar
                    progress_widget.setValue(current_frames)
                    f.write(f'current value of progress bar is {progress_widget.value()}\n')
                    if current_frames == num_frames:
                        widget_item.setText(2, 'COMPLETE')
                        #print ('freames all now complete')
                        f.write(f'num frames now equals total frames: {datetime.datetime.now()}\n')
                        render_status[pass_name] = False
                    #check to see if all passes have finished rendering
                    if any(render_status.values()) is False:
                        f.write(f'all render statuses are complete, setting rendering to False: {datetime.datetime.now()}\n')
                        rendering = False
        f.write(f'rendering now complete, emitting finished signal: {datetime.datetime.now()}\n')
        f.close()
        #self.progress.emit(i + 1)
        self.launch_render_button.setEnabled(True)
        self.finished.emit()

class RenderWatcherTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super(RenderWatcherTree, self).__init__(parent)
        self.setColumnCount(5)
        self.setHeaderLabels(['Job id', 'RenderPass', 'Status', 'FrameRange', 'Version', 'Progress'])
        self.status_data = dict()
        # TODO open in expanded state

    def populate_tree(self, data):
        for key, values in data.items():
            job_item = QtWidgets.QTreeWidgetItem([key])
            self.insertTopLevelItems(0, [job_item])
            for pass_info in values:
                frame_range = pass_info.get('frame_range')
                version = pass_info.get('version')
                child_item = QtWidgets.QTreeWidgetItem(['', pass_info.get('pass_name'), 'WAITING', frame_range, version, ''])
                job_item.addChild(child_item)
                self.status_data[pass_info.get('pass_name')] = {
                    'widget_item': child_item,
                    'output_path': pass_info.get('output_path'),
                    'num_frames': int(pass_info.get('num_frames'))
                }
                progress_bar = QtWidgets.QProgressBar()
                progress_bar.setTextVisible(True)
                progress_bar.setMinimum(0)
                progress_bar.setMaximum(int(pass_info.get('num_frames')))
                self.setItemWidget(child_item, 5, progress_bar)

    def update_status(self):
        pass

    def update_progress(self):
        pass


class JobsTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super(JobsTree, self).__init__(parent)
        self.setColumnCount(2)
        self.setHeaderLabels(['Job Name', 'Submission Date'])

    def populate_tree(self, jobs):
        for job in jobs:
            job_item = QtWidgets.QTreeWidgetItem([job[0], time.ctime(job[1])])
            # Add the new item to the tree
            self.addTopLevelItem(job_item)


class RenderWatcher(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.selected_job = None
        self.arrange_layout()
        self.populate_render_job_widget()
        self.connect_signals()

    def arrange_layout(self):
        # self.showMaximized()
        layout_main = QtWidgets.QVBoxLayout()
        self.setLayout(layout_main)
        view_widgets_hbox = QtWidgets.QHBoxLayout()
        layout_main.addLayout(view_widgets_hbox)
        self.render_tree_widget = RenderWatcherTree()
        view_widgets_hbox.addWidget(self.render_tree_widget)
        self.jobs_tree_widget = JobsTree()
        view_widgets_hbox.addWidget(self.jobs_tree_widget)
        buttons_hbox = QtWidgets.QHBoxLayout()
        layout_main.addLayout(buttons_hbox)
        self.load_job_btn = QtWidgets.QPushButton('Load Job')
        self.launch_render_button = QtWidgets.QPushButton('Launch Render')
        buttons_hbox.addWidget(self.launch_render_button)
        buttons_hbox.addWidget(self.load_job_btn)


    def run_check_render_status_task(self):
        """"Initializes the threading work"""
        # Step 2: Create a QThread object
        self.thread = QThread()
        # Step 3: Create a worker object
        self.worker = Worker()
        # Step 4: Move worker to the thread
        self.worker.moveToThread(self.thread)
        # Step 5: Connect signals and slots
        # TODO move these to the signals connect_signals
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        # self.worker.progress.connect(self.reportProgress)
        self.launch_render_button.setEnabled(False)
        self.thread.start()

    def connect_signals(self):
        self.load_job_btn.clicked.connect(self.load_job_btn_clicked)
        self.launch_render_button.clicked.connect(self.launch_render_btn_clicked)

    def load_job_btn_clicked(self):
        curent_item = self.jobs_tree_widget.currentItem()
        if not curent_item:
            return
        id_txt = curent_item.text(0)
        self.selected_job = id_txt
        data = core.get_job_data(id_txt)
        self.render_tree_widget.populate_tree(data)

    def launch_render_btn_clicked(self):
        if self.render_tree_widget.topLevelItemCount() == 0:
            print('need to load job first')
            return False
        data = core.get_job_data(self.selected_job)
        core.launch_render(self, self.render_tree_widget, data)
        self.run_check_render_status_task()


    def populate_render_job_widget(self):
        jobs = core.get_render_jobs()
        if jobs:
            self.jobs_tree_widget.populate_tree(jobs)


def launch_render_watcher():
    global RENDER_WATCHER
    app = QtWidgets.QApplication(sys.argv)
    RENDER_WATCHER = RenderWatcher()
    RENDER_WATCHER.show()
    sys.exit(app.exec_())
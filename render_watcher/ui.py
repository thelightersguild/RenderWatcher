from PyQt5 import QtWidgets, QtCore
import sys

from render_watcher import core



#TODO/NICE TO HAVES
'''
sort by latest jobs
add latest job button
update status when rendering and completed (with colour!) 
do style sheets, probably look like katana
add title for window
centre text in columns, add
'''


class RenderWatcherTree(QtWidgets.QTreeWidget):
    def __init__(self, parent=None):
        super(RenderWatcherTree, self).__init__(parent)
        self.setColumnCount(5)
        self.setHeaderLabels(['Job id', 'RenderPass', 'Status', 'FrameRange', 'Progress'])
        # TODO open in expanded state


    def populate_tree(self, data):
        for key, values in data.items():
            job_item = QtWidgets.QTreeWidgetItem([key])
            self.insertTopLevelItems(0, [job_item])
            for pass_info in values:
                frame_range = pass_info.get('frame_range')
                child_item = QtWidgets.QTreeWidgetItem(['', pass_info.get('pass_name'), 'WAITING', frame_range, ''])
                job_item.addChild(child_item)
                progress_bar = QtWidgets.QProgressBar()
                progress_bar.setTextVisible(True)
                start_frame = int(frame_range.split('-')[0])
                end_frame = int(frame_range.split('-')[1])
                progress_bar.setMinimum(start_frame)
                progress_bar.setMaximum(end_frame)
                self.setItemWidget(child_item, 4, progress_bar)


class RenderWatcher(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.selected_job = None
        layout_main = QtWidgets.QVBoxLayout()
        self.showMaximized()
        self.setLayout(layout_main)
        view_widgets_hbox = QtWidgets.QHBoxLayout()
        layout_main.addLayout(view_widgets_hbox)
        self.tree = RenderWatcherTree()
        view_widgets_hbox.addWidget(self.tree)
        self.render_job_window = QtWidgets.QListWidget()
        view_widgets_hbox.addWidget(self.render_job_window)
        buttons_hbox = QtWidgets.QHBoxLayout()
        layout_main.addLayout(buttons_hbox)
        self.load_job_btn = QtWidgets.QPushButton('Load Job')
        self.launch_render_button = QtWidgets.QPushButton('Launch Render')
        buttons_hbox.addWidget(self.launch_render_button)
        buttons_hbox.addWidget(self.load_job_btn)
        self.populate_render_job_widget()
        self.connect_signals()

    def connect_signals(self):
        self.load_job_btn.clicked.connect(self.load_job_btn_clicked)
        self.launch_render_button.clicked.connect(self.launch_render_btn_clicked)

    def load_job_btn_clicked(self):
        curent_item = self.render_job_window.currentItem()
        if not curent_item:
            #TODO put a dialog here
            pass
        id_txt = curent_item.text()
        self.selected_job = id_txt
        data = core.get_job_data(id_txt)
        self.tree.populate_tree(data)

    def launch_render_btn_clicked(self):
        if self.tree.topLevelItemCount() == 0:
            print('need to load job first')
            return False
        data = core.get_job_data(self.selected_job)
        core.launch_render(self, self.tree, data)


    # def launch_render(self):
    #     if self.tree.topLevelItemCount() == 0:
    #         print ('need to load job first')
    #         return False
    #     print ('is this really running?')
    #     for k, v in self.render_data.items():
    #         for pass_info in v:
    #             rndr_cmd = pass_info.get('batch_cmd')
    #             # here we need to break this down into frame chunks
    #             frames = pass_info.get('frame_range')
    #             frame_range_split = frames.split('-')
    #             frame_start = int(frame_range_split[0])
    #             frame_end = int(frame_range_split[1])
    #             frame_range_count = frame_end-frame_start
    #             for frame in range(frame_start, frame_end):
    #                 rndr_cmd[5] = str(frame)
    #                 subprocess.run(rndr_cmd)
    #                 self.update_progress(frame, pass_info.get('pass_name'))

    def update_progress(self, frame_number, pass_name):
        # get widget
        #TODO revisit this if neededm current iterator method is not very efficient
        #item = self.tree.findItems(pass_name, QtCore.Qt.MatchExactly, 2)
        iterator = QtWidgets.QTreeWidgetItemIterator(
            self.tree,
            flags=QtWidgets.QTreeWidgetItemIterator.NoChildren
        )
        while iterator.value():
            item = iterator.value()
            if pass_name == item.text(1):
                progress_widget = self.tree.itemWidget(item, 4)
                progress_widget.setValue(frame_number + 1)
                break
            iterator += 1

    def populate_render_job_widget(self):
        jobs = core.get_render_jobs()
        self.render_job_window.addItems(jobs)



def launch_render_watcher(arg):
    # running from terminal
    app = QtWidgets.QApplication(arg)
    render_watcher = RenderWatcher()
    render_watcher.show()
    sys.exit(app.exec_())
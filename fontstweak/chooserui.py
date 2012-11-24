# -*- coding: utf-8 -*-
# chooserui.py
# Copyright (C) 2012 Red Hat, Inc.
#
# Authors:
#   Akira TAGOH  <tagoh@redhat.com>
#
# This library is free software: you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from util import FontsTweakUtil

class ChooserUI:

    def __init__(self, builder, model, filter_func):
        self.filter = builder.get_object('filter')
        self.filter.connect('notify::text', self.on_filter_notify_text)
        self.view = builder.get_object('treeview')
        self.selector = builder.get_object('treeview-selection')
        self.filtered_model = model.filter_new()
        self.filtered_model.set_visible_func(filter_func, self.filter)
        self.view.set_model(self.filtered_model)
        self.add = builder.get_object('button-add')

        self.filter.set_property('secondary-icon-name',
                                 FontsTweakUtil.check_symbolic(self.filter.get_property('secondary-icon-name')))

    def _set_cursor(self):
        iter = self.filtered_model.get_iter_first()
        path = self.filtered_model.get_path(iter)
        self.view.set_cursor(path, None, False)

    def on_chooser_dialog_show(self, widget):
        self.filter.grab_focus()
        self._set_cursor()

    def on_filter_activate(self, widget):
        self.add.clicked()

    def on_filter_notify_text(self, widget, param):
        text = widget.get_text()
        if len(text) == 0:
            widget.set_property('secondary-icon-name', 'edit-find-symbolic')
            widget.set_property('secondary-icon-activatable', False)
            widget.set_property('secondary-icon-sensitive', False)
        else:
            widget.set_property('secondary-icon-name', 'edit-clear-symbolic')
            widget.set_property('secondary-icon-activatable', True)
            widget.set_property('secondary-icon-sensitive', True)
        self.filtered_model.refilter()
        model = self.filtered_model.get_model()
        if self.filtered_model.iter_n_children(None) == 0:
            self.add.set_sensitive(False)
        else:
            self.add.set_sensitive(True)
            if self.selector.get_selected()[1] == None:
                self._set_cursor()

    def on_filter_icon_release(self, widget, pos, event):
        widget.set_text('')

    def on_chooser_dialog_response(self, dlg, resid):
        self.filter.set_text('')

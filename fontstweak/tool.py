# vim: set et sts=4 sw=4:
# -*- encoding: utf-8 -*-
#
# Fonts Tweak Tool
#
# Copyright (c) 2011-2012 Jian Ni <jni@redhat.com>
# Copyright (c) 2012 Red Hat, Inc.
#
#This program is free software: you can redistribute it and/or 
#modify it under the terms of the GNU Lesser General Public 
#License as published by the Free Software Foundation, either
#version 3 of the License, or (at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
import string
import gi
import gettext
import locale
import re
from collections import OrderedDict
from gi.repository import Gtk
from gi.repository import GObject
from gi.repository import Easyfc
from xml.sax.saxutils import quoteattr
from xml.sax.saxutils import escape

__all__ = (
            "FontsTweakTool",
          )

def N_(s):
    return s

alias_names = ['sans-serif', 'serif', 'monospace', 'cursive', 'fantasy']
sample_text = N_('The quick brown fox jumps over the lazy dog')
GETTEXT_PACKAGE = 'fonts-tweak-tool'
LOCALEDIR = '/usr/share/locale'

class LangList:

    def __init__(self, parent):
        self.langlist = OrderedDict()
        self.parent_window = parent
        path = os.path.dirname(os.path.realpath(__file__))
        localefile = os.path.join(path, '..', 'data', 'locale-list')

        # Add "any" language to the list.
        self.langlist[''] = N_('Default')
        try:
            fd = open(localefile, "r")
        except:
            try:
                # XXX: need to polish it with the better way.
                fd = open("/usr/share/fonts-tweak-tool/locale-list", "r")
            except:
                raise RuntimeError, ("Cannot find locale-list")

        while True:
            line = fd.readline()
            if not line:
                break
            tokens = string.split(line)
            lang = str(tokens[0]).split('.')[0].replace('_', '-')
            self.langlist[lang] = string.join(tokens[3:], ' ')

    def show_dialog(self, column, disable_default):
        builder = Gtk.Builder()
        builder.set_translation_domain(GETTEXT_PACKAGE)
        path = os.path.dirname(os.path.realpath(__file__))
        uifile = os.path.join(path, '..', 'data', 'fontstools.ui')
        if not os.path.isfile(uifile):
            # need to polish it with the better way
            uifile = "/usr/share/fonts-tweak-tool/fontstools.ui"
        builder.add_from_file(uifile)
        self.dialog = builder.get_object("dialog2")
        self.dialog.set_transient_for(self.parent_window)
        self.langStore = builder.get_object("lang_and_locale_list")

        for l in self.langlist.keys():
            if disable_default and l == '':
                    continue
            iter = self.langStore.append()
            self.langStore.set_value(iter, 0, l)
            self.langStore.set_value(iter, 1, self.langlist[l])

        self.langView = builder.get_object("lang_view")
        col = Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=column)
        self.langView.append_column(col)
        self.dialog.show_all()
        return self.dialog.run()

    def close_dialog(self):
        self.dialog.destroy()
        self.dialog = None

    def get_selection(self):
        lang = None
        fullName = None
        if self.dialog != None:
            model, iterator = self.langView.get_selection().get_selected()
            if iterator:
                lang = model.get_value(iterator, 0)
                fullName = self.langStore.get_value(iterator, 1)
                return (lang, fullName)
            else:
                return None

class FontsTweakTool:

    def selectionChanged(self, *args):
        selection = self.lang_view.get_selection()
        model, iter = selection.get_selected()
        if iter == None:
            self.note_book.set_current_page(1)
            self.removelang_button.set_sensitive(False)
        else:
            lang = model.get_value(iter, 1)
            for n in alias_names:
                self.render_combobox(lang, n)
            self.note_book.set_current_page(0)
            self.removelang_button.set_sensitive(True)

    def pango_selectionChanged(self, *args):
        selection = self.pango_langview.get_selection()
        model, iter = selection.get_selected()
        if iter == None:
            self.pango_removelang.set_sensitive(False)
        else:
            lang = model.get_value(iter, 1)
            for n in alias_names:
                self.render_combobox(lang, n)
            self.pango_removelang.set_sensitive(True)

    def add_language(self, desc, lang):
        retval = True
        model = self.lang_view.get_model()
        iter = model.get_iter_first()
        while iter != None:
            n, l = model.get(iter, 0, 1)
            if l == lang:
                retval = False
                break
            iter = model.iter_next(iter)
        if retval == True:
            iter = self.lang_list.append()
            self.lang_list.set_value(iter, 0, desc)
            self.lang_list.set_value(iter, 1, lang)
        else:
            iter = None

        return iter

    def addlangClicked(self, *args):
        response = self.languages.show_dialog(1, False)
        if response != Gtk.ResponseType.CANCEL:
            selection = self.languages.get_selection()
            if selection != None:
                lang, desc = selection
                iter = self.add_language(desc, lang)
                if iter == None:
                    print "%s has already been added.\n" % lang
                else:
                    model = self.lang_view.get_model()
                    path = model.get_path(iter)
                    self.lang_view.set_cursor(path, None, False)

        self.languages.close_dialog()

    def pango_addlanguage(self, desc, language):
        retval = True
        model = self.pango_langview.get_model()
        iteration = model.get_iter_first()
        while iteration != None:
            name, lang = model.get(iteration, 0, 1)
            if lang == language:
                retval = False
                break
            iteration = model.iter_next(iteration)
        if retval == True:
            iteration = self.pango_langlist.append()
            self.pango_langlist.set_value(iteration, 0, desc)
            self.pango_langlist.set_value(iteration, 1, language)
        else:
            iteration = None

        return iteration

    def pango_addlangClicked(self, *args):
        response = self.languages.show_dialog(1, True)
        if response != Gtk.ResponseType.CANCEL:
            selection = self.languages.get_selection()
            if selection != None:
                lang, desc = selection
                iter = self.pango_addlanguage(desc, lang)
                if iter == None:
                    print "%s has already been added.\n" % lang
                else:
                    model = self.pango_langview.get_model()
                    path = model.get_path(iter)
                    self.pango_langview.set_cursor(path, None, False)

        self.languages.close_dialog()

    def removelangClicked(self, *args):
        selection = self.lang_view.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            lang = model.get(iter, 1)[0]
            self.lang_list.remove(iter)
            self.note_book.set_current_page(1)
            self.removelang_button.set_sensitive(False)
            self.config.remove_aliases(lang)

    def pango_langupClicked(self, *args):
        selection = self.pango_langview.get_selection()
        listmodel, listiter = selection.get_selected()
        first_iter = listmodel.get_iter_first()
        if listiter != None:
            path = listmodel.get_path(listiter)
            path.prev()
            prev_iter = listmodel.get_iter(path)
            if listiter != first_iter:
                listmodel.move_before(listiter, prev_iter)

    def pango_langdownClicked(self, *args):
        selection = self.pango_langview.get_selection()
        listmodel, listiter = selection.get_selected()
        first_iter = listmodel.get_iter_first()
        if listiter != None:
            next_iter = listmodel.iter_next(listiter)
            if next_iter:
                listmodel.move_after(listiter, next_iter)

    def pango_removelangClicked(self, *args):
        selection = self.pango_langview.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            lang = model.get(iter, 1)[0]
            self.pango_langlist.remove(iter)
            self.pango_removelang.set_sensitive(False)

    def pango_applyClicked(self, *args):
        pango_language = "export PANGO_LANGUAGE = "
        languages = ""
        model = self.pango_langview.get_model()
        iteration = model.get_iter_first()
        name, language = model.get(iteration, 0, 1)
        pango_language = language
        iteration = model.iter_next(iteration)
        while iteration != None:
            name, language = model.get(iteration, 0, 1)
            pango_language = pango_language + ":" +language
            iteration = model.iter_next(iteration)

        self.write_config(pango_language)

    def parse_content(self, path, pango_language):
        find_pangolanguage = False
        content = []

        if os.path.exists(path):
            config_file = open(path, 'r')
            lines = config_file.readlines()
            config_file.close

            for line in lines:
                if re.search(r'PANGO_LANGUAGE=', line):
                    line = re.sub(r'(PANGO_LANGUAGE=).*$', r'\1%s'%pango_language, line)
                    find_pangolanguage = True
                content.append(line)

        if not find_pangolanguage:
            content.append("#start: fonts-tweak-tool\n")
            content.append("PANGO_LANGUAGE=%s\n"%pango_language)
            content.append("#end:   fonts-tweak-tool")

        return content

    def write_config(self, pango_language):
        home = os.path.expanduser("~")
        configfile_path = home+"/.i18n"
        content = self.parse_content(configfile_path, pango_language)

        config_file = open(configfile_path, 'w')
        config_file.writelines(content)
        config_file.close()        

    def pango_closeClicked(self, *args):
        pass

    def fontChanged(self, combobox, *args):
        if self.__initialized == False:
            return
        selection = self.lang_view.get_selection()
        model, iter = selection.get_selected()
        if iter != None:
            lang = model.get(iter, 1)[0]
            model = combobox.get_model()
            iter = combobox.get_active_iter()
            if iter != None:
                font = model.get(iter, 0)[0]
                iter = model.get_iter_first()
                alias = model.get(iter, 0)[0]
                self.config.remove_alias(lang, alias)
                a = Easyfc.Alias.new(alias)
                try:
                    a.set_font(font)
                    self.config.add_alias(lang, a)
                except gi._glib.GError:
                    pass
                self.render_label(combobox, lang)

    def checkchange(self):
        changed = False
        language_added = False
        iter = self.lang_list.get_iter_first()
        while iter != None:
            n, l = self.lang_list.get(iter, 0, 1)
            if l not in self.init_status.keys():
                language_added = True
                aliases = self.config.get_aliases(l)
                if aliases:
                    changed = True
            else:
                aliases = self.config.get_aliases(l)
                fonts = []
                if aliases:
                    for a in aliases:
                        fonts.append(a.get_font())
                if set(fonts) != set(self.init_status[l]):
                    changed = True
            iter = self.lang_list.iter_next(iter)

        return language_added, changed

    def closeClicked(self, *args):
        language_added, font_changed = self.checkchange()
        if language_added and not font_changed:
            dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        Gtk.MessageType.WARNING, Gtk.ButtonsType.OK,
                        "The added language will be discard after closing")
            dialog.show_all()
            response = dialog.run()
            dialog.destroy()

        if font_changed:
            dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
                        Gtk.MessageType.WARNING, Gtk.ButtonsType.YES_NO,
                        "Do you want to save your changes before closing?")
            dialog.show_all()
            response = dialog.run()

            if response == Gtk.ResponseType.YES:
                self.applyClicked()
            dialog.destroy()
        Gtk.main_quit()

    def pango_closeClicked(self, *args):
        Gtk.main_quit()

    def applyClicked(self, *args):
        try:
            self.config.save()
        except gi._glib.GError, e:
            if e.domain != 'ezfc-error-quark' and e.code != 6:
                raise
            else:
                print "%s: %s" % (sys.argv[0], e)
        Gtk.main_quit()

    def translate_text(self, text, lang):
        if self.translations.has_key(lang) == False:
            self.translations[lang] = gettext.translation(
                domain=GETTEXT_PACKAGE,
                localedir=LOCALEDIR,
                languages=[lang.replace('-', '_')],
                fallback=True,
                codeset="utf8")
        return unicode(self.translations[lang].gettext(text), "utf8")

    def render_label(self, combobox, lang):
        model = combobox.get_model()
        iter = combobox.get_active_iter()
        if iter != None:
            font = model.get(iter, 0)[0]
            # Work around for PyGObject versions 3.0.3 and 3.1.0,
            # which decode strings in Gtk.TreeModel when retrieval.
            # This behavior was reverted in 3.1.1:
            # http://git.gnome.org/browse/pygobject/commit/?id=0285e107
            if type(font) is not unicode:
                font = unicode(font, "utf8")
            iter = model.get_iter_first()
            alias = model.get(iter, 0)[0]
            self.label[alias].set_markup(
                "<span font_family=%s font_size=\"small\">%s</span>" % (
                    quoteattr(font),
                    escape(self.translate_text(sample_text, lang))))

    def render_combobox(self, lang, alias):
        if self.fontslist.has_key(lang) == False:
            self.fontslist[lang] = {}
        if self.fontslist[lang].has_key(alias) == False:
            self.fontslist[lang][alias] = Easyfc.Font.get_list(lang, alias, False)
        self.lists[alias].clear()
        self.lists[alias].append([alias])
        for f in self.fontslist[lang][alias]:
            self.lists[alias].append([f])
        fn = None
        for a in self.config.get_aliases(lang):
            if a.get_name() == alias:
                fn = a.get_font()
                break
        if fn != None:
            model = self.combobox[alias].get_model()
            iter = model.get_iter_first()
            while iter != None:
                f = model.get(iter, 0)[0]
                if type(fn) is not unicode:
                    fontname = unicode(fn, "utf8") 
                if f == fontname:
                    self.combobox[alias].set_active_iter(iter)
                    break
                iter = model.iter_next(iter)
        else:
            self.combobox[alias].set_active(0)
        self.render_label(self.combobox[alias], lang)

    def __init__(self):
        self.__initialized = False
        builder = Gtk.Builder()
        builder.set_translation_domain(GETTEXT_PACKAGE)
        path = os.path.dirname(os.path.realpath(__file__))
        uifile = os.path.join(path, '..', 'data', 'fontstools.ui')
        if not os.path.isfile(uifile):
            # need to polish it with the better way
            uifile = "/usr/share/fonts-tweak-tool/fontstools.ui"
        builder.add_from_file(uifile) 
        self.window = builder.get_object("window1")
        self.window.connect("destroy", Gtk.main_quit)
        self.window.set_title("fonts-tweak-tool")
        self.window.set_size_request(640, 480)

        self.scrollwindow = builder.get_object("scrolledwindow1")
        self.scrollwindow.set_min_content_width(200)
        self.lang_view = builder.get_object("treeview1")
        self.lang_list = builder.get_object("lang_list")
        column = Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=0)
        self.lang_view.append_column(column)

        self.pango_scrollwindow = builder.get_object("pango_scrolledwindow")
        self.pango_scrollwindow.set_min_content_width(200)
        self.pango_langview = builder.get_object("pango_treeview")
        self.pango_langlist = builder.get_object("pango_langlist")
        column = Gtk.TreeViewColumn(None, Gtk.CellRendererText(), text=1)
        self.pango_langview.append_column(column)

        self.note_book = builder.get_object("notebook1")
        self.note_book.set_current_page(1)

        self.fontslist = {}

        self.combobox = {}
        self.combobox['sans-serif'] = builder.get_object("sans_combobox")
        self.combobox['serif'] = builder.get_object("serif_combobox")
        self.combobox['monospace'] = builder.get_object("monospace_combobox")
        self.combobox['cursive'] = builder.get_object("cursive_combobox")
        self.combobox['fantasy'] = builder.get_object("fantasy_combobox")

        self.label = {}
        self.label['sans-serif'] = builder.get_object("sans_label")
        self.label['serif'] = builder.get_object("serif_label")
        self.label['monospace'] = builder.get_object("monospace_label")
        self.label['cursive'] = builder.get_object("cursive_label")
        self.label['fantasy'] = builder.get_object("fantasy_label")

        for f in alias_names:
            renderer_text = Gtk.CellRendererText()
            self.combobox[f].pack_start(renderer_text, True)
            self.combobox[f].add_attribute(renderer_text, "text", 0)
            self.combobox[f].connect('changed', self.fontChanged)

        self.lists = {}
        self.lists['sans-serif'] = builder.get_object("sans_fonts_list")
        self.lists['serif'] = builder.get_object("serif_fonts_list")
        self.lists['monospace'] = builder.get_object("monospace_fonts_list")
        self.lists['cursive'] = builder.get_object("cursive_fonts_list")
        self.lists['fantasy'] = builder.get_object("fantasy_fonts_list")

        self.close_button = builder.get_object("button2")
        self.close_button.connect("clicked", self.closeClicked)

        self.addlang_button = builder.get_object("add-lang")
        self.addlang_button.connect("clicked", self.addlangClicked)

        self.removelang_button = builder.get_object("remove-lang")
        self.removelang_button.connect("clicked", self.removelangClicked)
        self.removelang_button.set_sensitive(False)

        self.addlang_button = builder.get_object("add-lang1")
        self.addlang_button.connect("clicked", self.pango_addlangClicked)

        self.pango_removelang = builder.get_object("remove-lang1")
        self.pango_removelang.connect("clicked", self.pango_removelangClicked)
        self.pango_removelang.set_sensitive(False)

        self.pango_applybutton = builder.get_object("pango_apply_button")
        self.pango_applybutton.connect("clicked", self.pango_applyClicked)

        self.pango_closebutton = builder.get_object("pango_close_button")
        self.pango_closebutton.connect("clicked", self.pango_closeClicked)
        #self.pango_closebutton.set_sensitive(False)

        self.langup_button = builder.get_object("lang-up")
        self.langup_button.connect("clicked", self.pango_langupClicked)

        self.langdown_button = builder.get_object("lang-down")
        self.langdown_button.connect("clicked", self.pango_langdownClicked)

        self.apply_button = builder.get_object("button1")
        self.apply_button.connect("clicked", self.applyClicked)

        selection = self.lang_view.get_selection()
        selection.connect("changed", self.selectionChanged)

        pango_selection = self.pango_langview.get_selection()
        pango_selection.connect("changed", self.pango_selectionChanged)

        self.languages = LangList(self.window)
        self.data = {}
        self.translations = {}

        self.init_status = {}

        Easyfc.init()

        self.config = Easyfc.Config()
        self.config.set_name("fontstweak")
        try:
            self.config.load()
        except gi._glib.GError, e:
            if e.domain != 'ezfc-error-quark' or e.code != 7:
                raise

        for l in self.config.get_language_list():
            # XXX: need to take care of the KeyError exception?
            desc = self.languages.langlist[l]
            self.add_language(desc, l)
            fontlist =[]
            for a in self.config.get_aliases(l):
                an = a.get_name()
                self.render_combobox(l, an)
                fn = a.get_font()
                fontlist.append(fn)
            self.init_status[l]=fontlist

        self.__initialized = True

def main(argv):
    try:
        locale.setlocale(locale.LC_ALL, '')
    except Locale.Error, e:
        os.environ['LC_ALL'] = 'C'
        locale.setlocale(locale.LC_ALL, '')

    gettext.bind_textdomain_codeset(GETTEXT_PACKAGE, locale.nl_langinfo(locale.CODESET))
    gettext.bindtextdomain(GETTEXT_PACKAGE, LOCALEDIR)
    gettext.textdomain(GETTEXT_PACKAGE)
    tool = FontsTweakTool()
    tool.window.show_all()
    tool.font_changed = False
    Gtk.main()

#!/bin/sh
# Run this to generate all the initial makefiles, etc.

srcdir=`dirname $0`
test -z "$srcdir" && srcdir=.

PKG_NAME="fonts-tweak-tool"

(test -f $srcdir/configure.ac \
  && test -f $srcdir/README \
  && test -d $srcdir/fontstweak) || {
    echo -n "**Error**: Directory "\`$srcdir\'" does not look like the"
    echo " top-level $PKG_NAME directory"
    exit 1
}

which gnome-autogen.sh || {
    echo "You need to install gnome-common from the GNOME CVS"
    exit 1
}
REQUIRED_AUTOMAKE_VERSION=1.11 . gnome-autogen.sh

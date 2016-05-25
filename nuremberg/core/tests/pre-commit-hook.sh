#!/bin/bash

mybasename=`basename $0`
hook_name=pre-commit
if [ ! -e .git/hooks/${mybasename} ] ; then
    ln -s ../../nuremberg/core/tests/${mybasename} .git/hooks/${hook_name}
    echo "Installed pre-commit hook."
else

  py.test

fi

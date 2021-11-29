vini_dir="$(locate vini | grep /vini$)"
vini_util_dir="$(locate utilities | grep /vini/utilities$)"

export PATH=${vini_dir}:$PATH
export PATH=${vini_util_dir}:$PATH
echo "PATH set to " $PATH
echo
export  PYTHONPATH=${vini_dir}:$PYTHONPATH
export  PYTHONPATH=${vini_util_dir}:$PYTHONPATH
echo "PYTHONPATH set to " $PYTHONPATH
echo

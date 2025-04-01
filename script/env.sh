set -e
set +u

if lsb_release -cs | grep -vq bookworm; then
	VENV_NAME=.venv
	if [ ! -d $VENV_NAME -a -z "$VIRTUAL_ENV" ]; then
		python3 -m venv $VENV_NAME
		. ./$VENV_NAME/bin/activate
		pip install -r script/requirements.txt
	else
		. ./$VENV_NAME/bin/activate
	fi
fi

export PYTHONPATH=$PYTHONPATH:`pwd`

set -u

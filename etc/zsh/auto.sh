export PYTHONPATH=$PYTHONPATH:$PROJDIR/src:$PROJDIR/src/dj

function push() {
  CWD=${1:-$PROJDIR}
  cd "$CWD" >> /dev/null || return;
}

function pop() {
  cd "${CWD:-$PROJDIR}" >> /dev/null || return;
  unset CWD
}


function manage() {
  push "$PROJDIR"/src/dj/
  python manage.py "$*"
  pop
}

function run() {
  push "$PROJDIR"/src/dj/
  manage runserver
  pop
}

function fmt() {
  push "$PROJDIR"/src/dj/
  black .
  pop
}

function 0() {
  cd "$PROJDIR" || return;
}
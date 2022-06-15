export PYTHONPATH=$PYTHONPATH:$PROJDIR/src:$PROJDIR/src/dj

function push() {
  CWD=$(pwd)
  cd "${1:-$PROJDIR}" >> /dev/null || return;
}

function pop() {
  cd "${CWD:-$PROJDIR}" >> /dev/null || return;
  unset CWD
}


function manage() {
  push "$PROJDIR"/src/dj/
  python manage.py "$*"
  response=$?
  pop
  return $response
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

function migrate() {
  manage migrate $*
  echo migrate_done
}

function recreatedb() {
    psql -h 127.0.0.1 -d postgres -c "CREATE USER root;"
    psql -h 127.0.0.1 -d postgres -c "ALTER USER root WITH SUPERUSER;"
    psql -h 127.0.0.1 -c "DROP DATABASE IF EXISTS fpm_controller;" template1
    psql -h 127.0.0.1 -c "CREATE DATABASE fpm_controller;" template1
    migrate $*
}

function makemigrations() {
  manage makemigrations $*
}

function djshell() {
  manage shell
}

function dbshell() {
  manage dbshell
}
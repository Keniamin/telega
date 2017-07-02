cd $(dirname $0)/../static

time sass \
    --scss \
    --force \
    --no-cache \
    --stop-on-error \
    --sourcemap=none \
    --style=compressed \
    --update scss/:css/

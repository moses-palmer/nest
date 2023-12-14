# If running interactively, source the full configuration, otherwise only
# update the path
if [[ $- == *i* ]]; then
    . ~/.bashrc
else
    . ~/.config/environment.d/ZZ-local-bin.conf
fi

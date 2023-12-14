if ! echo "$PATH" | grep -q '/usr/local/bin'; then
    PATH="/usr/local/bin:$PATH"
fi

. ~/.config/bash/rc


export PATH

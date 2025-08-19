DRC Sim Server
---

# Running from source directory

Last tested on Fedora 42

## Build wpa_supplicant

```sh
cd drc-hostap/wpa_supplicant
cp ../conf/wpa_supplicant.config .config
make "-j$(nproc)" EXTRA_CFLAGS='-Wno-format-truncation'
```

## Backend GUI

1. Install the dependencies (depends.fedora.txt)
1. Install Pipenv (`pipx install pipenv`)
1. `pipenv install -e .`
1. `sudo "$(pipenv --venv)/bin/drc-sim-backend" --verbose --wpa-supplicant="$(pwd)/drc-hostap/wpa_supplicant/wpa_supplicant" --wpa-cli="$(pwd)/drc-hostap/wpa_supplicant/wpa_cli"`

The GUI doesn't have any cleanup functionality, so it won't re-manage your wifi interface when it's done with it. Use `nmcli d se <interface name> managed yes` to re-enable NetworkManager functionality.

If you're running the GUI in a container, you'll need to give it some help. Use `nmcli d se <interface> managed no` to unmanage the interface for it.

# Credits

[drc-sim] \(original\) by [memahaxx]
- The original Python codebase

[libdrc documentation] by memahaxx
- Gamepad and Wii U software and hardware details

[drc-sim-keyboard] by justjake
- The readme that got me set up initially

# Additional Software

[wpa_supplicant] modified by memahaxx

[drc_sim_c] drc-sim rewritten in C++

[netifaces] Python network interfaces library

[pexpect] Python process interaction library



[drc-sim]: https://bitbucket.org/memahaxx/drc-sim
[drc-sim-keyboard]: https://github.com/justjake/drc-sim-keyboard
[Installation instructions]: https://github.com/rolandoislas/drc-sim/wiki/Install
[wpa_supplicant]: https://github.com/rolandoislas/drc-hostap
[drc_sim_c]: https://github.com/rodolforg/drc-sim-c
[memahaxx]: https://bitbucket.org/memahaxx/
[libdrc documentation]: http://libdrc.org/docs/index.html
[netifaces]: https://pypi.python.org/pypi/netifaces
[pexpect]: https://pypi.python.org/pypi/pexpect

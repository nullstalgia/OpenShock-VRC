# OpenShock-VRC
A companion script for OpenShock devices to be controlled by VRC Props and Contact Recievers!

## Setup

- Download the latest release from the [Releases](https://github.com/nullstalgia/OpenShock-VRC/releases) page. 
- Copy and edit the `VRCControl.json.example` file to match your setup. Makes sure to rename your resulting file to `VRCControl.json` .
    - ## **Things you may need to edit:**
    - `OpenShock` - `host`: the IP of the OpenShock unit you wish to send commands to. Default (`openshock.local`) should connect to the local unit on your network.
    - `OpenShock` - `ids`: a list of up to five Shocker IDs to be controlled by the expression menu controls. Can be a role (ex: "LUL", "LUA"), or a specific ID (ex: 1234, 4020).
    - `osc` - `ListeningPort`: the port to listen for incoming commands on. Default (`9001`) should be fine if you don't have other OSC apps, but you'll need to change it if you use [VOR](https://github.com/SutekhVRC/VOR) or other OSC routers.
    - `osc` - `unmuteOnTouch`: if true, will unmute VRChat Voice when a touchpoint is activated. If false, will leave the player muted.
    - `osc` - `touchpoints`: a list of touchpoints to be controlled by VRC Contact Recievers. See [here](https://github.com/nullstalgia/OpenShock-VRC/tree/main/VRChat%20Files#touchpoints) for more info on the format, or look at the included ones as a template.
    - The rest of the defaults should be fine as they are.
- Run the script's executable! It should connect to the OpenShock unit and start listening for commands.
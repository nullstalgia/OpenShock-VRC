# VRChat SDK Files


### Dependencies, import into your project first:

- [VRCFury](https://github.com/VRCFury/VRCFury)
- [Poiyomi 8.1+](https://github.com/poiyomi/PoiyomiToonShader)


## Panel 

![image](https://github.com/nullstalgia/OpenShock-VRC/assets/20761757/d3dd75ac-e1a5-42e6-8cd1-ec4e0874c621)

The panel is a world-placeable, interactable object that can be used to hand off shocker control to other players. It shows your set (max) intensity as well the current intensity being sent. Interactions are with buttons on the face that send in 25%+ increments, or by pulling the slider's physbone to the desired intensity. It is not network synced for late joiners, you will have to place the panel again for them to see it.

### Setup:

- Set up the companion script supplied in this repo, the example config contains the settings for the panel.
- Import the dependencies into your project
- Find the Panel prefab in the OpenShock folder and place it on the root of your avatar's hierarchy.
- Turn on Gizmos on the top right of the scene view
- Open the Panel prefab on your avatar, and move the "Panel Head Target" and the "Panel Reset Targets" to the spots described by the gizmo text. You can turn on the "Panel" object inside temporarily to preview your positioning. Example:

![image](https://github.com/nullstalgia/OpenShock-VRC/assets/20761757/87624312-3f5e-4d1e-9aa3-c47283c29e69)

## Menu Controls:

When connected to someone else's OpenShock with your companion script, there is the option of using the expression menu to send shocker commands.

### Setup:

- Set up the companion script supplied in this repo, except the "host" must be set to the IP of the person you are connecting to.
- You will need to set the appropriate targets in the config as well, the best is to do the roles. Ex: "LUL" and "RUL" for the left and right upper leg shockers.
- Import the dependencies into your project
- Find the Menu Controls prefab in the OpenShock folder and place it on the root of your avatar's hierarchy.
- When connected and running, you will need to select the "Targets" in the menu to activate sending commands to each of them.

## Touchpoints:

With Touchpoints, you are able to set up any arbitrary VRC Contact Reciever to send shocker commands, for example: headpats causing a vibration for the duration of the pat, a nose boop sending a quick single shock, or a tail pull sending a varying shock level based on the stretch.

### Setup:

- Set up the companion script supplied in this repo. If you are connecting to a local unit on your network, you should be able to leave the "host" at the default "openshock.local" value. In the event that it can not find the local device, you can set the IP of the unit manually.
- Import the dependencies into your project
- Find the Touchpoint Control prefab in the OpenShock folder and place it on the root of your avatar's hierarchy. This will let you set the intensity of and temporarily disable your touchpoints.
- Set up [Recievers](https://www.youtube.com/watch?v=LOZu6e8ozns) on your avatar, and note their parameter names (address).
- Add additional touchpoint JSON objects into the config as needed. Don't forget the comma between each object! 

You can ensure your JSON is valid by pasting it into [json.wtf](http://json.wtf/) and clicking the Thumbs Up ( 👍 ) button on the top right.


### JSON Touchpoint Format:

```json
{
    "address": "NoseBoop", # Avatar Paramater to listen to, can be float or bool
    "method": 1, # 1 - Shock, 2 - Vibrate
    "intensity": 0.8, # 0.0 - 1.0
    "duration": 300, # in milliseconds, optional, default 300
    "looping": false, # optional, default true. decides if action should loop until the paramater is false
    "unmute": false, # optional, default true. decides if action should un-mute you
    "absolute": false, # optional, default false. decides if the sent intensity should be scaled by the unit's set intensity
    "ids": ["LUL", "LUA"] # IDs of the shockers to send to, also takes Roles (shown)
}
```


#### Acknowledgements:

- Panel modelled by: amtcubus
- [VRLabs World Constraint](https://github.com/VRLabs/World-Constraint) (included in .unitypackage)

#### Changelog:

- 1.0 - Initial Release
- 1.1 - Fixed Lightning Bolt clipping when panel squished
Flávio J. Saraiva @ 2011-10-24

This repo contains a collection of pyogre apps created to test roint file formats.

Default behavior: (pyogre 1.7.2)
	A/D/S/W     : Move left/right/back/forward
	pgup/pgdown : Move up/down
	mouse               : Rotate (change look direction)
	right click + mouse : Move up/down/left/right
	Esc/Q  : Quit
	PrtScr : Take a screenshot (0.5s wait)
	T      : Toogle filtering [bilinear/trilinear/anisotropic] (0s wait, so bugged)
	R      : Toogle detail level [solid/wireframe/points] (0.5s wait)
	F      : Toogle debug overlay (1s wait)
	P      : Toogle camera details (0s wait, so bugged)

Windows:
	1) ensure you have python and pyogre installed
	2) copy roint.dll and it's depencies here (zlib1.dll)
	3) open the command line here
	4) run the python app script

URLs:
	roint - https://gitorious.org/open-ragnarok/roint
	pyogre - http://www.pythonogre.com/

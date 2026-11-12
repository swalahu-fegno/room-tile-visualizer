# Room Tile Visualizer

A 3D room in the browser where you can try floor and wall tiles.

- Pick a tile for the floor or walls (built-in samples, ABC Emporio tiles, or upload your own photo)
- Walk around: drag to look, W A S D / arrow keys to walk, scroll or pinch to zoom
- Change the room size (width, length, height) and the lighting (on/off, brightness, warm/cool)

Open `index.html` through any static web server. ABC Emporio tiles come from `abc-tiles.json`;
refresh it with `python3 fetch_abc_tiles.py 5` (5 pages ≈ 100 products).

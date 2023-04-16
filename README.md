# Analyzer for Minecraft speedrunigt

## Notes

1. Requirement: mod atum, MultiMC.

2. You can run this script anywhere but please first check out `config` file and modify your MultiMC path.

## What does it do?

It collects speedrunigt records of your Any% runs, RSG or FSG, and return a CSV table. It can also update a reset-counting txt for your OBS display.

## Todos

**Appreciated if anyone can make a display UI based on the output CSV, presenting all runs clearly.**

- [x] ~~Add compatability for atum-created SSG & RSG~~
- [x] ~~Show delta time (seconds) of each process, instead of timestamps~~
- [x] ~~Fix negative time issue, in case you enter fortress first~~
- [x] ~~Record incomplete saves that stopped after a blind~~
- [ ] Identify whether 'is_completed' is done via cheat(creative mode), because this leads to order error
- [ ] Make use of `igt_advancement.log`
- [ ] Create a detailed personal runs UI, which compares every attempt of yours, in each section
- [ ] Record portal type, pearls/wool/obsidian count?
- [x] ~~Rewrite order handling / delta calculating method~~

## Update Log
- Version 1.1, 20230416.
  - Rewrote delta calcu method.
  - Now it's able to automatically remove identical records.
  - Added various new configs.
  - Changed incomplete criteria to blind.
  - Now it **uses your python folder as output dir**, instead of MultiMC folder.
- Version 1.2, 20230416.
  - New feature: count resets and attempts, and output to obs_display.txt

# Analyzer for Minecraft speedrunigt

## Notes

1. Only saves named by the mod 'atum' can be read.

2. Please put this script in your 'MultiMC/instances' directory, and run the batchfile.

## What does it do?

It collects speedrunigt records of your completed runs, and output to a CSV file under MultiMC/instances.

## Todos

**Appreciated if anyone can make a display UI based on the output CSV, presenting all runs clearly.**

- [x] Add compatability for atum-created SSG & RSG
- [x] Show delta time (seconds) of each process, instead of timestamps
- [x] Fix negative time issue, in case you enter fortress first
- [x] Record incomplete saves that stopped after eye-spy
- [ ] Identify whether 'is_completed' is done via cheat(creative mode), because this leads to order error
- [ ] Make use of `igt_advancement.log`
- [ ] Add compatability for AA-tool
- [ ] Create a detailed personal runs UI, which compares every attempt of yours, in each section
- [ ] Record portal type, pearls/wool/obsidian count?
- [ ] Rewrite order handling / delta calculating method
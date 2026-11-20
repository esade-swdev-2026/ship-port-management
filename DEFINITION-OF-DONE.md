# Definition of Done

A backlog item is done when all of these are true:

1. From a clean clone, `uv sync && uv run ship-port-management --help` works.
2. CI is green on the pull request and on `main` after the merge.
3. There is at least one test for the new behaviour.
4. Bad input gives a clear message and a non-zero exit code, never a traceback.
5. The README explains the new behaviour (command table and, where useful, the worked example).
6. Another member of the group has read the change and approved the pull request.
7. Someone has edge-tested the code by hand (empty, zero, negative, wrong-format and
   boundary inputs).

> We submitted this Definition of Done on Moodle on 25 Sep 2026 ("Backlog and Definition of
> Done"). There, item 1 named the command `uv run port_management --help`. The app was published
> as `ship-port-management`, so the command above is the correct one. Nothing else has changed.

The backlog this applies to is in [backlog-breif.md](backlog-breif.md).

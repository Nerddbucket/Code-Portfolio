#!/usr/bin/env bash
# CST 130 Module 9 Lab — Commands to run on YOUR Linux system
# Usage:
#   chmod +x CST130_Module9_Lab_Commands.sh
#   ./CST130_Module9_Lab_Commands.sh
#
# Tip: Run sections in a real terminal window so you can take screenshots
# that show both the command and its output for submission.

set -uo pipefail

pause() {
  echo
  read -r -p "Press Enter to continue (or Ctrl+C to stop)... " _
  echo
}

echo "=============================================="
echo " CST 130 — Module 9: Managing Linux Processes"
echo "=============================================="
echo
echo "Safety: Only kill/renice the temporary sleep processes from this lab."
echo

############################################
# PART 1 — Viewing processes
############################################
echo "===== PART 1: Viewing and Interpreting Processes ====="
echo
echo ">>> Command: ps"
ps
pause

echo ">>> Command: ps -f"
ps -f
echo
echo "From the output above, record:"
echo "  - Shell PID  (your bash/sh line)"
echo "  - PID of ps -f"
echo "  - PPID of ps -f  (should match Shell PID)"
echo
echo "*** TAKE SCREENSHOT 1 now (ps -f with PID/PPID visible) ***"
pause

echo ">>> Command: ps -e | head"
ps -e | head
pause

echo ">>> Command: ps -el | head"
ps -el | head
pause

echo ">>> Command: pstree -p | head -30"
if command -v pstree >/dev/null 2>&1; then
  pstree -p | head -30
else
  echo "pstree not installed. Showing forest view instead:"
  ps -ef --forest | head -30
fi
pause

############################################
# PART 2 — Job control
############################################
echo "===== PART 2: Process States and Job Control ====="
echo
echo "This part needs interactive Ctrl+Z / fg / bg."
echo "Run these commands MANUALLY in your terminal:"
echo
cat <<'MANUAL'
  sleep 300
  # Press Ctrl+Z to stop it

  jobs -l
  # Note the PID shown by jobs -l

  ps -o pid,ppid,state,stat,cmd -p <PID>
  # *** TAKE SCREENSHOT 2 here (Stopped / state T) ***

  bg
  jobs -l

  fg
  # Press Ctrl+Z again
  bg

  # When finished with Part 2, clean up:
  kill %1 2>/dev/null || true
MANUAL
pause

############################################
# PART 3 — Signals
############################################
echo "===== PART 3: Signals and Safe Termination ====="
echo
echo ">>> Starting test process: sleep 300 &"
sleep 300 &
PID1=$!
echo "PID1=$PID1"
jobs -l
pause

echo ">>> Command: kill $PID1   (default = SIGTERM)"
kill "$PID1"
sleep 0.5
jobs -l
echo
echo "*** TAKE SCREENSHOT 3 now (default kill terminating sleep) ***"
pause

echo ">>> Starting another test process for SIGKILL"
sleep 300 &
PID2=$!
echo "PID2=$PID2"
echo ">>> Command: kill -9 $PID2"
kill -9 "$PID2"
sleep 0.5
jobs -l
pause

############################################
# PART 4 — fork/exec/wait observation
############################################
echo "===== PART 4: fork, exec, and wait ====="
echo
echo ">>> Foreground (shell waits): sleep 5"
sleep 5
echo "Prompt returned after sleep finished."
echo
echo ">>> Background (shell does not wait): sleep 5 &"
sleep 5 &
echo "Prompt returned immediately. Background PID=$!"
wait || true
pause

############################################
# PART 5 — nice / renice
############################################
echo "===== PART 5: nice and renice ====="
echo
echo ">>> Command: nice -n 10 sleep 300 &"
nice -n 10 sleep 300 &
NPID=$!
echo "NPID=$NPID"
sleep 0.2
echo ">>> Before renice:"
ps -o pid,ppid,pri,ni,state,cmd -p "$NPID"
pause

echo ">>> Command: renice 15 -p $NPID"
renice 15 -p "$NPID"
echo ">>> After renice:"
ps -o pid,ppid,pri,ni,state,cmd -p "$NPID"
echo
echo "*** TAKE SCREENSHOT 4 now (NI before=10, after=15) ***"
pause

echo ">>> Cleaning up: kill $NPID"
kill "$NPID" 2>/dev/null || true
pause

############################################
# PART 6 — at and cron
############################################
echo "===== PART 6: at and cron ====="
echo
echo ">>> Command: which at"
if command -v at >/dev/null 2>&1; then
  which at
  echo
  echo "Schedule a one-time job (example):"
  echo '  at now + 2 minutes'
  echo '  then type:  echo "Module 9 at job completed" > ~/module9_at_test.txt'
  echo '  then press Ctrl+D'
  echo '  later run:  cat ~/module9_at_test.txt'
else
  echo "at is not installed on this system."
  echo "Write this as the command you WOULD schedule:"
  echo '  echo "Module 9 at job completed" > ~/module9_at_test.txt'
  echo "  scheduled with: at now + 2 minutes"
fi
echo
echo ">>> Command: crontab -l"
if command -v crontab >/dev/null 2>&1; then
  crontab -l || echo "(no crontab for this user)"
else
  echo "crontab not installed on this system."
fi
echo
echo "Cron entry to WRITE for daily 2:00 AM backup:"
echo "  0 2 * * * /home/student/backup.sh"
echo
echo "=============================================="
echo " Done. Paste screenshots into the completed"
echo " Word document, add your name, and submit."
echo "=============================================="

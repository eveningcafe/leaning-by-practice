# Git Branching Lab

## Scenario: 3 Users Working on Same Project

```
main ─────●─────●─────●─────●───────────────●──── (final merge)
           \         \         \           /
user-a      ●───●───●  \         \         / (conflict with user-b)
                        \         \       /
user-b                   ●───●───●─\─────/ (conflict with user-a)
                                    \
user-c                               ●───●───● (no conflict)
```

---

## Setup: Initialize Project

```bash
mkdir myproject && cd myproject
git init
echo "Hello World" > greeting.txt
git add greeting.txt
git commit -m "Initial commit"
```

---

## User A: Change Greeting

```bash
git checkout -b hello_git_from_a

# Change line 1 (will conflict with user-b)
echo "Welcome back!" > greeting.txt
git commit -am "User A: change greeting to welcome"
```

---

## User B: Change Greeting (Conflicts with A)

```bash
git checkout main
git checkout -b hello_git_from_b

# Change SAME line 1 (CONFLICT!)
echo "Good morning!" > greeting.txt
git commit -am "User B: change greeting to good morning"
```

---

## User C: Add New Line (No Conflict)

```bash
git checkout main
git checkout -b hello_git_from_c

# Add new line (no conflict)
echo "Hello World" > greeting.txt
echo "Have a nice day!" >> greeting.txt
git commit -am "User C: add second line"
```

---

## Merge: User C First (No Conflict)

```bash
git checkout main
git merge hello_git_from_c -m "Merge user-c"
# Success!
```

---

## Merge: User A (No Conflict Yet)

```bash
git merge hello_git_from_a -m "Merge user-a"
# Success!
```

---

## Merge: User B (CONFLICT!)

```bash
git merge hello_git_from_b
# CONFLICT!
```

Output:
```
Auto-merging greeting.txt
CONFLICT (content): Merge conflict in greeting.txt
Automatic merge failed; fix conflicts and then commit the result.
```

---

## Resolving Conflict

### Step 1: See the conflict

```bash
git status
cat greeting.txt
```

The file now looks like:
```
<<<<<<< HEAD
Welcome back!
=======
Good morning!
>>>>>>> hello_git_from_b
Have a nice day!
```

### Step 2: Fix manually

```bash
# Choose one, or combine both
echo "Good morning! Welcome back!" > greeting.txt
echo "Have a nice day!" >> greeting.txt
```

### Step 3: Complete the merge

```bash
git add greeting.txt
git commit -m "Merge user-b: resolve conflict"
```

---

## View Branch History

```bash
git log --oneline --graph --all
```

Output:
```
*   abc1234 Merge user-b: resolve conflict
|\
| * def5678 User B: change greeting to good morning
* |   ghi9012 Merge user-a
|\ \
| * | jkl3456 User A: change greeting to welcome
| |/
* | mno7890 Merge user-c
|/
* pqr1234 Initial commit
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `git branch` | List branches |
| `git branch -a` | List all branches (local + remote) |
| `git checkout -b <name>` | Create + switch branch |
| `git checkout <name>` | Switch branch |
| `git merge <branch>` | Merge into current |
| `git log --oneline --graph --all` | Visual history |
| `git diff` | Show conflicts |
| `git status` | Show current state |
| `git remote -v` | List remotes |
| `git push -u origin <branch>` | Push + set upstream |
| `git push` | Push to tracked remote |
| `git push origin --delete <branch>` | Delete remote branch |
| `git fetch` | Download only (no merge) |
| `git pull` | Fetch + merge |

---

## Working with Remote (Push/Pull/Fetch)

```
┌──────────────────────────────────┐
│      GitHub (origin)             │
│                                  │
│   origin/main                    │
│   origin/hello_git_from_a        │
│   origin/hello_git_from_b        │
└──────────────────────────────────┘
              ▲       │
         push │       │ fetch/pull
              │       ▼
┌──────────────────────────────────┐
│      Your Computer (local)       │
│                                  │
│   main                           │
│   hello_git_from_a               │
└──────────────────────────────────┘
```

### What is Origin?

```
origin = nickname for remote URL

git remote add origin https://github.com/eveningcafe/lab-git.git
              ^^^^^^
              just a name (could be "github", "server", anything)
```

### What is Upstream?

```
upstream = which remote branch your local branch tracks

git push -u origin hello_git_from_a
         ^^
         -u sets upstream, so next time just "git push" works
```

### Fetch vs Pull

```
fetch: Download changes, don't merge
pull:  Download + merge (fetch + merge)
```

### Setup Remote

```bash
git remote add origin https://github.com/eveningcafe/lab-git.git
git push -u origin main
```

### User A: Push Branch

```bash
git checkout hello_git_from_a
git push -u origin hello_git_from_a
```

### User B: Get User A's Branch

```bash
git fetch origin
git checkout hello_git_from_a
```

### User B: Make Changes and Push

```bash
echo "User B was here" >> greeting.txt
git commit -am "User B: add message"
git push
```

### User A: Get User B's Changes

```bash
git pull
```

### Sync Before Merge

```bash
git checkout main
git pull origin main
git merge hello_git_from_a
git push origin main
```

---

## Quick Demo Script

```bash
#!/bin/bash
rm -rf /tmp/git-demo && mkdir /tmp/git-demo && cd /tmp/git-demo
git init && git config user.email "test@test.com" && git config user.name "Test"

# Initial
echo "Hello World" > greeting.txt
git add . && git commit -m "Initial"

# User A
git checkout -b hello_git_from_a
echo "Welcome back!" > greeting.txt
git commit -am "User A"

# User B
git checkout main && git checkout -b hello_git_from_b
echo "Good morning!" > greeting.txt
git commit -am "User B"

# User C
git checkout main && git checkout -b hello_git_from_c
echo "Hello World" > greeting.txt && echo "Have a nice day!" >> greeting.txt
git commit -am "User C"

# Merge
git checkout main
git merge hello_git_from_c -m "Merge C"
git merge hello_git_from_a -m "Merge A"
git merge hello_git_from_b || echo ">>> CONFLICT! Fix greeting.txt then: git add . && git commit"

git log --oneline --graph --all
```

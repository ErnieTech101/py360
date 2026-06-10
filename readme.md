# PY/360 - Python-based S/360 Mainframe Simulator
<img width="2816" height="1536" alt="Gemini_Generated_Image_iu07exiu07exiu07" src="https://github.com/user-attachments/assets/64011303-b453-4276-9ce5-c39122a3e1e8" /> 

### PY/360 is a Python-based simulation of the IBM S/360 interactive terminal environment for Windows 10/11. It is not an emulator — it does not run real mainframe code or require mainframe software licenses. Instead, PY/360 recreates the **look, feel, and workflow** of interacting with an IBM S/360 system, making mainframe concepts accessible to anyone curious enough to try it.  

---

## Introduction

If you've ever used an ATM, booked a flight, or paid a bill online, you've almost certainly interacted with a mainframe computer without knowing it. These remarkable machines, pioneered by IBM with the legendary System/360 back in 1964, have been quietly running much of the world's most critical computing for over sixty years. Banks, airlines, insurance companies, and governments all rely on them because mainframes do one thing better than anything else ever built — they handle enormous volumes of data with rock solid reliability, day in and day out, year after year. They're not glamorous, they don't make headlines, but when a mainframe goes down, the world notices.

The IBM System/360 was a genuinely revolutionary design. Before it arrived, computers were largely one-off creations — each model incompatible with the next, programs written for one machine useless on another. IBM changed all of that with a single bold stroke, introducing a complete family of compatible computers ranging from small business machines to room-sized giants, all sharing the same instruction set and architecture. It was a concept so successful that its direct descendants, the System/370, System/390, and today's IBM Z series, are still running in data centers around the world.

What made the S/360 and its successors truly special wasn't raw speed — that's the domain of supercomputers, which are optimized for pure number crunching in scientific and engineering applications. And it wasn't personal productivity, which is what your laptop and desktop PC are designed for. The mainframe occupied a unique middle ground, engineered specifically for reliability, throughput, and the simultaneous management of enormous amounts of structured data.

The architecture reflects that purpose in some fascinating ways. Rather than serving one user doing one thing at a time like a personal computer, a mainframe was designed from the start to share its resources across hundreds or even thousands of simultaneous users and processes. This happened in two complementary ways. Time-sharing allowed multiple users sitting at terminals — those iconic green-screen IBM 3270 displays — to interact with the system simultaneously, each getting a slice of the processor's attention so quickly that it felt like they had the machine to themselves. At the same time, batch job processing allowed work to be submitted as formal jobs written in Job Control Language, or JCL, queued up by the Job Entry Subsystem, and executed in an orderly, managed sequence. Output from those jobs was routed to a spool, a managed queue of printer and output data that could be reviewed, reprinted, or archived. That combination of interactive time-sharing and disciplined batch processing remains the heartbeat of mainframe computing to this day.

So why should anyone bother learning about them today? Because understanding mainframes gives you a genuine appreciation for how enterprise computing actually works under the hood. Concepts like batch job processing, spooled printer output, dataset management, and job control language were all mainframe innovations that shaped the computing world we live in. PY360 is a lighthearted attempt to bring that experience to anyone curious enough to try it — Big Iron from the comfort of your own desk.

---
<img width="1003" height="549" alt="Screenshot 2026-06-09 235534" src="https://github.com/user-attachments/assets/14e0a2da-aab6-4900-9409-07d3373e4c95" />

## Some Key Concepts Before You Get Started

MFT Operating System (Multiprogramming with a Fixed number of Tasks): This was a variant of OS/360 designed for smaller System/360 models. It divided memory into fixed-size partitions, allowing several programs to reside in memory simultaneously. Historical guides detail MFT configuration and how operators managed jobs and I/O within these environments.  PY/360's look and feel is based on it's reduced feature-set of MFT.

TSO (Time Sharing Option): Using 3270-type CRT terminals, this became the standard interactive facility for IBM mainframes. It functions similarly to a command-line interface and can use ISPF menus, allowing users to interact with the system in real-time rather than purely through batch processing.  

ISPF (Interactive System Productivity Facility): Although text-based, this is similar to a PC's "graphical UI," ISPF is a menu-based environment built on top of TSO. It includes essential tools such as a text editor, file browsers, and utilities for allocating data sets. It's roots lie in enhancing productivity for system programmers and developers on older mainframe architectures.  

## The Hardware of a Very Simple S/360 System

To understand how a mainframe environment works, it helps to picture the physical hardware that made it up. At the heart of everything was the Central Processing Unit — a large cabinet-sized unit that housed the processor, main memory, and the channel controllers that managed communication with all attached devices. Unlike a modern PC where the processor does much of the I/O work itself, the S/360 offloaded input and output operations to dedicated hardware channels, freeing the CPU to focus on computation.

Attached to the CPU were a carefully chosen collection of peripheral devices. Primary among them was the **DASD** — Direct Access Storage Device — the mainframe's equivalent of a hard drive, though the resemblance ends there. Early disk storage units like the iconic IBM 2311 were large, washing machine-sized devices storing data on spinning magnetic disk platters. Unlike tape, a disk drive, often refered to as a Direct-Access Storage Drive (DASD) allowed any record to be read or written directly without reading through everything before it, like tape required.

For output, the **IBM 1403 chain printer** was the output workhorse of the data center. Capable of printing at speeds of up to 1,100 lines per minute, the 1403 produced the familiar wide greenbar paper reports that became synonymous with mainframe computing. Its distinctive chattering sound was the soundtrack of countless data centers.

Finally, tying the human operator to all of this machinery was the **IBM 3270 terminal** — a sleek, green-phosphor display device that connected to the mainframe over coaxial cable. The 3270 was a pure display terminal, sending keystrokes to the mainframe and receiving screen updates in return. It was through the 3270 that operators managed the system, users ran their Time-Share Option (TSO) sessions, and ISPF presented its now legendary full-screen panels.

PY/360 simulates these components in software, running entirely on a standard Windows 10/11 PC.

---

## Features

- **Authentic 3270-style terminal** — Custom tkinter window with green phosphor display, OIA status line, and period-correct fonts
- **IPL boot sequence** — Type `IPL 201` to initiate system startup with real host hardware interrogation via Python's psutil and WMI packages
- **TSO/ISPF simulation** — Full primary option menu with system information panel
- **ISPF-style editor** — Full screen editor with line commands (D, I, R, C, M, A, B) and primary commands (FIND, CHANGE, SAVE)
- **ISPF browse** — Read-only dataset viewer with search and scroll
- **Dataset management** — Catalog-based dataset system with LISTCAT, ALLOCATE, DELETE, RENAME, COPY, LISTDS
- **REXX interpreter** — Subset REXX with variables, loops, conditionals, and 20+ built-in functions
- **JCL interpreter** — JES2-style batch job submission with job log and condition codes
- **1403 Printer simulation** — Spool output with ASA carriage control and job headers
- **Spool viewer** — Browse, search and purge printer spool output
- **Help system** — Context-sensitive F1 help with full mainframe concept glossary
- **Sample library** — Pre-installed SYS.REXX and SYS.JCL sample datasets
- **User profiles** — Per-user JSON profiles with dataset prefix and last login tracking
- **Security model** — User prefix isolation with read access to system datasets

---

## Screenshots
<img width="1201" height="762" alt="IPL" src="https://github.com/user-attachments/assets/42c3a724-6893-4051-adb3-3e25707c6f28" />
* PY360 IPL sequence showing real host hardware interrogation *  
  
<img width="1149" height="703" alt="logon" src="https://github.com/user-attachments/assets/2981f17c-1752-490d-8cea-8539f267a53c" />  
* 3270-style login screen *  
  
<img width="1149" height="703" alt="ISPS_menu" src="https://github.com/user-attachments/assets/823bde04-f830-4999-9dbd-502a3da981ea" />  
* ISPF Primary Option Menu with system information panel *  
  
<img width="1149" height="703" alt="editor" src="https://github.com/user-attachments/assets/1166d103-ce8d-41de-beef-c64ac1fad871" />  
* ISPF-style full screen editor *  
  
<img width="1149" height="703" alt="spool_prt_out" src="https://github.com/user-attachments/assets/5d5ef3f4-7378-4e15-8ecd-f9efda4cfea6" />  
* 1403 printer spool output viewer *  
  
---

## Requirements

- Windows 10 or Windows 11 (Sorry, no Linux for now)
- Python 3.10 or higher
- The following Python packages (see `requirements.txt`):

```
psutil
wmi
windows-curses
```

---

## Installation

1. **Clone the repository:** - Or just download the .zip file and unpack it anywhere you want
```
git clone https://github.com/ErnieTech101/py360.git
cd py360
```

2. **Install required packages:**
```
pip install -r requirements.txt
```

3. **Run PY360:**
```
python py360.py
```

That's it! On first run PY/360 will automatically create all required directories, install the sample library, and initialize the catalog. No additional configuration is needed.

---

## Quick Start

1. Run `python py360.py` from a Windows Command Prompt
2. At the blinking cursor, type `IPL 201` and press ENTER
3. Watch the IPL sequence initialize the system
4. The terminal window will open at the login screen
5. Enter any USERID (e.g. `JOHN01`) and press TAB - Any USERID that does not already exist will be created
6. Enter any PASSWORD and press ENTER - password security is not implemented for simplicity
7. You are now at the ISPF Primary Option Menu

**Try these first:**
- Type `1` to BROWSE — enter `SYS.REXX.*` to see sample programs
- Type `4` to FOREGROUND — enter `SYS.REXX.HELLO` to run a REXX program
- Type `5` to BATCH — enter `SYS.JCL.HELLO` to submit a batch job
- Type `6` to SPOOL — view the printer output
- Press `F1` at any screen for context-sensitive help
- Type `HELP GLOSSARY` at any COMMAND ===> prompt for mainframe terminology

---

## Writing Your First REXX Program

1. From the menu select option `2` EDIT
2. Enter a dataset name like `USER.DAVE.MYFIRST`
3. Type YES to allocate the new dataset
4. Type your REXX program:

```rexx
/* My first PY360 REXX program */
SAY "Hello from PY360!"
SAY "Today is" DATE()

DO I = 1 TO 5
  SAY "Line" I
END

EXIT 0
```

5. Press F3 to save
6. Select option `4` FOREGROUND and enter your dataset name to run it

---

## Writing Your First JCL Job

1. Create a REXX program as above (e.g. `USER.DAVE.MYPROG`)
2. Select option `2` EDIT and create a JCL dataset (e.g. `USER.DAVE.MYJCL`)
3. Enter your JCL:

```jcl
//MYJOB   JOB (001),'YOUR NAME',CLASS=A,MSGCLASS=A
//* My first JCL job
//STEP1   EXEC PGM=REXXRUN
//SYSIN   DD DSN=USER.DAVE.MYPROG,DISP=SHR
//SYSOUT  DD SYSOUT=*
```

4. Press F3 to save
5. Select option `5` BATCH and enter your JCL dataset name
6. View the job log and then check option `6` SPOOL for output

---

## Project Structure

```
py360/
├── py360.py          # Master bootstrap and boot sequence
├── config.py         # IPL sequence and system configuration
├── terminal.py       # 3270-style tkinter terminal engine
├── logo.py           # Login screen
├── menu.py           # ISPF primary option menu
├── editor.py         # ISPF-style full screen editor
├── browse.py         # Dataset browser
├── utilities.py      # Dataset utility functions
├── spool.py          # Spool viewer and 1403 printer simulation
├── jcl.py            # JCL interpreter and JES2 simulation
├── rexx.py           # REXX interpreter
├── catalog.py        # Dataset catalog management
├── samples.py        # Sample library installer
├── help.py           # Help system
├── PY360.cfg         # System configuration file
├── requirements.txt  # Python dependencies
└── help/             # Help text files
    ├── main.txt
    ├── menu.txt
    ├── editor.txt
    ├── browse.txt
    ├── util.txt
    ├── catalog.txt
    ├── jcl.txt
    ├── rexx.txt
    ├── spool.txt
    ├── login.txt
    └── glossary.txt
```

*The following directories are created automatically at runtime:*
- `datasets/` — Simulated DASD storage
- `spool/` — Printer and punch output
- `users/` — User profile JSON files

---

## REXX Language Support

PY/360 includes a REXX interpreter supporting:

| Feature | Details |
|---------|---------|
| Variables | Simple assignment, string and numeric |
| Output | SAY statement |
| Input | PULL, PARSE PULL |
| Conditionals | IF/THEN/ELSE (inline and multiline) |
| Loops | DO/END, DO i=1 TO n, DO WHILE, DO UNTIL, DO FOREVER |
| Branching | SIGNAL (GOTO), CALL/RETURN |
| String functions | LENGTH, SUBSTR, STRIP, UPPER, LOWER, LEFT, RIGHT, CENTER, COPIES, REVERSE, WORDS, WORD, POS, SPACE |
| Math functions | ABS, MAX, MIN, SIGN, TRUNC, FORMAT |
| System functions | DATE, TIME, DATATYPE |
| Comments | /* */ inline and multiline |

---

## JCL Support

PY360 supports a practical JCL subset:

| Statement | Support |
|-----------|---------|
| JOB | jobname, CLASS, MSGCLASS |
| EXEC | PGM=REXXRUN, PGM=IEFBR14 |
| DD | DSN=, DISP=SHR/OLD/NEW, SYSOUT=* |
| Comments | //* |

---

## Keyboard Reference

| Key | Function |
|-----|----------|
| F1 | Context-sensitive HELP |
| F3 | Save and exit / Exit screen |
| F4 | Exit without saving |
| F7 / PgUp | Scroll up |
| F8 / PgDn | Scroll down |
| TAB | Cycle between fields (editor) |
| ENTER | Execute command |

---

## Known Limitations

- Windows only (uses tkinter, WMI, and windows-curses)
- Single user environment
- REXX subset only — not full IBM REXX compliance
- JCL subset only — one step jobs, REXXRUN and IEFBR14 programs
- No PDS member support (planned)
- No VSAM support (planned)

---

## Roadmap

- PDS member support (`USER.DAVE.SOURCE(MYPROG)`)
- SORT utility
- Multi-step JCL condition code testing
- ISPF settings panel
- Extended REXX built-in functions
- VSAM file simulation
- Additional sample programs

---

## Acknowledgements

PY360 was developed in collaboration with **Claude** (claude.ai), Anthropic's AI assistant. This project represents an extended pair-programming session where Claude contributed substantially to the architecture and code throughout the development process.

The author believes in transparency about AI collaboration in software development. Rather than presenting AI-assisted work as purely human-authored, this project acknowledges that the boundaries between human creativity and AI assistance are increasingly intertwined — and that's something worth celebrating rather than obscuring. 

**ErnieTech's Human contributions:**
- Project concept, vision and direction
- Mainframe domain expertise and authenticity guidance
- Design decisions, feature priorities and future vision
- Testing, debugging feedback and quality control
- Documentation and help text with Claude's accuracy and consistency checking
- The enthusiasm that kept the project moving! 😄

**Claude's contributions:**
- Architecture design and module structure
- Python implementation across all modules
- Problem solving and debugging
- Assistance with documentation and help text
- General coding partnership

If you find PY360 useful, consider exploring what's possible with AI-assisted development at [claude.ai](https://claude.ai) and supporting [Anthropic's mission](https://www.anthropic.com) to develop AI safely and beneficially.

---

## License

MIT License — feel free to use, modify and distribute PY360. If you build something cool with it, let us know!

---

## Contributing

Contributions welcome! Whether you're a mainframe veteran who wants to improve authenticity, or a Python developer who wants to add features, feel free to open an issue or submit a pull request.

If you find a bug or have a feature request, please open an issue on GitHub.

---

*PY360 — Big Iron from the comfort of your own desk.* 🖥️

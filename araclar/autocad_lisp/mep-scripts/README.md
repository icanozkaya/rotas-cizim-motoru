MEP-AUTOCAD-Scripts

A collection of AutoLISP scripts developed to streamline common MEP drafting tasks in AutoCAD. This includes automatic device tagging, sprinkler layout generation, and length calculation with customizable parameters.

📁 Scripts Included
1. TagDevices.lsp – Auto Device Tagger

Automates the process of tagging MEP devices in AutoCAD.

🔧 Features:

Automatically detects block name (e.g., SD, MD, HD, etc.).

Inserts MTEXT tags under each selected device.

Tag format: Loop/DeviceType-Number-Floor (e.g., L1/SD-1-GF)

Supports:

Custom loop (L1, L2, etc.)

Custom floor (GF, 1F, etc.)

Auto-incrementing device numbers

Manual reset of counter (ResetTagCount)

Remembers last used loop and floor for ease of use.

Skipped or previously tagged devices don’t break numbering.

📌 Usage:

Load the script with APPLOAD.

Type TagDevices in the command line.

Select blocks → Tags will be placed below each block.

2. SprinklerLayout.lsp – Auto Sprinkler Layout

Auto-generates sprinkler layout grids based on user-defined dimensions and spacing.

🔧 Features:

Accepts custom area dimensions (length, width).

Accepts custom spacing (X and Y direction).

Automatically inserts Sprinkler blocks in grid.

User provides reference point inside the drawing, blocks are inserted relative to it (suggested 5ft by 5ft margin from top).

Ensures correct spacing between each block.

📌 Usage:

Load the script with APPLOAD.

Type SprinklerLayout in the command line.

Enter:

Length of the area

Width of the area

Horizontal and vertical spacing

Click on the insertion point inside drawing for grid reference.

Sprinkler blocks will be inserted accordingly.

3. TotLen.lsp – Total Length Calculator

Calculates the total length of selected polylines or lines in the drawing.

🔧 Features:

Works for multiple selected entities.

Shows total length in current drawing units.

Displays a summary including unit type (e.g., mm, m, ft, inch).

Can be used for piping, ducting, or cable routing measurement.

📌 Usage:

1.Load the script with APPLOAD.

2.Select the lines/polylines to measure.

3.Type TotLen in the command line.

The total length will be displayed in the command line and optionally as a message box.

📘 Requirements

AutoCAD 2020 or later (tested)

AutoLISP support

🚀 Getting Started

Open AutoCAD

Load .lsp files using APPLOAD

Run the commands:

TagDevices for tagging

ResetTagCount to reset count

SprinklerLayout for layout generation

TotLen for total length calculation

🧠 Author

MD Hassin Arman Nihal
Intern MEP Engineer | AutoCAD Automation Enthusiast

📝 License

Free to use and modify.
